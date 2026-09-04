"""Fixed policy for PostGIS comparison evidence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from geoagent_harness.postgis_change_assessment.schemas import (
    PostGISChangeAssessment,
    PostGISChangeDisposition,
    PostGISChangeFinding,
)
from geoagent_harness.postgis_comparison import PostGISComparisonResult
from geoagent_harness.postgis_inspection import PostGISInspectionResult


def _geometry_profiles(
    result: PostGISInspectionResult,
) -> dict[str, Any]:
    geometries = sorted(
        result.geometry_columns,
        key=lambda item: item.name,
    )
    return {
        "registration": [
            {
                "name": item.name,
                "declared_type": item.declared_type,
                "srid": item.srid,
            }
            for item in geometries
        ],
        "observed_types": [
            {
                "name": item.name,
                "observed_types": item.observed_types,
            }
            for item in geometries
        ],
        "quality": [
            {
                "name": item.name,
                "null_count": item.null_count,
                "invalid_count": item.invalid_count,
            }
            for item in geometries
        ],
        "extent": [
            {
                "name": item.name,
                "extent": (
                    item.extent.model_dump(mode="json")
                    if item.extent is not None
                    else None
                ),
            }
            for item in geometries
        ],
    }


def _finding(
    *,
    code: str,
    disposition: PostGISChangeDisposition,
    reference: Any,
    candidate: Any,
    reason: str,
) -> PostGISChangeFinding:
    return PostGISChangeFinding(
        code=code,
        disposition=disposition,
        reference=reference,
        candidate=candidate,
        reason=reason,
    )


def assess_postgis_change(
    comparison: PostGISComparisonResult,
) -> PostGISChangeAssessment:
    """Classify trusted comparison evidence with fixed policy."""

    reference = comparison.reference
    candidate = comparison.candidate
    findings: list[PostGISChangeFinding] = []

    structural_rules: tuple[
        tuple[str, Callable[[PostGISInspectionResult], Any], str], ...
    ] = (
        (
            "columns_changed",
            lambda value: [
                item.model_dump(mode="json")
                for item in value.columns
            ],
            "Column identity, order, type, or nullability changed.",
        ),
        (
            "primary_key_changed",
            lambda value: (
                value.primary_key.columns
                if value.primary_key is not None
                else None
            ),
            "Primary-key column structure changed.",
        ),
        (
            "unique_keys_changed",
            lambda value: sorted(
                [item.columns for item in value.unique_keys]
            ),
            "Unique-key column structure changed.",
        ),
    )
    for code, selector, reason in structural_rules:
        before = selector(reference)
        after = selector(candidate)
        if before != after:
            findings.append(_finding(
                code=code,
                disposition=PostGISChangeDisposition.INCOMPATIBLE,
                reference=before,
                candidate=after,
                reason=reason,
            ))

    before_geometry = _geometry_profiles(reference)
    after_geometry = _geometry_profiles(candidate)
    geometry_rules = (
        (
            "registration",
            "geometry_registration_changed",
            PostGISChangeDisposition.INCOMPATIBLE,
            "Geometry-column identity, declared type, or CRS changed.",
        ),
        (
            "observed_types",
            "geometry_type_changed",
            PostGISChangeDisposition.INCOMPATIBLE,
            "Observed geometry types changed.",
        ),
        (
            "quality",
            "geometry_quality_changed",
            PostGISChangeDisposition.REVIEW_REQUIRED,
            "Null or invalid geometry counts changed.",
        ),
        (
            "extent",
            "extent_changed",
            PostGISChangeDisposition.REVIEW_REQUIRED,
            "Observed geometry extent changed.",
        ),
    )
    for key, code, disposition, reason in geometry_rules:
        before = before_geometry[key]
        after = after_geometry[key]
        if before != after:
            findings.append(_finding(
                code=code,
                disposition=disposition,
                reference=before,
                candidate=after,
                reason=reason,
            ))

    if reference.row_count != candidate.row_count:
        findings.append(_finding(
            code="row_count_changed",
            disposition=PostGISChangeDisposition.REVIEW_REQUIRED,
            reference=reference.row_count,
            candidate=candidate.row_count,
            reason="Observed row count changed.",
        ))

    if not findings and not comparison.matches:
        findings.append(_finding(
            code="unclassified_change",
            disposition=PostGISChangeDisposition.INCOMPATIBLE,
            reference=comparison.reference.model_dump(mode="json"),
            candidate=comparison.candidate.model_dump(mode="json"),
            reason="Comparison contains a change outside known policy.",
        ))

    dispositions = {item.disposition for item in findings}
    if PostGISChangeDisposition.INCOMPATIBLE in dispositions:
        disposition = PostGISChangeDisposition.INCOMPATIBLE
        reason = "One or more structural changes are incompatible."
    elif PostGISChangeDisposition.REVIEW_REQUIRED in dispositions:
        disposition = PostGISChangeDisposition.REVIEW_REQUIRED
        reason = (
            "Structure is compatible, but observed data facts require "
            "operator review."
        )
    else:
        disposition = PostGISChangeDisposition.COMPATIBLE
        reason = "No structural or observed data differences were found."

    return PostGISChangeAssessment(
        disposition=disposition,
        compatible=(
            disposition == PostGISChangeDisposition.COMPATIBLE
        ),
        operator_review_required=(
            disposition
            == PostGISChangeDisposition.REVIEW_REQUIRED
        ),
        comparison=comparison,
        findings=findings,
        reason=reason,
    )

