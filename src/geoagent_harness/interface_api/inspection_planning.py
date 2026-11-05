"""Compatibility import; implementation lives in task_actions.inspection_planning."""
import sys
from geoagent_harness.task_actions import inspection_planning as _implementation

sys.modules[__name__] = _implementation
