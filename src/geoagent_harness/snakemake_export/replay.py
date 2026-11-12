"""Compatibility alias for geoagent_harness.agents.runtime.snakemake_replay."""
import sys
from geoagent_harness.agents.runtime import snakemake_replay as _implementation
sys.modules[__name__] = _implementation
