"""Independent validation for raster conversion."""

from __future__ import annotations

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterConversionValidationResult,
    validate_raster_conversion as execute_validation,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)


class ConvertRasterValidationError(ValueError):
    """Raised when raster validation cannot complete."""


def validate_raster_conversion(
    arguments: ConvertRasterArguments,
    *,
    settings: MCPSettings,
) -> RasterConversionValidationResult:
    """Validate one exact source and target pair."""

    try:
        return execute_validation(
            path=arguments.path,
            target_path=arguments.target_path,
            target_crs=arguments.target_crs,
            input_root=settings.input_root,
            output_root=settings.output_root,
        )
    except RasterConversionError as exc:
        raise ConvertRasterValidationError(
            "raster conversion validation failed"
        ) from exc
