"""Compatibility import; implementation lives in task_actions.method_helper."""
import sys
from geoagent_harness.task_actions import method_helper as _implementation

sys.modules[__name__] = _implementation
