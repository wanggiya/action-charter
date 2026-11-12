"""Compatibility exports; native code imports the explicit layer owners."""
"""Deterministic read-only PostGIS table comparison."""

from geoagent_harness.data.databases.postgis.comparison.schemas import PostGISComparisonRequest, PostGISComparisonResult, PostGISDifference
from geoagent_harness.data.databases.postgis.comparison.service import PostGISComparisonError, compare_postgis_tables

__all__ = [
    "PostGISComparisonError",
    "PostGISComparisonRequest",
    "PostGISComparisonResult",
    "PostGISDifference",
    "compare_postgis_tables",
]
