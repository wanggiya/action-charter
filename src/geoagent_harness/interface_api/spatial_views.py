"""Compatibility import; implementation lives in task_actions.spatial_views."""
import sys
from geoagent_harness.task_actions import spatial_views as _implementation

sys.modules[__name__] = _implementation
