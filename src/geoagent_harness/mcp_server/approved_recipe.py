"""Compatibility import; implementation lives in task_actions.approved_recipe."""
import sys
from geoagent_harness.task_actions import approved_recipe as _implementation

sys.modules[__name__] = _implementation
