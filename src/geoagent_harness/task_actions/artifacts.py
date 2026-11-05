"""Saved plan, review and approval actions. No transport or model authority."""
from __future__ import annotations
import hashlib
import json
import os
import re
from geoagent_harness.storage import repositories, RepositoryError
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any
from geoagent_harness.workspace import WorkspaceLayout
from geoagent_harness.redaction import redact_value
from geoagent_harness.skill_registry import load_skill_registry
from geoagent_harness.planner import PlannerResult, validate_plan_policy
from geoagent_harness.approvals import (
    ApprovalError,
    create_approval,
    load_approval,
    load_planner_result,
    plan_sha256,
    verify_approval,
)
from geoagent_harness.executor import ExecutorPolicyError, build_execution_envelope
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.recipes import (
    RecipePolicyError,
    load_recipe,
    recipe_path,
    recipe_sha256,
    save_recipe,
    validate_recipe_policy,
    create_recipe_approval,
    load_recipe_approval,
    verify_recipe_approval,
)
from geoagent_harness.recipes.schemas import WorkflowRecipe
from .storage_paths import runtime_store_path, ensure_state_root
from .common import InterfaceApiError, _trusted_root
from .contracts import (
    InterfaceApprovalDecision,
    InterfaceApprovalVerificationRequest,
    InterfaceReviewedPlanSaveRequest,
    InterfaceGeneratedPlanSaveRequest,
    InterfacePlanApprovalPreparationRequest,
    InterfacePlanApprovalDecisionRequest,
    InterfacePlanApprovalVerificationRequest,
    InterfacePlanExecutionPreviewRequest,
    InterfacePlanRecipeCompilationRequest,
    InterfacePlanRecipeSaveRequest,
)

SAFE_RECIPE_FILENAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")


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


def prepare_interface_plan_approval(
    request: InterfacePlanApprovalPreparationRequest,
    *,
    project_root: Path,
    plan_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare exact plan approval scope without recording a decision."""

    root = _trusted_root(project_root)
    destination = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    if destination.is_symlink() or not destination.is_dir():
        raise InterfaceApiError("plan root is unsafe or unavailable")
    resolved_destination = destination.resolve(strict=True)
    path = resolved_destination / request.plan_filename
    if path.is_symlink() or path.parent != resolved_destination:
        raise InterfaceApiError("plan artifact is unsafe")
    try:
        planner_result = repositories(root).documents('plans', directory=resolved_destination).load((path).name)
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
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    planner_result = repositories(root).documents('plans', directory=plans.resolve(strict=True)).load((plans.resolve(strict=True) / request.plan_filename).name)
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    if approvals.is_symlink() or not approvals.is_dir():
        raise InterfaceApiError("approval root is unsafe or unavailable")
    resolved_approvals = approvals.resolve(strict=True)
    approval_path = resolved_approvals / request.approval_filename
    if approval_path.is_symlink() or approval_path.parent != resolved_approvals:
        raise InterfaceApiError("approval artifact is unsafe")
    try:
        planner_result = repositories(root).documents('plans', directory=plans.resolve(strict=True)).load((plans.resolve(strict=True) / request.plan_filename).name)
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
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
        planner_result = repositories(root).documents('plans', directory=plans.resolve()).load((plans.resolve() / request.plan_filename).name)
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
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
    result = repositories(root).documents('plans', directory=plans.resolve()).load((plans.resolve() / request.plan_filename).name)
    recipe = _planner_recipe_definition(result, request.confirmed_plan_sha256)
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


def _planner_recipe_definition(result: PlannerResult, plan_digest: str) -> WorkflowRecipe:
    from geoagent_harness.planner.recipe_definition import planner_recipe_definition, PlannerRecipeDefinitionError
    try:
        return planner_recipe_definition(result, plan_digest)
    except PlannerRecipeDefinitionError as exc:
        raise InterfaceApiError(str(exc)) from exc


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
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
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
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
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
    recipes = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
        project_root=root,
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
    recipes = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
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
