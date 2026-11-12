"""Compatibility alias for geoagent_harness.capabilities.registry.packages."""
import sys
from geoagent_harness.capabilities.registry import packages as _implementation
sys.modules[__name__] = _implementation
