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

from pydantic import BaseModel, ConfigDict, Field, ValidationError

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
from geoagent_harness.redaction import redact_value
from geoagent_harness.mcp_server.approved_recipe import (
    ApprovedRecipeError,
    run_approved_recipe as execute_approved_recipe,
)
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.recipes import (
    RecipeApprovalError,
    RecipePolicyError,
    RecipeStorageError,
    load_recipe,
    recipe_sha256,
    save_recipe,
    validate_recipe_policy,
    create_recipe_approval,
    load_recipe_approval,
    verify_recipe_approval,
    build_recipe_execution_envelope,
)


MAX_INTERFACE_REQUEST_BYTES = 65_536
MAX_INTERFACE_RECIPES = 200
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


def _trusted_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceApiError("trusted project root is unavailable") from exc
    if not resolved.is_dir():
        raise InterfaceApiError("trusted project root must be a directory")
    return resolved


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
            }
            for template in catalog.templates
        ],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }


def compile_interface_recipe_proposal(
    payload: object,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Validate and compile one proposal without persistence or execution."""

    proposal = RecipeProposal.model_validate(payload)
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
    proposal = RecipeProposal.model_validate(payload)
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
                self._send(HTTPStatus.BAD_REQUEST, {"error": "recipe proposal is invalid"})
                return
            except RecipeCompilationError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "recipe proposal could not be compiled"})
                return
            except InterfaceApiError as exc:
                status = HTTPStatus.CONFLICT if "digest no longer matches" in str(exc) else HTTPStatus.BAD_REQUEST
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
