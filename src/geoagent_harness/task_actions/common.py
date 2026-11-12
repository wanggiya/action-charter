"""Compatibility exports for shared errors, roots and bounded result projection."""
from geoagent_harness.contracts.errors import InterfaceApiError, TaskActionError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.platform.outcomes import MAX_INTERFACE_OUTCOME_BYTES, _bounded_outcome
