"""Small fail-closed HTTP boundary for governed interface operations."""

from __future__ import annotations
from geoagent_harness.task_actions.storage_paths import runtime_store_path, ensure_state_root
from geoagent_harness.workspace import WorkspaceLayout, runtime_reference, runtime_reference_path

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
from geoagent_harness.storage import repositories
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
from geoagent_harness.task_history import TaskHistoryError, append_task_event, build_task_context, load_task_events, inspect_task_inventory, inspect_task_artifacts, attach_task_artifact, record_task_attempt_state
from geoagent_harness.critic.evidence import (
    CriticEvidenceError,
    MAX_TRACE_BYTES,
    MAX_REPORT_BYTES,
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
    load_critic_result_record,
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
from geoagent_harness.approvals.schemas import ApprovalRecord
from geoagent_harness.task_actions.approved_recipe import (
    ApprovedRecipeError,
    run_approved_recipe as execute_approved_recipe,
)
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.write_policy import (effective as effective_write_settings, snapshot as write_policy_snapshot,
    session as write_policy_session, update as update_write_policy, PolicyUpdate, WritePolicyError)

from geoagent_harness.recipes import (
    RecipeApprovalError,
    RecipeEvidenceStorageError,
    RecipePolicyError,
    RecipeStorageError,
    load_recipe,
    load_recipe_evidence,
    load_recipe_run_result,
    recipe_evidence_sha256,
    recipe_run_result_sha256,
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
from geoagent_harness.releases import (
    AuthoritativeReleaseStorageError,
    ReleaseAssessmentError,
    assess_recipe_release_candidate,
    authoritative_release_candidate_sha256,
    load_authoritative_release,
    persist_authoritative_release,
)
from geoagent_harness.operational_history import (
    AgentRole,
    OperationalHistoryError,
    OperationalIdentity,
    operational_event_log_path,
    record_gis_workflow_history,
)
from geoagent_harness.recipes import recipe_run_result_path
from geoagent_harness.snakemake_export import (
    SnakemakeExportContractError,
    SnakemakeExportGenerationError,
    SnakemakeExportPolicyError,
    generate_snakemake_recipe_export,
    plan_snakemake_recipe_export,
    validate_snakemake_export_contract,
)


# Compatibility exports; task actions own these implementations and shared state.
from geoagent_harness.task_actions.common import (
    InterfaceApiError,
    _trusted_root,
    _bounded_outcome,
)
from geoagent_harness.task_actions.contracts import (
    InterfaceApprovalDecision,
    InterfaceApprovalVerificationRequest,
    InterfaceExecutionPreviewRequest,
    InterfaceRecipeExecutionRequest,
    InterfaceReviewedPlanSaveRequest,
    InterfaceGeneratedPlanSaveRequest,
    InterfacePlanApprovalPreparationRequest,
    InterfacePlanApprovalDecisionRequest,
    InterfacePlanApprovalVerificationRequest,
    InterfacePlanExecutionPreviewRequest,
    InterfacePlanRecipeCompilationRequest,
    InterfacePlanRecipeSaveRequest,
)
from geoagent_harness.task_actions.artifacts import (
    save_interface_reviewed_plan,
    prepare_interface_plan_approval,
    record_interface_plan_approval,
    verify_interface_plan_approval,
    preview_interface_plan_execution,
    compile_interface_plan_recipe,
    _planner_recipe_definition,
    save_interface_plan_recipe,
    prepare_interface_recipe_approval,
    record_interface_recipe_approval,
    verify_interface_recipe_approval,
)
from geoagent_harness.task_actions.execution import (
    _progress_path,
    _persist_execution_progress,
    _load_execution_progress,
    interface_execution_inventory,
    prepare_interface_execution_preview,
    execute_interface_recipe,
    _EXECUTION_LOCK,
    _ACTIVE_EXECUTIONS,
    _ACTIVE_PROGRESS,
    _EXECUTION_PROGRESS,
)

MAX_INTERFACE_REQUEST_BYTES = 65_536
MAX_INTERFACE_RECIPES = 200
MAX_INTERFACE_PLANS = 200
MAX_INTERFACE_PLAN_APPROVALS = 500
MAX_INTERFACE_EXECUTION_ATTEMPTS = 200
SAFE_RECIPE_FILENAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$"
)
LOOPBACK_HOST = "127.0.0.1"
MAX_INTERFACE_OUTCOME_BYTES = 16_384
MAX_INTERFACE_DATA_RESOURCES = 500
MAX_INTERFACE_CRITIC_EVIDENCE = 200
INTERFACE_DATA_EXTENSIONS = {
    ".csv", ".geojson", ".gpkg", ".json", ".kml", ".parquet",
    ".shp", ".tif", ".tiff", ".tsv", ".xlsx", ".jsonl", ".ndjson",
}


class InterfaceContextRetrievalRequest(BaseModel):
    """Read-only candidates from explicit task selection; not reviewed memory."""
    model_config = ConfigDict(extra="forbid")
    action: Literal["retrieve_task_context"]
    query: str = Field(min_length=1, max_length=1000)
    task_ids: list[str] = Field(min_length=1, max_length=5)


class InterfaceContextReviewRequest(InterfaceContextRetrievalRequest):
    action: Literal["review_task_context"]
    confirmed_context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


class InterfaceIntentRequest(BaseModel):
    """Reasoning-only current request and explicit answers, without hidden history."""
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["reason_task_intent"]
    review_filename: str | None = Field(pattern=r"^context-review\.[a-f0-9]{64}\.json$")
    request: str = Field(min_length=1, max_length=4000)
    selected_input_path: str | None = Field(default=None, min_length=1, max_length=960)
    clarification_answers: list[str] = Field(default_factory=list, max_length=5)


class InterfaceIntentInspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["inspect_intent_proposal"]
    intent: dict[str, Any]


class InterfaceIntentReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["review_task_intent"]
    intent: dict[str, Any]
    confirmed_intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


class InterfaceIntentHandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["plan_reviewed_intent"]
    review_filename: str = Field(pattern=r"^intent-review\.[a-f0-9]{64}\.json$")
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=1)


class InterfaceIntentPlanSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["save_reviewed_intent_plan"]
    review_filename: str = Field(pattern=r"^intent-review\.[a-f0-9]{64}\.json$")
    planner_result: PlannerResult
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceTaskEventRequest(BaseModel):
    """History entry only; no approval or execution authority is conferred."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["record_task_event"]
    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    event_type: Literal["request", "clarification", "selection", "decision", "outcome", "failure", "artifact_reference"]
    summary: str = Field(min_length=1, max_length=1000)
    details: str = Field(default="", max_length=8000)
    artifact_path: str | None = Field(default=None, max_length=240)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class InterfacePlanRequest(BaseModel):
    """One bounded natural-language request for the existing planner agent."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["plan_task"]
    request: str = Field(min_length=1, max_length=8000)
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=64)
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
        normalized = []
        for item in value:
            if len(item) > 960:
                raise ValueError("input path is too long")
            item = item.strip()
            if "/" not in item:
                item = "data/input/" + item
            if (not re.fullmatch(r"data/input/[A-Za-z0-9._/-]+", item)
                    or any(part in {"", ".", ".."} for part in item.split("/"))):
                raise ValueError("input path is outside the governed input root")
            normalized.append(item)
        if len(normalized) != len(set(normalized)):
            raise ValueError("input paths must be unique after normalization")
        return normalized


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


class InterfaceRecipeReleaseRequest(BaseModel):
    """Exact recorded recipe-run evidence selected for release assessment."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["prepare_recipe_release"]
    release_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    trace_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.json$")
    report_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.md$")
    critic_record_file: str = Field(
        pattern=r"^critic-results/[A-Za-z0-9._-]+\.critic-result/CRITIC_RESULT\.json$"
    )
    confirmed_critic_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceRecipeReleaseCreationRequest(InterfaceRecipeReleaseRequest):
    """Exact assessed candidate explicitly confirmed for immutable release."""

    action: Literal["create_recipe_release"]
    confirmed_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_assessed_at: datetime
    confirmation: Literal["create_exact_release"]

    @field_validator("confirmed_assessed_at")
    @classmethod
    def assessed_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("confirmed assessment timestamp must include a timezone")
        return value


class InterfaceSnakemakeExportPreviewRequest(InterfaceApprovalVerificationRequest):
    """Exact approved recipe selected for a non-writing export preview."""

    action: Literal["preview_snakemake_export"]


class InterfaceSnakemakeExportRequest(InterfaceSnakemakeExportPreviewRequest):
    """Exact preview explicitly confirmed for immutable export generation."""

    action: Literal["export_snakemake"]
    confirmed_export_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: Literal["export_exact_approved_recipe"]


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
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
    items: list[dict[str, Any]] = []
    truncated = False

    if trace_root.exists() and trace_root.is_symlink():
        raise InterfaceApiError("trace root cannot be a symlink")
    if report_root.exists() and report_root.is_symlink():
        raise InterfaceApiError("report root cannot be a symlink")

    critic_root = runtime_store_path(root, "critic-results")
    if critic_root.is_symlink() or (critic_root.exists() and not critic_root.is_dir()):
        raise InterfaceApiError("Critic-result root is unsafe")
    critic_paths = sorted(critic_root.glob("*.critic-result/CRITIC_RESULT.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if critic_root.is_dir() else []
    if len(critic_paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        critic_paths = critic_paths[:MAX_INTERFACE_CRITIC_EVIDENCE]
        truncated = True
    critic_records = []
    for path in critic_paths:
        try:
            critic_records.append((path, load_critic_result_record(path, record_root=critic_root)))
        except CriticResultStorageError:
            continue
    release_root = runtime_store_path(root, "releases")
    if release_root.is_symlink() or (release_root.exists() and not release_root.is_dir()):
        raise InterfaceApiError("release root is unsafe")
    release_paths = sorted(release_root.glob("*.release/RELEASE.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if release_root.is_dir() else []
    if len(release_paths) > 25:
        release_paths = release_paths[:25]
        truncated = True
    releases = []
    for path in release_paths:
        try:
            releases.append((path, load_authoritative_release(path, release_root=release_root)))
        except AuthoritativeReleaseStorageError:
            continue

    trace_paths = sorted(trace_root.glob("*.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if trace_root.is_dir() else []
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
        matching_records = [runtime_reference(root,path) for path, record in critic_records
                            if record.task_id == pack.task_id
                            and record.deterministic_status == pack.deterministic_status
                            and record.critic_result.evidence_references == pack.evidence_references
                            and record.critic_result.evidence_gaps == pack.evidence_gaps
                            and record.critic_result.workflow_warnings == pack.warnings
                            and record.critic_result.human_corrections == pack.human_corrections]
        references = {reference.path: reference.sha256 for reference in pack.evidence_references}
        release_links = []
        for record_path in matching_records:
            record_digest = hashlib.sha256(runtime_reference_path(root,record_path).read_bytes()).hexdigest()
            required = {**references, record_path: record_digest}
            for release_path, manifest in releases:
                components = {part.path: part.sha256 for part in manifest.components}
                if all(components.get(path) == digest for path, digest in required.items()):
                    release_links.append(runtime_reference(root,release_path))
        release_links = sorted(set(release_links))
        items.append({
            "trace_name": trace_path.name,
            "report_name": report_path.name,
            "available": True,
            "finding": None,
            "evidence": pack.model_dump(mode="json"),
            "critic_record_link": "verified" if matching_records else "unavailable",
            "critic_record_files": matching_records,
            "release_link": "verified" if release_links else "unavailable",
            "release_manifests": release_links,
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


def _exact_recipe_progress(
    records: list[tuple[Path, dict[str, Any]]],
    *,
    recipe_id: str,
    recipe_digest: str,
    approval_id: str,
    evidence_digest: str,
    result_digest: str,
    final_status: str,
) -> tuple[Path, dict[str, Any]]:
    """Bind one evidence record to exactly one persisted interface attempt."""

    matching = [
        (path, payload) for path, payload in records
        if payload.get("recipe_id") == recipe_id
        and payload.get("recipe_sha256") == recipe_digest
        and payload.get("approval_id") == approval_id
        and payload.get("approval_filename") == f"{approval_id}.json"
        and payload.get("evidence_sha256") == evidence_digest
        and payload.get("run_result_sha256") == result_digest
        and payload.get("status") == final_status
        and payload.get("execution_performed") is True
        and payload.get("execution_preview_sha256") == path.stem
    ]
    if len(matching) != 1:
        raise RecipeTraceAdapterError(
            "exact durable interface execution identity is unavailable or ambiguous"
        )
    return matching[0]


def _stored_trace_pair_exact(root: Path, trace: WorkflowTrace, report_text: str) -> bool:
    """Compare stored trace and report with an exact in-memory candidate."""

    trace_path = runtime_store_path(root, "traces") / f"{trace.task_id}.json"
    report_path = runtime_store_path(root, "reports") / f"{trace.task_id}.md"
    if (not trace_path.is_file() or not report_path.is_file()
            or trace_path.is_symlink() or report_path.is_symlink()):
        return False
    try:
        return (
            trace_path.stat().st_size <= MAX_TRACE_BYTES
            and report_path.stat().st_size <= MAX_REPORT_BYTES
            and WorkflowTrace.model_validate(json.loads(trace_path.read_text(encoding="utf-8"))) == trace
            and report_path.read_text(encoding="utf-8") == report_text
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError):
        return False


def _interface_recipe_trace_candidates(root: Path) -> list[dict[str, Any]]:
    """Preview truthful recipe-run trace adaptations without writing artifacts."""

    evidence_root = runtime_store_path(root, "recipe-evidence")
    recipe_root = runtime_store_path(root, "workflow-recipes")
    approval_root = runtime_store_path(root, "approvals")
    progress_root = runtime_store_path(root, "workflow-state", "interface-executions")
    for candidate_root in (evidence_root, recipe_root, approval_root, progress_root):
        if candidate_root.exists() and candidate_root.is_symlink():
            raise InterfaceApiError("recipe trace source root cannot be a symlink")
    paths = sorted(evidence_root.glob("*.json"), reverse=True) if evidence_root.is_dir() else []
    if len(paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        paths = paths[:MAX_INTERFACE_CRITIC_EVIDENCE]

    progress_records: list[tuple[Path, dict[str, Any]]] = []
    if progress_root.is_dir():
        progress_paths = sorted(progress_root.glob("*.json"))
        if len(progress_paths) > MAX_INTERFACE_EXECUTION_ATTEMPTS:
            raise InterfaceApiError("recipe trace progress inventory exceeds its limit")
        for path in progress_paths:
            if path.is_symlink() or path.stat().st_size > MAX_INTERFACE_OUTCOME_BYTES:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
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
            "execution_preview_sha256": None,
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
            run_digest = recipe_run_result_sha256(evidence.run_result)
            result_root = runtime_store_path(root, "recipe-runs")
            result = load_recipe_run_result(
                result_root / f"{evidence.recipe_id}.{run_digest}.json",
                result_root=result_root,
            )
            if result != evidence.run_result:
                raise RecipeTraceAdapterError("durable result does not match recipe evidence")
            progress_path, progress = _exact_recipe_progress(
                progress_records,
                recipe_id=evidence.recipe_id,
                recipe_digest=evidence.recipe_sha256,
                approval_id=evidence.approval_id,
                evidence_digest=digest,
                result_digest=run_digest,
                final_status=evidence.final_status,
            )
            references = [
                runtime_reference(root, recipe_path),
                runtime_reference(root, approval_path),
                runtime_reference(root, evidence_path),
                runtime_reference(root, progress_path),
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
            stored_exact = _stored_trace_pair_exact(root, trace, render_recipe_trace_report(trace))
            base.update({
                "adaptable": True,
                "trace": trace.model_dump(mode="json"),
                "trace_sha256": recipe_trace_sha256(trace),
                "critic_status": pack.deterministic_status,
                "critic_gaps": pack.evidence_gaps,
                "execution_preview_sha256": progress_path.stem,
                "stored": stored_exact,
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
            trace_root=runtime_store_path(root, "traces"),
            report_root=runtime_store_path(root, "reports"),
        )
    except RecipeTraceAdapterError as exc:
        raise InterfaceApiError(redact_text(str(exc))[:500]) from exc
    pack = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=runtime_store_path(root, "traces"),
        report_root=runtime_store_path(root, "reports"),
    )
    return {
        "schema_version": "1.0",
        "status": "stored",
        "task_id": trace.task_id,
        "trace_sha256": trace_digest,
        "report_sha256": report_digest,
        "trace_path": runtime_reference(root,trace_path),
        "report_path": runtime_reference(root,report_path),
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
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
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
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
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
        record_root=runtime_store_path(root, "critic-results"),
    )
    record_directory = runtime_reference(root,Path(stored.record_directory))
    record_file = runtime_reference(root,Path(stored.record_file))
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


def _recipe_release_candidate(
    request: InterfaceRecipeReleaseRequest,
    *,
    project_root: Path,
    assessed_at: datetime,
):
    """Resolve and reassess exact release inputs from trusted trace references."""

    root = _trusted_root(project_root)
    trace_root, report_root = runtime_store_path(root, "traces"), runtime_store_path(root, "reports")
    trace_path, report_path = trace_root / request.trace_name, report_root / request.report_name
    build_critic_evidence(
        trace_path=trace_path, report_path=report_path,
        trace_root=trace_root, report_root=report_root,
    )
    try:
        trace = WorkflowTrace.model_validate(json.loads(trace_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise InterfaceApiError("stored recipe trace is invalid") from exc
    if trace.recipe_sha256 is None:
        raise InterfaceApiError("stored trace is not recipe-derived")

    references = set(trace.context_references)
    def exact_reference(prefix: str, suffix: str = ".json") -> str:
        matches = sorted(item for item in references if item.startswith(prefix) and item.endswith(suffix))
        if len(matches) != 1:
            raise InterfaceApiError("recipe release source references are incomplete")
        candidate = Path(matches[0])
        if candidate.is_absolute() or ".." in candidate.parts:
            raise InterfaceApiError("recipe release source reference is unsafe")
        return matches[0]

    recipe_reference = exact_reference("workflow-recipes/")
    approval_reference = exact_reference("approvals/")
    evidence_reference = exact_reference("recipe-evidence/")
    recipe_root, approval_root = runtime_store_path(root, "workflow-recipes"), runtime_store_path(root, "approvals")
    evidence_root, result_root = runtime_store_path(root, "recipe-evidence"), runtime_store_path(root, "recipe-runs")
    recipe_file = recipe_root / Path(recipe_reference).relative_to('workflow-recipes')
    approval_file = approval_root / Path(approval_reference).relative_to('approvals')
    evidence_file = evidence_root / Path(evidence_reference).relative_to('recipe-evidence')
    recipe_evidence = load_recipe_evidence(evidence_file, evidence_root=evidence_root)
    result_file = recipe_run_result_path(result=recipe_evidence.run_result, result_root=result_root)

    critic_file = runtime_reference_path(root,request.critic_record_file)
    try:
        resolved_critic = critic_file.resolve(strict=True)
        resolved_critic.relative_to((runtime_store_path(root, "critic-results")).resolve(strict=True))
        critic_digest = hashlib.sha256(resolved_critic.read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        raise InterfaceApiError("recorded Critic result is unavailable") from exc
    if critic_digest != request.confirmed_critic_record_sha256:
        raise InterfaceApiError("recorded Critic-result digest no longer matches")

    history_root = runtime_store_path(root, "operational-history")
    correlation_id = f"release-{trace.task_id}"
    history_root.mkdir(parents=True, exist_ok=True)
    history_file = operational_event_log_path(
        event_root=history_root, correlation_id=correlation_id
    )
    if not history_file.exists():
        identity = OperationalIdentity(
            agent_id=AgentRole.GIS,
            agent_instance_id="interface-release-preparer",
            agent_run_id=f"release-run-{trace.task_id}",
            task_id=trace.task_id,
            correlation_id=correlation_id,
        )
        record_gis_workflow_history(
            trace_path=trace_path, report_path=report_path,
            trace_root=trace_root, report_root=report_root,
            event_root=history_root, identity=identity,
        )

    candidate = assess_recipe_release_candidate(
        release_id=request.release_id,
        recipe_file=recipe_file,
        approval_file=approval_file,
        run_result_file=result_file,
        recipe_evidence_file=evidence_file,
        trace_file=trace_path,
        report_file=report_path,
        critic_record_file=resolved_critic,
        history_file=history_file,
        recipe_root=recipe_root,
        approval_root=approval_root,
        run_result_root=result_root,
        recipe_evidence_root=evidence_root,
        trace_root=trace_root,
        report_root=report_root,
        critic_root=runtime_store_path(root, "critic-results"),
        history_root=history_root,
        project_root=root,
        registry=load_skill_registry(root),
        assessed_at=assessed_at,
        approval_verified_at=trace.timestamps.finished_at,
    )
    return candidate, history_file


def prepare_interface_recipe_release(
    request: InterfaceRecipeReleaseRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Prepare exact history and assess readiness without creating a release."""

    root = _trusted_root(project_root)
    candidate, history_file = _recipe_release_candidate(
        request, project_root=root, assessed_at=now or datetime.now(timezone.utc)
    )
    return {
        "schema_version": "1.0",
        "status": "ready_not_released" if candidate.ready_for_release else "not_ready",
        "candidate_sha256": authoritative_release_candidate_sha256(candidate),
        "candidate": candidate.model_dump(mode="json"),
        "history_file": runtime_reference(root,history_file),
        "operational_history_prepared": True,
        "release_created": False,
        "execution_performed": False,
    }


def create_interface_recipe_release(
    request: InterfaceRecipeReleaseCreationRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reassess and atomically persist one explicitly confirmed release."""

    root = _trusted_root(project_root)
    active_now = now or datetime.now(timezone.utc)
    candidate, _ = _recipe_release_candidate(
        request, project_root=root, assessed_at=request.confirmed_assessed_at
    )
    digest = authoritative_release_candidate_sha256(candidate)
    if digest != request.confirmed_candidate_sha256:
        raise InterfaceApiError("reviewed release candidate digest no longer matches")
    stored = persist_authoritative_release(
        candidate, project_root=root, release_root=runtime_store_path(root, "releases"), released_at=active_now
    )
    return {
        **stored.model_dump(mode="json"),
        "status": "released",
        "release_directory": runtime_reference(root,Path(stored.release_directory)),
        "release_manifest": runtime_reference(root,Path(stored.release_manifest)),
        "release_created": True,
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
    selected_context = "\n\nFile input convention: resolve a bare input filename under data/input. Keep explicit normalized data/input paths. This convention does not grant file access or execution authority."
    if request.input_paths:
        selected_context += "\n\nOperator-selected governed input references:\n" + "\n".join(
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


def interface_planner_skill_catalog(project_root: Path) -> dict[str, Any]:
    """Return safe implemented skills for explicit planner selection."""

    from geoagent_harness.operations.registry import operation_catalog
    contracts = operation_catalog(_trusted_root(project_root))['operations']
    skills = [{key:operation[key] for key in ['id','name','workflow_supported','default_arguments','package_sha256','parameters_schema','outputs','kind','approval_required','validation_required']} | {'access':operation['effects']['access']} for operation in contracts]
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
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return bounded validated plans and matching approval summaries."""

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    if plans.is_symlink() or (plans.exists() and not plans.is_dir()):
        raise InterfaceApiError("plan root is unsafe")
    if approvals.is_symlink() or (approvals.exists() and not approvals.is_dir()):
        raise InterfaceApiError("approval root is unsafe")
    approval_by_plan: dict[str, list[tuple[dict[str, Any], ApprovalRecord]]] = {}
    if approvals.exists():
        approval_paths = sorted(approvals.glob("approval-*.json"))
        if len(approval_paths) > MAX_INTERFACE_PLAN_APPROVALS:
            raise InterfaceApiError("plan approval inventory exceeds its limit")
        for path in approval_paths:
            if path.is_symlink():
                raise InterfaceApiError("approval inventory contains an unsafe artifact")
            record = load_approval(path=path, approval_root=approvals)
            approval_by_plan.setdefault(record.plan_sha256, []).append(({
                "approval_id": record.approval_id,
                "approval_filename": path.name,
                "decision": record.decision,
                "step_ids": record.step_ids,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            }, record))
    items = []
    if plans.exists():
        paths = [plans / name for name in repositories(root).documents('plans',directory=plans).names(order='recent') if name.startswith('planner-plan.')]
        if len(paths) > MAX_INTERFACE_PLANS:
            raise InterfaceApiError("saved plan inventory exceeds its limit")
        for path in paths:
            if path.is_symlink():
                raise InterfaceApiError("plan inventory contains an unsafe artifact")
            result = repositories(root).documents('plans',directory=plans).load(path.name)
            digest = plan_sha256(result.plan)
            if path.name != f"planner-plan.{digest}.json":
                raise InterfaceApiError("saved plan filename does not match its digest")
            required_steps = [step.step_id for step in result.plan.steps if step.requires_approval]
            linked_approvals = []
            for summary, record in approval_by_plan.get(digest, []):
                verification = verify_approval(
                    approval=record,
                    plan=result.plan,
                    required_step_ids=required_steps,
                    now=now,
                )
                linked_approvals.append({
                    **summary,
                    "authority_link": "verified" if verification.approved else "blocked",
                    "authority_reason": verification.reason,
                })
            items.append({
                "plan_filename": path.name, "plan_sha256": digest,
                "saved_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "planner_result": result.model_dump(mode="json"),
                "approvals": linked_approvals,
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
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
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
    approval_root: Path | None = None,
    plan_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return bounded safe summaries of immutable stored recipes."""

    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise InterfaceApiError("recipe root is unsafe")
    if approvals.is_symlink() or (approvals.exists() and not approvals.is_dir()):
        raise InterfaceApiError("approval root is unsafe")
    if plans.is_symlink() or (plans.exists() and not plans.is_dir()):
        raise InterfaceApiError("plan root is unsafe")
    approval_by_recipe: dict[str, list[tuple[Path, Any]]] = {}
    if approvals.exists():
        approval_paths = sorted(approvals.glob("recipe-approval-*.json"))
        if len(approval_paths) > MAX_INTERFACE_PLAN_APPROVALS:
            raise InterfaceApiError("recipe approval inventory exceeds its limit")
        for approval_path in approval_paths:
            if approval_path.is_symlink():
                raise InterfaceApiError("approval inventory contains an unsafe artifact")
            record = load_recipe_approval(approval_path, approval_root=approvals)
            approval_by_recipe.setdefault(record.recipe_sha256, []).append((approval_path, record))
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
            digest = recipe_sha256(recipe)
            plan_match = "unavailable"
            matched_plan_digest: str | None = None
            plan_match_reason = "No exact saved Planner definition found"
            planner_id = re.fullmatch(r"planner-([a-f0-9]{16})", recipe.recipe_id)
            if planner_id and plans.is_dir():
                plan_paths = list(plans.glob(f"planner-plan.{planner_id.group(1)}*.json"))
                if len(plan_paths) > MAX_INTERFACE_PLANS:
                    raise InterfaceApiError("matching Planner inventory exceeds its limit")
                matches = []
                for plan_path in plan_paths:
                    if plan_path.is_symlink():
                        raise InterfaceApiError("matching Planner artifact is unsafe")
                    planner_result = load_planner_result(path=plan_path, plan_root=plans)
                    plan_digest = plan_sha256(planner_result.plan)
                    if plan_path.name != f"planner-plan.{plan_digest}.json":
                        raise InterfaceApiError("matching Planner filename is invalid")
                    try:
                        reconstructed = _planner_recipe_definition(planner_result, plan_digest)
                    except (InterfaceApiError, ValidationError):
                        continue
                    if recipe_sha256(reconstructed) == digest:
                        matches.append(plan_digest)
                if len(matches) == 1:
                    plan_match, matched_plan_digest = "verified", matches[0]
                    plan_match_reason = "Canonical recipe definition matches the saved Planner result"
                elif plan_paths:
                    plan_match = "blocked"
                    plan_match_reason = "No unique exact Planner definition matches this recipe"
            linked_approvals = []
            for approval_path, record in approval_by_recipe.get(digest, []):
                verification = verify_recipe_approval(
                    approval=record, recipe=recipe, registry=registry, now=now,
                )
                linked_approvals.append({
                    "approval_id": record.approval_id,
                    "approval_filename": approval_path.name,
                    "decision": record.decision,
                    "step_ids": record.step_ids,
                    "created_at": record.created_at.isoformat(),
                    "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                    "authority_link": "verified" if verification.approved else "blocked",
                    "authority_reason": verification.reason,
                })
            recipes.append({
                "recipe_id": recipe.recipe_id,
                "recipe_sha256": digest,
                "recipe_filename": path.name,
                "matching_plan_sha256": matched_plan_digest,
                "plan_definition_link": plan_match,
                "plan_definition_reason": plan_match_reason,
                "saved_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    timezone.utc,
                ).isoformat(),
                "steps": [
                    {"step_id": step.step_id, "skill_id": step.skill_id, "depends_on": step.depends_on}
                    for step in recipe.steps
                ],
                "approval_required_step_ids": policy.approval_required_step_ids,
                "validation_required_step_ids": policy.validation_required_step_ids,
                "approvals": linked_approvals,
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


def _snakemake_export_plan(
    request: InterfaceSnakemakeExportPreviewRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
):
    root = _trusted_root(project_root)
    verified = verify_interface_recipe_approval(
        InterfaceApprovalVerificationRequest(
            action="verify_recipe_approval",
            recipe_filename=request.recipe_filename,
            confirmed_recipe_sha256=request.confirmed_recipe_sha256,
            confirmed_approval_request_sha256=request.confirmed_approval_request_sha256,
            approval_filename=request.approval_filename,
        ),
        project_root=root,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=now,
    )
    if not verified["approved"]:
        raise InterfaceApiError("recorded approval does not authorize Snakemake export")
    recipes = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    recipe = load_recipe(recipes / request.recipe_filename, recipe_root=recipes)
    approval = load_recipe_approval(
        approvals / request.approval_filename, approval_root=approvals
    )
    return plan_snakemake_recipe_export(
        recipe=recipe,
        approval=approval,
        registry=load_skill_registry(root),
        recipe_path=recipes / request.recipe_filename,
        approval_path=approvals / request.approval_filename,
    )


def preview_interface_snakemake_export(
    request: InterfaceSnakemakeExportPreviewRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
) -> dict[str, Any]:
    """Build an exact approved export plan without writing or executing."""

    plan = _snakemake_export_plan(
        request, project_root=project_root, now=now,
        recipe_root=recipe_root, approval_root=approval_root,
    )
    canonical = json.dumps(
        plan.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return {
        "schema_version": "1.0",
        "status": "previewed_not_exported",
        "export_plan_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "plan": plan.model_dump(mode="json"),
        "export_performed": False,
        "contract_validated": False,
        "workflow_executed": False,
        "recipe_execution_performed": False,
    }


def export_interface_snakemake_recipe(
    request: InterfaceSnakemakeExportRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    export_root: Path | None = None,
) -> dict[str, Any]:
    """Rebuild, export and statically validate one confirmed replay package."""

    root = _trusted_root(project_root)
    plan = _snakemake_export_plan(
        request, project_root=root, now=now,
        recipe_root=recipe_root, approval_root=approval_root,
    )
    canonical = json.dumps(
        plan.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if digest != request.confirmed_export_plan_sha256:
        raise InterfaceApiError("reviewed Snakemake export plan no longer matches")
    exports = export_root if export_root is not None else runtime_store_path(root, "snakemake-exports")
    expected_path = exports.resolve() / (
        f"{plan.recipe_id}.{plan.recipe_sha256}.snakemake"
    )
    already_existed = expected_path.exists()
    if already_existed:
        export_path = expected_path
        generated_payload = {
            "recipe_id": plan.recipe_id,
            "recipe_sha256": plan.recipe_sha256,
            "approval_id": plan.approval_id,
            "export_path": export_path.as_posix(),
            "generated_files": [
                plan.workflow_filename,
                plan.configuration_filename,
                plan.manifest_filename,
            ],
            "export_performed": False,
            "workflow_executed": False,
            "recipe_execution_performed": False,
        }
    else:
        generated = generate_snakemake_recipe_export(plan, export_root=exports, project_root=root)
        export_path = Path(generated.export_path)
        generated_payload = generated.model_dump(mode="json")
    contract = validate_snakemake_export_contract(export_path)
    if not contract.passed:
        raise InterfaceApiError("generated Snakemake export failed static validation")
    if already_existed:
        manifest = json.loads(
            (export_path / plan.manifest_filename).read_text(encoding="utf-8")
        )
        generated_payload.update({
            "workflow_path": manifest["workflow_path"],
            "workflow_sha256": manifest["workflow_sha256"],
            "configuration_path": manifest["configuration_path"],
            "configuration_sha256": manifest["configuration_sha256"],
            "manifest_path": plan.manifest_filename,
        })
    try:
        displayed_export_path = runtime_reference(root, export_path)
    except ValueError:
        displayed_export_path = export_path.as_posix()
    return {
        "schema_version": "1.0",
        "status": "existing_export_validated" if already_existed else "exported_and_validated",
        "export_plan_sha256": digest,
        "export": {
            **generated_payload,
            "export_path": displayed_export_path,
        },
        "contract": {
            **contract.model_dump(mode="json"),
            "export_path": displayed_export_path,
        },
        "export_performed": not already_existed,
        "export_already_existed": already_existed,
        "contract_validated": True,
        "workflow_executed": False,
        "recipe_execution_performed": False,
    }


def record_interface_task_event(
    request: InterfaceTaskEventRequest,
    *,
    project_root: Path,
    task_root: Path | None = None,
) -> dict[str, Any]:
    """Store one explicit task-history event, never an approval decision."""

    root = task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history")
    if request.task_id is None and request.event_type != "request":
        raise InterfaceApiError("a new task must begin with a request event")
    task_id = request.task_id or f"task-{uuid4().hex}"
    stored = append_task_event(
        root=root, task_id=task_id, event_type=request.event_type,
        summary=request.summary, details=request.details, artifact_path=request.artifact_path,
        artifact_sha256=request.artifact_sha256,
        require_existing=request.task_id is not None,
    )
    return {
        "schema_version": "1.0", "status": "recorded_history_only",
        "task_id": task_id, "event_reference": stored["reference"],
        "approval_recorded": False, "execution_performed": False,
    }


def inspect_interface_task_context(
    *, project_root: Path, task_id: str, task_root: Path | None = None,
) -> dict[str, Any]:
    """Recheck one complete task chain and return a cited context preview."""

    root = task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history")
    if not load_task_events(root=root, task_id=task_id):
        raise TaskHistoryError("task history does not exist")
    return build_task_context(root=root, task_id=task_id)


def _handler(
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    task_root: Path | None = None,
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
            configured_origin = os.environ.get("INTERFACE_FRONTEND_ORIGIN")
            allowed_origins = {
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            }
            if configured_origin and re.fullmatch(
                r"http://(?:127\.0\.0\.1|localhost):[1-9][0-9]{0,4}",
                configured_origin,
            ):
                allowed_origins.add(configured_origin)
            if origin is None or origin in allowed_origins:
                return False
            self._send(HTTPStatus.FORBIDDEN, {"error": "request origin is not allowed"})
            return True

        def do_GET(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path == "/api/v1/health":
                from geoagent_harness.task_actions.conversation import PLANNER_CONTRACT_REVISION
                from geoagent_harness.task_actions.inspection_planning import ANALYTICAL_PLANNING_REVISION
                execution_enabled = effective_write_settings(load_settings(), project_root).enable_write_tools
                self._send(HTTPStatus.OK, {
                    "schema_version": "1.0",
                    "status": "ready",
                    "bound_to_loopback": True,
                    "planner_contract_revision": PLANNER_CONTRACT_REVISION,
                    "inspection_on_send_revision": "inspection-batch-v5",
                    "result_exploration_revision": "typed-views-v1",
                    "analytical_table_revision": "table-analysis-v1",
                    "analytical_planning_revision": ANALYTICAL_PLANNING_REVISION,
                    "analytical_loop_revision": "bounded-analyst-v1",
                    "model_selection_revision": "ollama-selection-v1",
                    "planner_correction_limit": 1,
                    "write_authority": "bounded_recipe_and_approval_evidence",
                    "execution_authority": execution_enabled,
                    "execution_mode": "exact_approved_recipe" if execution_enabled else "disabled",
                })
                return
            if self.path == '/api/v1/write-policy':
                try:
                    self._send(HTTPStatus.OK, write_policy_snapshot(project_root) or {'active': False, 'enabled': False, 'locked': True, 'execution_performed': False})
                except (WritePolicyError, OSError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Write policy unavailable; no permission granted', 'execution_performed': False})
                return
            if self.path == "/api/v1/model-status":
                from geoagent_harness.model.diagnostics import inspect_model_configuration
                from geoagent_harness.model.catalog import request_selection
                with request_selection(project_root):
                    self._send(HTTPStatus.OK, inspect_model_configuration())
                return
            if self.path == '/api/v1/models':
                from geoagent_harness.model.catalog import catalog, CatalogError
                try:
                    self._send(HTTPStatus.OK, catalog(project_root))
                except (CatalogError, ModelSettingsError, OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Ollama discovery unavailable. Check the configured endpoint and service. No model call or download occurred.'})
                return
            task_match = re.fullmatch(r"/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/context", self.path)
            if self.path == "/api/v1/tasks":
                try:
                    self._send(HTTPStatus.OK, inspect_task_inventory(root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history")))
                except (TaskHistoryError, OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "task inventory is unavailable"})
                return
            if task_match:
                try:
                    self._send(HTTPStatus.OK, inspect_interface_task_context(
                        project_root=project_root, task_id=task_match.group(1), task_root=task_root,
                    ))
                except TaskHistoryError:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "task context is unavailable"})
                except (OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "task context could not be loaded"})
                return
            relationship_match = re.fullmatch(r"/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/relationships", self.path)
            if relationship_match:
                from geoagent_harness.task_history.relationships import inspect_task_relationships
                try:
                    self._send(HTTPStatus.OK, inspect_task_relationships(
                        root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        task_id=relationship_match.group(1), project_root=_trusted_root(project_root),
                    ))
                except TaskHistoryError:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "task relationship inspection is unavailable"})
                except (OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "task relationships could not be inspected"})
                return
            artifact_match = re.fullmatch(r"/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/artifacts", self.path)
            if artifact_match:
                try:
                    self._send(HTTPStatus.OK, inspect_task_artifacts(
                        root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        task_id=artifact_match.group(1), project_root=_trusted_root(project_root),
                    ))
                except TaskHistoryError:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "task artifact inspection is unavailable"})
                except (OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "task evidence could not be inspected"})
                return
            if self.path == "/api/v1/reviewed-context-inventory":
                from geoagent_harness.intent.inventory import reviewed_context_inventory
                try:
                    self._send(HTTPStatus.OK, reviewed_context_inventory(project_root=_trusted_root(project_root)))
                except (OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "review inventory is unavailable"})
                return
            review_match = re.fullmatch(r"/api/v1/context/reviews/(context-review\.[a-f0-9]{64}\.json)", self.path)
            if review_match:
                from geoagent_harness.context_retrieval import load_reviewed_context, ContextReviewError, ContextRetrievalError
                try:
                    self._send(HTTPStatus.OK, load_reviewed_context(
                        review_root=runtime_store_path(_trusted_root(project_root), "reviewed-contexts"),
                        history_root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        filename=review_match.group(1),
                    ))
                except (ContextReviewError, ContextRetrievalError, OSError, ValueError, KeyError):
                    self._send(HTTPStatus.CONFLICT, {"error": "reviewed context is unavailable or stale; retrieve and review again"})
                return
            intent_review_match = re.fullmatch(r"/api/v1/intent/reviews/(intent-review\.[a-f0-9]{64}\.json)", self.path)
            if intent_review_match:
                from geoagent_harness.intent.review import load_reviewed_intent
                try:
                    self._send(HTTPStatus.OK, load_reviewed_intent(
                        project_root=_trusted_root(project_root), filename=intent_review_match.group(1)))
                except (OSError, ValueError, KeyError):
                    self._send(HTTPStatus.CONFLICT, {"error": "reviewed intent is unavailable, invalid or stale; inspect and review again", "execution_performed": False})
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
            if self.path.startswith('/api/v1/operations/'):
                from urllib.parse import urlparse,parse_qs
                from geoagent_harness.operations.api import operation_catalog,library_inventory,read_scan,candidate_page
                from geoagent_harness.operations.storage import saved_scans
                url=urlparse(self.path);params=parse_qs(url.query)
                try:
                    if url.path=='/api/v1/operations/catalog':payload=operation_catalog(project_root,params.get('q',[''])[0])
                    elif url.path=='/api/v1/operations/libraries':payload=library_inventory()
                    elif url.path=='/api/v1/operations/scans':payload=saved_scans(project_root)
                    elif url.path=='/api/v1/operations/candidates':payload=candidate_page(read_scan(project_root,params.get('scan',[''])[0]),params.get('q',[''])[0],params.get('distribution',[''])[0],params.get('kind',[''])[0],int(params.get('offset',['0'])[0]),int(params.get('limit',['50'])[0]))
                    else:self._send(HTTPStatus.NOT_FOUND,{'error':'Operation metadata endpoint not available'});return
                except (ValueError,OSError,RuntimeError):
                    self._send(HTTPStatus.UNPROCESSABLE_ENTITY,{'error':'Operation metadata is unavailable or request bounds/identity are invalid'});return
                self._send(HTTPStatus.OK,payload);return
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
            if self.path == "/api/v1/inspection-runs":
                from geoagent_harness.task_actions.workflow import inspection_inventory
                try:
                    self._send(HTTPStatus.OK, inspection_inventory(project_root=project_root))
                except (InterfaceApiError, OSError, ValueError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "inspection history unavailable"})
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
            from geoagent_harness.model.catalog import request_selection
            with request_selection(project_root):
                self._post_selected()

        def _post_selected(self) -> None:
            if self._reject_origin():
                return
            if self.path not in {
                "/api/v1/models/select",
                "/api/v1/models/reasoning",
                "/api/v1/models/review-timeout",
                "/api/v1/write-policy",
                "/api/v1/recipe-proposals/compile",
                "/api/v1/tasks/events",
                "/api/v1/context/retrieve",
                "/api/v1/context/review",
                "/api/v1/intent/reason",
                "/api/v1/intent/inspect",
                "/api/v1/intent/review",
                "/api/v1/intent/plan",
                "/api/v1/intent/save-plan",
                "/api/v1/recipe-proposals/save-reviewed",
                "/api/v1/recipes/prepare-approval",
                "/api/v1/recipes/record-approval",
                "/api/v1/recipes/verify-approval",
                "/api/v1/recipes/preview-execution",
                "/api/v1/recipes/execute",
                "/api/v1/plans/validate-edit",
                "/api/v1/workflow/prepare",
                "/api/v1/workflow/authorize",
                "/api/v1/workflow/execute",
                "/api/v1/workflow/runs",
                "/api/v1/reusable-recipes",
                "/api/v1/planner/conversation",
                "/api/v1/planner/submit",
                "/api/v1/planner/diagnostics",
                "/api/v1/analysis/view",
                "/api/v1/chat/history",
                "/api/v1/method-memory",
                "/api/v1/operations/scan",
                "/api/v1/operations/test-package",
                "/api/v1/operations/install-package",
                "/api/v1/plans/create",
                "/api/v1/plans/save-generated",
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
                "/api/v1/releases/prepare-recipe",
                "/api/v1/releases/create-recipe",
                "/api/v1/snakemake/preview-export",
                "/api/v1/snakemake/export",
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
                if self.path == '/api/v1/models/select':
                    from geoagent_harness.model.catalog import select, Selection, CatalogError
                    try:
                        response = select(project_root, Selection.model_validate(payload))
                    except CatalogError as error:
                        self._send(HTTPStatus.CONFLICT, {'error': str(error), 'execution_performed': False})
                        return
                elif self.path == '/api/v1/models/reasoning':
                    from geoagent_harness.model.catalog import select_reasoning,ReasoningSelection,CatalogError
                    try:response=select_reasoning(project_root,ReasoningSelection.model_validate(payload))
                    except CatalogError as error:
                        self._send(HTTPStatus.CONFLICT,{'error':str(error),'execution_performed':False});return
                elif self.path == '/api/v1/models/review-timeout':
                    from geoagent_harness.model.catalog import select_review_timeout,ReviewTimeoutSelection,CatalogError
                    try:response=select_review_timeout(project_root,ReviewTimeoutSelection.model_validate(payload))
                    except CatalogError as error:
                        self._send(HTTPStatus.CONFLICT,{'error':str(error),'execution_performed':False});return
                elif self.path == '/api/v1/write-policy':
                    response = update_write_policy(project_root, PolicyUpdate.model_validate(payload))
                elif self.path == "/api/v1/context/retrieve":
                    from geoagent_harness.context_retrieval import retrieve_task_context, ContextRetrievalError
                    context_request = InterfaceContextRetrievalRequest.model_validate(payload)
                    try:
                        response = retrieve_task_context(
                            root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                            query=context_request.query, task_ids=context_request.task_ids,
                        )
                    except ContextRetrievalError as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return
                elif self.path == "/api/v1/context/review":
                    from geoagent_harness.context_retrieval import save_reviewed_context, ContextReviewError, ContextRetrievalError
                    review_request = InterfaceContextReviewRequest.model_validate(payload)
                    try:
                        response = save_reviewed_context(
                            history_root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                            review_root=runtime_store_path(_trusted_root(project_root), "reviewed-contexts"),
                            query=review_request.query, task_ids=review_request.task_ids,
                            confirmed_context_sha256=review_request.confirmed_context_sha256,
                            reviewer=review_request.reviewer, reason=review_request.reason,
                        )
                    except (ContextReviewError, ContextRetrievalError) as exc:
                        self._send(HTTPStatus.CONFLICT, {"error": str(exc)})
                        return
                elif self.path == "/api/v1/intent/reason":
                    from geoagent_harness.intent.service import reason_task_intent, IntentError
                    from geoagent_harness.context_retrieval import ContextReviewError, ContextRetrievalError
                    intent_request = InterfaceIntentRequest.model_validate(payload)
                    try:
                        response = reason_task_intent(
                            project_root=_trusted_root(project_root),
                            history_root=task_root,
                            review_filename=intent_request.review_filename,
                            request=intent_request.request,
                            clarification_answers=intent_request.clarification_answers,
                            selected_input_path=intent_request.selected_input_path,
                        )
                    except (ContextReviewError, ContextRetrievalError, OSError, KeyError) as exc:
                        self._send(HTTPStatus.CONFLICT, {"error": "reviewed context is unavailable or stale; retrieve and review again", "execution_performed": False})
                        return
                    except IntentError as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc), "execution_performed": False})
                        return
                    except (ModelClientError, ModelSettingsError) as exc:
                        from geoagent_harness.model.diagnostics import model_failure
                        self._send(HTTPStatus.BAD_GATEWAY, model_failure(exc))
                        return
                elif self.path in {"/api/v1/intent/inspect", "/api/v1/intent/review", "/api/v1/intent/plan", "/api/v1/intent/save-plan"}:
                    from geoagent_harness.intent.review import inspect_intent_for_review, save_reviewed_intent
                    from geoagent_harness.intent.handoff import plan_reviewed_intent, save_reviewed_intent_plan
                    from geoagent_harness.intent.service import IntentError
                    from geoagent_harness.context_retrieval import ContextReviewError, ContextRetrievalError
                    try:
                        if self.path == "/api/v1/intent/inspect":
                            inspected = InterfaceIntentInspectionRequest.model_validate(payload)
                            response = inspect_intent_for_review(payload=inspected.intent, project_root=_trusted_root(project_root))
                        elif self.path == "/api/v1/intent/review":
                            confirmed = InterfaceIntentReviewRequest.model_validate(payload)
                            response = save_reviewed_intent(payload=confirmed.intent, project_root=_trusted_root(project_root),
                                confirmed_intent_sha256=confirmed.confirmed_intent_sha256,
                                reviewer=confirmed.reviewer, reason=confirmed.reason)
                        elif self.path == "/api/v1/intent/save-plan":
                            saving = InterfaceIntentPlanSaveRequest.model_validate(payload)
                            response = save_reviewed_intent_plan(project_root=_trusted_root(project_root),
                                filename=saving.review_filename, planner_result=saving.planner_result,
                                confirmed_plan_sha256=saving.confirmed_plan_sha256)
                        else:
                            handoff = InterfaceIntentHandoffRequest.model_validate(payload)
                            response = plan_reviewed_intent(project_root=_trusted_root(project_root),
                                filename=handoff.review_filename, allowed_skill_ids=handoff.allowed_skill_ids)
                    except (ContextReviewError, ContextRetrievalError, OSError, KeyError):
                        self._send(HTTPStatus.CONFLICT, {"error": "reviewed intent/context is unavailable or stale; inspect and review again", "execution_performed": False})
                        return
                    except IntentError as exc:
                        status = HTTPStatus.CONFLICT if "already exists" in str(exc) or "changed" in str(exc) else HTTPStatus.BAD_REQUEST
                        self._send(status, {"error": redact_text(str(exc)), "execution_performed": False})
                        return
                    except (ModelClientError, ModelSettingsError) as exc:
                        from geoagent_harness.model.diagnostics import model_failure
                        self._send(HTTPStatus.BAD_GATEWAY, model_failure(exc))
                        return
                elif self.path == "/api/v1/tasks/events":
                    response = record_interface_task_event(
                        InterfaceTaskEventRequest.model_validate(payload),
                        project_root=project_root, task_root=task_root,
                    )
                elif self.path == "/api/v1/recipe-proposals/compile":
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
                elif self.path == "/api/v1/releases/prepare-recipe":
                    response = prepare_interface_recipe_release(
                        InterfaceRecipeReleaseRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/releases/create-recipe":
                    response = create_interface_recipe_release(
                        InterfaceRecipeReleaseCreationRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/snakemake/preview-export":
                    response = preview_interface_snakemake_export(
                        InterfaceSnakemakeExportPreviewRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/snakemake/export":
                    response = export_interface_snakemake_recipe(
                        InterfaceSnakemakeExportRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/validate-edit":
                    from geoagent_harness.task_actions.workflow import EditRequest, validate_edit
                    response = validate_edit(EditRequest.model_validate(payload), project_root=project_root)
                elif self.path == '/api/v1/workflow/runs':
                    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
                    response = run_action(RunRequest.model_validate(payload), project_root=project_root)
                elif self.path == '/api/v1/reusable-recipes':
                    from geoagent_harness.recipe_catalog.composition import RecipeRequest, recipe_action
                    response = recipe_action(RecipeRequest.model_validate(payload), project_root=project_root)
                elif self.path in {"/api/v1/workflow/prepare", "/api/v1/workflow/authorize", "/api/v1/workflow/execute"}:
                    from geoagent_harness.task_actions.workflow import WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow
                    workflow_request = WorkflowRequest.model_validate(payload)
                    expected_action = {"prepare": "prepare_workflow", "authorize": "authorize_workflow", "execute": "execute_workflow"}[self.path.rsplit("/", 1)[-1]]
                    if workflow_request.action != expected_action:
                        raise InterfaceApiError("workflow action does not match endpoint")
                    response = {"prepare_workflow": prepare_workflow, "authorize_workflow": authorize_workflow, "execute_workflow": execute_workflow}[expected_action](workflow_request, project_root=project_root)
                elif self.path.startswith('/api/v1/operations/'):
                    from geoagent_harness.operations.api import ScanRequest,PackageRequest,scan,package_action
                    if self.path=='/api/v1/operations/scan':response=scan(ScanRequest.model_validate(payload),project_root)
                    else:
                        operation_request=PackageRequest.model_validate(payload)
                        expected='test_operation_package' if self.path.endswith('/test-package') else 'install_operation_package'
                        if operation_request.action!=expected:raise InterfaceApiError('Package action does not match the endpoint')
                        response=package_action(operation_request,project_root)
                elif self.path == "/api/v1/method-memory":
                    from geoagent_harness.task_actions.method_memory import MethodRequest, method_action
                    response = method_action(MethodRequest.model_validate(payload), project_root=project_root)
                elif self.path == "/api/v1/planner/diagnostics":
                    from geoagent_harness.model.telemetry import read as read_diagnostics
                    class DiagnosticRequest(BaseModel):
                        model_config=ConfigDict(extra='forbid')
                        conversation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
                    diagnostic_request=DiagnosticRequest.model_validate(payload)
                    response=read_diagnostics(project_root,diagnostic_request.conversation_id)
                elif self.path == "/api/v1/planner/submit":
                    from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
                    response = submission_action(SubmissionRequest.model_validate(payload), project_root=project_root)
                elif self.path == "/api/v1/chat/history":
                    from geoagent_harness.task_actions.chat_history import HistoryRequest,history_action
                    response=history_action(HistoryRequest.model_validate(payload),project_root=project_root)
                elif self.path == "/api/v1/analysis/view":
                    from geoagent_harness.tabular.dataset_views import DatasetViewRequest,dataset_view
                    response=dataset_view(DatasetViewRequest.model_validate(payload),project_root=project_root)
                elif self.path == "/api/v1/planner/conversation":
                    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
                    response = conversation_turn(TurnRequest.model_validate(payload), project_root=project_root)
                elif self.path == "/api/v1/plans/create":
                    response = plan_interface_task(
                        InterfacePlanRequest.model_validate(payload),
                        project_root=project_root,
                    )
                elif self.path == "/api/v1/plans/save-generated":
                    generated = InterfaceGeneratedPlanSaveRequest.model_validate(payload)
                    response = save_interface_reviewed_plan(
                        generated, project_root=project_root,
                    )
                    response["human_review_performed"] = False
                    response["storage_kind"] = "generated_proposal"
                elif self.path == "/api/v1/plans/save-reviewed":
                    response = save_interface_reviewed_plan(
                        InterfaceReviewedPlanSaveRequest.model_validate(payload),
                        project_root=project_root,
                    )
                    response["task_reference"] = attach_task_artifact(
                        root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        task_id=payload.get("task_id"), project_root=_trusted_root(project_root),
                        artifact_path="plans/" + response["plan_filename"],
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
                    response["task_reference"] = attach_task_artifact(
                        root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        task_id=payload.get("task_id"), project_root=_trusted_root(project_root),
                        artifact_path="approvals/" + response["approval_filename"],
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
                    response["task_reference"] = attach_task_artifact(
                        root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                        task_id=payload.get("task_id"), project_root=_trusted_root(project_root),
                        artifact_path="workflow-recipes/" + response["recipe_filename"],
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
                    response["task_references"] = []
                    if execution_request.task_id is not None:
                        for key in ("run_result_path", "evidence_path"):
                            try:
                                path = Path(response[key])
                                relative = path.relative_to(_trusted_root(project_root)).as_posix() if path.is_absolute() else path.as_posix()
                                linked = attach_task_artifact(
                                    root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                                    task_id=execution_request.task_id, project_root=_trusted_root(project_root), artifact_path=relative,
                                )
                            except (ValueError, KeyError):
                                linked = {"status": "failed", "reason": "Run completed, but durable task reference was unavailable"}
                            response["task_references"].append(linked)
                        response["task_references"].append(attach_task_artifact(
                            root=task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history"),
                            task_id=execution_request.task_id, project_root=_trusted_root(project_root),
                            artifact_path="approvals/" + execution_request.approval_filename,
                        ))
            except (json.JSONDecodeError, ValidationError):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "request payload is invalid", **({'approval_performed':False,'execution_performed':False} if self.path=='/api/v1/method-memory' else {})})
                return
            except RecipeCompilationError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "recipe proposal could not be compiled"})
                return
            except InterfaceApiError as exc:
                status = HTTPStatus.CONFLICT if (
                    "digest no longer matches" in str(exc)
                    or "already exists" in str(exc)
                ) else HTTPStatus.BAD_REQUEST
                self._send(status, {"error": str(exc), **({"approval_performed":False,"execution_performed":False} if self.path=="/api/v1/method-memory" else {})})
                return
            except TaskHistoryError as exc:
                self._send(HTTPStatus.CONFLICT, {"error": str(exc)})
                return
            except RecipeStorageError:
                self._send(HTTPStatus.CONFLICT, {"error": "reviewed recipe could not be stored immutably"})
                return
            except RecipeApprovalError:
                self._send(HTTPStatus.CONFLICT, {"error": "recipe approval could not be recorded"})
                return
            except ApprovedRecipeError as exc:
                from geoagent_harness.task_actions.workflow import execution_failure_payload
                self._send(HTTPStatus.CONFLICT, execution_failure_payload(exc))
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
            except (
                ReleaseAssessmentError,
                AuthoritativeReleaseStorageError,
                OperationalHistoryError,
                SnakemakeExportContractError,
                SnakemakeExportGenerationError,
                SnakemakeExportPolicyError,
            ) as exc:
                self._send(HTTPStatus.CONFLICT, {
                    "error": str(exc),
                    "release_created": False,
                    "execution_performed": False,
                })
                return
            except PlannerAgentError as exc:
                from geoagent_harness.model.telemetry import error_code as diagnostic_error_code
                message = str(exc)
                if getattr(exc, "reason", None) == "unverified_reuse_claim":
                    error = "planner claimed unverified recipe reuse"
                    code = "planner_reuse_unverified"
                    finding = "; ".join(exc.findings)
                elif getattr(exc, "reason", None) == "request_coverage_incomplete":
                    error = "planner omitted a requested operation"
                    code = "planner_scope_incomplete"
                    finding = "; ".join(exc.findings)
                elif getattr(exc, "reason", None) == "schema_repair_deferred":
                    error = "planner did not return the requested workflow"
                    code = "planner_repair_deferred"
                    finding = "; ".join(exc.findings) or "The model repeated a schema-repair promise after one correction."
                elif getattr(exc, "reason", None) == "output_truncated":
                    error = "planner response hit the model output limit"
                    code = "planner_output_truncated"
                    finding = "; ".join(exc.findings)
                elif getattr(exc, "reason", None) == "capability_gap_unresolved":
                    error = "planner could not resolve the text-capability request"
                    code = "planner_capability_gap"
                    finding = "; ".join(exc.findings)
                elif "invalid JSON" in message:
                    error = "planner model returned invalid JSON"
                    code = "planner_invalid_json"
                    finding = "The model response was not one complete JSON object."
                elif "invalid plan schema" in message:
                    error = "planner model returned an invalid plan schema"
                    code = "planner_invalid_schema"
                    finding = "; ".join(exc.findings) or "The model response did not satisfy the required workflow-plan schema."
                elif diagnostic_error_code(exc)=='planner_review_needs_revision':
                    error='planner role review requested revision'
                    code='planner_review_needs_revision'
                    finding='An advisory role requested changes after the bounded correction. This is separate from deterministic operation validation.'
                elif "deterministic policy" in message:
                    error = "planner plan was rejected by deterministic policy"
                    code = "planner_policy_rejected"
                    finding = "; ".join(exc.findings) or message.partition("deterministic policy:")[2].strip() or "The candidate plan violated deterministic policy."
                else:
                    error = "planner could not produce a validated plan"
                    code = "planner_generation_failed"
                    finding = "The configured model did not produce a validated plan."
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {
                    "error": error,
                    "code": code,
                    "finding": finding[:1000],
                    "retryable": True,
                    "schema_findings": exc.findings,
                    "correction_attempted": exc.correction_attempted,
                    "planner_diagnostics": getattr(exc, "planner_diagnostics", None),
                    "retry_guidance": ("The Planner must follow the declared text-capability contract: propose a bounded missing candidate when ON, or use the supplied compatible installed operation. Do not substitute numeric arithmetic. Your workflow is preserved; do not add approval flags or edit stored files." if code == "planner_capability_gap" else "The model cited a reuse source that was unavailable, uninspected or unrelated. The saved workflow is preserved. Retry the same task; ordinary planning needs no recipe selection or extra authorization instructions." if code == "planner_reuse_unverified" else "The model omitted a requested operation after one correction. Your saved workflow is preserved. Inspect the listed missing method or operation and retry with a compatible selected model. No execution happened. Do not edit stored plans or add authorization instructions." if code == "planner_scope_incomplete" else "The endpoint reported finish_reason=length. Increase MODEL_MAX_TOKENS in the launcher environment and restart, or reduce the requested workflow scope. The saved workflow is preserved; no partial plan was accepted." if code == "planner_output_truncated" else "This is a model-output failure, not missing user authorization or technical details. Your saved workflow is preserved. Retry the same task after checking the running backend and selected skills; do not add approval or validation rules to your request." if code == "planner_repair_deferred" else "The model did not follow the plan structure after a bounded correction. Inspect the listed fields and retry generation with the same reviewed scope; do not modify stored review files." if code in {"planner_invalid_json", "planner_invalid_schema"} else "The role review requested changes after one correction. Inspect the supplied finding and current workflow. No authorization instruction can repair this review disagreement; no extra retry or execution happened." if code=="planner_review_needs_revision" else "The proposed workflow did not satisfy registered operation contracts. Review the listed finding and current workflow. Internal task IDs and approval flags are not user authorization instructions; changing permissions cannot repair an invalid plan."),
                    "plan_returned": False,
                    "plan_saved": False,
                    "approval_performed": False,
                    "execution_performed": False,
                })
                return
            except PlannerPolicyError as exc:
                message = ("Edited workflow failed policy: " + str(exc)[:240]) if self.path == "/api/v1/plans/validate-edit" else "reviewed plan was rejected by deterministic policy"
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
                return
            except (ContextPackError, ModelClientError, ModelSettingsError) as exc:
                if self.path in {"/api/v1/planner/conversation", "/api/v1/planner/submit", "/api/v1/method-memory", "/api/v1/reusable-recipes"}:
                    if isinstance(exc, ModelClientError):
                        message, code = str(exc), exc.code
                        guidance = ("The model did not finish before MODEL_TIMEOUT_SECONDS. The saved workflow is preserved; nothing executed and the timed-out call is not retried automatically. Request diagnostics show the stage, bytes and elapsed time when available. In Settings → Model service, try Reasoning effort None for a compatible model, fewer selected skills, or a smaller installed model. Saved project reasoning settings apply to new requests without a launcher restart. Inspect Ollama logs if it still times out; timeout alone does not prove context overflow."
                                    if code == "model_timeout" else "The configured endpoint rejected JSON-schema output. Check its structured-output support. For a compatible endpoint that only supports JSON mode, explicitly set MODEL_RESPONSE_FORMAT=json_object in the launcher environment and restart. No automatic fallback or retry occurred." if code == "model_response_format_rejected" else "Planner reached its call or configured time limit. Review request diagnostics; reduce the scope or adjust trusted launcher settings. Nothing executed." if code == "planner_budget_exhausted" else "Check the exact installed model name and endpoint in Settings. HTTP 404 can indicate a missing model or unsupported route.")
                    elif isinstance(exc, ModelSettingsError):
                        message, code = "Planner model configuration is invalid or missing", "model_configuration_failed"
                        guidance = "Check MODEL_NAME and MODEL_BASE_URL in the launcher environment, then restart the launcher."
                    else:
                        message, code = "Planner context could not be prepared", "planner_context_failed"
                        guidance = "Check trusted context files and the current workflow. Disable previous messages or reduce selected skills if the prompt exceeds its budget."
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": message, "code": code, "planner_diagnostics": getattr(exc,"planner_diagnostics",None), "retry_guidance": guidance, "approval_performed": False, "execution_performed": False})
                    return
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
            except WritePolicyError as exc:
                self._send(HTTPStatus.CONFLICT, {'error': str(exc), 'code': 'write_policy_blocked', 'execution_performed': False})
                return
            except (SkillRegistryError, OSError, ValueError) as exc:
                if self.path in {'/api/v1/analysis/view','/api/v1/chat/history'}:
                    self._send(HTTPStatus.UNPROCESSABLE_ENTITY,{'error':redact_text(str(exc))[:600],'approval_performed':False,'execution_performed':False})
                    return
                if self.path in {'/api/v1/reusable-recipes', '/api/v1/workflow/runs'}:
                    from geoagent_harness.recipe_catalog.composition import RecipePreparationError
                    message = str(exc) if isinstance(exc,RecipePreparationError) else 'Request failed recipe contracts, isolated fixture checks or safe run storage requirements. The saved workflow is preserved; inspect its parameters and retry.'
                    self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error':message, 'approval_performed':False,'execution_performed':False})
                    return
                if self.path == '/api/v1/method-memory':
                    self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error':'Method proposal failed its schema or safe storage checks. Edit the proposal or select fewer sources; nothing saved or executed.', 'approval_performed':False, 'execution_performed':False})
                    return
                if self.path.startswith('/api/v1/operations/'):
                    from geoagent_harness.operations.packages import PackageError
                    message = str(exc)[:600] if isinstance(exc, PackageError) else 'Operation package or discovery request failed its typed bounds, source/fixture checks or safe storage requirements'
                    self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error':message,'approval_performed':False,'execution_performed':False})
                    return
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
    from geoagent_harness.mcp_server.settings import parse_flag
    with write_policy_session(root, enabled=load_settings().enable_write_tools,
            locked=parse_flag(os.environ.get('ACTIONCHARTER_READ_ONLY_LOCK'))):
        server = server_factory((host, port), _handler(root))
        try:
            server.serve_forever()
        finally:
            server.server_close()
