"""Generated wrapper around the trusted raster adapter."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionResult,
    convert_raster as execute_adapter,
)
from geoagent_harness.skills.convert_raster.policy import (
    ConvertRasterPolicyError,
    validate_convert_raster_request,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterError(RuntimeError):
    """Raised when controlled raster conversion fails."""


def convert_raster(
    arguments: ConvertRasterArguments,
    *,
    settings: MCPSettings,
) -> RasterConversionResult:
    """Create one approved output pending validation."""

    try:
        validate_convert_raster_request(
            arguments=arguments,
            settings=settings,
        )

        return execute_adapter(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            settings=settings,
            resampling=arguments.resampling,
        )
    except (
        ConvertRasterPolicyError,
        RasterConversionError,
    ) as exc:
        raise ConvertRasterError(
            "controlled raster conversion failed"
        ) from exc
