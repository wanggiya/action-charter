"""Compatibility alias for the shared implementation owner."""
import sys
from geoagent_harness.apps.http import server as _implementation
sys.modules[__name__] = _implementation
