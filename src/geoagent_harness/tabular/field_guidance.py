"""Compatibility alias for geoagent_harness.data.tabular.field_guidance."""
import sys
from geoagent_harness.data.tabular import field_guidance as _implementation
sys.modules[__name__] = _implementation
