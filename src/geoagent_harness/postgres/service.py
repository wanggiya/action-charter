"""Compatibility alias for geoagent_harness.data.databases.postgres.service."""
import sys
from geoagent_harness.data.databases.postgres import service as _implementation
sys.modules[__name__] = _implementation
