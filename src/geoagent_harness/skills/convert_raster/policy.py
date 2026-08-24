"""Deterministic policy for raster conversion."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionPlan,
    plan_raster_conversion,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterPolicyError(ValueError):
    """Raised when raster conversion policy fails."""


def validate_convert_raster_request(
    *,
    arguments: ConvertRasterArguments,
    settings: MCPSettings,
) -> RasterConversionPlan:
    """Build a non-executing conversion plan."""

    try:
        return plan_raster_conversion(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            input_root=settings.input_root,
            output_root=settings.output_root,
            resampling=arguments.resampling,
        )
    except RasterConversionError as exc:
        raise ConvertRasterPolicyError(
            "raster conversion request failed policy"
        ) from exc
