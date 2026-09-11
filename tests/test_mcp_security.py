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


def test_bounded_geoserver_inspection_is_get_only() -> None:
    from geoagent_harness.geoserver_inspection import service

    source = inspect.getsource(service).lower()
    assert "client.get" in source
    assert "client.post" not in source
    assert "client.put" not in source
    assert "client.delete" not in source
    assert "subprocess" not in source
    assert "inspect_geoserver_layer" in tools.TOOL_ALLOWLIST


def test_geoserver_publication_planning_is_the_only_mcp_publication_tool() -> None:
    from geoagent_harness.geoserver_publication import service

    assert "plan_geoserver_publication" in tools.TOOL_ALLOWLIST
    assert "execute_geoserver_publication" not in tools.TOOL_ALLOWLIST
    assert service.FIXED_FEATURE_TYPE_BODY == {
        "featureType": {"enabled": True, "advertised": True}
    }


def test_postgis_comparison_reuses_inspection_boundary() -> None:
    from geoagent_harness.postgis_comparison import service

    source = inspect.getsource(service).lower()
    assert "inspect_postgis_table" in source
    assert "psycopg.connect" not in source
    assert "sql." not in source
    assert "subprocess" not in source
    assert "compare_postgis_tables" in tools.TOOL_ALLOWLIST


def test_change_assessment_is_pure_fixed_policy() -> None:
    from geoagent_harness.postgis_change_assessment import service

    source = inspect.getsource(service).lower()
    assert "psycopg" not in source
    assert "sql." not in source
    assert "subprocess" not in source
    assert "geoagent_harness.model" not in source
    assert "assess_postgis_change" in tools.TOOL_ALLOWLIST


def test_promotion_planning_has_no_write_or_sql_boundary() -> None:
    from geoagent_harness.postgis_promotion_plan import service

    source = inspect.getsource(service).lower()
    assert "execute(" not in source
    assert "alter table" not in source
    assert "subprocess" not in source
    assert "plan_postgis_promotion" in tools.TOOL_ALLOWLIST


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
