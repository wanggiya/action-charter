"""Compatibility alias for geoagent_harness.data.discovery.csv."""
import sys
from geoagent_harness.data.discovery import csv as _implementation
sys.modules[__name__] = _implementation
