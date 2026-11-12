"""Compatibility alias for geoagent_harness.data.tabular.service."""
import sys
from geoagent_harness.data.tabular import service as _implementation
sys.modules[__name__] = _implementation
