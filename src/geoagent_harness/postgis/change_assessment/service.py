"""Compatibility alias for geoagent_harness.data.databases.postgis.change_assessment.service."""
import sys
from geoagent_harness.data.databases.postgis.change_assessment import service as _implementation
sys.modules[__name__] = _implementation
