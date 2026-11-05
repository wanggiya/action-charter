"""Compatibility import; implementation lives in task_actions.storage_paths."""
import sys
from geoagent_harness.task_actions import storage_paths as _implementation

sys.modules[__name__] = _implementation
