import asyncio
import inspect

from geoagent_harness.mcp_server import tools
from geoagent_harness.mcp_server.server import mcp
from geoagent_harness.verifier import postgis

EXPECTED_TOOLS = [
    "health_check",
    "inspect_vector_dataset",
    "plan_load_vector_to_postgis",
    "load_vector_to_postgis",
    "validate_postgis_layer",
]


def test_server_registers_only_allowlisted_tools() -> None:
    registered = asyncio.run(mcp.list_tools())

    names = sorted(
        tool.name
        for tool in registered
    )

    assert names == sorted(EXPECTED_TOOLS)
    assert names == sorted(tools.TOOL_ALLOWLIST)


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


def test_write_tool_is_explicitly_named() -> None:
    assert "load_vector_to_postgis" in tools.TOOL_ALLOWLIST
    assert "validate_postgis_layer" in tools.TOOL_ALLOWLIST