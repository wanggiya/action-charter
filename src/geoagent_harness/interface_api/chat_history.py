"""Compatibility import; implementation lives in task_actions.chat_history."""
import sys
from geoagent_harness.task_actions import chat_history as _implementation

sys.modules[__name__] = _implementation
