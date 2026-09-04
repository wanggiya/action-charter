"""Plain deterministic functions exposed through the MCP boundary."""

from pathlib import Path

from geoagent_harness.mcp_server.schemas import (
    AssessSpatialDataContractToolResult,
    HealthCheckResult,
    InspectVectorToolResult,
    LoadVectorPlan,
)
from geoagent_harness.mcp_server.settings import (
    MCPSettings,
    load_settings,
    validate_identifier,
)
from geoagent_harness.skills.inspect_vector.service import (
    inspect_vector,
)
from geoagent_harness.spatial_contracts import (
    assess_spatial_data_contract as execute_contract_assessment,
    load_spatial_data_contract,
)
from geoagent_harness.skills.load_vector_to_postgis.service import (
    LoadVectorResult,
    load_vector_to_postgis as execute_vector_load,
)
from geoagent_harness.verifier.postgis import (
    PostGISValidationResult,
    validate_postgis_layer as execute_validation,
)
from geoagent_harness.postgis_inspection import (
    PostGISInspectionRequest,
    PostGISInspectionResult,
    inspect_postgis_table as execute_postgis_inspection,
)
from geoagent_harness.postgis_comparison import (
    PostGISComparisonRequest,
    PostGISComparisonResult,
    compare_postgis_tables as execute_postgis_comparison,
)
from geoagent_harness.postgis_change_assessment import (
    PostGISChangeAssessment,
    assess_postgis_change as execute_change_assessment,
)
from geoagent_harness.postgis_promotion_plan import (
    PostGISPromotionPlanRequest,
    PostGISPromotionPlanResult,
    plan_postgis_promotion as execute_promotion_planning,
)

TOOL_ALLOWLIST = [
    "health_check",
    "inspect_vector_dataset",
    "inspect_postgis_table",
    "compare_postgis_tables",
    "assess_postgis_change",
    "plan_postgis_promotion",
    "assess_spatial_data_contract",
    "plan_load_vector_to_postgis",
    "validate_postgis_layer",
    "run_approved_vector_postgis_workflow",
    "run_approved_recipe",
]


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
    active = settings or load_settings()
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
    active = settings or load_settings()
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
    active = settings or load_settings()
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
    active = settings or load_settings()

    return HealthCheckResult(
        write_tools_enabled=active.enable_write_tools,
        overwrite_enabled=active.allow_overwrite,
        input_root=active.input_root.as_posix(),
        tools=TOOL_ALLOWLIST.copy(),
    )


def inspect_vector_dataset(
    path: str,
    settings: MCPSettings | None = None,
) -> InspectVectorToolResult:
    """Inspect a vector file inside the approved input root."""
    active = settings or load_settings()

    result = inspect_vector(
        Path(path),
        input_root=active.input_root,
    )

    return InspectVectorToolResult(result=result)



def assess_spatial_data_contract(
    path: str,
    contract_file: str,
    settings: MCPSettings | None = None,
) -> AssessSpatialDataContractToolResult:
    """Assess one approved vector dataset against one contract."""

    active = settings or load_settings()
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


def plan_load_vector_to_postgis(
    path: str,
    target_schema: str,
    target_table: str,
    settings: MCPSettings | None = None,
) -> LoadVectorPlan:
    """Validate and describe a load without executing it."""
    active = settings or load_settings()

    validate_identifier(
        target_schema,
        label="target_schema",
    )
    validate_identifier(
        target_table,
        label="target_table",
    )

    if target_schema not in active.allowed_schemas:
        allowed = ", ".join(
            sorted(active.allowed_schemas)
        )

        raise ValueError(
            f"target_schema {target_schema!r} is not allowed; "
            f"allowed: {allowed}"
        )

    inspected = inspect_vector_dataset(
        path,
        settings=active,
    ).result

    return LoadVectorPlan(
        source=inspected.source,
        source_driver=inspected.driver,
        source_layers=[
            layer.name
            for layer in inspected.layers
        ],
        target_schema=target_schema,
        target_table=target_table,
        execution_allowed=False,
        approval_required=True,
        warnings=[
            (
                "Plan only: no database connection or "
                "SQL execution occurred."
            ),
            (
                "Execution requires ENABLE_WRITE_TOOLS=true "
                "and deterministic validation afterward."
            ),
        ],
    )


def load_vector_to_postgis(
    path: str,
    target_schema: str,
    target_table: str,
    source_layer: str | None = None,
    settings: MCPSettings | None = None,
) -> LoadVectorResult:
    """Run the controlled loader when writes are enabled."""
    active = settings or load_settings()

    return execute_vector_load(
        path=Path(path),
        source_layer=source_layer,
        target_schema=target_schema,
        target_table=target_table,
        settings=active,
    )


def validate_postgis_layer(
    target_schema: str,
    target_table: str,
    expected_row_count: int | None = None,
    expected_srid: int | None = None,
    expected_geometry_type: str | None = None,
    settings: MCPSettings | None = None,
) -> PostGISValidationResult:
    """Run deterministic read-only PostGIS validation."""
    active = settings or load_settings()

    return execute_validation(
        target_schema=target_schema,
        target_table=target_table,
        expected_row_count=expected_row_count,
        expected_srid=expected_srid,
        expected_geometry_type=expected_geometry_type,
        settings=active,
    )
