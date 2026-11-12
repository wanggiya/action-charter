"""Compatibility alias for geoagent_harness.contracts.recipe_evidence."""
import sys
from geoagent_harness.contracts import recipe_evidence as _implementation
sys.modules[__name__] = _implementation
