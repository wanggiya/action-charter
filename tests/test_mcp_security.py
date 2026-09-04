import asyncio
import inspect

from geoagent_harness.mcp_server import tools
from geoagent_harness.mcp_server.server import mcp
from geoagent_harness.verifier import postgis

EXPECTED_TOOLS = tools.TOOL_ALLOWLIST


def test_server_registers_only_allowlisted_tools() -> None:
    registered = asyncio.run(mcp.list_tools())

    names = sorted(
        tool.name
        for tool in registered
    )

    assert names == sorted(EXPECTED_TOOLS)
    assert names == sorted(tools.TOOL_ALLOWLIST)


def test_smoke_script_tracks_server_allowlist() -> None:
    from scripts.mcp_smoke import (
        EXPECTED_TOOLS as SMOKE_EXPECTED_TOOLS,
    )

    assert SMOKE_EXPECTED_TOOLS == set(
        tools.TOOL_ALLOWLIST
    )


def test_mcp_boundary_has_no_shell_or_destructive_sql() -> None:
    source = inspect.getsource(tools).lower()

    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shell=true" not in source

    assert "delete from" not in source
    assert "drop table" not in source
    assert "drop schema" not in source
    assert "truncate table" not in source


def test_verifier_uses_safe_read_only_sql() -> None:
    source = inspect.getsource(postgis).lower()

    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shell=true" not in source

    assert "delete from" not in source
    assert "drop table" not in source
    assert "drop schema" not in source
    assert "truncate table" not in source
    assert "alter table" not in source

    assert "sql.identifier" in source
    assert "read_only = true" in source


def test_allowlist_contains_no_delete_tool() -> None:
    assert all(
        "delete" not in name
        for name in tools.TOOL_ALLOWLIST
    )

    assert all(
        "drop" not in name
        for name in tools.TOOL_ALLOWLIST
    )


def test_bounded_postgis_inspection_is_read_only() -> None:
    from geoagent_harness.postgis_inspection import service

    source = inspect.getsource(service).lower()
    assert "sql.identifier" in source
    assert "read_only = true" in source
    assert "statement_timeout" in source
    assert "delete from" not in source
    assert "drop table" not in source
    assert "alter table" not in source
    assert "insert into" not in source
    assert "update " not in source
    assert "inspect_postgis_table" in tools.TOOL_ALLOWLIST


def test_only_approval_gated_write_tools_are_exposed() -> None:
    assert (
        "load_vector_to_postgis"
        not in tools.TOOL_ALLOWLIST
    )

    assert (
        "convert_vector"
        not in tools.TOOL_ALLOWLIST
    )

    assert (
        "run_approved_vector_postgis_workflow"
        in tools.TOOL_ALLOWLIST
    )

    assert (
        "run_approved_recipe"
        in tools.TOOL_ALLOWLIST
    )
    
def test_raw_load_is_not_registered_over_mcp() -> None:
    import asyncio

    from geoagent_harness.mcp_server.server import mcp

    registered = asyncio.run(mcp.list_tools())
    names = {
        tool.name
        for tool in registered
    }

    assert "load_vector_to_postgis" not in names
    assert (
        "run_approved_vector_postgis_workflow"
        in names
    )
    assert "convert_vector" not in names

    assert (
        "run_approved_recipe"
        in names
    )
