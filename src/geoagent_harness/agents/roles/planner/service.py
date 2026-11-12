"""High-level service for producing a validated plan."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Collection

from geoagent_harness.agents.runtime.manifest import load_agent_manifest
from geoagent_harness.agents.memory.context_pack import build_context_pack
from geoagent_harness.platform.model_gateway import SharedModelClient
from geoagent_harness.platform.model_gateway import load_model_settings
from geoagent_harness.agents.roles.planner.agent import ModelClientProtocol, run_planner_agent
from geoagent_harness.contracts.planning import PlannerResult


def plan_task(
    *,
    original_request: str,
    project_root: Path,
    agents_root: Path,
    model_client: ModelClientProtocol | None = None,
    allowed_skill_ids: Collection[str] | None = None,
) -> PlannerResult:
    """Build context, call the model, and validate its plan."""

    context_pack = build_context_pack(
        original_request,
        project_root,
        allowed_skill_ids=allowed_skill_ids,
    )

    manifest = load_agent_manifest(
        "planner",
        agents_root,
    )

    client = model_client

    if client is None:
        client = SharedModelClient(
            load_model_settings()
        )

    return run_planner_agent(
        context_pack=context_pack,
        manifest=manifest,
        model_client=client,
    )

from typing import Any
from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest, InterfaceGeneratedPlanSaveRequest
from geoagent_harness.contracts.errors import InterfaceApiError


def save_reviewed_plan(
    request: InterfaceReviewedPlanSaveRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
    registry_loader=None,
) -> dict[str, Any]:
    """Revalidate and immutably store one exact reviewed Planner result."""

    from geoagent_harness.platform.project import _trusted_root
    from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
    from geoagent_harness.platform.workspace import WorkspaceLayout
    from geoagent_harness.platform.storage import repositories
    from geoagent_harness.platform.storage import RepositoryError
    from geoagent_harness.platform.skill_registry import load_skill_registry
    from geoagent_harness.core.policy.approvals import ApprovalError, plan_sha256
    from geoagent_harness.core.policy.plan import validate_plan_policy

    root = _trusted_root(project_root)
    registry = (registry_loader or load_skill_registry)(root)
    implemented = {skill.id for skill in registry.implemented_skills()}
    selected = set(request.allowed_skill_ids)
    if not selected.issubset(implemented):
        raise InterfaceApiError("reviewed plan includes an unavailable skill selection")
    validate_plan_policy(request.planner_result.plan, available_skills=selected)
    digest = plan_sha256(request.planner_result.plan)
    if digest != request.confirmed_plan_sha256:
        raise InterfaceApiError("reviewed plan digest no longer matches")

    destination = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    if destination.exists() and destination.is_symlink():
        raise InterfaceApiError("plan root cannot be a symlink")
    if plan_root is None: ensure_state_root(root)
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or not destination.is_dir():
        raise InterfaceApiError("plan root is unsafe")
    resolved_destination = destination.resolve(strict=True)
    if plan_root is None and resolved_destination.parent != WorkspaceLayout.load(root).state_root:
        raise InterfaceApiError("plan root is outside the trusted project")

    filename = f"planner-plan.{digest}.json"
    path = resolved_destination / filename
    content = request.planner_result.model_dump_json(indent=2) + "\n"
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise InterfaceApiError("existing reviewed plan artifact is unsafe")
        try:
            existing = repositories(root).documents('plans', directory=resolved_destination).load((path).name)
        except ApprovalError as exc:
            raise InterfaceApiError("existing reviewed plan artifact is invalid") from exc
        # The generated proposal's wording/model are conversation-local context,
        # not execution authority. Reuse an identical immutable workflow without
        # copying its older request into the new conversation or modifying bytes.
        generated_reuse = isinstance(request, InterfaceGeneratedPlanSaveRequest) and (
            existing.plan == request.planner_result.plan and existing.agent_id == request.planner_result.agent_id
        )
        if existing != request.planner_result and not generated_reuse:
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
            **({"workflow_definition_reused": True, "result_metadata_saved": existing == request.planner_result}
               if isinstance(request, InterfaceGeneratedPlanSaveRequest) else {}),
        }
    try:
        repositories(root).documents('plans',directory=resolved_destination).create(filename,content)
    except FileExistsError as exc:
        raise InterfaceApiError("reviewed plan already exists") from exc
    except RepositoryError as exc:
        raise InterfaceApiError(str(exc)) from exc

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
