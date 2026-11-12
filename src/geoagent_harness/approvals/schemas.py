"""Compatibility alias for geoagent_harness.core.policy.approvals.schemas."""
import sys
from geoagent_harness.core.policy.approvals import schemas as _implementation
sys.modules[__name__] = _implementation
