"""Shared deterministic operation actions behind the existing MCP tool allowlist."""

from pathlib import Path
from geoagent_harness.core.policy.write_policy import effective as _effective
from geoagent_harness.platform.settings import authority_workspace_settings

def effective(settings):
    return _effective(authority_workspace_settings(settings))

from geoagent_harness.contracts.tool_results import AssessSpatialDataContractToolResult, HealthCheckResult, InspectVectorToolResult, LoadVectorPlan
from geoagent_harness.platform.settings import MCPSettings, load_settings, validate_identifier
from geoagent_harness.data.spatial.skills.inspect_vector.service import inspect_vector
from geoagent_harness.contracts.spatial import assess_spatial_data_contract as execute_contract_assessment
from geoagent_harness.contracts.spatial import load_spatial_data_contract
from geoagent_harness.data.spatial.skills.load_vector_to_postgis.service import LoadVectorResult, load_vector_to_postgis as execute_vector_load
from geoagent_harness.core.verification.postgis import PostGISValidationResult, validate_postgis_layer as execute_validation
from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest, PostGISInspectionResult
from geoagent_harness.data.databases.postgis.inspection import inspect_postgis_table as execute_postgis_inspection
from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonRequest, PostGISComparisonResult
from geoagent_harness.data.databases.postgis.comparison import compare_postgis_tables as execute_postgis_comparison
from geoagent_harness.data.databases.postgis.change_assessment import PostGISChangeAssessment
from geoagent_harness.data.databases.postgis.change_assessment import assess_postgis_change as execute_change_assessment
from geoagent_harness.data.databases.postgis.promotion.plan import PostGISPromotionPlanRequest, PostGISPromotionPlanResult
from geoagent_harness.data.databases.postgis.promotion.plan import plan_postgis_promotion as execute_promotion_planning
from geoagent_harness.data.spatial.geoserver.inspection import GeoServerInspectionRequest, GeoServerInspectionResult
from geoagent_harness.data.spatial.geoserver.inspection import inspect_geoserver_layer as execute_geoserver_inspection
from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationPlanRequest, GeoServerPublicationPlanResult
from geoagent_harness.data.spatial.geoserver.publication import plan_geoserver_publication as execute_geoserver_publication_planning

TOOL_ALLOWLIST = [
    "list_operation_contracts", "workflow_report",
    "discover_postgres_tables", "inspect_postgres_table", "validate_postgres_import",
    "discover_inputs",
    "assess_table",
    "profile_table",
    "table_statistics",
    "recommend_table_fields",
    "linear_regression",
    "profile_dataset",
    "explore_dataset_view",
    "discover_dataset",
    "health_check",
    "inspect_vector_dataset",
    "inspect_postgis_table",
    "inspect_geoserver_layer",
    "plan_geoserver_publication",
    "compare_postgis_tables",
    "assess_postgis_change",
    "plan_postgis_promotion",
    "assess_spatial_data_contract",
    "plan_load_vector_to_postgis",
    "validate_postgis_layer",
    "run_approved_vector_postgis_workflow",
    "run_approved_recipe",
]


def discover_inputs(directory:str,settings:MCPSettings|None=None)->dict:
    from geoagent_harness.data.tabular.strategy import discover_inputs as discover
    active=settings or load_settings()
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():raise ValueError('Discovery requires the configured project data/input root')
    return discover(active.project_root,directory)


def assess_table(path:str,operation:str='profile',settings:MCPSettings|None=None)->dict:
    from geoagent_harness.data.tabular.strategy import assess_table as assess
    active=settings or load_settings()
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():raise ValueError('Assessment requires the configured project data/input root')
    return assess(active.project_root,path,operation)


def explore_dataset_view(request:dict,settings:MCPSettings|None=None)->dict:
    from geoagent_harness.data.tabular.dataset_views import DatasetViewRequest, dataset_view
    active=settings or load_settings()
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():raise ValueError('Views require the project input root')
    return dataset_view(DatasetViewRequest.model_validate(request),project_root=active.project_root)


def profile_dataset(path:str,options:dict|None=None,settings:MCPSettings|None=None)->dict:
    """All-field typed profiles in the configured isolated runtime; no dataset writes or arbitrary code."""
    from geoagent_harness.data.tabular.dataset_service import profile_dataset as profile
    active=settings or load_settings()
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():raise ValueError('Profiles require the project input root')
    return profile(active.project_root,path,options)


def profile_table(path: str, options: dict | None = None, settings: MCPSettings | None = None) -> dict:
    """Read full-file summaries, exact quality/duplicate checks and grouped distinct counts through shared bounded services."""
    from geoagent_harness.data.tabular.analytical_service import profile_table as profile
    active = settings or load_settings()
    if active.input_root.resolve() != (active.project_root / 'data/input').resolve():
        raise ValueError('Analytical tools require the configured project data/input root')
    return profile(active.project_root, path, options)


def workflow_report(run_id:str,settings=None):
    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
    return run_action(RunRequest(action='report',run_id=run_id),project_root=(settings or load_settings()).project_root)

def list_operation_contracts(query:str='',settings:MCPSettings|None=None)->dict:
    """Registry discovery only: typed parameters/results/effects; no source reads."""
    if not isinstance(query,str) or len(query)>160:raise ValueError('Operation search supports up to 160 characters')
    from geoagent_harness.capabilities.registry.registry import operation_catalog
    active=settings or load_settings()
    return operation_catalog(active.project_root,query)


def table_statistics(path: str, specification: dict, missing_values: dict | None = None, settings: MCPSettings | None = None,source_options:dict|None=None) -> dict:
    """Typed full-file describe/correlation/OLS methods; shared bounded reader, no writes."""
    from geoagent_harness.contracts.statistics import StatisticsSpec
    specification=StatisticsSpec.model_validate(specification)
    return profile_table(path,{'statistics':specification.model_dump(mode='json'),'missing_values':missing_values or {},'source_options':source_options},settings)


def recommend_table_fields(path:str,settings:MCPSettings|None=None,source_options:dict|None=None)->dict:
    from geoagent_harness.data.tabular.analytical_service import recommend_fields
    active=settings or load_settings()
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():raise ValueError('Field guidance requires the configured project data/input root')
    return recommend_fields(active.project_root,path,source_options=source_options)


def plan_geoserver_publication(
    plan_id: str, workspace: str, datastore: str, layer: str,
    settings: MCPSettings | None = None,
) -> GeoServerPublicationPlanResult:
    """Create a read-only digest-bound plan for one existing layer."""
    active = effective(settings or load_settings())
    return execute_geoserver_publication_planning(
        request=GeoServerPublicationPlanRequest(
            plan_id=plan_id,
            target=GeoServerInspectionRequest(
                workspace=workspace, datastore=datastore, layer=layer,
            ),
        ), settings=active,
    )


def inspect_geoserver_layer(
    workspace: str, datastore: str, layer: str,
    settings: MCPSettings | None = None,
) -> GeoServerInspectionResult:
    """Inspect one exact GeoServer publication through the GET-only boundary."""
    active = effective(settings or load_settings())
    return execute_geoserver_inspection(
        request=GeoServerInspectionRequest(workspace=workspace, datastore=datastore, layer=layer),
        settings=active,
    )


def plan_postgis_promotion(
    plan_id: str,
    reference_schema: str,
    reference_table: str,
    candidate_schema: str,
    candidate_table: str,
    archive_schema: str,
    archive_table: str,
    settings: MCPSettings | None = None,
) -> PostGISPromotionPlanResult:
    """Plan an exact digest-bound promotion without mutation."""
    active = effective(settings or load_settings())
    return execute_promotion_planning(
        request=PostGISPromotionPlanRequest(
            plan_id=plan_id,
            reference=PostGISInspectionRequest(
                target_schema=reference_schema,
                target_table=reference_table,
            ),
            candidate=PostGISInspectionRequest(
                target_schema=candidate_schema,
                target_table=candidate_table,
            ),
            archive=PostGISInspectionRequest(
                target_schema=archive_schema,
                target_table=archive_table,
            ),
        ),
        settings=active,
    )


def assess_postgis_change(
    reference_schema: str,
    reference_table: str,
    candidate_schema: str,
    candidate_table: str,
    settings: MCPSettings | None = None,
) -> PostGISChangeAssessment:
    """Compare and classify two exact PostGIS relations."""
    comparison = compare_postgis_tables(
        reference_schema=reference_schema,
        reference_table=reference_table,
        candidate_schema=candidate_schema,
        candidate_table=candidate_table,
        settings=settings,
    )
    return execute_change_assessment(comparison)


def compare_postgis_tables(
    reference_schema: str,
    reference_table: str,
    candidate_schema: str,
    candidate_table: str,
    settings: MCPSettings | None = None,
) -> PostGISComparisonResult:
    """Compare two exact PostGIS relations through inspection."""
    active = effective(settings or load_settings())
    return execute_postgis_comparison(
        request=PostGISComparisonRequest(
            reference=PostGISInspectionRequest(
                target_schema=reference_schema,
                target_table=reference_table,
            ),
            candidate=PostGISInspectionRequest(
                target_schema=candidate_schema,
                target_table=candidate_table,
            ),
        ),
        settings=active,
    )


def inspect_postgis_table(
    target_schema: str,
    target_table: str,
    settings: MCPSettings | None = None,
) -> PostGISInspectionResult:
    """Inspect one exact PostGIS table through the read-only boundary."""
    active = effective(settings or load_settings())
    return execute_postgis_inspection(
        request=PostGISInspectionRequest(
            target_schema=target_schema,
            target_table=target_table,
        ),
        settings=active,
    )


def health_check(
    settings: MCPSettings | None = None,
) -> HealthCheckResult:
    """Return only non-secret status and policy information."""
    active = effective(settings or load_settings())

    return HealthCheckResult(
        write_tools_enabled=active.enable_write_tools,
        overwrite_enabled=active.allow_overwrite,
        input_root=active.input_root.as_posix(),
        tools=TOOL_ALLOWLIST.copy(),
    )


def discover_dataset(path:str,delimiter:str|None=None,settings:MCPSettings|None=None)->dict:
    """Read bounded local CSV/vector/TIFF characteristics and complete identity."""
    from geoagent_harness.data.discovery.service import discover_dataset as discover
    active=effective(settings or load_settings())
    if active.input_root.resolve()!=(active.project_root/'data/input').resolve():
        raise ValueError('Discovery requires the project data/input root; legacy tools retain custom-root support')
    return discover(active.project_root,path,delimiter)





def assess_spatial_data_contract(
    path: str,
    contract_file: str,
    settings: MCPSettings | None = None,
) -> AssessSpatialDataContractToolResult:
    """Assess one approved vector dataset against one contract."""

    active = effective(settings or load_settings())
    contract = load_spatial_data_contract(
        Path(contract_file),
        contract_root=active.contract_root,
    )
    assessment = execute_contract_assessment(
        path=Path(path),
        contract=contract,
        input_root=active.input_root,
    )
    return AssessSpatialDataContractToolResult(
        result=assessment
    )








def validate_postgres_import(arguments,settings=None):
    from geoagent_harness.data.databases.postgres.service import inspect
    return inspect('validate_postgres_import',arguments,settings or load_settings())

def discover_postgres_tables(target_schema='agent_sandbox',settings=None):
    from geoagent_harness.data.databases.postgres.service import inspect
    return inspect('discover_postgres_tables',{'target_schema':target_schema},settings or load_settings())

def inspect_postgres_table(target_schema,target_table,preview_rows=5,settings=None):
    from geoagent_harness.data.databases.postgres.service import inspect
    return inspect('inspect_postgres_table',{'target_schema':target_schema,'target_table':target_table,'preview_rows':preview_rows},settings or load_settings())

from geoagent_harness.data.databases.postgis.fixed_operations import inspect_vector_dataset, plan_load_vector_to_postgis, load_vector_to_postgis, validate_postgis_layer


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
discover_inputs = _task_entrypoint(discover_inputs, trigger='mcp', )
assess_table = _task_entrypoint(assess_table, trigger='mcp', )
explore_dataset_view = _task_entrypoint(explore_dataset_view, trigger='mcp', )
profile_dataset = _task_entrypoint(profile_dataset, trigger='mcp', )
profile_table = _task_entrypoint(profile_table, trigger='mcp', )
workflow_report = _task_entrypoint(workflow_report, trigger='mcp', audit=False)
list_operation_contracts = _task_entrypoint(list_operation_contracts, trigger='mcp', audit=False)
table_statistics = _task_entrypoint(table_statistics, trigger='mcp', )
recommend_table_fields = _task_entrypoint(recommend_table_fields, trigger='mcp', )
plan_geoserver_publication = _task_entrypoint(plan_geoserver_publication, trigger='mcp', )
inspect_geoserver_layer = _task_entrypoint(inspect_geoserver_layer, trigger='mcp', )
plan_postgis_promotion = _task_entrypoint(plan_postgis_promotion, trigger='mcp', )
assess_postgis_change = _task_entrypoint(assess_postgis_change, trigger='mcp', )
compare_postgis_tables = _task_entrypoint(compare_postgis_tables, trigger='mcp', )
inspect_postgis_table = _task_entrypoint(inspect_postgis_table, trigger='mcp', )
health_check = _task_entrypoint(health_check, trigger='mcp', audit=False)
discover_dataset = _task_entrypoint(discover_dataset, trigger='mcp', )
assess_spatial_data_contract = _task_entrypoint(assess_spatial_data_contract, trigger='mcp', )
validate_postgres_import = _task_entrypoint(validate_postgres_import, trigger='mcp', )
discover_postgres_tables = _task_entrypoint(discover_postgres_tables, trigger='mcp', )
inspect_postgres_table = _task_entrypoint(inspect_postgres_table, trigger='mcp', )
