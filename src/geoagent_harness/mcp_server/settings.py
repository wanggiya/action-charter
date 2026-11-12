"""Compatibility alias for geoagent_harness.platform.settings."""
import sys
from geoagent_harness.platform import settings as _implementation
sys.modules[__name__] = _implementation
