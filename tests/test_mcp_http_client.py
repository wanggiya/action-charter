"""Tests for the read-only MCP client boundary."""

import asyncio

import pytest

from geoagent_harness.mcp_client import (
    MCPClientError,
    MCPClientSettings,
    MCPReadOnlyClient,
    READ_ONLY_TOOL_ALLOWLIST,
)


def test_read_only_allowlist_has_no_write_tools() -> None:
    assert "health_check" in READ_ONLY_TOOL_ALLOWLIST
    assert "inspect_postgis_table" in READ_ONLY_TOOL_ALLOWLIST
    assert "compare_postgis_tables" in READ_ONLY_TOOL_ALLOWLIST
    assert "assess_postgis_change" in READ_ONLY_TOOL_ALLOWLIST
    assert (
        "inspect_vector_dataset"
        in READ_ONLY_TOOL_ALLOWLIST
    )

    assert (
        "load_vector_to_postgis"
        not in READ_ONLY_TOOL_ALLOWLIST
    )
    assert (
        "run_vector_postgis_workflow"
        not in READ_ONLY_TOOL_ALLOWLIST
    )


def test_write_tool_is_rejected_before_network() -> None:
    client = MCPReadOnlyClient(
        MCPClientSettings(
            url="http://mcp-gis:8000/mcp",
            timeout_seconds=5,
        )
    )

    with pytest.raises(
        MCPClientError,
        match="not allowed",
    ):
        asyncio.run(
            client.call_tool(
                "load_vector_to_postgis",
                arguments={},
            )
        )
