"""End-to-end Checkpoint 2 MCP smoke test."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "health_check",
    "inspect_vector_dataset",
    "plan_load_vector_to_postgis",
    "load_vector_to_postgis",
    "validate_postgis_layer",
}


def safe_environment() -> dict[str, str]:
    project_root = Path(__file__).resolve().parents[1]

    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get(
            "PYTHONPATH",
            "",
        ),
        "GEOAGENT_INPUT_ROOT": str(
            project_root / "data" / "input"
        ),
        "GEOAGENT_OUTPUT_ROOT": str(
            project_root / "data" / "output"
        ),
        "ENABLE_WRITE_TOOLS": "false",
        "ALLOW_OVERWRITE": "false",
        "ALLOWED_SCHEMAS": "agent_sandbox",
    }


async def run() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "geoagent_harness.mcp_server",
        ],
        env=safe_environment(),
    )

    async with stdio_client(
        parameters
    ) as (read, write):
        async with ClientSession(
            read,
            write,
        ) as session:
            await session.initialize()

            listed = await session.list_tools()

            names = {
                tool.name
                for tool in listed.tools
            }

            assert names == EXPECTED_TOOLS

            health = await session.call_tool(
                "health_check",
                arguments={},
            )
            assert health.isError is False

            inspected = await session.call_tool(
                "inspect_vector_dataset",
                arguments={
                    "path":
                        "data/input/sample_points.geojson"
                },
            )
            assert inspected.isError is False

            planned = await session.call_tool(
                "plan_load_vector_to_postgis",
                arguments={
                    "path":
                        "data/input/sample_points.geojson",
                    "target_schema":
                        "agent_sandbox",
                    "target_table":
                        "sample_points",
                },
            )
            assert planned.isError is False

            print(
                json.dumps(
                    {
                        "status": "ok",
                        "tools": sorted(names),
                        "health_check": "passed",
                        "inspect_vector_dataset":
                            "passed",
                        "plan_load_vector_to_postgis":
                            "planned_not_executed",
                    },
                    indent=2,
                )
            )


if __name__ == "__main__":
    asyncio.run(run())