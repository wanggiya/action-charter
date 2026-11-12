"""Compatibility alias for geoagent_harness.core.policy.plan."""
import sys
from geoagent_harness.core.policy import plan as _implementation
sys.modules[__name__] = _implementation
