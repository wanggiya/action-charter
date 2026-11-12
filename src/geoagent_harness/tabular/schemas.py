"""Compatibility alias for geoagent_harness.contracts.tabular."""
import sys
from geoagent_harness.contracts import tabular as _implementation
sys.modules[__name__] = _implementation
