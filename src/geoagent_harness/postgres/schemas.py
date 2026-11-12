"""Compatibility alias for geoagent_harness.contracts.postgres."""
import sys
from geoagent_harness.contracts import postgres as _implementation
sys.modules[__name__] = _implementation
