"""Compatibility import; implementation lives in task_actions.exploration_contracts."""
import sys
from geoagent_harness.task_actions import exploration_contracts as _implementation

sys.modules[__name__] = _implementation
