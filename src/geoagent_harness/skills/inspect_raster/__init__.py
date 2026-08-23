"""Generated candidate for raster inspection."""

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
    InspectRasterResult,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)


__all__ = [
    "InspectRasterArguments",
    "InspectRasterResult",
    "inspect_raster",
]
