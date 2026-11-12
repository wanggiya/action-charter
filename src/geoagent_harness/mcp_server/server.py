"""Compatibility alias for geoagent_harness.apps.mcp.server."""
import sys
from geoagent_harness.apps.mcp import server as _implementation
if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
