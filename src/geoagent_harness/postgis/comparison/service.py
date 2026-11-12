"""Compatibility alias for geoagent_harness.data.databases.postgis.comparison.service."""
import sys
from geoagent_harness.data.databases.postgis.comparison import service as _implementation
sys.modules[__name__] = _implementation
