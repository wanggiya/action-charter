"""Compatibility alias for geoagent_harness.apps.testing.raster."""
import sys
from geoagent_harness.apps.testing import raster as _implementation
sys.modules[__name__] = _implementation
