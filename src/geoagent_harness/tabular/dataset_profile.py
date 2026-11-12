"""Compatibility alias for geoagent_harness.data.tabular.dataset_profile."""
import sys
from geoagent_harness.data.tabular import dataset_profile as _implementation
sys.modules[__name__] = _implementation
