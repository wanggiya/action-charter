"""Compatibility import; implementation lives in task_actions.execution_assistance."""
import sys
from geoagent_harness.task_actions import execution_assistance as _implementation

sys.modules[__name__] = _implementation
