"""Compatibility alias for geoagent_harness.data.spatial.adapters.raster_conversion."""
import sys
from geoagent_harness.data.spatial.adapters import raster_conversion as _implementation
sys.modules[__name__] = _implementation
