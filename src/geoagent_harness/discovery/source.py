"""Compatibility alias for geoagent_harness.data.discovery.source."""
import sys
from geoagent_harness.data.discovery import source as _implementation
sys.modules[__name__] = _implementation
