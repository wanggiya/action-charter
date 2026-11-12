"""Loopback-only typed API for the guided interface."""

from importlib import import_module

# Keep lightweight CLI adapters importable without loading GIS execution services.
# Public exports remain compatible and load the server only when requested.
__all__ = [
    "MAX_INTERFACE_REQUEST_BYTES",
    "InterfaceApiError",
    "compile_interface_recipe_proposal",
    "interface_recipe_template_catalog",
    "interface_data_resource_inventory",
    "interface_execution_inventory",
    "interface_critic_evidence_inventory",
    "save_interface_recipe_trace",
    "run_interface_critic",
    "record_interface_critic_result",
    "prepare_interface_recipe_release",
    "create_interface_recipe_release",
    "preview_interface_snakemake_export",
    "export_interface_snakemake_recipe",
    "plan_interface_task",
    "save_interface_reviewed_plan",
    "prepare_interface_plan_approval",
    "record_interface_plan_approval",
    "verify_interface_plan_approval",
    "preview_interface_plan_execution",
    "compile_interface_plan_recipe",
    "save_interface_plan_recipe",
    "interface_planner_skill_catalog",
    "interface_saved_plan_inventory",
    "interface_saved_recipe_inventory",
    "prepare_interface_recipe_approval",
    "prepare_interface_execution_preview",
    "execute_interface_recipe",
    "record_interface_recipe_approval",
    "verify_interface_recipe_approval",
    "save_interface_reviewed_recipe",
    "serve_interface_api",
]


# Resolve shared action exports without importing the HTTP server.
_ACTION_OWNERS = {'InterfaceApiError': 'geoagent_harness.task_actions.common',
 'InterfaceApprovalDecision': 'geoagent_harness.contracts.actions',
 'InterfaceApprovalVerificationRequest': 'geoagent_harness.contracts.actions',
 'InterfaceExecutionPreviewRequest': 'geoagent_harness.contracts.actions',
 'InterfaceGeneratedPlanSaveRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanApprovalDecisionRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanApprovalPreparationRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanApprovalVerificationRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanExecutionPreviewRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanRecipeCompilationRequest': 'geoagent_harness.contracts.actions',
 'InterfacePlanRecipeSaveRequest': 'geoagent_harness.contracts.actions',
 'InterfaceRecipeExecutionRequest': 'geoagent_harness.contracts.actions',
 'InterfaceReviewedPlanSaveRequest': 'geoagent_harness.contracts.actions',
 'TaskActionError': 'geoagent_harness.task_actions.common',
 'compile_interface_plan_recipe': 'geoagent_harness.task_actions.artifacts',
 'execute_interface_recipe': 'geoagent_harness.task_actions.execution',
 'interface_execution_inventory': 'geoagent_harness.task_actions.execution',
 'prepare_interface_execution_preview': 'geoagent_harness.task_actions.execution',
 'prepare_interface_plan_approval': 'geoagent_harness.task_actions.artifacts',
 'prepare_interface_recipe_approval': 'geoagent_harness.task_actions.artifacts',
 'preview_interface_plan_execution': 'geoagent_harness.task_actions.artifacts',
 'record_interface_plan_approval': 'geoagent_harness.task_actions.artifacts',
 'record_interface_recipe_approval': 'geoagent_harness.task_actions.artifacts',
 'save_interface_plan_recipe': 'geoagent_harness.task_actions.artifacts',
 'save_interface_reviewed_plan': 'geoagent_harness.task_actions.artifacts',
 'verify_interface_plan_approval': 'geoagent_harness.task_actions.artifacts',
 'verify_interface_recipe_approval': 'geoagent_harness.task_actions.artifacts'}


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if name in ('InterfaceApiError', 'TaskActionError'):
        owner = import_module('geoagent_harness.task_actions.common')
    elif name in ('InterfaceApprovalDecision', 'InterfaceApprovalVerificationRequest', 'InterfaceExecutionPreviewRequest', 'InterfaceGeneratedPlanSaveRequest', 'InterfacePlanApprovalDecisionRequest', 'InterfacePlanApprovalPreparationRequest', 'InterfacePlanApprovalVerificationRequest', 'InterfacePlanExecutionPreviewRequest', 'InterfacePlanRecipeCompilationRequest', 'InterfacePlanRecipeSaveRequest', 'InterfaceRecipeExecutionRequest', 'InterfaceReviewedPlanSaveRequest'):
        owner = import_module('geoagent_harness.contracts.actions')
    elif name in ('compile_interface_plan_recipe', 'prepare_interface_plan_approval', 'prepare_interface_recipe_approval', 'preview_interface_plan_execution', 'record_interface_plan_approval', 'record_interface_recipe_approval', 'save_interface_plan_recipe', 'save_interface_reviewed_plan', 'verify_interface_plan_approval', 'verify_interface_recipe_approval'):
        owner = import_module('geoagent_harness.task_actions.artifacts')
    elif name in ('execute_interface_recipe', 'interface_execution_inventory', 'prepare_interface_execution_preview'):
        owner = import_module('geoagent_harness.task_actions.execution')
    else:
        owner = import_module('geoagent_harness.apps.http.server')
    value = getattr(owner, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
