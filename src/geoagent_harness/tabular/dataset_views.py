"""Compatibility alias for geoagent_harness.data.tabular.dataset_views."""
import sys
from geoagent_harness.data.tabular import dataset_views as _implementation
sys.modules[__name__] = _implementation
