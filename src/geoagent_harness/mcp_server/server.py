"""MCP server exposing a fixed GIS tool allowlist."""

from __future__ import annotations
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import (
    TransportSecuritySettings,
)
from geoagent_harness.mcp_server.approved_workflow import (
    run_approved_vector_postgis_workflow,
)

from geoagent_harness.mcp_server import tools
from geoagent_harness.mcp_server.transport import (
    MCPTransportSettings,
    load_transport_settings,
)


def create_mcp_server(
    settings: MCPTransportSettings | None = None,
) -> FastMCP:
    """Create the server with fixed tools and transport policy."""

    active = settings or MCPTransportSettings()

    server = FastMCP(
        "GeoAgent GIS MCP",
        host=active.host,
        port=active.port,
        streamable_http_path=active.path,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[
                "mcp-gis:*",
                "localhost:*",
                "127.0.0.1:*",
            ],
            allowed_origins=[
                "http://mcp-gis:*",
                "http://localhost:*",
                "http://127.0.0.1:*",
            ],
        ),
    )

    @server.tool()
    def health_check() -> dict:
        """Return redacted readiness and security state."""

        return tools.health_check().model_dump(
            mode="json"
        )

    @server.tool()
    def inspect_vector_dataset(
        path: str,
    ) -> dict:
        """Inspect an approved vector input dataset."""

        return tools.inspect_vector_dataset(
            path
        ).model_dump(mode="json")

    @server.tool()
    def plan_load_vector_to_postgis(
        path: str,
        target_schema: str,
        target_table: str,
    ) -> dict:
        """Create a non-executing PostGIS load plan."""

        return tools.plan_load_vector_to_postgis(
            path=path,
            target_schema=target_schema,
            target_table=target_table,
        ).model_dump(mode="json")

    @server.tool(
        name="run_approved_vector_postgis_workflow"
    )
    def run_approved_vector_postgis_workflow_tool(
        execution_envelope: dict[str, Any],
        plan_filename: str,
        approval_filename: str,
    ) -> dict:
        """Run only an exact server-verified approved workflow."""

        return run_approved_vector_postgis_workflow(
            execution_envelope=execution_envelope,
            plan_filename=plan_filename,
            approval_filename=approval_filename,
        ).model_dump(mode="json")

    @server.tool()
    def validate_postgis_layer(
        target_schema: str,
        target_table: str,
        expected_row_count: int | None = None,
        expected_srid: int | None = None,
        expected_geometry_type: str | None = None,
    ) -> dict:
        """Deterministically validate one PostGIS layer."""

        return tools.validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=expected_row_count,
            expected_srid=expected_srid,
            expected_geometry_type=(
                expected_geometry_type
            ),
        ).model_dump(mode="json")

    return server


# Used by existing in-process and STDIO tests.
mcp = create_mcp_server()


def main() -> None:
    """Run the configured MCP transport."""

    settings = load_transport_settings()
    server = create_mcp_server(settings)
    server.run(transport=settings.transport)


if __name__ == "__main__":
    main()