"""Typed schemas for raster inspection."""

from __future__ import annotations

from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionResult,
)


class InspectRasterArguments(BaseModel):
    """Validated arguments for raster inspection."""

    model_config = ConfigDict(extra="forbid")

    path: Path
    input_root: Path


InspectRasterResult = RasterInspectionResult
