"""CLI composition and public compatibility exports; commands live in their groups."""

import json
from pathlib import Path
from geoagent_harness.core.ledger.task_history.service import TaskHistoryError
from geoagent_harness.task_actions.command_actions import task_history_service__history_directory as runtime_history_directory
from typing import Annotated, NoReturn
from datetime import datetime
import typer
from geoagent_harness.task_actions.command_actions import agent_manifest__load_agent_manifest as load_agent_manifest
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.task_actions.command_actions import failures__failure_from_exception as failure_from_exception
from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError
from geoagent_harness.agents.roles.planner.recipe_proposal import RecipeProposalAgentError
from geoagent_harness.task_actions.command_actions import recipe_proposals__render_recipe_operator_review as render_recipe_operator_review, recipe_proposals__review_recipe_request as review_recipe_request
from geoagent_harness.apps.cli.workspace import WorkspaceTyper
from geoagent_harness.task_actions.command_actions import workspace__runtime_store_path as runtime_store_path
from geoagent_harness.apps.cli.registry import (
    register_commands,
    record_task_event_command,
    build_task_context_command,
    retrieve_task_context_command,
    review_task_context_command,
    inspect_reviewed_context_command,
    reason_task_intent_command,
    inspect_intent_proposal_command,
    review_task_intent_command,
    inspect_reviewed_intent_command,
    plan_reviewed_intent_command,
    save_reviewed_intent_plan_command,
    list_reviewed_context_command,
    serve_interface_api_command,
    _raise_typed_failure,
    agent_info_command,
    inspect_vector_command,
    assess_spatial_data_contract_command,
    assess_pilot_demo_readiness_command,
    plan_convert_vector_command,
    convert_vector_command,
    inspect_builder_candidate_command,
    assess_builder_candidate_tests_command,
    validate_vector_conversion_command,
    load_vector_to_postgis_command,
    validate_postgis_layer_command,
    inspect_postgis_table_command,
    inspect_geoserver_layer_command,
    plan_geoserver_publication_command,
    record_geoserver_publication_approval_command,
    execute_geoserver_publication_command,
    verify_geoserver_publication_command,
    compare_postgis_tables_command,
    assess_postgis_change_command,
    plan_postgis_promotion_command,
    record_postgis_promotion_approval_command,
    execute_postgis_promotion_command,
    verify_postgis_promotion_command,
    plan_postgis_rollback_command,
    record_postgis_rollback_approval_command,
    execute_postgis_rollback_command,
    verify_postgis_rollback_command,
    run_vector_postgis_workflow_command,
    plan_task_command,
    plan_digest_command,
    approve_plan_command,
    verify_plan_approval_command,
    build_execution_envelope_command,
    mcp_http_smoke_command,
    execute_approved_plan_command,
    inspect_workflow_state_command,
    assess_workflow_resume_command,
    build_critic_evidence_command,
    critique_task_command,
    record_critic_result_command,
    assess_workflow_release_command,
    create_workflow_release_command,
    inspect_authoritative_release_command,
    recipe_template_catalog_command,
    schema_policies_command,
    assess_schema_compatibility_command,
    assess_schema_migration_command,
    save_recipe_command,
    approve_recipe_command,
    verify_recipe_approval_command,
    run_approved_recipe_command,
    execute_approved_recipe_command,
    build_recipe_evidence_command,
    compile_recipe_proposal_command,
    propose_recipe_command,
    propose_and_compile_recipe_command,
    review_recipe_request_command,
    save_reviewed_recipe_command,
    plan_skill_scaffold_command,
    generate_skill_scaffold_command,
    validate_skill_scaffold_command,
    plan_snakemake_export_command,
    export_approved_recipe_snakemake_command,
    validate_snakemake_export_command,
    list_approved_recipes_command,
    assess_skill_definition_command,
    generate_skill_contract_command,
    validate_skill_contract_command,
    generate_skill_candidate_command,
    assess_skill_candidate_command,
    plan_skill_promotion_command,
    promote_skill_candidate_command,
    inspect_raster_command,
    plan_convert_raster_command,
    convert_raster_command,
    validate_raster_conversion_command,
    builder_propose_command,
    materialize_builder_proposal_command,
    create_builder_review_package_command,
    record_builder_review_decision_command,
    plan_builder_promotion_command,
    create_builder_promotion_plan_command,
    promote_builder_candidate_command,
    verify_builder_promotion_command,
    create_builder_promotion_verification_command,
    create_builder_activation_review_command,
    plan_builder_activation_command,
    create_builder_activation_plan_command,
    activate_builder_bundle_command,
    verify_builder_activation_command,
    create_builder_trust_evidence_command,
    record_gis_operational_history_command,
    inspect_operational_history_command,
    project_interface_workflow_command,
    export_interface_workflows_command,
    write_policy_command,
)

app = WorkspaceTyper(
    name="geoagent",
    help="Run allowlisted ActionCharter operations.",
    no_args_is_help=True,
)

register_commands(app)


if __name__ == "__main__":
    app()
