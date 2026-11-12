"""Compatibility alias for geoagent_harness.data.spatial.adapters.raster_inspection."""
import sys
from geoagent_harness.data.spatial.adapters import raster_inspection as _implementation
sys.modules[__name__] = _implementation
