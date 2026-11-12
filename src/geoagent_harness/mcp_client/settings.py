"""Compatibility alias for geoagent_harness.platform.client_settings."""
import sys
from geoagent_harness.platform import client_settings as _implementation
sys.modules[__name__] = _implementation
