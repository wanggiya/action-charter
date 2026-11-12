"""Generated schema contracts for convert_raster."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.data.spatial.skills.convert_raster.schemas import ConvertRasterArguments
from geoagent_harness.data.spatial.adapters.raster_conversion import RasterResampling


def test_arguments_are_strict() -> None:
    with pytest.raises(ValidationError):
        ConvertRasterArguments(
            path=Path("input/sample.tif"),
            target_path=Path("output/result.tif"),
            target_crs="EPSG:3857",
            unexpected=True,
        )


def test_resampling_is_allowlisted() -> None:
    arguments = ConvertRasterArguments(
        path=Path("input/sample.tif"),
        target_path=Path("output/result.tif"),
        target_crs="EPSG:3857",
        resampling="bilinear",
    )

    assert (
        arguments.resampling
        == RasterResampling.BILINEAR
    )

    with pytest.raises(ValidationError):
        ConvertRasterArguments(
            path=Path("input/sample.tif"),
            target_path=Path("output/result.tif"),
            target_crs="EPSG:3857",
            resampling="arbitrary",
        )
