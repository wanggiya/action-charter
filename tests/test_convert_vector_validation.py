"""Tests for deterministic vector conversion validation."""

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point

from geoagent_harness.skills.convert_vector.validation import (
    ConvertVectorValidationError,
    validate_vector_conversion,
)


def _frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "name": ["alpha", "beta"],
            "value": [1, 2],
        },
        geometry=[
            Point(-71.1, 42.3),
            Point(-71.0, 42.4),
        ],
        crs="EPSG:4326",
    )


def _write_source(path: Path) -> None:
    _frame().to_file(
        path,
        driver="GeoJSON",
        index=False,
    )


def test_valid_conversion_passes(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "points.geojson"
    target = output_root / "points.gpkg"

    frame = _frame()

    frame.to_file(
        source,
        driver="GeoJSON",
        index=False,
    )
    frame.to_file(
        target,
        layer="points",
        driver="GPKG",
        index=False,
    )

    result = validate_vector_conversion(
        path=source,
        target_path=target,
        input_root=input_root,
        output_root=output_root,
    )

    assert result.passed is True
    assert result.status == "validation_passed"
    assert all(
        check.passed
        for check in result.checks
    )


def test_changed_feature_count_fails(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "points.geojson"
    target = output_root / "points.geojson"

    source_frame = _frame()

    source_frame.to_file(
        source,
        driver="GeoJSON",
        index=False,
    )
    source_frame.iloc[:1].to_file(
        target,
        driver="GeoJSON",
        index=False,
    )

    result = validate_vector_conversion(
        path=source,
        target_path=target,
        input_root=input_root,
        output_root=output_root,
    )

    assert result.passed is False
    assert result.status == "validation_failed"

    failed = {
        check.name
        for check in result.checks
        if not check.passed
    }

    assert "feature_count_preserved" in failed


def test_target_outside_output_root_is_rejected(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "points.geojson"
    outside = tmp_path / "outside.geojson"

    _write_source(source)
    _write_source(outside)

    with pytest.raises(
        ConvertVectorValidationError,
        match="approved root",
    ):
        validate_vector_conversion(
            path=source,
            target_path=outside,
            input_root=input_root,
            output_root=output_root,
        )


def test_missing_target_is_rejected(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "points.geojson"
    _write_source(source)

    with pytest.raises(
        ConvertVectorValidationError,
        match="does not exist",
    ):
        validate_vector_conversion(
            path=source,
            target_path=(
                output_root / "missing.gpkg"
            ),
            input_root=input_root,
            output_root=output_root,
        )
