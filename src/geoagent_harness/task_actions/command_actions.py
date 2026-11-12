"""Lazy, explicit task-action catalog for existing CLI service entry points.

Exports are fixed first-party functions, not user-selected Python or MCP tools.
No caching: a command gets the current service binding and its existing test hooks.
Only the selected service module loads; optional runtimes stay optional.
"""

__all__ = ('agent_manifest__load_agent_manifest',
 'approvals__create_approval',
 'approvals__load_approval',
 'approvals__load_planner_result',
 'approvals__plan_sha256',
 'approvals__verify_approval',
 'builder__activate_builder_bundle',
 'builder__assemble_builder_review_package',
 'builder__assess_builder_candidate_tests',
 'builder__create_builder_activation_review_decision',
 'builder__create_builder_review_decision',
 'builder__inspect_builder_candidate',
 'builder__load_builder_request',
 'builder__materialize_builder_proposal',
 'builder__persist_builder_activation_plan',
 'builder__persist_builder_activation_review_decision',
 'builder__persist_builder_promotion_plan',
 'builder__persist_builder_promotion_verification',
 'builder__persist_builder_review_decision',
 'builder__persist_builder_review_package',
 'builder__persist_builder_trust_evidence',
 'builder__plan_builder_activation',
 'builder__plan_builder_promotion',
 'builder__promote_builder_candidate',
 'builder__propose_builder_candidate',
 'builder__verify_builder_activation',
 'builder__verify_builder_promotion_bundle',
 'context_retrieval__load_reviewed_context',
 'context_retrieval__retrieve_task_context',
 'context_retrieval__save_reviewed_context',
 'critic__build_critic_result_record',
 'critic__critique_task',
 'critic__persist_critic_result_record',
 'critic_evidence__build_critic_evidence',
 'executor__build_execution_envelope',
 'executor_service__execute_approved_plan',
 'executor_service__execute_approved_recipe_via_mcp',
 'failures__failure_from_exception',
 'geoserver_inspection__inspect_geoserver_layer',
 'geoserver_publication__create_geoserver_publication_approval',
 'geoserver_publication__execute_geoserver_publication',
 'geoserver_publication__load_json',
 'geoserver_publication__plan_geoserver_publication',
 'geoserver_publication__verify_geoserver_publication',
 'intent_handoff__plan_reviewed_intent',
 'intent_handoff__save_reviewed_intent_plan',
 'intent_inventory__reviewed_context_inventory',
 'intent_review__inspect_intent_for_review',
 'intent_review__load_reviewed_intent',
 'intent_review__read_intent_file',
 'intent_review__save_reviewed_intent',
 'intent_service__reason_task_intent',
 'operational_history__build_operational_timeline',
 'operational_history__load_operational_events',
 'operational_history__operational_event_log_path',
 'operational_history__record_gis_workflow_history',
 'orchestrator_workflow__run_vector_postgis_workflow',
 'planner__plan_task',
 'platform_settings__load_settings',
 'postgis_change_assessment__assess_postgis_change',
 'postgis_comparison__compare_postgis_tables',
 'postgis_inspection__inspect_postgis_table',
 'postgis_promotion_approval__create_postgis_promotion_approval',
 'postgis_promotion_approval__load_postgis_promotion_plan_result',
 'postgis_promotion_approval__persist_postgis_promotion_approval',
 'postgis_promotion_execution__execute_postgis_promotion',
 'postgis_promotion_execution__persist_postgis_promotion_execution',
 'postgis_promotion_plan__plan_postgis_promotion',
 'postgis_promotion_verification__persist_postgis_promotion_verification',
 'postgis_promotion_verification__verify_postgis_promotion',
 'postgis_rollback_approval__create_postgis_rollback_approval',
 'postgis_rollback_approval__persist_postgis_rollback_approval',
 'postgis_rollback_execution__execute_postgis_rollback',
 'postgis_rollback_execution__persist_postgis_rollback_execution',
 'postgis_rollback_plan__persist_postgis_rollback_plan',
 'postgis_rollback_plan__plan_postgis_rollback',
 'postgis_rollback_verification__persist_postgis_rollback_verification',
 'postgis_rollback_verification__verify_postgis_rollback',
 'recipe_catalog__load_recipe_template_catalog',
 'recipe_proposals__compile_recipe_proposal',
 'recipe_proposals__load_recipe_operator_review',
 'recipe_proposals__load_recipe_proposal',
 'recipe_proposals__propose_and_compile_recipe',
 'recipe_proposals__propose_recipe_with_shared_model',
 'recipe_proposals__render_recipe_operator_review',
 'recipe_proposals__review_recipe_request',
 'recipe_proposals__save_reviewed_recipe',
 'recipes__build_recipe_approval_inventory',
 'recipes__create_recipe_approval',
 'recipes__load_recipe',
 'recipes__load_recipe_approval',
 'recipes__load_recipe_draft',
 'recipes__load_recipe_run_result',
 'recipes__recipe_evidence_sha256',
 'recipes__recipe_sha256',
 'recipes__save_recipe',
 'recipes__validate_recipe_policy',
 'recipes__verify_recipe_approval',
 'recipes__write_recipe_evidence',
 'releases__assess_workflow_release_candidate',
 'releases__authoritative_release_candidate_sha256',
 'releases__inspect_authoritative_release',
 'releases__persist_authoritative_release',
 'schema_registry__assess_migration',
 'schema_registry__assess_schema_compatibility',
 'schema_registry__list_schema_policies',
 'skill_definitions__assess_declarative_skill',
 'skill_definitions__assess_skill_candidate_for_promotion',
 'skill_definitions__generate_declarative_skill_scaffold',
 'skill_definitions__generate_skill_contract_bundle',
 'skill_definitions__load_skill_candidate_test_record',
 'skill_definitions__load_skill_definition',
 'skill_definitions__materialize_trusted_adapter_candidate',
 'skill_definitions__plan_skill_candidate_promotion',
 'skill_definitions__promote_skill_candidate',
 'skill_definitions__validate_skill_contract_bundle',
 'skill_registry__load_skill_registry',
 'skill_scaffolding__generate_skill_scaffold',
 'skill_scaffolding__load_skill_scaffold_request',
 'skill_scaffolding__plan_skill_scaffold',
 'skill_scaffolding__validate_skill_scaffold_contract',
 'skills_convert_raster_policy__validate_convert_raster_request',
 'skills_convert_raster_service__convert_raster',
 'skills_convert_raster_validation__validate_raster_conversion',
 'skills_convert_vector__convert_vector',
 'skills_convert_vector__plan_vector_conversion',
 'skills_convert_vector__validate_vector_conversion',
 'skills_inspect_raster_service__inspect_raster',
 'skills_inspect_vector_service__inspect_vector',
 'skills_load_vector_to_postgis_service__load_vector_to_postgis',
 'snakemake_export__generate_snakemake_recipe_export',
 'snakemake_export__plan_snakemake_recipe_export',
 'snakemake_export__validate_snakemake_export_contract',
 'spatial_contracts__assess_spatial_data_contract',
 'spatial_contracts__load_spatial_data_contract',
 'task_history__append_task_event',
 'task_history__build_task_context',
 'task_history_service__history_directory',
 'verifier_postgis__validate_postgis_layer',
 'workflow_state__assess_resume',
 'workflow_state__load_state',
 'workspace__runtime_store_path',
 'write_policy__snapshot',
 'write_policy__update',
 'recipes__run_approved_recipe',
 'recipes__build_recipe_run_evidence')


def __getattr__(name):
    if name == 'agent_manifest__load_agent_manifest':
        from geoagent_harness.agents.runtime.manifest import load_agent_manifest as action
        return action
    if name == 'approvals__create_approval':
        from geoagent_harness.core.policy.approvals import create_approval as action
        return action
    if name == 'approvals__load_approval':
        from geoagent_harness.core.policy.approvals import load_approval as action
        return action
    if name == 'approvals__load_planner_result':
        from geoagent_harness.core.policy.approvals import load_planner_result as action
        return action
    if name == 'approvals__plan_sha256':
        from geoagent_harness.core.policy.approvals import plan_sha256 as action
        return action
    if name == 'approvals__verify_approval':
        from geoagent_harness.core.policy.approvals import verify_approval as action
        return action
    if name == 'builder__activate_builder_bundle':
        from geoagent_harness.evolution.builder import activate_builder_bundle as action
        return action
    if name == 'builder__assemble_builder_review_package':
        from geoagent_harness.evolution.builder import assemble_builder_review_package as action
        return action
    if name == 'builder__assess_builder_candidate_tests':
        from geoagent_harness.evolution.builder import assess_builder_candidate_tests as action
        return action
    if name == 'builder__create_builder_activation_review_decision':
        from geoagent_harness.evolution.builder import create_builder_activation_review_decision as action
        return action
    if name == 'builder__create_builder_review_decision':
        from geoagent_harness.evolution.builder import create_builder_review_decision as action
        return action
    if name == 'builder__inspect_builder_candidate':
        from geoagent_harness.evolution.builder import inspect_builder_candidate as action
        return action
    if name == 'builder__load_builder_request':
        from geoagent_harness.evolution.builder import load_builder_request as action
        return action
    if name == 'builder__materialize_builder_proposal':
        from geoagent_harness.evolution.builder import materialize_builder_proposal as action
        return action
    if name == 'builder__persist_builder_activation_plan':
        from geoagent_harness.evolution.builder import persist_builder_activation_plan as action
        return action
    if name == 'builder__persist_builder_activation_review_decision':
        from geoagent_harness.evolution.builder import persist_builder_activation_review_decision as action
        return action
    if name == 'builder__persist_builder_promotion_plan':
        from geoagent_harness.evolution.builder import persist_builder_promotion_plan as action
        return action
    if name == 'builder__persist_builder_promotion_verification':
        from geoagent_harness.evolution.builder import persist_builder_promotion_verification as action
        return action
    if name == 'builder__persist_builder_review_decision':
        from geoagent_harness.evolution.builder import persist_builder_review_decision as action
        return action
    if name == 'builder__persist_builder_review_package':
        from geoagent_harness.evolution.builder import persist_builder_review_package as action
        return action
    if name == 'builder__persist_builder_trust_evidence':
        from geoagent_harness.evolution.builder import persist_builder_trust_evidence as action
        return action
    if name == 'builder__plan_builder_activation':
        from geoagent_harness.evolution.builder import plan_builder_activation as action
        return action
    if name == 'builder__plan_builder_promotion':
        from geoagent_harness.evolution.builder import plan_builder_promotion as action
        return action
    if name == 'builder__promote_builder_candidate':
        from geoagent_harness.evolution.builder import promote_builder_candidate as action
        return action
    if name == 'builder__propose_builder_candidate':
        from geoagent_harness.evolution.builder import propose_builder_candidate as action
        return action
    if name == 'builder__verify_builder_activation':
        from geoagent_harness.evolution.builder import verify_builder_activation as action
        return action
    if name == 'builder__verify_builder_promotion_bundle':
        from geoagent_harness.evolution.builder import verify_builder_promotion_bundle as action
        return action
    if name == 'context_retrieval__load_reviewed_context':
        from geoagent_harness.agents.memory.context_retrieval import load_reviewed_context as action
        return action
    if name == 'context_retrieval__retrieve_task_context':
        from geoagent_harness.agents.memory.context_retrieval import retrieve_task_context as action
        return action
    if name == 'context_retrieval__save_reviewed_context':
        from geoagent_harness.agents.memory.context_retrieval import save_reviewed_context as action
        return action
    if name == 'critic__build_critic_result_record':
        from geoagent_harness.platform.storage.critic_records import build_critic_result_record as action
        return action
    if name == 'critic__critique_task':
        from geoagent_harness.agents.roles.critic import critique_task as action
        return action
    if name == 'critic__persist_critic_result_record':
        from geoagent_harness.platform.storage.critic_record_storage import persist_critic_result_record as action
        return action
    if name == 'critic_evidence__build_critic_evidence':
        from geoagent_harness.platform.evidence import build_critic_evidence as action
        return action
    if name == 'executor__build_execution_envelope':
        from geoagent_harness.agents.roles.executor import build_execution_envelope as action
        return action
    if name == 'executor_service__execute_approved_plan':
        from geoagent_harness.agents.roles.executor.service import execute_approved_plan as action
        return action
    if name == 'executor_service__execute_approved_recipe_via_mcp':
        from geoagent_harness.agents.roles.executor.service import execute_approved_recipe_via_mcp as action
        return action
    if name == 'failures__failure_from_exception':
        from geoagent_harness.contracts.failures import failure_from_exception as action
        return action
    if name == 'geoserver_inspection__inspect_geoserver_layer':
        from geoagent_harness.data.spatial.geoserver.inspection import inspect_geoserver_layer as action
        return action
    if name == 'geoserver_publication__create_geoserver_publication_approval':
        from geoagent_harness.data.spatial.geoserver.publication import create_geoserver_publication_approval as action
        return action
    if name == 'geoserver_publication__execute_geoserver_publication':
        from geoagent_harness.data.spatial.geoserver.publication import execute_geoserver_publication as action
        return action
    if name == 'geoserver_publication__load_json':
        from geoagent_harness.data.spatial.geoserver.publication import load_json as action
        return action
    if name == 'geoserver_publication__plan_geoserver_publication':
        from geoagent_harness.data.spatial.geoserver.publication import plan_geoserver_publication as action
        return action
    if name == 'geoserver_publication__verify_geoserver_publication':
        from geoagent_harness.data.spatial.geoserver.publication import verify_geoserver_publication as action
        return action
    if name == 'intent_handoff__plan_reviewed_intent':
        from geoagent_harness.agents.roles.intent.handoff import plan_reviewed_intent as action
        return action
    if name == 'intent_handoff__save_reviewed_intent_plan':
        from geoagent_harness.agents.roles.intent.handoff import save_reviewed_intent_plan as action
        return action
    if name == 'intent_inventory__reviewed_context_inventory':
        from geoagent_harness.agents.roles.intent.inventory import reviewed_context_inventory as action
        return action
    if name == 'intent_review__inspect_intent_for_review':
        from geoagent_harness.agents.roles.intent.review import inspect_intent_for_review as action
        return action
    if name == 'intent_review__load_reviewed_intent':
        from geoagent_harness.agents.roles.intent.review import load_reviewed_intent as action
        return action
    if name == 'intent_review__read_intent_file':
        from geoagent_harness.agents.roles.intent.review import read_intent_file as action
        return action
    if name == 'intent_review__save_reviewed_intent':
        from geoagent_harness.agents.roles.intent.review import save_reviewed_intent as action
        return action
    if name == 'intent_service__reason_task_intent':
        from geoagent_harness.agents.roles.intent.service import reason_task_intent as action
        return action
    if name == 'operational_history__build_operational_timeline':
        from geoagent_harness.core.ledger.operational_history import build_operational_timeline as action
        return action
    if name == 'operational_history__load_operational_events':
        from geoagent_harness.core.ledger.operational_history import load_operational_events as action
        return action
    if name == 'operational_history__operational_event_log_path':
        from geoagent_harness.core.ledger.operational_history import operational_event_log_path as action
        return action
    if name == 'operational_history__record_gis_workflow_history':
        from geoagent_harness.core.ledger.operational_history import record_gis_workflow_history as action
        return action
    if name == 'orchestrator_workflow__run_vector_postgis_workflow':
        from geoagent_harness.agents.runtime.orchestrator.workflow import run_vector_postgis_workflow as action
        return action
    if name == 'planner__plan_task':
        from geoagent_harness.agents.roles.planner import plan_task as action
        return action
    if name == 'platform_settings__load_settings':
        from geoagent_harness.platform.settings import load_settings as action
        return action
    if name == 'postgis_change_assessment__assess_postgis_change':
        from geoagent_harness.data.databases.postgis.change_assessment import assess_postgis_change as action
        return action
    if name == 'postgis_comparison__compare_postgis_tables':
        from geoagent_harness.data.databases.postgis.comparison import compare_postgis_tables as action
        return action
    if name == 'postgis_inspection__inspect_postgis_table':
        from geoagent_harness.data.databases.postgis.inspection import inspect_postgis_table as action
        return action
    if name == 'postgis_promotion_approval__create_postgis_promotion_approval':
        from geoagent_harness.data.databases.postgis.promotion.approval import create_postgis_promotion_approval as action
        return action
    if name == 'postgis_promotion_approval__load_postgis_promotion_plan_result':
        from geoagent_harness.data.databases.postgis.promotion.approval import load_postgis_promotion_plan_result as action
        return action
    if name == 'postgis_promotion_approval__persist_postgis_promotion_approval':
        from geoagent_harness.data.databases.postgis.promotion.approval import persist_postgis_promotion_approval as action
        return action
    if name == 'postgis_promotion_execution__execute_postgis_promotion':
        from geoagent_harness.data.databases.postgis.promotion.execution import execute_postgis_promotion as action
        return action
    if name == 'postgis_promotion_execution__persist_postgis_promotion_execution':
        from geoagent_harness.data.databases.postgis.promotion.execution import persist_postgis_promotion_execution as action
        return action
    if name == 'postgis_promotion_plan__plan_postgis_promotion':
        from geoagent_harness.data.databases.postgis.promotion.plan import plan_postgis_promotion as action
        return action
    if name == 'postgis_promotion_verification__persist_postgis_promotion_verification':
        from geoagent_harness.data.databases.postgis.promotion.verification import persist_postgis_promotion_verification as action
        return action
    if name == 'postgis_promotion_verification__verify_postgis_promotion':
        from geoagent_harness.data.databases.postgis.promotion.verification import verify_postgis_promotion as action
        return action
    if name == 'postgis_rollback_approval__create_postgis_rollback_approval':
        from geoagent_harness.data.databases.postgis.rollback.approval import create_postgis_rollback_approval as action
        return action
    if name == 'postgis_rollback_approval__persist_postgis_rollback_approval':
        from geoagent_harness.data.databases.postgis.rollback.approval import persist_postgis_rollback_approval as action
        return action
    if name == 'postgis_rollback_execution__execute_postgis_rollback':
        from geoagent_harness.data.databases.postgis.rollback.execution import execute_postgis_rollback as action
        return action
    if name == 'postgis_rollback_execution__persist_postgis_rollback_execution':
        from geoagent_harness.data.databases.postgis.rollback.execution import persist_postgis_rollback_execution as action
        return action
    if name == 'postgis_rollback_plan__persist_postgis_rollback_plan':
        from geoagent_harness.data.databases.postgis.rollback.plan import persist_postgis_rollback_plan as action
        return action
    if name == 'postgis_rollback_plan__plan_postgis_rollback':
        from geoagent_harness.data.databases.postgis.rollback.plan import plan_postgis_rollback as action
        return action
    if name == 'postgis_rollback_verification__persist_postgis_rollback_verification':
        from geoagent_harness.data.databases.postgis.rollback.verification import persist_postgis_rollback_verification as action
        return action
    if name == 'postgis_rollback_verification__verify_postgis_rollback':
        from geoagent_harness.data.databases.postgis.rollback.verification import verify_postgis_rollback as action
        return action
    if name == 'recipe_catalog__load_recipe_template_catalog':
        from geoagent_harness.capabilities.recipes.catalog import load_recipe_template_catalog as action
        return action
    if name == 'recipe_proposals__compile_recipe_proposal':
        from geoagent_harness.capabilities.recipes.proposals.compiler import compile_recipe_proposal as action
        return action
    if name == 'recipe_proposals__load_recipe_operator_review':
        from geoagent_harness.capabilities.recipes.proposals.review_storage import load_recipe_operator_review as action
        return action
    if name == 'recipe_proposals__load_recipe_proposal':
        from geoagent_harness.capabilities.recipes.proposals.storage import load_recipe_proposal as action
        return action
    if name == 'recipe_proposals__propose_and_compile_recipe':
        from geoagent_harness.agents.runtime.recipe_proposal import propose_and_compile_recipe as action
        return action
    if name == 'recipe_proposals__propose_recipe_with_shared_model':
        from geoagent_harness.agents.runtime.recipe_proposal import propose_recipe_with_shared_model as action
        return action
    if name == 'recipe_proposals__render_recipe_operator_review':
        from geoagent_harness.capabilities.recipes.proposals.rendering import render_recipe_operator_review as action
        return action
    if name == 'recipe_proposals__review_recipe_request':
        from geoagent_harness.agents.runtime.recipe_proposal import review_recipe_request as action
        return action
    if name == 'recipe_proposals__save_reviewed_recipe':
        from geoagent_harness.capabilities.recipes.proposals.operator_save import save_reviewed_recipe as action
        return action
    if name == 'recipes__build_recipe_approval_inventory':
        from geoagent_harness.capabilities.recipes.execution import build_recipe_approval_inventory as action
        return action
    if name == 'recipes__create_recipe_approval':
        from geoagent_harness.capabilities.recipes.execution import create_recipe_approval as action
        return action
    if name == 'recipes__load_recipe':
        from geoagent_harness.capabilities.recipes.execution import load_recipe as action
        return action
    if name == 'recipes__load_recipe_approval':
        from geoagent_harness.capabilities.recipes.execution import load_recipe_approval as action
        return action
    if name == 'recipes__load_recipe_draft':
        from geoagent_harness.capabilities.recipes.execution import load_recipe_draft as action
        return action
    if name == 'recipes__load_recipe_run_result':
        from geoagent_harness.capabilities.recipes.execution import load_recipe_run_result as action
        return action
    if name == 'recipes__recipe_evidence_sha256':
        from geoagent_harness.capabilities.recipes.execution import recipe_evidence_sha256 as action
        return action
    if name == 'recipes__recipe_sha256':
        from geoagent_harness.capabilities.recipes.execution import recipe_sha256 as action
        return action
    if name == 'recipes__save_recipe':
        from geoagent_harness.capabilities.recipes.execution import save_recipe as action
        return action
    if name == 'recipes__validate_recipe_policy':
        from geoagent_harness.capabilities.recipes.execution import validate_recipe_policy as action
        return action
    if name == 'recipes__verify_recipe_approval':
        from geoagent_harness.capabilities.recipes.execution import verify_recipe_approval as action
        return action
    if name == 'recipes__write_recipe_evidence':
        from geoagent_harness.capabilities.recipes.execution import write_recipe_evidence as action
        return action
    if name == 'releases__assess_workflow_release_candidate':
        from geoagent_harness.core.ledger.releases import assess_workflow_release_candidate as action
        return action
    if name == 'releases__authoritative_release_candidate_sha256':
        from geoagent_harness.core.ledger.releases import authoritative_release_candidate_sha256 as action
        return action
    if name == 'releases__inspect_authoritative_release':
        from geoagent_harness.core.ledger.releases import inspect_authoritative_release as action
        return action
    if name == 'releases__persist_authoritative_release':
        from geoagent_harness.core.ledger.releases import persist_authoritative_release as action
        return action
    if name == 'schema_registry__assess_migration':
        from geoagent_harness.contracts.schema_registry import assess_migration as action
        return action
    if name == 'schema_registry__assess_schema_compatibility':
        from geoagent_harness.contracts.schema_registry import assess_schema_compatibility as action
        return action
    if name == 'schema_registry__list_schema_policies':
        from geoagent_harness.contracts.schema_registry import list_schema_policies as action
        return action
    if name == 'skill_definitions__assess_declarative_skill':
        from geoagent_harness.capabilities.skills.definitions import assess_declarative_skill as action
        return action
    if name == 'skill_definitions__assess_skill_candidate_for_promotion':
        from geoagent_harness.capabilities.skills.definitions import assess_skill_candidate_for_promotion as action
        return action
    if name == 'skill_definitions__generate_declarative_skill_scaffold':
        from geoagent_harness.capabilities.skills.definitions import generate_declarative_skill_scaffold as action
        return action
    if name == 'skill_definitions__generate_skill_contract_bundle':
        from geoagent_harness.capabilities.skills.definitions import generate_skill_contract_bundle as action
        return action
    if name == 'skill_definitions__load_skill_candidate_test_record':
        from geoagent_harness.capabilities.skills.definitions import load_skill_candidate_test_record as action
        return action
    if name == 'skill_definitions__load_skill_definition':
        from geoagent_harness.capabilities.skills.definitions import load_skill_definition as action
        return action
    if name == 'skill_definitions__materialize_trusted_adapter_candidate':
        from geoagent_harness.capabilities.skills.definitions import materialize_trusted_adapter_candidate as action
        return action
    if name == 'skill_definitions__plan_skill_candidate_promotion':
        from geoagent_harness.capabilities.skills.definitions import plan_skill_candidate_promotion as action
        return action
    if name == 'skill_definitions__promote_skill_candidate':
        from geoagent_harness.capabilities.skills.definitions import promote_skill_candidate as action
        return action
    if name == 'skill_definitions__validate_skill_contract_bundle':
        from geoagent_harness.capabilities.skills.definitions import validate_skill_contract_bundle as action
        return action
    if name == 'skill_registry__load_skill_registry':
        from geoagent_harness.platform.skill_registry import load_skill_registry as action
        return action
    if name == 'skill_scaffolding__generate_skill_scaffold':
        from geoagent_harness.capabilities.skills.scaffolding import generate_skill_scaffold as action
        return action
    if name == 'skill_scaffolding__load_skill_scaffold_request':
        from geoagent_harness.capabilities.skills.scaffolding import load_skill_scaffold_request as action
        return action
    if name == 'skill_scaffolding__plan_skill_scaffold':
        from geoagent_harness.capabilities.skills.scaffolding import plan_skill_scaffold as action
        return action
    if name == 'skill_scaffolding__validate_skill_scaffold_contract':
        from geoagent_harness.capabilities.skills.scaffolding import validate_skill_scaffold_contract as action
        return action
    if name == 'skills_convert_raster_policy__validate_convert_raster_request':
        from geoagent_harness.data.spatial.skills.convert_raster.policy import validate_convert_raster_request as action
        return action
    if name == 'skills_convert_raster_service__convert_raster':
        from geoagent_harness.data.spatial.skills.convert_raster.service import convert_raster as action
        return action
    if name == 'skills_convert_raster_validation__validate_raster_conversion':
        from geoagent_harness.data.spatial.skills.convert_raster.validation import validate_raster_conversion as action
        return action
    if name == 'skills_convert_vector__convert_vector':
        from geoagent_harness.data.spatial.skills.convert_vector import convert_vector as action
        return action
    if name == 'skills_convert_vector__plan_vector_conversion':
        from geoagent_harness.data.spatial.skills.convert_vector import plan_vector_conversion as action
        return action
    if name == 'skills_convert_vector__validate_vector_conversion':
        from geoagent_harness.data.spatial.skills.convert_vector import validate_vector_conversion as action
        return action
    if name == 'skills_inspect_raster_service__inspect_raster':
        from geoagent_harness.data.spatial.skills.inspect_raster.service import inspect_raster as action
        return action
    if name == 'skills_inspect_vector_service__inspect_vector':
        from geoagent_harness.data.spatial.skills.inspect_vector.service import inspect_vector as action
        return action
    if name == 'skills_load_vector_to_postgis_service__load_vector_to_postgis':
        from geoagent_harness.data.spatial.skills.load_vector_to_postgis.service import load_vector_to_postgis as action
        return action
    if name == 'snakemake_export__generate_snakemake_recipe_export':
        from geoagent_harness.data.export.snakemake.generator import generate_snakemake_recipe_export as action
        return action
    if name == 'snakemake_export__plan_snakemake_recipe_export':
        from geoagent_harness.data.export.snakemake.planner import plan_snakemake_recipe_export as action
        return action
    if name == 'snakemake_export__validate_snakemake_export_contract':
        from geoagent_harness.data.export.snakemake.contracts import validate_snakemake_export_contract as action
        return action
    if name == 'spatial_contracts__assess_spatial_data_contract':
        from geoagent_harness.contracts.spatial import assess_spatial_data_contract as action
        return action
    if name == 'spatial_contracts__load_spatial_data_contract':
        from geoagent_harness.contracts.spatial import load_spatial_data_contract as action
        return action
    if name == 'task_history__append_task_event':
        from geoagent_harness.core.ledger.task_history import append_task_event as action
        return action
    if name == 'task_history__build_task_context':
        from geoagent_harness.core.ledger.task_history import build_task_context as action
        return action
    if name == 'task_history_service__history_directory':
        from geoagent_harness.core.ledger.task_history.service import history_directory as action
        return action
    if name == 'verifier_postgis__validate_postgis_layer':
        from geoagent_harness.core.verification.postgis import validate_postgis_layer as action
        return action
    if name == 'workflow_state__assess_resume':
        from geoagent_harness.core.ledger.workflow_state import assess_resume as action
        return action
    if name == 'workflow_state__load_state':
        from geoagent_harness.core.ledger.workflow_state import load_state as action
        return action
    if name == 'workspace__runtime_store_path':
        from geoagent_harness.platform.workspace import runtime_store_path as action
        return action
    if name == 'write_policy__snapshot':
        from geoagent_harness.core.policy.write_policy import snapshot as action
        return action
    if name == 'write_policy__update':
        from geoagent_harness.core.policy.write_policy import update as action
        return action
    if name == 'recipes__run_approved_recipe':
        from geoagent_harness.capabilities.recipes.execution import run_approved_recipe as action
        return action
    if name == 'recipes__build_recipe_run_evidence':
        from geoagent_harness.capabilities.recipes.execution import build_recipe_run_evidence as action
        return action
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
