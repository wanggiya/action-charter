"""Compatibility alias for geoagent_harness.contracts.tool_results."""
import sys
from geoagent_harness.contracts import tool_results as _implementation
sys.modules[__name__] = _implementation
