"""Tests for the deterministic raster fixture."""

from pathlib import Path

import rasterio

from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_writes_deterministic_raster(
    tmp_path: Path,
) -> None:
    path = write_test_raster(
        tmp_path / "sample_dem.tif"
    )

    with rasterio.open(path) as dataset:
        assert dataset.driver == "GTiff"
        assert dataset.width == 3
        assert dataset.height == 2
        assert dataset.count == 1
        assert dataset.crs.to_string() == (
            "EPSG:4326"
        )
        assert dataset.dtypes == ("uint16",)
        assert dataset.nodata == 0
        assert dataset.bounds.left == -71.1
        assert dataset.bounds.top == 42.4

        values = dataset.read(1)

    assert values.tolist() == [
        [1, 2, 3],
        [4, 5, 6],
    ]

