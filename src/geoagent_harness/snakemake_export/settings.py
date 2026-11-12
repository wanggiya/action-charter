"""Compatibility alias for geoagent_harness.platform.replay_settings."""
import sys
from geoagent_harness.platform import replay_settings as _implementation
sys.modules[__name__] = _implementation
