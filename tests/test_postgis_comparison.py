from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_comparison import (
    PostGISComparisonError,
    PostGISComparisonRequest,
    compare_postgis_tables,
)
from geoagent_harness.postgis_inspection import (
    PostGISColumn,
    PostGISInspectionRequest,
)
from geoagent_harness.skill_registry import load_skill_registry
from geoagent_harness.verifier.postgis import LayerExtent


def request() -> PostGISComparisonRequest:
    return PostGISComparisonRequest(
        reference=PostGISInspectionRequest(
            target_schema="agent_sandbox",
            target_table="reference_layer",
        ),
        candidate=PostGISInspectionRequest(
            target_schema="agent_sandbox",
            target_table="candidate_layer",
        ),
    )


class FakeReader:
    def __init__(self, *, candidate_rows=2, missing=None) -> None:
        self.candidate_rows = candidate_rows
        self.missing = missing
        self.closed = False

    def table_exists(self, schema, table):
        return table != self.missing

    def columns(self, schema, table):
        return [
            PostGISColumn(
                ordinal_position=1,
                name="id",
                data_type="integer",
                nullable=False,
            )
        ]

    def keys(self, schema, table):
        return [("p", f"{table}_pkey", ["id"])]

    def geometry_metadata(self, schema, table):
        return [("geometry", "POINT", 4326)]

    def row_count(self, schema, table):
        if table == "candidate_layer":
            return self.candidate_rows
        return 2

    def geometry_statistics(self, schema, table, column):
        extent = LayerExtent(
            min_x=-71.1,
            min_y=42.3,
            max_x=-71.0,
            max_y=42.4,
        )
        return ["POINT"], 0, 0, extent

    def close(self):
        self.closed = True


@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        allowed_schemas=frozenset({"agent_sandbox"}),
    )


def test_equal_relation_facts_match(settings):
    result = compare_postgis_tables(
        request=request(),
        settings=settings,
        reader=FakeReader(),
    )
    assert result.status == "matched"
    assert result.matches is True
    assert result.differences == []
    assert result.database_modified is False
    assert result.arbitrary_sql_accepted is False


def test_constraint_names_do_not_create_false_difference(settings):
    result = compare_postgis_tables(
        request=request(),
        settings=settings,
        reader=FakeReader(),
    )
    assert result.reference.primary_key.name == "reference_layer_pkey"
    assert result.candidate.primary_key.name == "candidate_layer_pkey"
    assert result.matches is True


def test_row_count_difference_is_typed(settings):
    result = compare_postgis_tables(
        request=request(),
        settings=settings,
        reader=FakeReader(candidate_rows=3),
    )
    assert result.status == "different"
    assert result.matches is False
    assert [item.field for item in result.differences] == ["row_count"]
    assert result.differences[0].reference == 2
    assert result.differences[0].candidate == 3


def test_missing_relation_fails_closed(settings):
    with pytest.raises(PostGISComparisonError, match="candidate"):
        compare_postgis_tables(
            request=request(),
            settings=settings,
            reader=FakeReader(missing="candidate_layer"),
        )


def test_same_relation_is_rejected():
    relation = {
        "target_schema": "agent_sandbox",
        "target_table": "sample_points",
    }
    with pytest.raises(ValidationError, match="must be distinct"):
        PostGISComparisonRequest(
            reference=relation,
            candidate=relation,
        )


def test_query_fields_are_forbidden():
    payload = request().model_dump(mode="json")
    payload["sql"] = "select 1"
    with pytest.raises(ValidationError, match="sql"):
        PostGISComparisonRequest.model_validate(payload)


def test_unapproved_schema_is_rejected(settings):
    unsafe = PostGISComparisonRequest(
        reference=PostGISInspectionRequest(
            target_schema="public",
            target_table="reference_layer",
        ),
        candidate=request().candidate,
    )
    with pytest.raises(RuntimeError, match="not allowed"):
        compare_postgis_tables(
            request=unsafe,
            settings=settings,
            reader=FakeReader(),
        )


def test_skill_is_registered_read_only():
    project_root = Path(__file__).resolve().parents[1]
    skill = load_skill_registry(project_root).get_skill(
        "compare_postgis_tables"
    )
    assert skill.kind.value == "validation"
    assert skill.access.value == "read_only"
    assert skill.approval_required is False

