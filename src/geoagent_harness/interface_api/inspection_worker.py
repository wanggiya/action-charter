"""Compatibility import; implementation lives in task_actions.inspection_worker."""
import sys
from geoagent_harness.task_actions import inspection_worker as _implementation

sys.modules[__name__] = _implementation
