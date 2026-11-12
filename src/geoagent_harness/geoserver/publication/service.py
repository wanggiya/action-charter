"""Compatibility alias for geoagent_harness.data.spatial.geoserver.publication.service."""
import sys
from geoagent_harness.data.spatial.geoserver.publication import service as _implementation
sys.modules[__name__] = _implementation
