"""Compatibility import; implementation lives in task_actions.workflow."""
import sys
from geoagent_harness.task_actions import workflow as _implementation

sys.modules[__name__] = _implementation
