"""Compatibility alias for geoagent_harness.data.tabular.calculations."""
import sys
from geoagent_harness.data.tabular import calculations as _implementation
sys.modules[__name__] = _implementation
