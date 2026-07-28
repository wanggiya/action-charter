"""MCP server with a fixed read-only GIS tool allowlist."""

from mcp.server.fastmcp import FastMCP

from geoagent_harness.mcp_server import tools

mcp = FastMCP(
    "GeoAgent GIS MCP",
    json_response=True,
)


@mcp.tool()
def health_check() -> dict:
    """Return redacted readiness and security state."""
    return tools.health_check().model_dump(
        mode="json"
    )


@mcp.tool()
def inspect_vector_dataset(path: str) -> dict:
    """Inspect an approved vector input dataset."""
    return tools.inspect_vector_dataset(
        path
    ).model_dump(mode="json")


@mcp.tool()
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


def main() -> None:
    """Run the local MCP server over STDIO."""
    mcp.run()


if __name__ == "__main__":
    main()