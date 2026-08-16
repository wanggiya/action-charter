"""Tests for controlled vector-conversion planning."""

from pathlib import Path

import pytest

import geopandas as gpd
from shapely.geometry import Point

from geoagent_harness.skills.convert_vector import (
    ConvertVectorPolicyError,
    VectorOutputFormat,
    plan_vector_conversion,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input"
SAMPLE = INPUT_ROOT / "sample_points.geojson"


def test_plans_geojson_conversion(
    tmp_path: Path,
) -> None:
    target = tmp_path / "converted_points.geojson"

    plan = plan_vector_conversion(
        path=SAMPLE,
        target_path=target,
        input_root=INPUT_ROOT,
        output_root=tmp_path,
    )

    assert plan.schema_version == "1.0"
    assert plan.status == "planned_not_executed"
    assert plan.target_format == (
        VectorOutputFormat.GEOJSON
    )
    assert plan.target_driver == "GeoJSON"
    assert plan.source_feature_count == 2
    assert plan.execution_allowed is False
    assert plan.approval_required is True
    assert plan.validation_required is True
    assert plan.overwrite is False
    assert target.exists() is False


def test_plans_geopackage_conversion(
    tmp_path: Path,
) -> None:
    target = tmp_path / "converted_points.gpkg"

    plan = plan_vector_conversion(
        path=SAMPLE,
        target_path=target,
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        target_layer="converted_points",
    )

    assert plan.target_format == (
        VectorOutputFormat.GEOPACKAGE
    )
    assert plan.target_driver == "GPKG"
    assert plan.target_layer == "converted_points"
    assert target.exists() is False


def test_rejects_target_outside_output_root(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "output"
    outside = tmp_path / "outside.geojson"

    with pytest.raises(
        ConvertVectorPolicyError,
        match="approved output root",
    ):
        plan_vector_conversion(
            path=SAMPLE,
            target_path=outside,
            input_root=INPUT_ROOT,
            output_root=output_root,
        )


def test_rejects_existing_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing.geojson"
    target.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ConvertVectorPolicyError,
        match="already exists",
    ):
        plan_vector_conversion(
            path=SAMPLE,
            target_path=target,
            input_root=INPUT_ROOT,
            output_root=tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    [
        "unsafe file.geojson",
        "UPPER.geojson",
        "../escape.geojson",
        "output.shp",
        "output.json",
        "output.tif",
    ],
)
def test_rejects_unsafe_target_names(
    tmp_path: Path,
    filename: str,
) -> None:
    target = tmp_path / filename

    with pytest.raises(
        ConvertVectorPolicyError,
    ):
        plan_vector_conversion(
            path=SAMPLE,
            target_path=target,
            input_root=INPUT_ROOT,
            output_root=tmp_path,
        )


@pytest.mark.parametrize(
    "layer",
    [
        "Bad-Layer",
        "1layer",
        "layer name",
        "layer;drop",
        "public.layer",
    ],
)
def test_rejects_unsafe_target_layer(
    tmp_path: Path,
    layer: str,
) -> None:
    with pytest.raises(
        ConvertVectorPolicyError,
        match="target_layer",
    ):
        plan_vector_conversion(
            path=SAMPLE,
            target_path=(
                tmp_path / "converted.gpkg"
            ),
            input_root=INPUT_ROOT,
            output_root=tmp_path,
            target_layer=layer,
        )


def test_rejects_source_outside_input_root(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.geojson"
    outside.write_text(
        '{"type":"FeatureCollection","features":[]}',
        encoding="utf-8",
    )

    with pytest.raises(
        ConvertVectorPolicyError,
        match="approved root",
    ):
        plan_vector_conversion(
            path=outside,
            target_path=(
                tmp_path / "converted.geojson"
            ),
            input_root=INPUT_ROOT,
            output_root=tmp_path,
        )

def test_conversion_plan_uses_registered_version(
    tmp_path: Path,
) -> None:
    plan = plan_vector_conversion(
        path=SAMPLE,
        target_path=(
            tmp_path / "versioned.geojson"
        ),
        input_root=INPUT_ROOT,
        output_root=tmp_path,
    )

    assert plan.schema_version == "1.0"

def test_default_layer_normalizes_filename_hyphens(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "points.geojson"

    frame = gpd.GeoDataFrame(
        {
            "name": ["one"],
        },
        geometry=[
            Point(-71.0, 42.0),
        ],
        crs="EPSG:4326",
    )

    frame.to_file(
        source,
        driver="GeoJSON",
        index=False,
    )

    plan = plan_vector_conversion(
        path=source,
        target_path=(
            output_root
            / "converted-points.gpkg"
        ),
        input_root=input_root,
        output_root=output_root,
    )

    assert plan.target_layer == (
        "converted_points"
    )
