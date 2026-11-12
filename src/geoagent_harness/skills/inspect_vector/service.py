"""Compatibility alias for geoagent_harness.data.spatial.skills.inspect_vector.service."""
import sys
from geoagent_harness.data.spatial.skills.inspect_vector import service as _implementation
sys.modules[__name__] = _implementation
