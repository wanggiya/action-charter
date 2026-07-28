import asyncio
import inspect

from geoagent_harness.mcp_server import tools
from geoagent_harness.mcp_server.server import mcp


def test_server_registers_only_allowlisted_tools() -> None:
    registered = asyncio.run(mcp.list_tools())

    names = sorted(
        tool.name
        for tool in registered
    )

    assert names == sorted(tools.TOOL_ALLOWLIST)


def test_tool_implementation_has_no_shell_or_sql() -> None:
    source = inspect.getsource(tools).lower()

    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shell=true" not in source
    assert "psycopg" not in source
    assert "sqlalchemy" not in source
    assert "delete from" not in source
    assert "drop table" not in source
    assert "drop schema" not in source


def test_allowlist_has_no_execution_or_delete_tool() -> None:
    assert all(
        "delete" not in name
        for name in tools.TOOL_ALLOWLIST
    )

    assert all(
        "execute" not in name
        for name in tools.TOOL_ALLOWLIST
    )

    assert (
        "load_vector_to_postgis"
        not in tools.TOOL_ALLOWLIST
    )