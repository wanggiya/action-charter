from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_inspection import (
    PostGISColumn,
    PostGISInspectionError,
    PostGISInspectionRequest,
    inspect_postgis_table,
)
from geoagent_harness.verifier.postgis import LayerExtent
from geoagent_harness.skill_registry import load_skill_registry


class FakeReader:
    def __init__(self, *, exists: bool = True) -> None:
        self.exists = exists
        self.closed = False

    def table_exists(self, schema, table): return self.exists
    def columns(self, schema, table):
        return [PostGISColumn(ordinal_position=1, name="id", data_type="integer", nullable=False)]
    def keys(self, schema, table):
        return [("p", "sample_pkey", ["id"]), ("u", "sample_name_key", ["name"])]
    def geometry_metadata(self, schema, table): return [("geometry", "POINT", 4326)]
    def row_count(self, schema, table): return 2
    def geometry_statistics(self, schema, table, column):
        return ["POINT"], 0, 0, LayerExtent(min_x=-71.1, min_y=42.3, max_x=-71.0, max_y=42.4)
    def close(self): self.closed = True


@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(input_root=tmp_path / "in", output_root=tmp_path / "out", allowed_schemas=frozenset({"agent_sandbox"}))


def test_inspects_bounded_metadata(settings):
    reader = FakeReader()
    result = inspect_postgis_table(request=PostGISInspectionRequest(target_schema="agent_sandbox", target_table="sample_points"), settings=settings, reader=reader)
    assert result.status == "inspected"
    assert result.row_count == 2
    assert result.primary_key.columns == ["id"]
    assert result.unique_keys[0].columns == ["name"]
    assert result.geometry_columns[0].srid == 4326
    assert result.geometry_columns[0].observed_types == ["POINT"]
    assert result.database_modified is False
    assert result.arbitrary_sql_accepted is False
    assert result.credentials_redacted is True
    assert reader.closed is False


def test_missing_table_is_typed(settings):
    result = inspect_postgis_table(request=PostGISInspectionRequest(target_schema="agent_sandbox", target_table="missing"), settings=settings, reader=FakeReader(exists=False))
    assert result.status == "not_found"
    assert result.table_exists is False
    assert result.row_count is None


def test_unapproved_schema_is_rejected(settings):
    with pytest.raises(PostGISInspectionError, match="not allowed"):
        inspect_postgis_table(request=PostGISInspectionRequest(target_schema="public", target_table="sample_points"), settings=settings, reader=FakeReader())


@pytest.mark.parametrize("table", ["public.sample", "sample;drop", "Bad-Name", "1table"])
def test_unsafe_table_is_rejected(settings, table):
    with pytest.raises(ValueError, match="target_table"):
        inspect_postgis_table(request=PostGISInspectionRequest(target_schema="agent_sandbox", target_table=table), settings=settings, reader=FakeReader())


def test_request_forbids_query_shaped_fields():
    with pytest.raises(ValidationError, match="sql"):
        PostGISInspectionRequest.model_validate({"target_schema": "agent_sandbox", "target_table": "sample", "sql": "select 1"})


def test_result_schema_bounds_columns(settings):
    reader = FakeReader()
    reader.columns = lambda schema, table: [PostGISColumn(ordinal_position=i + 1, name=f"c{i}", data_type="text", nullable=True) for i in range(257)]
    with pytest.raises(ValidationError):
        inspect_postgis_table(request=PostGISInspectionRequest(target_schema="agent_sandbox", target_table="sample"), settings=settings, reader=reader)


def test_skill_is_registered_read_only():
    project_root = Path(__file__).resolve().parents[1]
    skill = load_skill_registry(project_root).get_skill(
        "inspect_postgis_table"
    )
    assert skill.kind.value == "inspection"
    assert skill.access.value == "read_only"
    assert skill.approval_required is False
