"""Exact approved dispatch, durable progress and independent attempt inventory."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from geoagent_harness.redaction import redact_value
from geoagent_harness.skill_registry import load_skill_registry
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.write_policy import (
    effective as effective_write_settings,
    snapshot as write_policy_snapshot,
)
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
    recipe_sha256,
    load_recipe_approval,
    verify_recipe_approval,
    build_recipe_execution_envelope,
)
from .storage_paths import runtime_store_path, ensure_state_root
from .common import InterfaceApiError, _trusted_root, _bounded_outcome
from .contracts import (
    InterfaceApprovalDecision,
    InterfaceApprovalVerificationRequest,
    InterfaceExecutionPreviewRequest,
    InterfaceRecipeExecutionRequest,
    InterfacePlanApprovalPreparationRequest,
    InterfacePlanApprovalDecisionRequest,
    InterfacePlanApprovalVerificationRequest,
)

import tempfile
from threading import Lock
from geoagent_harness.task_history import record_task_attempt_state
from .approved_recipe import run_approved_recipe as execute_approved_recipe
from .artifacts import (
    prepare_interface_plan_approval,
    record_interface_plan_approval,
    verify_interface_plan_approval,
    prepare_interface_recipe_approval,
    record_interface_recipe_approval,
    verify_interface_recipe_approval,
    SAFE_RECIPE_FILENAME,
)

MAX_INTERFACE_EXECUTION_ATTEMPTS = 200
_EXECUTION_LOCK = Lock()
_ACTIVE_EXECUTIONS: set[tuple[str, str]] = set()
_ACTIVE_PROGRESS: set[str] = set()
_EXECUTION_PROGRESS: dict[str, dict[str, Any]] = {}


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
        else runtime_store_path(_trusted_root(project_root), "workflow-state", "interface-executions")
    )
    if root.exists() and root.is_symlink():
        raise InterfaceApiError("execution progress root cannot be a symlink")
    resolved = root.resolve()
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
    if progress_root is None:
        ensure_state_root(project_root)
    destination.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
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
    if payload.get("status") == "interrupted":
        if not record_task_attempt_state(root=runtime_store_path(_trusted_root(project_root), "task-history"),
                task_id=payload.get("task_id"), attempt_sha256=digest, state="interrupted"):
            payload["task_history_warning"] = "Interrupted attempt is recorded in durable progress, but its task note could not be recorded"
    return payload


def interface_execution_inventory(
    project_root: Path,
    *,
    progress_root: Path | None = None,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    result_root: Path | None = None,
    evidence_root: Path | None = None,
) -> dict[str, Any]:
    """Return bounded durable attempt summaries without execution authority."""

    project = _trusted_root(project_root)
    recipes = recipe_root if recipe_root is not None else runtime_store_path(project, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(project, "approvals")
    results = result_root if result_root is not None else runtime_store_path(project, "recipe-runs")
    evidence_files = evidence_root if evidence_root is not None else runtime_store_path(project, "recipe-evidence")
    for directory in (recipes, approvals, results, evidence_files):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise InterfaceApiError("authority root is unsafe")
    root = (
        progress_root
        if progress_root is not None
        else runtime_store_path(project, "workflow-state", "interface-executions")
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
    registry = load_skill_registry(project)
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
        authority_link = "unavailable"
        authority_reason = "Legacy attempt has no recorded approval identity"
        recipe_name = state.get("recipe_filename")
        approval_name = state.get("approval_filename")
        recipe_digest = state.get("recipe_sha256")
        approval_id = state.get("approval_id")
        if approval_name is not None or approval_id is not None:
            authority_link = "blocked"
            authority_reason = "Recorded recipe or approval identity is incomplete"
            if (
                isinstance(recipe_name, str) and SAFE_RECIPE_FILENAME.fullmatch(recipe_name)
                and isinstance(recipe_digest, str) and re.fullmatch(r"[a-f0-9]{64}", recipe_digest)
                and isinstance(approval_name, str) and re.fullmatch(r"recipe-approval-[a-z0-9-]+\.json", approval_name)
                and isinstance(approval_id, str) and approval_name == f"{approval_id}.json"
            ):
                try:
                    recipe = load_recipe(recipes / recipe_name, recipe_root=recipes)
                    approval = load_recipe_approval(approvals / approval_name, approval_root=approvals)
                    if (recipe.recipe_id != state.get("recipe_id") or recipe_sha256(recipe) != recipe_digest
                            or approval.approval_id != approval_id):
                        authority_reason = "Stored recipe or approval identity does not match the attempt"
                    else:
                        started_at = datetime.fromisoformat(state["started_at"])
                        if started_at.tzinfo is None or started_at.utcoffset() is None:
                            raise ValueError("start timestamp has no timezone")
                        verification = verify_recipe_approval(
                            approval=approval, recipe=recipe, registry=registry, now=started_at,
                        )
                        authority_link = "verified" if verification.approved else "blocked"
                        authority_reason = verification.reason
                except (RecipeStorageError, RecipeApprovalError, RecipePolicyError, ValueError, KeyError, TypeError):
                    authority_reason = "Stored recipe or approval cannot be independently verified"
        result_link = "unavailable"
        result_reason = "This attempt has no recorded durable result and evidence digests"
        recorded_outputs: list[dict[str, Any]] = []
        outputs_truncated = False
        run_digest = state.get("run_result_sha256")
        evidence_digest = state.get("evidence_sha256")
        if run_digest is not None or evidence_digest is not None:
            result_link = "blocked"
            result_reason = "Durable result and evidence identities are incomplete"
            if (isinstance(run_digest, str) and re.fullmatch(r"[a-f0-9]{64}", run_digest)
                    and isinstance(evidence_digest, str) and re.fullmatch(r"[a-f0-9]{64}", evidence_digest)
                    and isinstance(state.get("recipe_id"), str)
                    and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,100}", state["recipe_id"])):
                try:
                    result = load_recipe_run_result(
                        results / f"{state['recipe_id']}.{run_digest}.json", result_root=results,
                    )
                    evidence = load_recipe_evidence(
                        evidence_files / f"{state['recipe_id']}.{evidence_digest}.json",
                        evidence_root=evidence_files,
                    )
                    if (recipe_run_result_sha256(result) != run_digest
                            or recipe_evidence_sha256(evidence) != evidence_digest
                            or recipe_run_result_sha256(evidence.run_result) != run_digest
                            or result.recipe_id != state.get("recipe_id")
                            or result.recipe_sha256 != recipe_digest
                            or result.approval_id != approval_id
                            or result.final_status != state.get("status")
                            or evidence.recipe_id != result.recipe_id
                            or evidence.recipe_sha256 != result.recipe_sha256
                            or evidence.approval_id != result.approval_id
                            or evidence.final_status != result.final_status):
                        result_reason = "Durable result or evidence does not match the recorded attempt"
                    elif authority_link != "verified":
                        result_reason = "Durable evidence matches, but recipe approval authority is not verified"
                    else:
                        result_link = "verified"
                        result_reason = "Exact durable result and evidence match the authorized attempt"
                        outputs = [item for item in evidence.artifacts if item.role.value == "output"]
                        outputs_truncated = len(outputs) > 20
                        recorded_outputs = [{
                            "artifact_id": item.artifact_id,
                            "path": item.path,
                            "sha256": item.sha256,
                            "producer_step_id": item.producer_step_id,
                        } for item in outputs[:20]]
                except (RecipeEvidenceStorageError, ValueError, TypeError):
                    result_reason = "Durable result or evidence cannot be independently verified"
        attempts.append({
            "execution_preview_sha256": digest,
            "status": state.get("status"),
            "recipe_id": state.get("recipe_id"),
            "recipe_filename": state.get("recipe_filename"),
            "recipe_sha256": state.get("recipe_sha256"),
            "approval_id": approval_id if isinstance(approval_id, str) else None,
            "authority_link": authority_link,
            "authority_reason": authority_reason,
            "result_link": result_link,
            "result_reason": result_reason,
            "recorded_outputs": recorded_outputs,
            **({"partial_outputs": state["partial_outputs"][:20],
                "recovery_guidance": state.get("recovery_guidance")}
               if "partial_outputs" in state else {}),
            "outputs_truncated": outputs_truncated,
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
    recipes = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
        "execution_available": effective_write_settings(load_settings(), root).enable_write_tools,
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
    recipes = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
    configured = effective_write_settings(load_settings(), root)

    def project_path(path: Path) -> Path:
        return path if path.is_absolute() else root / path

    settings = configured.model_copy(update={
        "project_root": root,
        "recipe_root": recipes,
        "approval_root": approvals,
        "input_root": project_path(configured.input_root),
        "output_root": project_path(configured.output_root),
        "contract_root": project_path(configured.contract_root),
        "report_root": (runtime_store_path(root,'reports') if configured.report_root == Path('reports') else project_path(configured.report_root)),
        "recipe_run_root": (runtime_store_path(root,'recipe-runs') if configured.recipe_run_root == Path('recipe-runs') else project_path(configured.recipe_run_root)),
        "recipe_evidence_root": (runtime_store_path(root,'recipe-evidence') if configured.recipe_evidence_root == Path('recipe-evidence') else project_path(configured.recipe_evidence_root)),
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
            "task_id": request.task_id,
            "recipe_id": envelope.recipe_id,
            "recipe_filename": request.recipe_filename,
            "recipe_sha256": envelope.recipe_sha256,
            "approval_id": envelope.approval_id,
            "approval_filename": request.approval_filename,
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

    record_task_attempt_state(root=runtime_store_path(root, "task-history"), task_id=request.task_id,
                              attempt_sha256=progress_key, state="running")

    from geoagent_harness.tabular.schemas import is_table_write
    from geoagent_harness.tabular.service import read_bytes as read_table_bytes, TabularError
    table_targets = {
        step.step_id: step.arguments["target_path"]
        for step in envelope.steps if is_table_write(step.skill_id)
    }
    existing_table_targets = set()
    for target in table_targets.values():
        try:
            read_table_bytes(root, target, "output")
            existing_table_targets.add(target)
        except TabularError:
            pass

    def progress_callback(step_id: str, skill_id: str, status: str) -> None:
        with _EXECUTION_LOCK:
            state = _EXECUTION_PROGRESS[progress_key]
            for item in state["steps"]:
                if item["step_id"] == step_id and item["skill_id"] == skill_id:
                    item["status"] = status
                    break
            if status in {"failed", "validation_failed"}:
                state["failed_step_id"] = step_id
            if status in {"completed", "validated_success", "validation_failed"}:
                state["execution_performed"] = True
            snapshot = json.loads(json.dumps(state))
        _persist_execution_progress(root, snapshot, progress_root=progress_root)

    execution_returned = False
    try:
        result = execute_approved_recipe(
            execution_envelope=envelope.model_dump(mode="json"),
            recipe_filename=request.recipe_filename,
            approval_filename=request.approval_filename,
            settings=settings,
            progress_callback=progress_callback,
        )
        execution_returned = True
    except Exception as execution_error:
        partial_outputs = []
        for step_id, target in table_targets.items():
            if target in existing_table_targets:
                continue
            try:
                data = read_table_bytes(root, target, "output")
            except TabularError:
                continue
            partial_outputs.append({"step_id": step_id, "path": target,
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                    "status": "present_after_failure"})
        with _EXECUTION_LOCK:
            state = _EXECUTION_PROGRESS[progress_key]
            from geoagent_harness.recipes.control import ExecutionCancelled
            cancelled = isinstance(execution_error, ExecutionCancelled)
            state["status"] = "cancelled" if cancelled else "failed"
            for pending in state['steps']:
                if pending['status'] == 'queued':
                    pending['status'] = 'skipped'
            state["finished_at"] = datetime.now(timezone.utc).isoformat()
            state["failed_step_id"] = state["failed_step_id"] or next(
                (item["step_id"] for item in state["steps"] if item["status"] == "running"),
                None,
            )
            state["recovery_guidance"] = (
                "Inspect the failed step and durable evidence before creating "
                "a new approval for any retry. Existing CSV outputs cannot be overwritten; "
                "choose fresh target paths. No retry is performed automatically."
            )
            if table_targets:
                state["partial_outputs"] = partial_outputs
                state["execution_performed"] = state["execution_performed"] or bool(partial_outputs)
            failed_snapshot = json.loads(json.dumps(state))
        _persist_execution_progress(root, failed_snapshot, progress_root=progress_root)
        record_task_attempt_state(root=runtime_store_path(root, "task-history"), task_id=request.task_id,
                                  attempt_sha256=progress_key, state="cancelled" if cancelled else "failed")
        raise
    finally:
        if not execution_returned:
            with _EXECUTION_LOCK:
                _ACTIVE_EXECUTIONS.discard(execution_key)
                _ACTIVE_PROGRESS.discard(progress_key)
    with _EXECUTION_LOCK:
        state = _EXECUTION_PROGRESS[progress_key]
        state["status"] = result.execution_record.final_status
        state["finished_at"] = datetime.now(timezone.utc).isoformat()
        state["failed_step_id"] = getattr(result.run_result, "failed_step_id", None)
        state["execution_performed"] = True
        state["run_result_sha256"] = result.execution_record.run_result_sha256
        state["evidence_sha256"] = result.execution_record.evidence_sha256
        final_snapshot = json.loads(json.dumps(state))
    try:
        _persist_execution_progress(root, final_snapshot, progress_root=progress_root)
    finally:
        with _EXECUTION_LOCK:
            _ACTIVE_EXECUTIONS.discard(execution_key)
            _ACTIVE_PROGRESS.discard(progress_key)
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
