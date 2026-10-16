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


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".server", __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
