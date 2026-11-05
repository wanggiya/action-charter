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
 'InterfaceApprovalDecision': 'geoagent_harness.task_actions.contracts',
 'InterfaceApprovalVerificationRequest': 'geoagent_harness.task_actions.contracts',
 'InterfaceExecutionPreviewRequest': 'geoagent_harness.task_actions.contracts',
 'InterfaceGeneratedPlanSaveRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanApprovalDecisionRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanApprovalPreparationRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanApprovalVerificationRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanExecutionPreviewRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanRecipeCompilationRequest': 'geoagent_harness.task_actions.contracts',
 'InterfacePlanRecipeSaveRequest': 'geoagent_harness.task_actions.contracts',
 'InterfaceRecipeExecutionRequest': 'geoagent_harness.task_actions.contracts',
 'InterfaceReviewedPlanSaveRequest': 'geoagent_harness.task_actions.contracts',
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
    value = getattr(import_module(_ACTION_OWNERS.get(name, ".server"), __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
