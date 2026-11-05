"""Compatibility import; implementation lives in task_actions.approved_workflow."""
import sys
from geoagent_harness.task_actions import approved_workflow as _implementation

sys.modules[__name__] = _implementation
