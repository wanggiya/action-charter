"""Compatibility alias for geoagent_harness.platform.model_settings."""
import sys
from geoagent_harness.platform import model_settings as _implementation
sys.modules[__name__] = _implementation
