"""Compatibility alias for geoagent_harness.data.spatial.skills.convert_raster.service."""
import sys
from geoagent_harness.data.spatial.skills.convert_raster import service as _implementation
sys.modules[__name__] = _implementation
