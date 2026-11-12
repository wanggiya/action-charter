"""Compatibility alias for geoagent_harness.data.spatial.skills.load_vector_to_postgis.service."""
import sys
from geoagent_harness.data.spatial.skills.load_vector_to_postgis import service as _implementation
sys.modules[__name__] = _implementation
