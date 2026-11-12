"""Existing legacy export coordination, independent of HTTP."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.workspace import WorkspaceLayout, runtime_reference, runtime_reference_path
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from geoagent_harness.platform.skill_registry import SkillRegistryError, load_skill_registry
from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError, create_recipe_approval, load_recipe_approval, verify_recipe_approval
from geoagent_harness.capabilities.recipes.execution import RecipeStorageError, load_recipe, recipe_path, save_recipe
from geoagent_harness.data.export.snakemake.contracts import SnakemakeExportContractError, validate_snakemake_export_contract
from geoagent_harness.data.export.snakemake.generator import SnakemakeExportGenerationError, generate_snakemake_recipe_export
from geoagent_harness.data.export.snakemake.planner import SnakemakeExportPolicyError, plan_snakemake_recipe_export
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.contracts.actions import InterfaceApprovalDecision, InterfaceApprovalVerificationRequest, InterfaceExecutionPreviewRequest, InterfaceRecipeExecutionRequest, InterfaceReviewedPlanSaveRequest, InterfaceGeneratedPlanSaveRequest, InterfacePlanApprovalPreparationRequest, InterfacePlanApprovalDecisionRequest, InterfacePlanApprovalVerificationRequest, InterfacePlanExecutionPreviewRequest, InterfacePlanRecipeCompilationRequest, InterfacePlanRecipeSaveRequest
from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan, prepare_interface_plan_approval, record_interface_plan_approval, verify_interface_plan_approval, preview_interface_plan_execution, compile_interface_plan_recipe, _planner_recipe_definition, save_interface_plan_recipe, prepare_interface_recipe_approval, record_interface_recipe_approval, verify_interface_recipe_approval
from geoagent_harness.contracts.interface_requests import (
    InterfaceSnakemakeExportPreviewRequest,
    InterfaceSnakemakeExportRequest,
)


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


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
preview_interface_snakemake_export = _task_entrypoint(preview_interface_snakemake_export, audit=False)
export_interface_snakemake_recipe = _task_entrypoint(export_interface_snakemake_recipe)
