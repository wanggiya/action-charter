"""Compatibility alias for geoagent_harness.platform.execution_control."""
import sys
from geoagent_harness.platform import execution_control as _implementation
sys.modules[__name__] = _implementation
