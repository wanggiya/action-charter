"""Compatibility alias for geoagent_harness.apps.mcp.__main__."""
import sys
from geoagent_harness.apps.mcp import __main__ as _implementation
sys.modules[__name__] = _implementation
