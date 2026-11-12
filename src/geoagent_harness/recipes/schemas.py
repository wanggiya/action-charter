"""Compatibility alias for geoagent_harness.contracts.recipes."""
import sys
from geoagent_harness.contracts import recipes as _implementation
sys.modules[__name__] = _implementation
