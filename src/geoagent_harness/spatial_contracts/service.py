"""Compatibility alias for geoagent_harness.contracts.spatial.service."""
import sys
from geoagent_harness.contracts.spatial import service as _implementation
sys.modules[__name__] = _implementation
