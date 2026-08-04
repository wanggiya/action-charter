from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.verifier.postgis import (
    LayerExtent,
    LayerStatistics,
    PostGISVerificationError,
    validate_postgis_layer,
)


class FakeReader:
    def __init__(
        self,
        *,
        exists: bool = True,
        metadata: tuple[str, str, int] | None = (
            "geometry",
            "POINT",
            4326,
        ),
        statistics: LayerStatistics | None = None,
    ) -> None:
        self.exists = exists
        self.metadata = metadata
        self.layer_statistics = (
            statistics
            or LayerStatistics(
                row_count=2,
                null_geometry_count=0,
                invalid_geometry_count=0,
                geometry_types=["POINT"],
                extent=LayerExtent(
                    min_x=-71.1,
                    min_y=42.3,
                    max_x=-71.0,
                    max_y=42.4,
                ),
            )
        )
        self.closed = False

    def table_exists(
        self,
        schema: str,
        table: str,
    ) -> bool:
        return self.exists

    def geometry_metadata(
        self,
        schema: str,
        table: str,
    ) -> tuple[str, str, int] | None:
        return self.metadata

    def statistics(
        self,
        schema: str,
        table: str,
        geometry_column: str,
    ) -> LayerStatistics:
        return self.layer_statistics

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        enable_write_tools=False,
        allow_overwrite=False,
        allowed_schemas=frozenset({"agent_sandbox"}),
    )


def test_valid_layer_passes(
    settings: MCPSettings,
) -> None:
    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="sample_points",
        expected_row_count=2,
        expected_srid=4326,
        expected_geometry_type="POINT",
        settings=settings,
        reader=FakeReader(),
    )

    assert result.status == "validation_passed"
    assert result.passed is True
    assert result.row_count == 2
    assert result.srid == 4326
    assert result.geometry_type == "POINT"
    assert result.invalid_geometry_count == 0
    assert result.null_geometry_count == 0
    assert result.extent is not None


def test_missing_table_fails(
    settings: MCPSettings,
) -> None:
    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="missing",
        settings=settings,
        reader=FakeReader(exists=False),
    )

    assert result.status == "validation_failed"
    assert result.passed is False
    assert result.table_exists is False


def test_missing_geometry_column_fails(
    settings: MCPSettings,
) -> None:
    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="attributes_only",
        settings=settings,
        reader=FakeReader(metadata=None),
    )

    assert result.status == "validation_failed"
    assert result.geometry_column_exists is False


def test_invalid_geometry_fails(
    settings: MCPSettings,
) -> None:
    statistics = LayerStatistics(
        row_count=2,
        null_geometry_count=0,
        invalid_geometry_count=1,
        geometry_types=["POINT"],
        extent=LayerExtent(
            min_x=-71.1,
            min_y=42.3,
            max_x=-71.0,
            max_y=42.4,
        ),
    )

    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="sample_points",
        settings=settings,
        reader=FakeReader(statistics=statistics),
    )

    assert result.status == "validation_failed"
    assert result.passed is False


def test_null_geometry_fails(
    settings: MCPSettings,
) -> None:
    statistics = LayerStatistics(
        row_count=2,
        null_geometry_count=1,
        invalid_geometry_count=0,
        geometry_types=["POINT"],
        extent=LayerExtent(
            min_x=-71.1,
            min_y=42.3,
            max_x=-71.0,
            max_y=42.4,
        ),
    )

    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="sample_points",
        settings=settings,
        reader=FakeReader(statistics=statistics),
    )

    assert result.status == "validation_failed"
    assert result.passed is False


def test_wrong_expected_row_count_fails(
    settings: MCPSettings,
) -> None:
    result = validate_postgis_layer(
        target_schema="agent_sandbox",
        target_table="sample_points",
        expected_row_count=999,
        settings=settings,
        reader=FakeReader(),
    )

    assert result.status == "validation_failed"
    assert result.passed is False


def test_unapproved_schema_is_blocked(
    settings: MCPSettings,
) -> None:
    with pytest.raises(
        PostGISVerificationError,
        match="not allowed",
    ):
        validate_postgis_layer(
            target_schema="public",
            target_table="sample_points",
            settings=settings,
            reader=FakeReader(),
        )


@pytest.mark.parametrize(
    "table",
    [
        "Bad-Name",
        "public.sample",
        "sample;drop_table",
        "1sample",
        "sample points",
    ],
)
def test_unsafe_identifier_is_blocked(
    settings: MCPSettings,
    table: str,
) -> None:
    with pytest.raises(ValueError, match="target_table"):
        validate_postgis_layer(
            target_schema="agent_sandbox",
            target_table=table,
            settings=settings,
            reader=FakeReader(),
        )