"""Small fail-closed HTTP boundary for governed interface operations."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from geoagent_harness.recipe_catalog import (
    RecipeTemplateCatalogError,
    load_recipe_template_catalog,
)
from geoagent_harness.recipe_proposals import (
    RecipeCompilationError,
    RecipeProposal,
    compile_recipe_proposal,
)
from geoagent_harness.skill_registry import (
    SkillRegistryError,
    load_skill_registry,
)
from geoagent_harness.redaction import redact_text, redact_value
from geoagent_harness.context_pack import ContextPackError
from geoagent_harness.critic.evidence import (
    CriticEvidenceError,
    build_critic_evidence,
)
from geoagent_harness.critic.recipe_trace import (
    RecipeTraceAdapterError,
    build_recipe_trace_candidate,
    persist_recipe_trace_candidate,
    recipe_trace_sha256,
    render_recipe_trace_report,
)
from geoagent_harness.critic import (
    CriticAgentError,
    CriticResult,
    CriticResultRecordError,
    CriticResultStorageError,
    build_critic_result_record,
    critique_task,
    critic_result_sha256,
    persist_critic_result_record,
)
from geoagent_harness.trace import WorkflowTrace
from geoagent_harness.model import ModelClientError, ModelSettingsError
from geoagent_harness.planner import (
    PlannerAgentError,
    PlannerPolicyError,
    PlannerResult,
    validate_plan_policy,
)
from geoagent_harness.executor import ExecutorPolicyError, build_execution_envelope
from geoagent_harness.approvals import (
    ApprovalError,
    create_approval,
    load_approval,
    load_planner_result,
    plan_sha256,
    verify_approval,
)
from geoagent_harness.mcp_server.approved_recipe import (
    ApprovedRecipeError,
    run_approved_recipe as execute_approved_recipe,
)
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.recipes import (
    RecipeApprovalError,
    RecipeEvidenceStorageError,
    RecipePolicyError,
    RecipeStorageError,
    load_recipe,
    load_recipe_evidence,
    recipe_evidence_sha256,
    recipe_path,
    recipe_sha256,
    save_recipe,
    validate_recipe_policy,
    create_recipe_approval,
    load_recipe_approval,
    verify_recipe_approval,
    build_recipe_execution_envelope,
)
from geoagent_harness.recipes.schemas import RecipeStep, WorkflowRecipe


MAX_INTERFACE_REQUEST_BYTES = 65_536
MAX_INTERFACE_RECIPES = 200
MAX_INTERFACE_PLANS = 200
MAX_INTERFACE_PLAN_APPROVALS = 500
MAX_INTERFACE_EXECUTION_ATTEMPTS = 200
SAFE_RECIPE_FILENAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$"
)
LOOPBACK_HOST = "127.0.0.1"
_EXECUTION_LOCK = Lock()
_ACTIVE_EXECUTIONS: set[tuple[str, str]] = set()
_ACTIVE_PROGRESS: set[str] = set()
_EXECUTION_PROGRESS: dict[str, dict[str, Any]] = {}
MAX_INTERFACE_OUTCOME_BYTES = 16_384
MAX_INTERFACE_DATA_RESOURCES = 500
MAX_INTERFACE_CRITIC_EVIDENCE = 200
INTERFACE_DATA_EXTENSIONS = {
    ".csv", ".geojson", ".gpkg", ".json", ".kml", ".parquet",
    ".shp", ".tif", ".tiff", ".tsv",
}


def _progress_path(
    project_root: Path,
    digest: str,
    *,
    progress_root: Path | None = None,
) -> Path:
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise InterfaceApiError("execution progress digest is invalid")
    root = (
        progress_root
        if progress_root is not None
        else _trusted_root(project_root) / "workflow-state" / "interface-executions"
    )
    if root.exists() and root.is_symlink():
        raise InterfaceApiError("execution progress root cannot be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    resolved = root.resolve(strict=True)
    if resolved.parent.is_symlink():
        raise InterfaceApiError("execution progress parent cannot be a symlink")
    return resolved / f"{digest}.json"


def _persist_execution_progress(
    project_root: Path,
    state: dict[str, Any],
    *,
    progress_root: Path | None = None,
) -> None:
    digest = str(state["execution_preview_sha256"])
    destination = _progress_path(project_root, digest, progress_root=progress_root)
    content = json.dumps(state, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{digest}.",
        suffix=".tmp",
        dir=destination.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _load_execution_progress(
    project_root: Path,
    digest: str,
    *,
    progress_root: Path | None = None,
) -> dict[str, Any] | None:
    path = _progress_path(project_root, digest, progress_root=progress_root)
    if not path.exists():
        return None
    if path.is_symlink() or path.resolve().parent != path.parent.resolve():
        raise InterfaceApiError("execution progress artifact is unsafe")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("execution_preview_sha256") != digest:
        raise InterfaceApiError("execution progress artifact is invalid")
    if payload.get("status") == "running" and digest not in _ACTIVE_PROGRESS:
        payload["status"] = "interrupted"
        payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        payload["interruption_detected"] = True
        payload["recovery_guidance"] = (
            "Execution was interrupted. Inspect outputs and durable evidence; "
            "use a fresh target and new approval before retrying any write step."
        )
        for step in payload.get("steps", []):
            if isinstance(step, dict) and step.get("status") == "running":
                step["status"] = "interrupted"
                payload["failed_step_id"] = step.get("step_id")
        _persist_execution_progress(
            project_root,
            payload,
            progress_root=progress_root,
        )
    return payload


def interface_execution_inventory(
    project_root: Path,
    *,
    progress_root: Path | None = None,
) -> dict[str, Any]:
    """Return bounded durable attempt summaries without execution authority."""

    root = (
        progress_root
        if progress_root is not None
        else _trusted_root(project_root) / "workflow-state" / "interface-executions"
    )
    if not root.exists():
        return {
            "schema_version": "1.0",
            "attempts": [],
            "attempt_count": 0,
            "inventory_truncated": False,
            "execution_performed": False,
        }
    if root.is_symlink() or not root.is_dir():
        raise InterfaceApiError("execution progress root is unsafe")
    paths = sorted(
        root.glob("*.json"),
        key=lambda candidate: candidate.lstat().st_mtime,
        reverse=True,
    )
    truncated = len(paths) > MAX_INTERFACE_EXECUTION_ATTEMPTS
    attempts = []
    for path in paths[:MAX_INTERFACE_EXECUTION_ATTEMPTS]:
        if path.is_symlink() or not re.fullmatch(r"[a-f0-9]{64}\.json", path.name):
            raise InterfaceApiError("execution progress artifact is unsafe")
        digest = path.stem
        state = _load_execution_progress(
            project_root,
            digest,
            progress_root=root,
        )
        if state is None:
            continue
        attempts.append({
            "execution_preview_sha256": digest,
            "status": state.get("status"),
            "recipe_id": state.get("recipe_id"),
            "recipe_filename": state.get("recipe_filename"),
            "recipe_sha256": state.get("recipe_sha256"),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "failed_step_id": state.get("failed_step_id"),
            "interruption_detected": bool(state.get("interruption_detected", False)),
            "step_count": len(state.get("steps", [])),
        })
    return {
        "schema_version": "1.0",
        "attempts": attempts,
        "attempt_count": len(attempts),
        "inventory_truncated": truncated,
        "execution_performed": False,
    }


def _bounded_outcome(value: object) -> object:
    """Return a redacted bounded result projection for interface inspection."""

    projected = redact_value(value)
    encoded = json.dumps(projected, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    if len(encoded) > MAX_INTERFACE_OUTCOME_BYTES:
        return {
            "outcome_available": True,
            "projection_truncated": True,
            "message": "Outcome is too large for the interface projection; inspect durable evidence.",
        }
    return projected


class InterfaceApiError(RuntimeError):
    """Raised when the bounded interface API cannot fulfill a request."""


class InterfaceApprovalDecision(BaseModel):
    """Exact human decision accepted by the local interface boundary."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["record_recipe_approval"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    valid_for_minutes: int | None = Field(default=None, ge=1, le=1440)


class InterfaceApprovalVerificationRequest(BaseModel):
    """Exact recorded decision selected for independent verification."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["verify_recipe_approval"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")


class InterfaceExecutionPreviewRequest(BaseModel):
    """Exact verified artifacts selected for a non-executing preview."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["prepare_execution_preview"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")


class InterfaceRecipeExecutionRequest(BaseModel):
    """One explicit confirmation of an exact previewed execution."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["execute_exact_preview"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")
    confirmed_execution_preview_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: Literal["execute_exact_preview"]


class InterfacePlanRequest(BaseModel):
    """One bounded natural-language request for the existing planner agent."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["plan_task"]
    request: str = Field(min_length=1, max_length=8000)
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=20)
    input_paths: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("allowed_skill_ids")
    @classmethod
    def skill_ids_are_unique_and_safe(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("allowed skill IDs must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in value):
            raise ValueError("allowed skill ID is invalid")
        return value

    @field_validator("input_paths")
    @classmethod
    def input_paths_are_bounded(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("input paths must be unique")
        if any(
            not re.fullmatch(r"data/input/[A-Za-z0-9._/-]+", item)
            or ".." in item.split("/")
            for item in value
        ):
            raise ValueError("input path is outside the governed input root")
        return value


class InterfaceReviewedPlanSaveRequest(BaseModel):
    """Exact validated Planner result selected for immutable storage."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["save_reviewed_plan"]
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=20)
    planner_result: PlannerResult

    @field_validator("allowed_skill_ids")
    @classmethod
    def skill_ids_are_unique_and_safe(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("allowed skill IDs must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in value):
            raise ValueError("allowed skill ID is invalid")
        return value


class InterfacePlanApprovalPreparationRequest(BaseModel):
    """Exact immutable plan selected for non-writing approval preparation."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["prepare_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfacePlanApprovalDecisionRequest(BaseModel):
    """One explicit human decision bound to an exact prepared plan request."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["record_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    valid_for_minutes: int | None = Field(default=None, ge=1, le=1440)


class InterfacePlanApprovalVerificationRequest(BaseModel):
    """Exact recorded plan decision selected for independent verification."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["verify_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}\.json$")


class InterfacePlanExecutionPreviewRequest(InterfacePlanApprovalVerificationRequest):
    """Exact verified evidence selected for non-executing envelope preview."""

    action: Literal["preview_plan_execution"]


class InterfacePlanRecipeCompilationRequest(InterfacePlanApprovalVerificationRequest):
    """Exact verified plan selected for non-writing recipe compilation."""

    action: Literal["compile_plan_recipe"]


class InterfacePlanRecipeSaveRequest(InterfacePlanApprovalVerificationRequest):
    """Exact reviewed Planner-derived recipe selected for immutable storage."""

    action: Literal["save_reviewed_plan_recipe"]
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceRecipeTraceSaveRequest(BaseModel):
    """Exact adapted trace explicitly reviewed for immutable persistence."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["save_adapted_recipe_trace"]
    evidence_name: str = Field(
        pattern=r"^[a-z0-9][a-z0-9_-]{0,100}\.[a-f0-9]{64}\.json$"
    )
    confirmed_trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceCriticRunRequest(BaseModel):
    """Exact stored evidence selected for one in-memory Critic assessment."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["run_critic"]
    trace_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.json$")
    report_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.md$")
    confirmed_trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceCriticRecordRequest(InterfaceCriticRunRequest):
    """Exact validated Critic result selected for immutable recording."""

    action: Literal["record_critic_result"]
    confirmed_critic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result: CriticResult


def _trusted_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceApiError("trusted project root is unavailable") from exc
    if not resolved.is_dir():
        raise InterfaceApiError("trusted project root must be a directory")
    return resolved


def interface_data_resource_inventory(project_root: Path) -> dict[str, Any]:
    """List bounded project inputs and existing output directories read-only."""

    root = _trusted_root(project_root)
    input_root = root / "data" / "input"
    output_root = root / "data" / "output"
    inputs: list[dict[str, Any]] = []
    output_directories = ["data/output"]

    if input_root.is_symlink() or output_root.is_symlink():
        raise InterfaceApiError("data roots cannot be symlinks")
    if input_root.is_dir():
        for path in sorted(input_root.rglob("*")):
            if path.is_symlink():
                continue
            if not path.is_file() or path.suffix.lower() not in INTERFACE_DATA_EXTENSIONS:
                continue
            inputs.append({
                "path": path.relative_to(root).as_posix(),
                "name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            })
            if len(inputs) > MAX_INTERFACE_DATA_RESOURCES:
                raise InterfaceApiError("input data inventory exceeds its limit")
    if output_root.is_dir():
        for path in sorted(output_root.rglob("*")):
            if path.is_symlink() or not path.is_dir():
                continue
            output_directories.append(path.relative_to(root).as_posix())
            if len(output_directories) > MAX_INTERFACE_DATA_RESOURCES:
                raise InterfaceApiError("output directory inventory exceeds its limit")

    return {
        "schema_version": "1.0",
        "status": "inspected",
        "inputs": inputs,
        "output_directories": output_directories,
        "input_count": len(inputs),
        "inventory_performed": True,
        "files_modified": False,
        "execution_performed": False,
    }


def interface_critic_evidence_inventory(project_root: Path) -> dict[str, Any]:
    """Inspect trace/report pairs through the existing deterministic Critic boundary."""

    root = _trusted_root(project_root)
    trace_root = root / "traces"
    report_root = root / "reports"
    items: list[dict[str, Any]] = []
    truncated = False

    if trace_root.exists() and trace_root.is_symlink():
        raise InterfaceApiError("trace root cannot be a symlink")
    if report_root.exists() and report_root.is_symlink():
        raise InterfaceApiError("report root cannot be a symlink")

    trace_paths = sorted(trace_root.glob("*.json")) if trace_root.is_dir() else []
    if len(trace_paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        trace_paths = trace_paths[:MAX_INTERFACE_CRITIC_EVIDENCE]
        truncated = True

    for trace_path in trace_paths:
        if trace_path.is_symlink() or not trace_path.is_file():
            continue
        report_path = report_root / f"{trace_path.stem}.md"
        if report_path.is_symlink() or not report_path.is_file():
            items.append({
                "trace_name": trace_path.name,
                "report_name": None,
                "available": False,
                "finding": "matching Markdown report is unavailable",
                "evidence": None,
            })
            continue
        try:
            pack = build_critic_evidence(
                trace_path=trace_path,
                report_path=report_path,
                trace_root=trace_root,
                report_root=report_root,
            )
        except (CriticEvidenceError, OSError, ValueError):
            items.append({
                "trace_name": trace_path.name,
                "report_name": report_path.name,
                "available": False,
                "finding": "trace and report did not pass deterministic Critic evidence checks",
                "evidence": None,
            })
            continue
        items.append({
            "trace_name": trace_path.name,
            "report_name": report_path.name,
            "available": True,
            "finding": None,
            "evidence": pack.model_dump(mode="json"),
        })

    recipe_candidates = _interface_recipe_trace_candidates(root)
    return {
        "schema_version": "1.0",
        "status": "inspected",
        "items": items,
        "item_count": len(items),
        "recipe_candidates": recipe_candidates,
        "recipe_candidate_count": len(recipe_candidates),
        "inventory_truncated": truncated,
        "critic_model_called": False,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def _interface_recipe_trace_candidates(root: Path) -> list[dict[str, Any]]:
    """Preview truthful recipe-run trace adaptations without writing artifacts."""

    evidence_root = root / "recipe-evidence"
    recipe_root = root / "workflow-recipes"
    approval_root = root / "approvals"
    progress_root = root / "workflow-state" / "interface-executions"
    for candidate_root in (evidence_root, recipe_root, approval_root, progress_root):
        if candidate_root.exists() and candidate_root.is_symlink():
            raise InterfaceApiError("recipe trace source root cannot be a symlink")
    paths = sorted(evidence_root.glob("*.json"), reverse=True) if evidence_root.is_dir() else []
    if len(paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        paths = paths[:MAX_INTERFACE_CRITIC_EVIDENCE]

    progress_records: list[tuple[Path, dict[str, Any]]] = []
    if progress_root.is_dir():
        for path in sorted(progress_root.glob("*.json")):
            if path.is_symlink() or path.stat().st_size > MAX_INTERFACE_OUTCOME_BYTES:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                progress_records.append((path, payload))

    results: list[dict[str, Any]] = []
    for evidence_path in paths:
        base = {
            "evidence_name": evidence_path.name,
            "adaptable": False,
            "finding": None,
            "trace": None,
            "trace_sha256": None,
            "critic_status": None,
            "critic_gaps": [],
            "stored": False,
            "files_modified": False,
        }
        try:
            if evidence_path.is_symlink():
                raise RecipeTraceAdapterError("recipe evidence cannot be a symlink")
            evidence = load_recipe_evidence(evidence_path, evidence_root=evidence_root)
            digest = recipe_evidence_sha256(evidence)
            recipe_path = recipe_root / f"{evidence.recipe_id}.{evidence.recipe_sha256}.json"
            approval_path = approval_root / f"{evidence.approval_id}.json"
            recipe = load_recipe(recipe_path, recipe_root=recipe_root)
            approval = load_recipe_approval(approval_path, approval_root=approval_root)
            progress_match = next((
                (path, payload) for path, payload in progress_records
                if payload.get("recipe_id") == evidence.recipe_id
                and payload.get("recipe_sha256") == evidence.recipe_sha256
                and payload.get("status") == evidence.final_status
            ), None)
            if progress_match is None:
                raise RecipeTraceAdapterError("matching durable interface execution timing is unavailable")
            progress_path, progress = progress_match
            references = [
                recipe_path.relative_to(root).as_posix(),
                approval_path.relative_to(root).as_posix(),
                evidence_path.relative_to(root).as_posix(),
                progress_path.relative_to(root).as_posix(),
            ]
            trace = build_recipe_trace_candidate(
                recipe=recipe,
                approval=approval,
                evidence=evidence,
                evidence_sha256=digest,
                progress=progress,
                context_references=references,
            )
            with tempfile.TemporaryDirectory(prefix="actioncharter-critic-preview-") as directory:
                preview_root = Path(directory)
                traces = preview_root / "traces"
                reports = preview_root / "reports"
                traces.mkdir()
                reports.mkdir()
                trace_path = traces / f"{trace.task_id}.json"
                report_path = reports / f"{trace.task_id}.md"
                trace_path.write_text(trace.model_dump_json(indent=2) + "\n", encoding="utf-8")
                report_path.write_text(render_recipe_trace_report(trace), encoding="utf-8")
                pack = build_critic_evidence(
                    trace_path=trace_path,
                    report_path=report_path,
                    trace_root=traces,
                    report_root=reports,
                )
            base.update({
                "adaptable": True,
                "trace": trace.model_dump(mode="json"),
                "trace_sha256": recipe_trace_sha256(trace),
                "critic_status": pack.deterministic_status,
                "critic_gaps": pack.evidence_gaps,
                "stored": (
                    (root / "traces" / f"{trace.task_id}.json").is_file()
                    and (root / "reports" / f"{trace.task_id}.md").is_file()
                ),
            })
        except (
            RecipeTraceAdapterError,
            CriticEvidenceError,
            RecipePolicyError,
            RecipeStorageError,
            RecipeApprovalError,
            RecipeEvidenceStorageError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            base["finding"] = redact_text(str(exc))[:500]
        results.append(base)
    return results


def save_interface_recipe_trace(
    request: InterfaceRecipeTraceSaveRequest,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Rebuild and immutably store one exactly reviewed adapted trace."""

    root = _trusted_root(project_root)
    candidate = next(
        (
            item for item in _interface_recipe_trace_candidates(root)
            if item["evidence_name"] == request.evidence_name
        ),
        None,
    )
    if candidate is None or not candidate["adaptable"] or candidate["trace"] is None:
        raise InterfaceApiError("recipe evidence cannot enter the trace persistence boundary")
    trace = WorkflowTrace.model_validate(candidate["trace"])
    try:
        trace_path, report_path, trace_digest, report_digest = persist_recipe_trace_candidate(
            trace=trace,
            confirmed_trace_sha256=request.confirmed_trace_sha256,
            trace_root=root / "traces",
            report_root=root / "reports",
        )
    except RecipeTraceAdapterError as exc:
        raise InterfaceApiError(redact_text(str(exc))[:500]) from exc
    pack = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=root / "traces",
        report_root=root / "reports",
    )
    return {
        "schema_version": "1.0",
        "status": "stored",
        "task_id": trace.task_id,
        "trace_sha256": trace_digest,
        "report_sha256": report_digest,
        "trace_path": trace_path.relative_to(root).as_posix(),
        "report_path": report_path.relative_to(root).as_posix(),
        "critic_status": pack.deterministic_status,
        "critic_gaps": pack.evidence_gaps,
        "trace_stored": True,
        "report_stored": True,
        "critic_model_called": False,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def run_interface_critic(
    request: InterfaceCriticRunRequest,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Run one schema-constrained Critic assessment without persisting it."""

    root = _trusted_root(project_root)
    trace_root = root / "traces"
    report_root = root / "reports"
    trace_path = trace_root / request.trace_name
    report_path = report_root / request.report_name
    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )
    references = {Path(item.path).name: item.sha256 for item in evidence.evidence_references}
    if references.get(request.trace_name) != request.confirmed_trace_sha256:
        raise InterfaceApiError("reviewed trace digest no longer matches")
    if references.get(request.report_name) != request.confirmed_report_sha256:
        raise InterfaceApiError("reviewed report digest no longer matches")
    result = critique_task(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
        agents_root=root / "agents",
    )
    return {
        "schema_version": "1.0",
        "status": "assessed_not_recorded",
        "critic_result_sha256": critic_result_sha256(result),
        "result": result.model_dump(mode="json"),
        "critic_model_called": True,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def record_interface_critic_result(
    request: InterfaceCriticRecordRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reverify evidence and immutably record one exact Critic result."""

    root = _trusted_root(project_root)
    trace_root = root / "traces"
    report_root = root / "reports"
    evidence = build_critic_evidence(
        trace_path=trace_root / request.trace_name,
        report_path=report_root / request.report_name,
        trace_root=trace_root,
        report_root=report_root,
    )
    references = {Path(item.path).name: item.sha256 for item in evidence.evidence_references}
    if references.get(request.trace_name) != request.confirmed_trace_sha256:
        raise InterfaceApiError("reviewed trace digest no longer matches")
    if references.get(request.report_name) != request.confirmed_report_sha256:
        raise InterfaceApiError("reviewed report digest no longer matches")
    result = request.result
    if critic_result_sha256(result) != request.confirmed_critic_result_sha256:
        raise InterfaceApiError("reviewed Critic-result digest no longer matches")
    if (
        result.task_id != evidence.task_id
        or result.deterministic_status != evidence.deterministic_status
        or result.evidence_references != evidence.evidence_references
        or result.evidence_gaps != evidence.evidence_gaps
        or result.workflow_warnings != evidence.warnings
        or result.human_corrections != evidence.human_corrections
    ):
        raise InterfaceApiError("Critic result no longer matches deterministic evidence")
    record = build_critic_result_record(
        result=result,
        recorded_at=now or datetime.now(timezone.utc),
    )
    stored = persist_critic_result_record(
        record,
        record_root=root / "critic-results",
    )
    record_directory = Path(stored.record_directory).relative_to(root).as_posix()
    record_file = Path(stored.record_file).relative_to(root).as_posix()
    return {
        **stored.model_dump(mode="json"),
        "status": "recorded",
        "record_directory": record_directory,
        "record_file": record_file,
        "critic_model_called": False,
        "critic_result_recorded": True,
        "release_created": False,
        "execution_performed": False,
    }


def interface_recipe_template_catalog(project_root: Path) -> dict[str, Any]:
    """Return the same validated non-executing catalog projection as the CLI."""

    catalog = load_recipe_template_catalog(_trusted_root(project_root))
    optional_by_profile = {
        "vector_inspection": ["source_layer"],
        "raster_inspection": [],
        "raster_conversion": ["resampling"],
        "vector_conversion": ["source_layer", "target_layer", "target_format"],
        "vector_postgis": ["source_layer"],
    }
    return {
        "schema_version": catalog.schema_version,
        "templates": [
            {
                **template.model_dump(mode="json"),
                "optional_parameters": optional_by_profile[template.parameter_profile],
                "parameter_roots": {
                    name: root
                    for name, root in (
                        ("path", "data/input"),
                        ("target_path", "data/output"),
                    )
                    if name in template.required_parameters
                },
            }
            for template in catalog.templates
        ],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }


def _normalize_interface_recipe_paths(payload: object) -> object:
    """Expand filename-only interface parameters into governed data roots.

    Explicit relative and absolute paths remain unchanged so the existing
    compiler and execution policies retain final authority over them.
    """

    if not isinstance(payload, dict):
        return payload
    selection = payload.get("selection")
    if not isinstance(selection, dict):
        return payload
    parameters = selection.get("parameters")
    if not isinstance(parameters, dict):
        return payload

    normalized_parameters = dict(parameters)
    for name, root in (("path", "data/input"), ("target_path", "data/output")):
        value = normalized_parameters.get(name)
        if (
            isinstance(value, str)
            and value
            and "/" not in value
            and "\\" not in value
            and value not in {".", ".."}
        ):
            normalized_parameters[name] = f"{root}/{value}"

    return {
        **payload,
        "selection": {
            **selection,
            "parameters": normalized_parameters,
        },
    }


def plan_interface_task(
    request: InterfacePlanRequest,
    *,
    project_root: Path,
    agents_root: Path | None = None,
) -> dict[str, Any]:
    """Call the existing planner without persistence, approval, or execution."""

    from geoagent_harness.planner import plan_task

    root = _trusted_root(project_root)
    trusted_agents = agents_root if agents_root is not None else root / "agents"
    selected_context = ""
    if request.input_paths:
        selected_context = "\n\nOperator-selected governed input references:\n" + "\n".join(
            f"- {path}" for path in request.input_paths
        )
    result = plan_task(
        original_request=request.request + selected_context,
        project_root=root,
        agents_root=trusted_agents,
        allowed_skill_ids=request.allowed_skill_ids,
    )
    return {
        "schema_version": "1.0",
        "status": "planned_not_saved",
        "agent_id": result.agent_id,
        "model": result.model,
        "original_request": request.request,
        "allowed_skill_ids": request.allowed_skill_ids,
        "context_references": [*result.context_references, *request.input_paths],
        "plan": result.plan.model_dump(mode="json"),
        "plan_sha256": plan_sha256(result.plan),
        "warnings": result.warnings,
        "plan_saved": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def save_interface_reviewed_plan(
    request: InterfaceReviewedPlanSaveRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
) -> dict[str, Any]:
    """Revalidate and immutably store one exact reviewed Planner result."""

    root = _trusted_root(project_root)
    registry = load_skill_registry(root)
    implemented = {skill.id for skill in registry.implemented_skills()}
    selected = set(request.allowed_skill_ids)
    if not selected.issubset(implemented):
        raise InterfaceApiError("reviewed plan includes an unavailable skill selection")
    validate_plan_policy(request.planner_result.plan, available_skills=selected)
    digest = plan_sha256(request.planner_result.plan)
    if digest != request.confirmed_plan_sha256:
        raise InterfaceApiError("reviewed plan digest no longer matches")

    destination = plan_root if plan_root is not None else root / "plans"
    if destination.exists() and destination.is_symlink():
        raise InterfaceApiError("plan root cannot be a symlink")
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or not destination.is_dir():
        raise InterfaceApiError("plan root is unsafe")
    resolved_destination = destination.resolve(strict=True)
    if plan_root is None and resolved_destination.parent != root:
        raise InterfaceApiError("plan root is outside the trusted project")

    filename = f"planner-plan.{digest}.json"
    path = resolved_destination / filename
    content = request.planner_result.model_dump_json(indent=2) + "\n"
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise InterfaceApiError("existing reviewed plan artifact is unsafe")
        try:
            existing = load_planner_result(
                path=path,
                plan_root=resolved_destination,
            )
        except ApprovalError as exc:
            raise InterfaceApiError("existing reviewed plan artifact is invalid") from exc
        if existing != request.planner_result:
            raise InterfaceApiError("existing reviewed plan does not match exact result")
        return {
            "schema_version": "1.0",
            "status": "already_stored",
            "plan_sha256": digest,
            "plan_filename": filename,
            "plan_saved": True,
            "plan_modified": False,
            "approval_performed": False,
            "execution_performed": False,
        }
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise InterfaceApiError("reviewed plan already exists") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise

    return {
        "schema_version": "1.0",
        "status": "stored",
        "plan_sha256": digest,
        "plan_filename": filename,
        "plan_saved": True,
        "plan_modified": True,
        "approval_performed": False,
        "execution_performed": False,
    }


def prepare_interface_plan_approval(
    request: InterfacePlanApprovalPreparationRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare exact plan approval scope without recording a decision."""

    root = _trusted_root(project_root)
    destination = plan_root if plan_root is not None else root / "plans"
    if destination.is_symlink() or not destination.is_dir():
        raise InterfaceApiError("plan root is unsafe or unavailable")
    resolved_destination = destination.resolve(strict=True)
    path = resolved_destination / request.plan_filename
    if path.is_symlink() or path.parent != resolved_destination:
        raise InterfaceApiError("plan artifact is unsafe")
    try:
        planner_result = load_planner_result(path=path, plan_root=resolved_destination)
    except ApprovalError as exc:
        raise InterfaceApiError("stored plan is unavailable or invalid") from exc
    digest = plan_sha256(planner_result.plan)
    if digest != request.confirmed_plan_sha256:
        raise InterfaceApiError("stored plan digest no longer matches")
    implemented = {
        skill.id for skill in load_skill_registry(root).implemented_skills()
    }
    validate_plan_policy(planner_result.plan, available_skills=implemented)
    required = [
        step.step_id for step in planner_result.plan.steps if step.requires_approval
    ]
    basis = {
        "schema_version": "1.0",
        "plan_filename": request.plan_filename,
        "plan_sha256": digest,
        "approval_required_step_ids": required,
    }
    request_digest = hashlib.sha256(json.dumps(
        basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    return {
        **basis,
        "status": "prepared_not_recorded" if required else "approval_not_required",
        "approval_request_sha256": request_digest,
        "steps": [{
            "step_id": step.step_id,
            "skill": step.skill,
            "purpose": step.purpose,
            "arguments": redact_value(step.arguments),
            "requires_approval": step.requires_approval,
            "validation_required": step.validation_required,
        } for step in planner_result.plan.steps],
        "approval_recorded": False,
        "execution_performed": False,
    }


def record_interface_plan_approval(
    request: InterfacePlanApprovalDecisionRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append one exact plan decision without executing the plan."""

    preparation = prepare_interface_plan_approval(
        InterfacePlanApprovalPreparationRequest(
            action="prepare_plan_approval",
            plan_filename=request.plan_filename,
            confirmed_plan_sha256=request.confirmed_plan_sha256,
        ),
        project_root=project_root,
        plan_root=plan_root,
    )
    if preparation["approval_request_sha256"] != request.confirmed_approval_request_sha256:
        raise InterfaceApiError("plan approval request digest no longer matches")
    required = preparation["approval_required_step_ids"]
    if not required:
        raise InterfaceApiError("read-only plan does not require an approval record")

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else root / "plans"
    planner_result = load_planner_result(
        path=plans.resolve(strict=True) / request.plan_filename,
        plan_root=plans.resolve(strict=True),
    )
    approvals = approval_root if approval_root is not None else root / "approvals"
    if approvals.exists() and approvals.is_symlink():
        raise InterfaceApiError("approval root cannot be a symlink")
    active_now = now or datetime.now(timezone.utc)
    expires_at = (
        active_now + timedelta(minutes=request.valid_for_minutes)
        if request.valid_for_minutes is not None else None
    )
    try:
        record, path = create_approval(
            planner_result=planner_result,
            step_ids=required,
            decision=request.decision,
            approver=request.approver,
            reason=request.reason,
            approval_root=approvals,
            project_root=root,
            expires_at=expires_at,
            now=active_now,
        )
    except ApprovalError as exc:
        raise InterfaceApiError("plan approval could not be recorded") from exc
    return {
        "schema_version": "1.0",
        "status": "recorded",
        "decision": record.decision,
        "approval_id": record.approval_id,
        "approval_filename": path.name,
        "plan_sha256": record.plan_sha256,
        "approved_step_ids": record.step_ids if record.decision == "approved" else [],
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "secrets_redacted": record.secrets_redacted,
        "approval_recorded": True,
        "execution_performed": False,
    }


def verify_interface_plan_approval(
    request: InterfacePlanApprovalVerificationRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Independently verify immutable plan and decision evidence."""

    preparation = prepare_interface_plan_approval(
        InterfacePlanApprovalPreparationRequest(
            action="prepare_plan_approval",
            plan_filename=request.plan_filename,
            confirmed_plan_sha256=request.confirmed_plan_sha256,
        ),
        project_root=project_root,
        plan_root=plan_root,
    )
    if preparation["approval_request_sha256"] != request.confirmed_approval_request_sha256:
        raise InterfaceApiError("plan approval request digest no longer matches")
    required = preparation["approval_required_step_ids"]
    if not required:
        raise InterfaceApiError("read-only plan has no approval to verify")
    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else root / "plans"
    approvals = approval_root if approval_root is not None else root / "approvals"
    if approvals.is_symlink() or not approvals.is_dir():
        raise InterfaceApiError("approval root is unsafe or unavailable")
    resolved_approvals = approvals.resolve(strict=True)
    approval_path = resolved_approvals / request.approval_filename
    if approval_path.is_symlink() or approval_path.parent != resolved_approvals:
        raise InterfaceApiError("approval artifact is unsafe")
    try:
        planner_result = load_planner_result(
            path=plans.resolve(strict=True) / request.plan_filename,
            plan_root=plans.resolve(strict=True),
        )
        approval = load_approval(
            path=approval_path,
            approval_root=resolved_approvals,
        )
    except ApprovalError as exc:
        raise InterfaceApiError("plan approval evidence is unavailable or invalid") from exc
    verification = verify_approval(
        approval=approval,
        plan=planner_result.plan,
        required_step_ids=required,
        now=now,
    )
    return {
        "schema_version": "1.0",
        "status": "verified",
        "approved": verification.approved,
        "decision": approval.decision,
        "approval_id": approval.approval_id,
        "plan_sha256": verification.plan_sha256,
        "verified_step_ids": verification.approved_step_ids,
        "reason": verification.reason,
        "independent_verification_performed": True,
        "plan_modified": False,
        "approval_modified": False,
        "execution_performed": False,
    }


def preview_interface_plan_execution(
    request: InterfacePlanExecutionPreviewRequest,
    *, project_root: Path,
    plan_root: Path | None = None,
    approval_root: Path | None = None,
) -> dict[str, Any]:
    """Build the existing fixed execution envelope without executing it."""

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else root / "plans"
    approvals = approval_root if approval_root is not None else root / "approvals"
    verification = verify_interface_plan_approval(
        InterfacePlanApprovalVerificationRequest(
            action="verify_plan_approval",
            plan_filename=request.plan_filename,
            confirmed_plan_sha256=request.confirmed_plan_sha256,
            confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
            approval_filename=request.approval_filename,
        ), project_root=root, plan_root=plans, approval_root=approvals,
    )
    if not verification["approved"]:
        raise InterfaceApiError("verified plan authority does not permit execution preview")
    try:
        planner_result = load_planner_result(path=plans.resolve() / request.plan_filename, plan_root=plans.resolve())
        approval = load_approval(path=approvals.resolve() / request.approval_filename, approval_root=approvals.resolve())
        envelope = build_execution_envelope(
            planner_result=planner_result,
            approval=approval,
            allowed_schemas=load_settings().allowed_schemas,
        )
    except (ApprovalError, ExecutorPolicyError, ValueError) as exc:
        raise InterfaceApiError(f"plan cannot enter the supported execution envelope: {exc}") from exc
    payload = envelope.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema_version": "1.0", "status": "previewed_not_executed",
        "execution_preview_sha256": digest, "envelope": payload,
        "execution_available": False, "execution_performed": False,
    }


def compile_interface_plan_recipe(
    request: InterfacePlanRecipeCompilationRequest,
    *, project_root: Path,
    plan_root: Path | None = None,
    approval_root: Path | None = None,
) -> dict[str, Any]:
    """Compile verified Planner steps into a reviewed recipe candidate only."""

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else root / "plans"
    approvals = approval_root if approval_root is not None else root / "approvals"
    verified = verify_interface_plan_approval(
        InterfacePlanApprovalVerificationRequest(
            action="verify_plan_approval", plan_filename=request.plan_filename,
            confirmed_plan_sha256=request.confirmed_plan_sha256,
            confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
            approval_filename=request.approval_filename,
        ), project_root=root, plan_root=plans, approval_root=approvals,
    )
    if not verified["approved"]:
        raise InterfaceApiError("verified plan authority does not permit recipe compilation")
    result = load_planner_result(path=plans.resolve() / request.plan_filename, plan_root=plans.resolve())
    supported_outputs = {
        "inspect_vector": ["source_metadata"],
        "convert_vector": ["converted_vector"],
        "inspect_raster": ["raster_metadata"],
        "convert_raster": ["converted_raster"],
    }
    unsupported = [step.skill for step in result.plan.steps if step.skill not in supported_outputs]
    if unsupported:
        raise InterfaceApiError("plan contains skills not supported by the governed recipe dispatcher: " + ", ".join(unsupported))
    steps = [RecipeStep(
        step_id=step.step_id,
        skill_id=step.skill,
        depends_on=[] if index == 0 else [result.plan.steps[index - 1].step_id],
        arguments=step.arguments,
        output_ids=supported_outputs[step.skill],
    ) for index, step in enumerate(result.plan.steps)]
    recipe = WorkflowRecipe(
        recipe_id=f"planner-{request.confirmed_plan_sha256[:16]}",
        summary=result.plan.summary,
        original_request=result.original_request,
        steps=steps,
    )
    try:
        validation = validate_recipe_policy(recipe, registry=load_skill_registry(root))
    except RecipePolicyError as exc:
        raise InterfaceApiError(f"Planner recipe candidate failed deterministic policy: {exc}") from exc
    return {
        "schema_version": "1.0", "status": "compiled_not_saved",
        "source_plan_sha256": request.confirmed_plan_sha256,
        "recipe_sha256": recipe_sha256(recipe),
        "recipe": recipe.model_dump(mode="json"),
        "approval_required_step_ids": validation.approval_required_step_ids,
        "validation_required_step_ids": validation.validation_required_step_ids,
        "recipe_saved": False, "recipe_approval_performed": False,
        "execution_performed": False,
    }


def save_interface_plan_recipe(
    request: InterfacePlanRecipeSaveRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
    approval_root: Path | None = None,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Recompile and immutably store one explicitly reviewed plan recipe."""

    root = _trusted_root(project_root)
    compiled = compile_interface_plan_recipe(
        InterfacePlanRecipeCompilationRequest(
            action="compile_plan_recipe",
            plan_filename=request.plan_filename,
            confirmed_plan_sha256=request.confirmed_plan_sha256,
            confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
            approval_filename=request.approval_filename,
        ),
        project_root=root,
        plan_root=plan_root,
        approval_root=approval_root,
    )
    if compiled["recipe_sha256"] != request.confirmed_recipe_sha256:
        raise InterfaceApiError("reviewed Planner recipe digest no longer matches")
    recipe = WorkflowRecipe.model_validate(compiled["recipe"])
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    path = recipe_path(recipe, recipe_root=destination)
    already_stored = path.exists()
    if already_stored:
        saved = load_recipe(path=path, recipe_root=destination)
        if recipe_sha256(saved) != request.confirmed_recipe_sha256:
            raise InterfaceApiError("existing Planner recipe does not match the reviewed digest")
    else:
        saved, path = save_recipe(recipe, recipe_root=destination)
    return {
        "schema_version": "1.0", "status": "stored",
        "recipe_id": saved.recipe_id, "recipe_sha256": recipe_sha256(saved),
        "recipe_filename": path.name, "source_plan_sha256": request.confirmed_plan_sha256,
        "recipe_saved": True, "recipe_created": not already_stored,
        "recipe_modified": False, "approval_performed": False,
        "execution_performed": False,
    }


def interface_planner_skill_catalog(project_root: Path) -> dict[str, Any]:
    """Return safe implemented skills for explicit planner selection."""

    registry = load_skill_registry(_trusted_root(project_root))
    skills = []
    for skill in registry.implemented_skills():
        skills.append({
            "id": skill.id,
            "kind": skill.kind.value if skill.kind else None,
            "access": skill.access.value if skill.access else None,
            "approval_required": bool(skill.approval_required),
            "validation_required": bool(skill.validation_required),
        })
    return {
        "schema_version": "1.0",
        "skills": skills,
        "skill_count": len(skills),
        "catalog_validated": True,
        "execution_performed": False,
    }


def interface_saved_plan_inventory(
    project_root: Path,
    *, plan_root: Path | None = None,
    approval_root: Path | None = None,
) -> dict[str, Any]:
    """Return bounded validated plans and matching approval summaries."""

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else root / "plans"
    approvals = approval_root if approval_root is not None else root / "approvals"
    if plans.is_symlink() or (plans.exists() and not plans.is_dir()):
        raise InterfaceApiError("plan root is unsafe")
    if approvals.is_symlink() or (approvals.exists() and not approvals.is_dir()):
        raise InterfaceApiError("approval root is unsafe")
    approval_by_plan: dict[str, list[dict[str, Any]]] = {}
    if approvals.exists():
        approval_paths = sorted(approvals.glob("approval-*.json"))
        if len(approval_paths) > MAX_INTERFACE_PLAN_APPROVALS:
            raise InterfaceApiError("plan approval inventory exceeds its limit")
        for path in approval_paths:
            if path.is_symlink():
                raise InterfaceApiError("approval inventory contains an unsafe artifact")
            record = load_approval(path=path, approval_root=approvals)
            approval_by_plan.setdefault(record.plan_sha256, []).append({
                "approval_id": record.approval_id,
                "approval_filename": path.name,
                "decision": record.decision,
                "step_ids": record.step_ids,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            })
    items = []
    if plans.exists():
        paths = sorted(plans.glob("planner-plan.*.json"), key=lambda value: value.stat().st_mtime, reverse=True)
        if len(paths) > MAX_INTERFACE_PLANS:
            raise InterfaceApiError("saved plan inventory exceeds its limit")
        for path in paths:
            if path.is_symlink():
                raise InterfaceApiError("plan inventory contains an unsafe artifact")
            result = load_planner_result(path=path, plan_root=plans)
            digest = plan_sha256(result.plan)
            if path.name != f"planner-plan.{digest}.json":
                raise InterfaceApiError("saved plan filename does not match its digest")
            items.append({
                "plan_filename": path.name, "plan_sha256": digest,
                "saved_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "planner_result": result.model_dump(mode="json"),
                "approvals": approval_by_plan.get(digest, []),
            })
    return {"schema_version": "1.0", "status": "inspected", "plans": items, "plan_count": len(items), "files_modified": False, "execution_performed": False}
def compile_interface_recipe_proposal(
    payload: object,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Validate and compile one proposal without persistence or execution."""

    proposal = RecipeProposal.model_validate(_normalize_interface_recipe_paths(payload))
    root = _trusted_root(project_root)
    result = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    if result.recipe_saved or result.approval_performed or result.execution_performed:
        raise InterfaceApiError("compiler crossed the non-mutating interface boundary")
    return {
        "schema_version": "1.0",
        "status": "compiled",
        "result": result.model_dump(mode="json"),
        "recipe_sha256": recipe_sha256(result.recipe),
        "files_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def save_interface_reviewed_recipe(
    payload: object,
    *,
    confirmed_recipe_sha256: str,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Recompile, verify the reviewed digest, and immutably save one recipe."""

    if not isinstance(confirmed_recipe_sha256, str) or len(confirmed_recipe_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in confirmed_recipe_sha256
    ):
        raise InterfaceApiError("confirmed recipe digest is invalid")
    proposal = RecipeProposal.model_validate(_normalize_interface_recipe_paths(payload))
    root = _trusted_root(project_root)
    compiled = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    digest = recipe_sha256(compiled.recipe)
    if digest != confirmed_recipe_sha256:
        raise InterfaceApiError("reviewed recipe digest no longer matches")
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    saved, path = save_recipe(compiled.recipe, recipe_root=destination)
    return {
        "schema_version": "1.0",
        "status": "stored",
        "recipe_id": saved.recipe_id,
        "recipe_sha256": recipe_sha256(saved),
        "recipe_filename": path.name,
        "recipe_saved": True,
        "approval_performed": False,
        "execution_performed": False,
    }


def interface_saved_recipe_inventory(
    *,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Return bounded safe summaries of immutable stored recipes."""

    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    if not destination.exists():
        recipes: list[dict[str, Any]] = []
    else:
        paths = sorted(destination.glob("*.json"), key=lambda path: path.name)
        if len(paths) > MAX_INTERFACE_RECIPES:
            raise InterfaceApiError("recipe inventory exceeds its limit")
        registry = load_skill_registry(root)
        recipes = []
        for path in paths:
            if path.is_symlink() or path.resolve().parent != destination.resolve():
                raise InterfaceApiError("recipe inventory contains an unsafe artifact")
            recipe = load_recipe(path, recipe_root=destination)
            policy = validate_recipe_policy(recipe, registry=registry)
            recipes.append({
                "recipe_id": recipe.recipe_id,
                "recipe_sha256": recipe_sha256(recipe),
                "recipe_filename": path.name,
                "saved_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    timezone.utc,
                ).isoformat(),
                "steps": [
                    {"step_id": step.step_id, "skill_id": step.skill_id}
                    for step in recipe.steps
                ],
                "approval_required_step_ids": policy.approval_required_step_ids,
                "validation_required_step_ids": policy.validation_required_step_ids,
            })
    return {
        "schema_version": "1.0",
        "status": "inspected",
        "recipes": recipes,
        "recipe_count": len(recipes),
        "inventory_performed": True,
        "recipe_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def prepare_interface_recipe_approval(
    *,
    recipe_filename: str,
    confirmed_recipe_sha256: str,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare a digest-bound approval request without recording a decision."""

    if not isinstance(recipe_filename, str) or not SAFE_RECIPE_FILENAME.fullmatch(recipe_filename):
        raise InterfaceApiError("recipe filename is invalid")
    if not isinstance(confirmed_recipe_sha256, str) or not re.fullmatch(
        r"[a-f0-9]{64}", confirmed_recipe_sha256
    ):
        raise InterfaceApiError("confirmed recipe digest is invalid")
    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    recipe = load_recipe(destination / recipe_filename, recipe_root=destination)
    digest = recipe_sha256(recipe)
    if digest != confirmed_recipe_sha256:
        raise InterfaceApiError("stored recipe digest no longer matches")
    policy = validate_recipe_policy(recipe, registry=load_skill_registry(root))
    if not policy.approval_required_step_ids:
        raise InterfaceApiError("recipe has no approval-required steps")
    request = {
        "schema_version": "1.0",
        "status": "prepared_not_recorded",
        "recipe_id": recipe.recipe_id,
        "recipe_filename": recipe_filename,
        "recipe_sha256": digest,
        "steps": [
            {
                "step_id": step.step_id,
                "skill_id": step.skill_id,
                "depends_on": step.depends_on,
            }
            for step in recipe.steps
        ],
        "approval_required_step_ids": policy.approval_required_step_ids,
        "validation_required_step_ids": policy.validation_required_step_ids,
        "approval_recorded": False,
        "execution_performed": False,
    }
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return {
        **request,
        "approval_request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def record_interface_recipe_approval(
    request: InterfaceApprovalDecision,
    *,
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reprepare and append one exact human decision without execution."""

    prepared = prepare_interface_recipe_approval(
        recipe_filename=request.recipe_filename,
        confirmed_recipe_sha256=request.confirmed_recipe_sha256,
        project_root=project_root,
        recipe_root=recipe_root,
    )
    if prepared["approval_request_sha256"] != request.confirmed_approval_request_sha256:
        raise InterfaceApiError("prepared approval request digest no longer matches")
    root = _trusted_root(project_root)
    recipes = recipe_root if recipe_root is not None else root / "workflow-recipes"
    approvals = approval_root if approval_root is not None else root / "approvals"
    if approvals.is_symlink():
        raise InterfaceApiError("approval root cannot be a symlink")
    recipe = load_recipe(recipes / request.recipe_filename, recipe_root=recipes)
    active_now = now or datetime.now(timezone.utc)
    expires_at = (
        active_now + timedelta(minutes=request.valid_for_minutes)
        if request.valid_for_minutes is not None
        else None
    )
    record, path = create_recipe_approval(
        recipe=recipe,
        registry=load_skill_registry(root),
        step_ids=prepared["approval_required_step_ids"],
        decision=request.decision,
        approver=request.approver,
        reason=request.reason,
        approval_root=approvals,
        expires_at=expires_at,
        now=active_now,
    )
    return {
        "schema_version": "1.0",
        "status": "recorded",
        "approval_id": record.approval_id,
        "approval_filename": path.name,
        "recipe_sha256": record.recipe_sha256,
        "approval_request_sha256": request.confirmed_approval_request_sha256,
        "decision": record.decision,
        "approved_step_ids": record.step_ids,
        "created_at": record.created_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "secrets_redacted": record.secrets_redacted,
        "approval_recorded": True,
        "execution_performed": False,
    }


def verify_interface_recipe_approval(
    request: InterfaceApprovalVerificationRequest,
    *,
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Independently verify stored recipe and approval evidence without execution."""

    prepared = prepare_interface_recipe_approval(
        recipe_filename=request.recipe_filename,
        confirmed_recipe_sha256=request.confirmed_recipe_sha256,
        project_root=project_root,
        recipe_root=recipe_root,
    )
    if prepared["approval_request_sha256"] != request.confirmed_approval_request_sha256:
        raise InterfaceApiError("prepared approval request digest no longer matches")
    root = _trusted_root(project_root)
    recipes = recipe_root if recipe_root is not None else root / "workflow-recipes"
    approvals = approval_root if approval_root is not None else root / "approvals"
    if approvals.is_symlink():
        raise InterfaceApiError("approval root cannot be a symlink")
    recipe = load_recipe(recipes / request.recipe_filename, recipe_root=recipes)
    approval = load_recipe_approval(
        approvals / request.approval_filename,
        approval_root=approvals,
    )
    verification = verify_recipe_approval(
        approval=approval,
        recipe=recipe,
        registry=load_skill_registry(root),
        now=now,
    )
    return {
        "schema_version": "1.0",
        "status": "verified",
        "approval_id": approval.approval_id,
        "approval_filename": request.approval_filename,
        "recipe_id": recipe.recipe_id,
        "recipe_sha256": verification.recipe_sha256,
        "approval_request_sha256": request.confirmed_approval_request_sha256,
        "decision": approval.decision,
        "approved": verification.approved,
        "required_step_ids": verification.required_step_ids,
        "approved_step_ids": verification.approved_step_ids,
        "missing_step_ids": verification.missing_step_ids,
        "reason": verification.reason,
        "independent_verification_performed": True,
        "approval_modified": False,
        "execution_performed": False,
    }


def prepare_interface_execution_preview(
    request: InterfaceExecutionPreviewRequest,
    *,
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the existing execution envelope and project it without running it."""

    verified = verify_interface_recipe_approval(
        InterfaceApprovalVerificationRequest(
            action="verify_recipe_approval",
            recipe_filename=request.recipe_filename,
            confirmed_recipe_sha256=request.confirmed_recipe_sha256,
            confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
            approval_filename=request.approval_filename,
        ),
        project_root=project_root,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=now,
    )
    if not verified["approved"]:
        raise InterfaceApiError("recorded approval does not authorize execution")
    root = _trusted_root(project_root)
    recipes = recipe_root if recipe_root is not None else root / "workflow-recipes"
    approvals = approval_root if approval_root is not None else root / "approvals"
    recipe = load_recipe(recipes / request.recipe_filename, recipe_root=recipes)
    approval = load_recipe_approval(
        approvals / request.approval_filename,
        approval_root=approvals,
    )
    registry = load_skill_registry(root)
    envelope = build_recipe_execution_envelope(
        recipe=recipe,
        approval=approval,
        registry=registry,
        now=now,
    )
    steps = []
    for position, step in enumerate(envelope.steps, start=1):
        skill = registry.get_skill(step.skill_id)
        steps.append({
            "position": position,
            "step_id": step.step_id,
            "skill_id": step.skill_id,
            "skill_kind": skill.kind.value if skill.kind else None,
            "access": skill.access.value if skill.access else None,
            "approval_required": skill.approval_required,
            "validation_required": skill.validation_required,
            "depends_on": step.depends_on,
            "arguments": redact_value(step.arguments),
            "output_ids": step.output_ids,
        })
    preview = {
        "schema_version": "1.0",
        "status": "previewed_not_executed",
        "recipe_id": envelope.recipe_id,
        "recipe_filename": request.recipe_filename,
        "recipe_sha256": envelope.recipe_sha256,
        "approval_id": envelope.approval_id,
        "approval_filename": request.approval_filename,
        "approval_request_sha256": request.confirmed_approval_request_sha256,
        "tool_name": envelope.tool_name,
        "approved_step_ids": envelope.approved_step_ids,
        "topological_step_ids": envelope.topological_step_ids,
        "steps": steps,
        "evidence_destinations": ["recipe-runs/", "recipe-evidence/"],
        "approval_reverified": True,
        "secrets_redacted": True,
        "execution_available": load_settings().enable_write_tools,
        "execution_performed": False,
    }
    canonical = json.dumps(preview, sort_keys=True, separators=(",", ":"))
    return {
        **preview,
        "execution_preview_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def execute_interface_recipe(
    request: InterfaceRecipeExecutionRequest,
    *,
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    progress_root: Path | None = None,
) -> dict[str, Any]:
    """Execute one exact confirmed preview through the existing governed boundary."""

    preview_request = InterfaceExecutionPreviewRequest(
        action="prepare_execution_preview",
        recipe_filename=request.recipe_filename,
        confirmed_recipe_sha256=request.confirmed_recipe_sha256,
        confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
        approval_filename=request.approval_filename,
    )
    preview = prepare_interface_execution_preview(
        preview_request,
        project_root=project_root,
        recipe_root=recipe_root,
        approval_root=approval_root,
    )
    if preview["execution_preview_sha256"] != request.confirmed_execution_preview_sha256:
        raise InterfaceApiError("execution preview digest no longer matches")
    if not preview["execution_available"]:
        raise InterfaceApiError("write tools are disabled for interface execution")
    root = _trusted_root(project_root)
    recipes = recipe_root if recipe_root is not None else root / "workflow-recipes"
    approvals = approval_root if approval_root is not None else root / "approvals"
    recipe = load_recipe(recipes / request.recipe_filename, recipe_root=recipes)
    approval = load_recipe_approval(
        approvals / request.approval_filename,
        approval_root=approvals,
    )
    registry = load_skill_registry(root)
    envelope = build_recipe_execution_envelope(
        recipe=recipe,
        approval=approval,
        registry=registry,
    )
    configured = load_settings()

    def project_path(path: Path) -> Path:
        return path if path.is_absolute() else root / path

    settings = configured.model_copy(update={
        "project_root": root,
        "recipe_root": recipes,
        "approval_root": approvals,
        "input_root": project_path(configured.input_root),
        "output_root": project_path(configured.output_root),
        "contract_root": project_path(configured.contract_root),
        "report_root": project_path(configured.report_root),
        "recipe_run_root": project_path(configured.recipe_run_root),
        "recipe_evidence_root": project_path(configured.recipe_evidence_root),
    })
    execution_key = (envelope.recipe_sha256, envelope.approval_id)
    progress_key = request.confirmed_execution_preview_sha256
    with _EXECUTION_LOCK:
        if execution_key in _ACTIVE_EXECUTIONS:
            raise InterfaceApiError("this exact recipe execution is already in progress")
        _ACTIVE_EXECUTIONS.add(execution_key)
        _ACTIVE_PROGRESS.add(progress_key)
        _EXECUTION_PROGRESS[progress_key] = {
            "schema_version": "1.0",
            "status": "running",
            "execution_preview_sha256": progress_key,
            "recipe_id": envelope.recipe_id,
            "recipe_filename": request.recipe_filename,
            "recipe_sha256": envelope.recipe_sha256,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "failed_step_id": None,
            "interruption_detected": False,
            "recovery_guidance": None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "skill_id": step.skill_id,
                    "depends_on": step.depends_on,
                    "status": "queued",
                }
                for step in envelope.steps
            ],
            "execution_performed": False,
        }
        initial_progress = json.loads(json.dumps(_EXECUTION_PROGRESS[progress_key]))
    try:
        _persist_execution_progress(root, initial_progress, progress_root=progress_root)
    except Exception:
        with _EXECUTION_LOCK:
            _ACTIVE_EXECUTIONS.discard(execution_key)
            _ACTIVE_PROGRESS.discard(progress_key)
            _EXECUTION_PROGRESS.pop(progress_key, None)
        raise

    def progress_callback(step_id: str, skill_id: str, status: str) -> None:
        with _EXECUTION_LOCK:
            state = _EXECUTION_PROGRESS[progress_key]
            for item in state["steps"]:
                if item["step_id"] == step_id and item["skill_id"] == skill_id:
                    item["status"] = status
                    break
            if status in {"failed", "validation_failed"}:
                state["failed_step_id"] = step_id
            snapshot = json.loads(json.dumps(state))
        _persist_execution_progress(root, snapshot, progress_root=progress_root)

    try:
        result = execute_approved_recipe(
            execution_envelope=envelope.model_dump(mode="json"),
            recipe_filename=request.recipe_filename,
            approval_filename=request.approval_filename,
            settings=settings,
            progress_callback=progress_callback,
        )
    except Exception:
        with _EXECUTION_LOCK:
            state = _EXECUTION_PROGRESS[progress_key]
            state["status"] = "failed"
            state["finished_at"] = datetime.now(timezone.utc).isoformat()
            state["failed_step_id"] = state["failed_step_id"] or next(
                (item["step_id"] for item in state["steps"] if item["status"] == "running"),
                None,
            )
            state["recovery_guidance"] = (
                "Inspect the failed step and durable evidence before creating "
                "a new approval for any retry."
            )
            failed_snapshot = json.loads(json.dumps(state))
        _persist_execution_progress(root, failed_snapshot, progress_root=progress_root)
        raise
    finally:
        with _EXECUTION_LOCK:
            _ACTIVE_EXECUTIONS.discard(execution_key)
            _ACTIVE_PROGRESS.discard(progress_key)
    with _EXECUTION_LOCK:
        state = _EXECUTION_PROGRESS[progress_key]
        state["status"] = result.execution_record.final_status
        state["finished_at"] = datetime.now(timezone.utc).isoformat()
        state["failed_step_id"] = getattr(result.run_result, "failed_step_id", None)
        state["execution_performed"] = True
        final_snapshot = json.loads(json.dumps(state))
    _persist_execution_progress(root, final_snapshot, progress_root=progress_root)
    record = result.execution_record
    return {
        "schema_version": "1.0",
        "status": record.final_status,
        "recipe_id": record.recipe_id,
        "recipe_sha256": record.recipe_sha256,
        "approval_id": record.approval_id,
        "execution_preview_sha256": request.confirmed_execution_preview_sha256,
        "step_results": [
            {
                "step_id": step.step_id,
                "skill_id": step.skill_id,
                "status": step.status,
                "validation_performed": step.validation_performed,
                "output_ids": step.execution.output_ids,
                "outcome": _bounded_outcome(step.execution.result),
                "validation_outcome": _bounded_outcome(step.validation_result) if step.validation_result is not None else None,
            }
            for step in result.run_result.step_results
        ],
        "run_result_sha256": record.run_result_sha256,
        "run_result_path": record.run_result_path,
        "evidence_sha256": record.evidence_sha256,
        "evidence_path": record.evidence_path,
        "report_path": record.report_path,
        "execution_performed": True,
        "evidence_recorded": True,
        "report_written": True,
    }


def _handler(
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
) -> type[BaseHTTPRequestHandler]:
    class InterfaceRequestHandler(BaseHTTPRequestHandler):
        server_version = "ActionCharterInterface/1.0"
        sys_version = ""

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _reject_origin(self) -> bool:
            origin = self.headers.get("Origin")
            if origin is None or origin in {
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            }:
                return False
            self._send(HTTPStatus.FORBIDDEN, {"error": "request origin is not allowed"})
            return True

        def do_GET(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path == "/api/v1/health":
                execution_enabled = load_settings().enable_write_tools
                self._send(HTTPStatus.OK, {
                    "schema_version": "1.0",
                    "status": "ready",
                    "bound_to_loopback": True,
                    "write_authority": "bounded_recipe_and_approval_evidence",
                    "execution_authority": execution_enabled,
                    "execution_mode": "exact_approved_recipe" if execution_enabled else "disabled",
                })
                return
            if self.path == "/api/v1/executions":
                try:
                    self._send(
                        HTTPStatus.OK,
                        interface_execution_inventory(project_root),
                    )
                except (InterfaceApiError, OSError, ValueError, json.JSONDecodeError):
                    self._send(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {"error": "execution inventory is unavailable"},
                    )
                return
            progress_match = re.fullmatch(r"/api/v1/executions/([a-f0-9]{64})", self.path)
            if progress_match:
                digest = progress_match.group(1)
                with _EXECUTION_LOCK:
                    progress = _EXECUTION_PROGRESS.get(digest)
                    payload = json.loads(json.dumps(progress)) if progress is not None else None
                if payload is None:
                    try:
                        payload = _load_execution_progress(project_root, digest)
                    except (InterfaceApiError, OSError, ValueError, json.JSONDecodeError):
                        self._send(
                            HTTPStatus.SERVICE_UNAVAILABLE,
                            {"error": "execution progress is unavailable"},
                        )
                        return
                    if payload is not None:
                        with _EXECUTION_LOCK:
                            _EXECUTION_PROGRESS[digest] = payload
                if payload is None:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "execution progress is not available"})
                else:
                    self._send(HTTPStatus.OK, payload)
                return
            if self.path == "/api/v1/recipe-templates":
                try:
                    self._send(HTTPStatus.OK, interface_recipe_template_catalog(project_root))
                except (InterfaceApiError, RecipeTemplateCatalogError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted template catalog is unavailable"})
                return
            if self.path == "/api/v1/data-resources":
                try:
                    self._send(HTTPStatus.OK, interface_data_resource_inventory(project_root))
                except (InterfaceApiError, OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "data resource inventory is unavailable"})
                return
            if self.path == "/api/v1/critic-evidence":
                try:
                    self._send(
                        HTTPStatus.OK,
                        interface_critic_evidence_inventory(project_root),
                    )
                except (InterfaceApiError, OSError, ValueError):
                    self._send(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {"error": "Critic evidence inventory is unavailable"},
                    )
                return
            if self.path == "/api/v1/planner-skills":
                try:
                    self._send(
                        HTTPStatus.OK,
                        interface_planner_skill_catalog(project_root),
                    )
                except (InterfaceApiError, SkillRegistryError, OSError, ValueError):
                    self._send(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {"error": "planner skill catalog is unavailable"},
                    )
                return
            if self.path == "/api/v1/plans":
                try:
                    self._send(HTTPStatus.OK, interface_saved_plan_inventory(project_root))
                except (InterfaceApiError, ApprovalError, OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "saved plan inventory is unavailable"})
                return
            if self.path == "/api/v1/recipes":
                try:
                    self._send(HTTPStatus.OK, interface_saved_recipe_inventory(
                        project_root=project_root,
                        recipe_root=recipe_root,
                    ))
                except (
                    InterfaceApiError,
                    RecipePolicyError,
                    RecipeStorageError,
                    SkillRegistryError,
                    OSError,
                    ValueError,
                ):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted recipe inventory is unavailable"})
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})

        def do_POST(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path not in {
                "/api/v1/recipe-proposals/compile",
                "/api/v1/recipe-proposals/save-reviewed",
                "/api/v1/recipes/prepare-approval",
                "/api/v1/recipes/record-approval",
                "/api/v1/recipes/verify-approval",
                "/api/v1/recipes/preview-execution",
                "/api/v1/recipes/execute",
                "/api/v1/plans/create",
                "/api/v1/plans/save-reviewed",
                "/api/v1/plans/prepare-approval",
                "/api/v1/plans/record-approval",
                "/api/v1/plans/verify-approval",
                "/api/v1/plans/preview-execution",
                "/api/v1/plans/compile-recipe",
                "/api/v1/plans/save-reviewed-recipe",
                "/api/v1/critic-evidence/save-adapted-trace",
                "/api/v1/critic-evidence/run",
                "/api/v1/critic-evidence/record-result",
            }:
                self._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})
                return
            if self.headers.get_content_type() != "application/json":
                self._send(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "application/json is required"})
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = -1
            if length < 1 or length > MAX_INTERFACE_REQUEST_BYTES:
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request body size is invalid"})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                if self.path == "/api/v1/recipe-proposals/compile":
                    response = compile_interface_recipe_proposal(payload, project_root=project_root)
                elif self.path == "/api/v1/critic-evidence/save-adapted-trace":
                    response = save_interface_recipe_trace(
                        InterfaceRecipeTraceSaveRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/critic-evidence/run":
                    response = run_interface_critic(
                        InterfaceCriticRunRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/critic-evidence/record-result":
                    response = record_interface_critic_result(
                        InterfaceCriticRecordRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/create":
                    response = plan_interface_task(
                        InterfacePlanRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/save-reviewed":
                    response = save_interface_reviewed_plan(
                        InterfaceReviewedPlanSaveRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/prepare-approval":
                    response = prepare_interface_plan_approval(
                        InterfacePlanApprovalPreparationRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/record-approval":
                    response = record_interface_plan_approval(
                        InterfacePlanApprovalDecisionRequest.model_validate(payload),
                        project_root=project_root,
                        approval_root=approval_root,
                    )
                elif self.path == "/api/v1/plans/verify-approval":
                    response = verify_interface_plan_approval(
                        InterfacePlanApprovalVerificationRequest.model_validate(payload),
                        project_root=project_root,
                        approval_root=approval_root,
                    )
                elif self.path == "/api/v1/plans/preview-execution":
                    response = preview_interface_plan_execution(
                        InterfacePlanExecutionPreviewRequest.model_validate(payload),
                        project_root=project_root, approval_root=approval_root,
                    )
                elif self.path == "/api/v1/plans/compile-recipe":
                    response = compile_interface_plan_recipe(
                        InterfacePlanRecipeCompilationRequest.model_validate(payload),
                        project_root=project_root, approval_root=approval_root,
                    )
                elif self.path == "/api/v1/plans/save-reviewed-recipe":
                    response = save_interface_plan_recipe(
                        InterfacePlanRecipeSaveRequest.model_validate(payload),
                        project_root=project_root, approval_root=approval_root,
                        recipe_root=recipe_root,
                    )
                elif self.path == "/api/v1/recipe-proposals/save-reviewed":
                    if not isinstance(payload, dict) or set(payload) != {
                        "proposal",
                        "confirmed_recipe_sha256",
                        "action",
                    } or payload.get("action") != "save_reviewed_recipe":
                        raise InterfaceApiError("reviewed save request is invalid")
                    response = save_interface_reviewed_recipe(
                        payload["proposal"],
                        confirmed_recipe_sha256=payload["confirmed_recipe_sha256"],
                        project_root=project_root,
                        recipe_root=recipe_root,
                    )
                elif self.path == "/api/v1/recipes/prepare-approval":
                    if not isinstance(payload, dict) or set(payload) != {
                        "recipe_filename",
                        "confirmed_recipe_sha256",
                        "action",
                    } or payload.get("action") != "prepare_recipe_approval":
                        raise InterfaceApiError("approval preparation request is invalid")
                    response = prepare_interface_recipe_approval(
                        recipe_filename=payload["recipe_filename"],
                        confirmed_recipe_sha256=payload["confirmed_recipe_sha256"],
                        project_root=project_root,
                        recipe_root=recipe_root,
                    )
                elif self.path == "/api/v1/recipes/record-approval":
                    decision = InterfaceApprovalDecision.model_validate(payload)
                    response = record_interface_recipe_approval(
                        decision,
                        project_root=project_root,
                        recipe_root=recipe_root,
                        approval_root=approval_root,
                    )
                elif self.path == "/api/v1/recipes/verify-approval":
                    verification_request = InterfaceApprovalVerificationRequest.model_validate(payload)
                    response = verify_interface_recipe_approval(
                        verification_request,
                        project_root=project_root,
                        recipe_root=recipe_root,
                        approval_root=approval_root,
                    )
                elif self.path == "/api/v1/recipes/preview-execution":
                    preview_request = InterfaceExecutionPreviewRequest.model_validate(payload)
                    response = prepare_interface_execution_preview(
                        preview_request,
                        project_root=project_root,
                        recipe_root=recipe_root,
                        approval_root=approval_root,
                    )
                else:
                    execution_request = InterfaceRecipeExecutionRequest.model_validate(payload)
                    response = execute_interface_recipe(
                        execution_request,
                        project_root=project_root,
                        recipe_root=recipe_root,
                        approval_root=approval_root,
                    )
            except (json.JSONDecodeError, ValidationError):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "request payload is invalid"})
                return
            except RecipeCompilationError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "recipe proposal could not be compiled"})
                return
            except InterfaceApiError as exc:
                status = HTTPStatus.CONFLICT if (
                    "digest no longer matches" in str(exc)
                    or "already exists" in str(exc)
                ) else HTTPStatus.BAD_REQUEST
                self._send(status, {"error": str(exc)})
                return
            except RecipeStorageError:
                self._send(HTTPStatus.CONFLICT, {"error": "reviewed recipe could not be stored immutably"})
                return
            except RecipeApprovalError:
                self._send(HTTPStatus.CONFLICT, {"error": "recipe approval could not be recorded"})
                return
            except ApprovedRecipeError:
                self._send(HTTPStatus.CONFLICT, {"error": "approved recipe execution failed; inspect evidence and outputs"})
                return
            except CriticAgentError as exc:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {
                    "error": "Critic model did not produce a policy-valid assessment",
                    "finding": redact_text(str(exc))[:500],
                    "critic_result_recorded": False,
                    "release_created": False,
                    "execution_performed": False,
                })
                return
            except CriticEvidenceError:
                self._send(HTTPStatus.CONFLICT, {
                    "error": "stored Critic evidence failed deterministic verification",
                    "critic_result_recorded": False,
                    "release_created": False,
                    "execution_performed": False,
                })
                return
            except (CriticResultRecordError, CriticResultStorageError):
                self._send(HTTPStatus.CONFLICT, {
                    "error": "Critic result could not be recorded immutably",
                    "critic_result_recorded": False,
                    "release_created": False,
                    "execution_performed": False,
                })
                return
            except PlannerAgentError as exc:
                message = str(exc)
                if "invalid JSON" in message:
                    error = "planner model returned invalid JSON"
                    code = "planner_invalid_json"
                    finding = "The model response was not one complete JSON object."
                elif "invalid plan schema" in message:
                    error = "planner model returned an invalid plan schema"
                    code = "planner_invalid_schema"
                    finding = "The model response did not satisfy the required workflow-plan schema."
                elif "deterministic policy" in message:
                    error = "planner plan was rejected by deterministic policy"
                    code = "planner_policy_rejected"
                    finding = message.partition("deterministic policy:")[2].strip() or "The candidate plan violated deterministic policy."
                else:
                    error = "planner could not produce a validated plan"
                    code = "planner_generation_failed"
                    finding = "The configured model did not produce a validated plan."
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {
                    "error": error,
                    "code": code,
                    "finding": finding[:1000],
                    "retryable": True,
                    "retry_guidance": "Clarify the exact skills, arguments, approval requirements, and validation requirements, then retry.",
                    "plan_returned": False,
                    "plan_saved": False,
                    "approval_performed": False,
                    "execution_performed": False,
                })
                return
            except PlannerPolicyError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "reviewed plan was rejected by deterministic policy"})
                return
            except (ContextPackError, ModelClientError, ModelSettingsError):
                if self.path == "/api/v1/critic-evidence/run":
                    self._send(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {"error": "Critic model service is unavailable"},
                    )
                    return
                self._send(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "planner could not produce a validated plan"},
                )
                return
            except (SkillRegistryError, OSError, ValueError):
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted compilation service is unavailable"})
                return
            self._send(HTTPStatus.OK, response)

    return InterfaceRequestHandler


def serve_interface_api(
    *,
    project_root: Path,
    host: str = LOOPBACK_HOST,
    port: int = 8765,
    server_factory: Callable[..., ThreadingHTTPServer] = ThreadingHTTPServer,
) -> None:
    """Serve the non-mutating API and refuse non-loopback binding."""

    if host != LOOPBACK_HOST:
        raise InterfaceApiError("interface API must bind to 127.0.0.1")
    if port < 1 or port > 65_535:
        raise InterfaceApiError("interface API port is invalid")
    root = _trusted_root(project_root)
    server = server_factory((host, port), _handler(root))
    try:
        server.serve_forever()
    finally:
        server.server_close()
