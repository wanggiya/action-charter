"""Existing release review coordination, independent of HTTP."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.workspace import WorkspaceLayout, runtime_reference, runtime_reference_path
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from geoagent_harness.platform.skill_registry import SkillRegistryError, load_skill_registry
from geoagent_harness.platform.evidence import CriticEvidenceError, MAX_TRACE_BYTES, MAX_REPORT_BYTES, build_critic_evidence
from geoagent_harness.core.ledger.trace import WorkflowTrace
from geoagent_harness.capabilities.recipes.execution import RecipeEvidenceStorageError, load_recipe_evidence, load_recipe_run_result, recipe_evidence_sha256, recipe_run_result_sha256
from geoagent_harness.core.ledger.releases import AuthoritativeReleaseStorageError, load_authoritative_release, persist_authoritative_release
from geoagent_harness.core.ledger.releases import ReleaseAssessmentError, assess_recipe_release_candidate, authoritative_release_candidate_sha256
from geoagent_harness.core.ledger.operational_history import AgentRole, OperationalIdentity
from geoagent_harness.core.ledger.operational_history import OperationalHistoryError, operational_event_log_path
from geoagent_harness.core.ledger.operational_history import record_gis_workflow_history
from geoagent_harness.capabilities.recipes.execution import recipe_run_result_path
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.contracts.interface_requests import (
    InterfaceRecipeReleaseCreationRequest,
    InterfaceRecipeReleaseRequest,
)


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


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
prepare_interface_recipe_release = _task_entrypoint(prepare_interface_recipe_release, audit=False)
create_interface_recipe_release = _task_entrypoint(create_interface_recipe_release)
