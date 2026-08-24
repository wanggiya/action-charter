"""Typed schemas for controlled raster conversion."""

from __future__ import annotations

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
)

from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionResult,
    RasterConversionValidationResult,
    RasterResampling,
)


class ConvertRasterArguments(BaseModel):
    """Validated arguments for raster conversion."""

    model_config = ConfigDict(extra="forbid")

    path: Path
    target_path: Path
    target_crs: str
    resampling: RasterResampling = (
        RasterResampling.NEAREST
    )


ConvertRasterResult = RasterConversionResult
ConvertRasterValidationResult = (
    RasterConversionValidationResult
)
