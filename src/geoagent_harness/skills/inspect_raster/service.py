"""Compatibility alias for geoagent_harness.data.spatial.skills.inspect_raster.service."""
import sys
from geoagent_harness.data.spatial.skills.inspect_raster import service as _implementation
sys.modules[__name__] = _implementation
