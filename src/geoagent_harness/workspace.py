"""Compatibility alias for geoagent_harness.platform.workspace."""
import sys
from geoagent_harness.platform import workspace as _implementation
sys.modules[__name__] = _implementation
