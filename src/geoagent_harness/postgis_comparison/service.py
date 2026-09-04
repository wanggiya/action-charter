"""Deterministic comparison composed over bounded PostGIS inspection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_comparison.schemas import (
    PostGISComparisonRequest,
    PostGISComparisonResult,
    PostGISDifference,
)
from geoagent_harness.postgis_inspection import (
    PostGISInspectionResult,
    inspect_postgis_table,
)
from geoagent_harness.postgis_inspection.service import (
    PostGISInspectionReader,
    PsycopgPostGISInspectionReader,
)


class PostGISComparisonError(RuntimeError):
    """Raised when exact comparison evidence is unavailable."""


def _profile(result: PostGISInspectionResult) -> Mapping[str, Any]:
    return {
        "columns": [
            column.model_dump(mode="json")
            for column in result.columns
        ],
        "primary_key": (
            result.primary_key.columns
            if result.primary_key is not None
            else None
        ),
        "unique_keys": sorted(
            [key.columns for key in result.unique_keys]
        ),
        "row_count": result.row_count,
        "geometry_columns": [
            geometry.model_dump(mode="json")
            for geometry in result.geometry_columns
        ],
    }


def compare_postgis_tables(
    *,
    request: PostGISComparisonRequest,
    settings: MCPSettings,
    reader: PostGISInspectionReader | None = None,
) -> PostGISComparisonResult:
    """Compare two exact relations in one bounded read-only transaction."""

    active_reader = reader
    owns_reader = reader is None

    try:
        if active_reader is None:
            active_reader = PsycopgPostGISInspectionReader(settings)

        reference = inspect_postgis_table(
            request=request.reference,
            settings=settings,
            reader=active_reader,
        )
        candidate = inspect_postgis_table(
            request=request.candidate,
            settings=settings,
            reader=active_reader,
        )

        missing = [
            name
            for name, result in (
                ("reference", reference),
                ("candidate", candidate),
            )
            if not result.table_exists
        ]
        if missing:
            raise PostGISComparisonError(
                "comparison relation is unavailable: "
                + ", ".join(missing)
            )

        reference_profile = _profile(reference)
        candidate_profile = _profile(candidate)
        differences = [
            PostGISDifference(
                field=field,
                reference=reference_profile[field],
                candidate=candidate_profile[field],
            )
            for field in reference_profile
            if reference_profile[field] != candidate_profile[field]
        ]
        matches = not differences

        return PostGISComparisonResult(
            status="matched" if matches else "different",
            matches=matches,
            reference=reference,
            candidate=candidate,
            differences=differences,
            warnings=[],
        )
    finally:
        if owns_reader and active_reader is not None:
            active_reader.close()
