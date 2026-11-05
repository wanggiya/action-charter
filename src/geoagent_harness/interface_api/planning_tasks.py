"""Compatibility import; implementation lives in task_actions.planning_tasks."""
import sys
from geoagent_harness.task_actions import planning_tasks as _implementation

sys.modules[__name__] = _implementation
