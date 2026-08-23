"""Tests for the trusted raster-inspection adapter."""

from pathlib import Path

import pytest

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionError,
    inspect_raster,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_inspects_raster_read_only(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    raster_path = write_test_raster(
        input_root / "sample_dem.tif"
    )

    before = raster_path.stat()

    result = inspect_raster(
        raster_path,
        input_root=input_root,
    )

    after = raster_path.stat()

    assert result.status == "completed"
    assert result.source == "sample_dem.tif"
    assert result.driver == "GTiff"
    assert result.width == 3
    assert result.height == 2
    assert result.band_count == 1
    assert result.data_types == ["uint16"]
    assert result.crs == "EPSG:4326"
    assert result.nodata_values == [0.0]

    assert result.filesystem_modified is False
    assert result.database_modified is False
    assert result.execution_performed is True

    assert before.st_size == after.st_size
    assert before.st_mtime_ns == after.st_mtime_ns


def test_rejects_path_escape(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()

    outside = write_test_raster(
        tmp_path / "outside.tif"
    )

    with pytest.raises(
        RasterInspectionError,
        match="escaped",
    ):
        inspect_raster(
            outside,
            input_root=input_root,
        )


def test_rejects_symlink(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    target = write_test_raster(
        input_root / "target.tif"
    )
    link = input_root / "link.tif"
    link.symlink_to(target)

    with pytest.raises(
        RasterInspectionError,
        match="symlink",
    ):
        inspect_raster(
            link,
            input_root=input_root,
        )


def test_rejects_missing_raster(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()

    with pytest.raises(
        RasterInspectionError,
        match="does not exist",
    ):
        inspect_raster(
            input_root / "missing.tif",
            input_root=input_root,
        )


def test_rejects_non_raster_file(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()

    path = input_root / "not-raster.tif"
    path.write_text(
        "not a raster",
        encoding="utf-8",
    )

    with pytest.raises(
        RasterInspectionError,
        match="inspection failed",
    ):
        inspect_raster(
            path,
            input_root=input_root,
        )

