"""Compatibility alias for geoagent_harness.data.spatial.geoserver.inspection.service."""
import sys
from geoagent_harness.data.spatial.geoserver.inspection import service as _implementation
sys.modules[__name__] = _implementation
