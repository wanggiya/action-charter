"""Compatibility import; implementation lives in task_actions.workflow_runs."""
import sys
from geoagent_harness.task_actions import workflow_runs as _implementation

sys.modules[__name__] = _implementation
