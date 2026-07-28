"""Plain deterministic functions for read-only MCP tools."""

from pathlib import Path

from geoagent_harness.mcp_server.schemas import (
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

TOOL_ALLOWLIST = [
    "health_check",
    "inspect_vector_dataset",
    "plan_load_vector_to_postgis",
]


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


def plan_load_vector_to_postgis(
    path: str,
    target_schema: str,
    target_table: str,
    settings: MCPSettings | None = None,
) -> LoadVectorPlan:
    """Validate and describe a load without connecting to PostGIS."""
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
                "A later write checkpoint requires explicit "
                "approval and deterministic validation."
            ),
        ],
    )