"""Compatibility import; implementation lives in task_actions.inspection_policy."""
import sys
from geoagent_harness.task_actions import inspection_policy as _implementation

sys.modules[__name__] = _implementation
