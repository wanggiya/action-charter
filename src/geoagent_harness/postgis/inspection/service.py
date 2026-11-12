"""Compatibility alias for geoagent_harness.data.databases.postgis.inspection.service."""
import sys
from geoagent_harness.data.databases.postgis.inspection import service as _implementation
sys.modules[__name__] = _implementation
