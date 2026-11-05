"""Compatibility import; implementation lives in task_actions.result_exploration."""
import sys
from geoagent_harness.task_actions import result_exploration as _implementation

sys.modules[__name__] = _implementation
