"""Generated wrapper around the trusted raster adapter."""

from __future__ import annotations

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionResult,
    inspect_raster as execute_adapter,
)
from geoagent_harness.skills.inspect_raster.policy import (
    validate_inspect_raster_request,
)
from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)


def inspect_raster(
    arguments: InspectRasterArguments,
) -> RasterInspectionResult:
    """Inspect one approved raster without writing data."""

    safe_path = validate_inspect_raster_request(
        path=arguments.path,
        input_root=arguments.input_root,
    )

    return execute_adapter(
        safe_path,
        input_root=arguments.input_root,
    )
