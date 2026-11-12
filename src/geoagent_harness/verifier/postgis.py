"""Compatibility alias for geoagent_harness.core.verification.postgis."""
import sys
from geoagent_harness.core.verification import postgis as _implementation
sys.modules[__name__] = _implementation
