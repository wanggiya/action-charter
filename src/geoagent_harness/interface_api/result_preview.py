"""Compatibility import; implementation lives in task_actions.result_preview."""
import sys
from geoagent_harness.task_actions import result_preview as _implementation

sys.modules[__name__] = _implementation
