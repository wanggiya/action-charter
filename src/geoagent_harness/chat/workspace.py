"""Compatibility alias for geoagent_harness.apps.chat.workspace."""
import sys
from geoagent_harness.apps.chat import workspace as _implementation
if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
