"""Compatibility import; implementation lives in task_actions.planner_submission."""
import sys
from geoagent_harness.task_actions import planner_submission as _implementation

sys.modules[__name__] = _implementation
