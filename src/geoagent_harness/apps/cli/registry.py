"""Explicit command registration in historical order; no command dispatch logic."""

from geoagent_harness.apps.cli.history import (
    record_task_event_command,
    build_task_context_command,
    retrieve_task_context_command,
    review_task_context_command,
    inspect_reviewed_context_command,
    list_reviewed_context_command,
    record_gis_operational_history_command,
    inspect_operational_history_command,
)
from geoagent_harness.apps.cli.planning import (
    reason_task_intent_command,
    inspect_intent_proposal_command,
    review_task_intent_command,
    inspect_reviewed_intent_command,
    plan_reviewed_intent_command,
    save_reviewed_intent_plan_command,
    plan_task_command,
)
from geoagent_harness.apps.cli.interface import (
    serve_interface_api_command,
    project_interface_workflow_command,
    export_interface_workflows_command,
)
from geoagent_harness.apps.cli.common import (
    _raise_typed_failure,
)
from geoagent_harness.apps.cli.settings import (
    agent_info_command,
    write_policy_command,
)
from geoagent_harness.apps.cli.spatial import (
    inspect_vector_command,
    assess_spatial_data_contract_command,
    assess_pilot_demo_readiness_command,
    plan_convert_vector_command,
    convert_vector_command,
    validate_vector_conversion_command,
    load_vector_to_postgis_command,
    validate_postgis_layer_command,
)
from geoagent_harness.apps.cli.builder.inspection import (
    inspect_builder_candidate_command,
    assess_builder_candidate_tests_command,
)
from geoagent_harness.apps.cli.postgis_inspection import (
    inspect_postgis_table_command,
    compare_postgis_tables_command,
    assess_postgis_change_command,
)
from geoagent_harness.apps.cli.geoserver import (
    inspect_geoserver_layer_command,
    plan_geoserver_publication_command,
    record_geoserver_publication_approval_command,
    execute_geoserver_publication_command,
    verify_geoserver_publication_command,
)
from geoagent_harness.apps.cli.postgis_promotion import (
    plan_postgis_promotion_command,
    record_postgis_promotion_approval_command,
    execute_postgis_promotion_command,
    verify_postgis_promotion_command,
)
from geoagent_harness.apps.cli.postgis_rollback import (
    plan_postgis_rollback_command,
    record_postgis_rollback_approval_command,
    execute_postgis_rollback_command,
    verify_postgis_rollback_command,
)
from geoagent_harness.apps.cli.workflows import (
    run_vector_postgis_workflow_command,
    build_execution_envelope_command,
    mcp_http_smoke_command,
    execute_approved_plan_command,
    inspect_workflow_state_command,
    assess_workflow_resume_command,
)
from geoagent_harness.apps.cli.approvals import (
    plan_digest_command,
    approve_plan_command,
    verify_plan_approval_command,
)
from geoagent_harness.apps.cli.critic import (
    build_critic_evidence_command,
    critique_task_command,
    record_critic_result_command,
)
from geoagent_harness.apps.cli.releases import (
    assess_workflow_release_command,
    create_workflow_release_command,
    inspect_authoritative_release_command,
)
from geoagent_harness.apps.cli.recipe_planning import (
    recipe_template_catalog_command,
    compile_recipe_proposal_command,
    propose_recipe_command,
    propose_and_compile_recipe_command,
    review_recipe_request_command,
    save_reviewed_recipe_command,
    list_approved_recipes_command,
)
from geoagent_harness.apps.cli.schemas import (
    schema_policies_command,
    assess_schema_compatibility_command,
    assess_schema_migration_command,
)
from geoagent_harness.apps.cli.recipes import (
    save_recipe_command,
    approve_recipe_command,
    verify_recipe_approval_command,
    run_approved_recipe_command,
    execute_approved_recipe_command,
    build_recipe_evidence_command,
)
from geoagent_harness.apps.cli.skills import (
    plan_skill_scaffold_command,
    generate_skill_scaffold_command,
    validate_skill_scaffold_command,
    assess_skill_definition_command,
    generate_skill_contract_command,
    validate_skill_contract_command,
    generate_skill_candidate_command,
    assess_skill_candidate_command,
    plan_skill_promotion_command,
    promote_skill_candidate_command,
)
from geoagent_harness.apps.cli.exports import (
    plan_snakemake_export_command,
    export_approved_recipe_snakemake_command,
    validate_snakemake_export_command,
)
from geoagent_harness.apps.cli.raster import (
    inspect_raster_command,
    plan_convert_raster_command,
    convert_raster_command,
    validate_raster_conversion_command,
)
from geoagent_harness.apps.cli.builder.review import (
    builder_propose_command,
    materialize_builder_proposal_command,
    create_builder_review_package_command,
    record_builder_review_decision_command,
)
from geoagent_harness.apps.cli.builder.promotion import (
    plan_builder_promotion_command,
    create_builder_promotion_plan_command,
    promote_builder_candidate_command,
    verify_builder_promotion_command,
    create_builder_promotion_verification_command,
)
from geoagent_harness.apps.cli.builder.activation import (
    create_builder_activation_review_command,
    plan_builder_activation_command,
    create_builder_activation_plan_command,
    activate_builder_bundle_command,
    verify_builder_activation_command,
    create_builder_trust_evidence_command,
)
from geoagent_harness.apps.cli.workspace import register_workspace_commands
from geoagent_harness.apps.cli.tabular import register as register_tabular_cli
from geoagent_harness.apps.cli.discovery import register as register_discovery_cli
from geoagent_harness.apps.chat.cli import register as register_chat_cli
from geoagent_harness.apps.cli.operations import register as register_operations_cli
from geoagent_harness.apps.cli.planning_tasks import register as register_planning_tasks_cli
from geoagent_harness.apps.cli.method_memory import register as register_method_memory_cli
from geoagent_harness.apps.cli.workflow_tools import register as register_workflow_tools_cli
from geoagent_harness.apps.cli.postgres import install as install_postgres_cli


def register_commands(app):
    register_workspace_commands(app)
    app.command('record-task-event')(record_task_event_command)
    app.command('build-task-context')(build_task_context_command)
    app.command('retrieve-task-context')(retrieve_task_context_command)
    app.command('review-task-context')(review_task_context_command)
    app.command('inspect-reviewed-context')(inspect_reviewed_context_command)
    app.command('reason-task-intent')(reason_task_intent_command)
    app.command('inspect-intent-proposal')(inspect_intent_proposal_command)
    app.command('review-task-intent')(review_task_intent_command)
    app.command('inspect-reviewed-intent')(inspect_reviewed_intent_command)
    app.command('plan-reviewed-intent')(plan_reviewed_intent_command)
    app.command('save-reviewed-intent-plan')(save_reviewed_intent_plan_command)
    app.command('list-reviewed-context')(list_reviewed_context_command)
    app.command('serve-interface-api')(serve_interface_api_command)
    app.command('agent-info')(agent_info_command)
    app.command('inspect-vector')(inspect_vector_command)
    app.command('assess-spatial-data-contract')(assess_spatial_data_contract_command)
    app.command('assess-pilot-demo-readiness')(assess_pilot_demo_readiness_command)
    app.command('plan-convert-vector')(plan_convert_vector_command)
    app.command('convert-vector')(convert_vector_command)
    app.command('inspect-builder-candidate')(inspect_builder_candidate_command)
    app.command('assess-builder-candidate-tests')(assess_builder_candidate_tests_command)
    app.command('validate-vector-conversion')(validate_vector_conversion_command)
    app.command('load-vector-to-postgis')(load_vector_to_postgis_command)
    app.command('validate-postgis-layer')(validate_postgis_layer_command)
    app.command('inspect-postgis-table')(inspect_postgis_table_command)
    app.command('inspect-geoserver-layer')(inspect_geoserver_layer_command)
    app.command('plan-geoserver-publication')(plan_geoserver_publication_command)
    app.command('record-geoserver-publication-approval')(record_geoserver_publication_approval_command)
    app.command('execute-geoserver-publication')(execute_geoserver_publication_command)
    app.command('verify-geoserver-publication')(verify_geoserver_publication_command)
    app.command('compare-postgis-tables')(compare_postgis_tables_command)
    app.command('assess-postgis-change')(assess_postgis_change_command)
    app.command('plan-postgis-promotion')(plan_postgis_promotion_command)
    app.command('record-postgis-promotion-approval')(record_postgis_promotion_approval_command)
    app.command('execute-postgis-promotion')(execute_postgis_promotion_command)
    app.command('verify-postgis-promotion')(verify_postgis_promotion_command)
    app.command('plan-postgis-rollback')(plan_postgis_rollback_command)
    app.command('record-postgis-rollback-approval')(record_postgis_rollback_approval_command)
    app.command('execute-postgis-rollback')(execute_postgis_rollback_command)
    app.command('verify-postgis-rollback')(verify_postgis_rollback_command)
    app.command('run-vector-postgis-workflow')(run_vector_postgis_workflow_command)
    app.command('plan-task')(plan_task_command)
    app.command('plan-digest')(plan_digest_command)
    app.command('approve-plan')(approve_plan_command)
    app.command('verify-plan-approval')(verify_plan_approval_command)
    app.command('build-execution-envelope')(build_execution_envelope_command)
    app.command('mcp-http-smoke')(mcp_http_smoke_command)
    app.command('execute-approved-plan')(execute_approved_plan_command)
    app.command('inspect-workflow-state')(inspect_workflow_state_command)
    app.command('assess-workflow-resume')(assess_workflow_resume_command)
    app.command('build-critic-evidence')(build_critic_evidence_command)
    app.command('critique-task')(critique_task_command)
    app.command('record-critic-result')(record_critic_result_command)
    app.command('assess-workflow-release')(assess_workflow_release_command)
    app.command('create-workflow-release')(create_workflow_release_command)
    app.command('inspect-authoritative-release')(inspect_authoritative_release_command)
    app.command('recipe-template-catalog')(recipe_template_catalog_command)
    app.command('schema-policies')(schema_policies_command)
    app.command('assess-schema-compatibility')(assess_schema_compatibility_command)
    app.command('assess-schema-migration')(assess_schema_migration_command)
    app.command('save-recipe')(save_recipe_command)
    app.command('approve-recipe')(approve_recipe_command)
    app.command('verify-recipe-approval')(verify_recipe_approval_command)
    app.command('run-approved-recipe')(run_approved_recipe_command)
    app.command('execute-approved-recipe')(execute_approved_recipe_command)
    app.command('build-recipe-evidence')(build_recipe_evidence_command)
    app.command('compile-recipe-proposal')(compile_recipe_proposal_command)
    app.command('propose-recipe')(propose_recipe_command)
    app.command('propose-and-compile-recipe')(propose_and_compile_recipe_command)
    app.command('review-recipe-request')(review_recipe_request_command)
    app.command('save-reviewed-recipe')(save_reviewed_recipe_command)
    app.command('plan-skill-scaffold')(plan_skill_scaffold_command)
    app.command('generate-skill-scaffold')(generate_skill_scaffold_command)
    app.command('validate-skill-scaffold')(validate_skill_scaffold_command)
    app.command('plan-snakemake-export')(plan_snakemake_export_command)
    app.command('export-approved-recipe-snakemake')(export_approved_recipe_snakemake_command)
    app.command('validate-snakemake-export')(validate_snakemake_export_command)
    app.command('list-approved-recipes')(list_approved_recipes_command)
    app.command('assess-skill-definition')(assess_skill_definition_command)
    app.command('generate-skill-contract')(generate_skill_contract_command)
    app.command('validate-skill-contract')(validate_skill_contract_command)
    app.command('generate-skill-candidate')(generate_skill_candidate_command)
    app.command('assess-skill-candidate')(assess_skill_candidate_command)
    app.command('plan-skill-promotion')(plan_skill_promotion_command)
    app.command('promote-skill-candidate')(promote_skill_candidate_command)
    app.command('inspect-raster')(inspect_raster_command)
    app.command('plan-convert-raster')(plan_convert_raster_command)
    app.command('convert-raster')(convert_raster_command)
    app.command('validate-raster-conversion')(validate_raster_conversion_command)
    app.command('builder-propose')(builder_propose_command)
    app.command('materialize-builder-proposal')(materialize_builder_proposal_command)
    app.command('create-builder-review-package')(create_builder_review_package_command)
    app.command('record-builder-review-decision')(record_builder_review_decision_command)
    app.command('plan-builder-promotion')(plan_builder_promotion_command)
    app.command('create-builder-promotion-plan')(create_builder_promotion_plan_command)
    app.command('promote-builder-candidate')(promote_builder_candidate_command)
    app.command('verify-builder-promotion')(verify_builder_promotion_command)
    app.command('create-builder-promotion-verification')(create_builder_promotion_verification_command)
    app.command('create-builder-activation-review')(create_builder_activation_review_command)
    app.command('plan-builder-activation')(plan_builder_activation_command)
    app.command('create-builder-activation-plan')(create_builder_activation_plan_command)
    app.command('activate-builder-bundle')(activate_builder_bundle_command)
    app.command('verify-builder-activation')(verify_builder_activation_command)
    app.command('create-builder-trust-evidence')(create_builder_trust_evidence_command)
    app.command('record-gis-operational-history')(record_gis_operational_history_command)
    app.command('inspect-operational-history')(inspect_operational_history_command)
    app.command('project-interface-workflow')(project_interface_workflow_command)
    app.command('export-interface-workflows')(export_interface_workflows_command)
    register_tabular_cli(app)
    register_discovery_cli(app)
    register_chat_cli(app)
    register_operations_cli(app)
    register_planning_tasks_cli(app)
    register_method_memory_cli(app)
    register_workflow_tools_cli(app)
    app.command('write-policy')(write_policy_command)
    install_postgres_cli(app)
