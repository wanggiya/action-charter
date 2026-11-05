"""Compatibility import; deterministic actions live in task_actions.data_tools."""
import sys
from geoagent_harness.task_actions import data_tools as _implementation

sys.modules[__name__] = _implementation
