"""Compatibility alias for geoagent_harness.data.spatial.skills.convert_raster.policy."""
import sys
from geoagent_harness.data.spatial.skills.convert_raster import policy as _implementation
sys.modules[__name__] = _implementation
