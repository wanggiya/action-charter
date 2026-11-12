"""Compatibility alias for geoagent_harness.contracts.workflow."""
import sys
from geoagent_harness.contracts import workflow as _implementation
sys.modules[__name__] = _implementation
