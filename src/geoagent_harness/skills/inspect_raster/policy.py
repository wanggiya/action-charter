"""Compatibility alias for geoagent_harness.data.spatial.skills.inspect_raster.policy."""
import sys
from geoagent_harness.data.spatial.skills.inspect_raster import policy as _implementation
sys.modules[__name__] = _implementation
