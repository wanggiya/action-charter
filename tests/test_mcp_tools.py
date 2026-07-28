from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.mcp_server.tools import (
    TOOL_ALLOWLIST,
    health_check,
    inspect_vector_dataset,
    plan_load_vector_to_postgis,
)
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input"
SAMPLE = INPUT_ROOT / "sample_points.geojson"


@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(
        input_root=INPUT_ROOT,
        output_root=tmp_path / "output",
        enable_write_tools=False,
        allow_overwrite=False,
        allowed_schemas=frozenset(
            {"agent_sandbox"}
        ),
    )


def test_health_check_is_redacted(
    settings: MCPSettings,
) -> None:
    result = health_check(settings)
    payload = result.model_dump(mode="json")

    assert result.status == "ok"
    assert result.write_tools_enabled is False
    assert result.overwrite_enabled is False
    assert result.tools == TOOL_ALLOWLIST

    assert "password" not in payload
    assert "database_url" not in payload
    assert "connection_string" not in payload


def test_inspect_vector_dataset_uses_existing_skill(
    settings: MCPSettings,
) -> None:
    result = inspect_vector_dataset(
        str(SAMPLE),
        settings,
    )

    assert result.status == "inspected"
    assert result.result.driver == "GeoJSON"
    assert result.result.layers[0].feature_count == 2
    assert result.result.layers[0].geometry_type == "Point"


def test_inspection_rejects_outside_path(
    settings: MCPSettings,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.geojson"

    outside.write_text(
        '{"type":"FeatureCollection","features":[]}',
        encoding="utf-8",
    )

    with pytest.raises(
        InspectVectorError,
        match="approved root",
    ):
        inspect_vector_dataset(
            str(outside),
            settings,
        )


def test_plan_is_non_executing(
    settings: MCPSettings,
) -> None:
    result = plan_load_vector_to_postgis(
        path=str(SAMPLE),
        target_schema="agent_sandbox",
        target_table="sample_points",
        settings=settings,
    )

    assert result.status == "planned_not_executed"
    assert result.execution_allowed is False
    assert result.approval_required is True
    assert result.target_schema == "agent_sandbox"
    assert result.target_table == "sample_points"

    assert any(
        "no database connection" in warning.lower()
        for warning in result.warnings
    )


def test_plan_rejects_unapproved_schema(
    settings: MCPSettings,
) -> None:
    with pytest.raises(
        ValueError,
        match="not allowed",
    ):
        plan_load_vector_to_postgis(
            path=str(SAMPLE),
            target_schema="public",
            target_table="sample_points",
            settings=settings,
        )


@pytest.mark.parametrize(
    "identifier",
    [
        "Bad-Name",
        "public.sample",
        "sample;drop_table",
        "1sample",
        "sample points",
    ],
)
def test_plan_rejects_unsafe_table_names(
    settings: MCPSettings,
    identifier: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="target_table",
    ):
        plan_load_vector_to_postgis(
            path=str(SAMPLE),
            target_schema="agent_sandbox",
            target_table=identifier,
            settings=settings,
        )