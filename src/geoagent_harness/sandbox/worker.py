"""Compatibility alias for geoagent_harness.workspaces.sandbox.worker."""
import sys
from geoagent_harness.workspaces.sandbox import worker as _implementation
if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
