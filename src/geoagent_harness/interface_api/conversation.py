"""Compatibility import; implementation lives in task_actions.conversation."""
import sys
from geoagent_harness.task_actions import conversation as _implementation

sys.modules[__name__] = _implementation
