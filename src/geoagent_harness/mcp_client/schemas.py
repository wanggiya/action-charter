"""Compatibility alias for geoagent_harness.contracts.mcp."""
import sys
from geoagent_harness.contracts import mcp as _implementation
sys.modules[__name__] = _implementation
