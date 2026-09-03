"""Tests for deterministic vector contract assessment."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point

from geoagent_harness.spatial_contracts import (
    SpatialDataContractAssessmentError,
    VectorSpatialDataContract,
    assess_spatial_data_contract,
    spatial_data_contract_sha256,
)


def contract(**updates) -> VectorSpatialDataContract:
    payload = {
        "contract_id": "assess_points",
        "contract_version": "1.0.0",
        "description": "Assessment test contract.",
        "expected_crs": "EPSG:4326",
        "allowed_geometry_types": ["Point"],
        "required_fields": [
            {
                "name": "feature_id",
                "field_type": "integer",
                "nullable": False,
                "max_null_fraction": 0.0,
            },
            {
                "name": "name",
                "field_type": "string",
                "nullable": False,
                "max_null_fraction": 0.0,
            },
        ],
        "unique_keys": [{"fields": ["feature_id"]}],
        "feature_count": {"minimum": 1, "maximum": 10},
        "permitted_extent": {
            "min_x": -80.0,
            "min_y": 40.0,
            "max_x": -70.0,
            "max_y": 50.0,
        },
    }
    payload.update(updates)
    return VectorSpatialDataContract.model_validate(payload)


def write_points(root: Path, *, duplicate_ids: bool = False) -> Path:
    path = root / "points.geojson"
    frame = gpd.GeoDataFrame(
        {
            "feature_id": [1, 1 if duplicate_ids else 2],
            "name": ["alpha", "beta"],
        },
        geometry=[Point(-75.0, 43.0), Point(-74.0, 44.0)],
        crs="EPSG:4326",
    )
    frame.to_file(path, driver="GeoJSON", engine="pyogrio")
    return path


def test_passes_complete_vector_contract(tmp_path: Path) -> None:
    path = write_points(tmp_path)
    expected_contract = contract()

    result = assess_spatial_data_contract(
        path=path,
        contract=expected_contract,
        input_root=tmp_path,
    )

    assert result.passed is True
    assert result.violations == []
    assert result.feature_count == 2
    assert result.geometry_types == ["Point"]
    assert result.contract_sha256 == spatial_data_contract_sha256(
        expected_contract
    )
    assert result.dataset_sha256 == result.dataset_sha256_after
    assert result.dataset_unchanged is True
    assert result.assessment_performed is True
    assert result.filesystem_modified is False
    assert result.database_modified is False
    assert result.execution_performed is False


def test_reports_multiple_deterministic_violations(tmp_path: Path) -> None:
    path = write_points(tmp_path, duplicate_ids=True)
    strict = contract(
        expected_crs="EPSG:3857",
        allowed_geometry_types=["Polygon"],
        feature_count={"minimum": 3, "maximum": 4},
        permitted_extent={
            "min_x": 0.0,
            "min_y": 0.0,
            "max_x": 1.0,
            "max_y": 1.0,
        },
    )

    result = assess_spatial_data_contract(
        path=path,
        contract=strict,
        input_root=tmp_path,
    )

    failed = {check.check_id for check in result.checks if not check.passed}
    assert result.passed is False
    assert "crs" in failed
    assert "geometry_types" in failed
    assert "feature_count" in failed
    assert "unique_key:feature_id" in failed
    assert "permitted_extent" in failed
    assert result.violations


def test_reports_missing_required_field(tmp_path: Path) -> None:
    path = write_points(tmp_path)
    expected_contract = contract(
        required_fields=[
            {
                "name": "missing_field",
                "field_type": "string",
                "nullable": False,
                "max_null_fraction": 0.0,
            }
        ],
        unique_keys=[],
    )

    result = assess_spatial_data_contract(
        path=path,
        contract=expected_contract,
        input_root=tmp_path,
    )

    failed = {check.check_id for check in result.checks if not check.passed}
    assert result.passed is False
    assert "required_field:missing_field" in failed


def test_rejects_dataset_outside_input_root(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    path = write_points(outside_root)

    with pytest.raises(
        SpatialDataContractAssessmentError,
        match="escaped",
    ):
        assess_spatial_data_contract(
            path=path,
            contract=contract(),
            input_root=root,
        )


def test_rejects_symlinked_dataset(tmp_path: Path) -> None:
    target = write_points(tmp_path)
    link = tmp_path / "linked.geojson"
    link.symlink_to(target)

    with pytest.raises(
        SpatialDataContractAssessmentError,
        match="cannot be a symlink",
    ):
        assess_spatial_data_contract(
            path=link,
            contract=contract(),
            input_root=tmp_path,
        )


def test_requires_layer_for_multilayer_dataset(tmp_path: Path) -> None:
    path = tmp_path / "layers.gpkg"
    first = gpd.GeoDataFrame(
        {"feature_id": [1], "name": ["first"]},
        geometry=[Point(-75.0, 43.0)],
        crs="EPSG:4326",
    )
    second = gpd.GeoDataFrame(
        {"feature_id": [2], "name": ["second"]},
        geometry=[Point(-74.0, 44.0)],
        crs="EPSG:4326",
    )
    first.to_file(
        path,
        layer="first",
        driver="GPKG",
        engine="pyogrio",
    )
    second.to_file(
        path,
        layer="second",
        driver="GPKG",
        engine="pyogrio",
        append=True,
    )

    with pytest.raises(
        SpatialDataContractAssessmentError,
        match="must select a layer",
    ):
        assess_spatial_data_contract(
            path=path,
            contract=contract(),
            input_root=tmp_path,
        )
