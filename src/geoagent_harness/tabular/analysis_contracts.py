"""Compatibility alias for geoagent_harness.contracts.analysis_options."""
import sys
from geoagent_harness.contracts import analysis_options as _implementation
sys.modules[__name__] = _implementation
