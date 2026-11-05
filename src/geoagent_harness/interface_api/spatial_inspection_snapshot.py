"""Compatibility import; implementation lives in task_actions.spatial_inspection_snapshot."""
import sys
from geoagent_harness.task_actions import spatial_inspection_snapshot as _implementation

sys.modules[__name__] = _implementation
