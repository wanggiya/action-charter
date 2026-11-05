"""Compatibility import; implementation lives in task_actions.method_memory."""
import sys
from geoagent_harness.task_actions import method_memory as _implementation

sys.modules[__name__] = _implementation
