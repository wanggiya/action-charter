"""Compatibility import; implementation lives in task_actions.run_assessment."""
import sys
from geoagent_harness.task_actions import run_assessment as _implementation

sys.modules[__name__] = _implementation
