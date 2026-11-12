"""Compatibility alias for geoagent_harness.data.tabular.reporting."""
import sys
from geoagent_harness.data.tabular import reporting as _implementation
sys.modules[__name__] = _implementation
