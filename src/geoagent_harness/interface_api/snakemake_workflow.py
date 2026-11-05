"""Compatibility import; implementation lives in task_actions.snakemake_workflow."""
import sys
from geoagent_harness.task_actions import snakemake_workflow as _implementation

sys.modules[__name__] = _implementation
