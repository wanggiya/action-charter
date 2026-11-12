"""Compatibility alias for the native CLI command owner."""
import sys
from geoagent_harness.apps.cli import main as _implementation

if __name__ == "__main__":
    _implementation.app()
else:
    sys.modules[__name__] = _implementation
