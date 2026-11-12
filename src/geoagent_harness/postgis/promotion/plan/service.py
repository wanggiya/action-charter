"""Compatibility alias for geoagent_harness.data.databases.postgis.promotion.plan.service."""
import sys
from geoagent_harness.data.databases.postgis.promotion.plan import service as _implementation
sys.modules[__name__] = _implementation
