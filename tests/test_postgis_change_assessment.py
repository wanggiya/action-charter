from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.postgis_change_assessment import (
    PostGISChangeAssessment,
    PostGISChangeDisposition,
    assess_postgis_change,
)
from geoagent_harness.postgis_comparison import (
    PostGISComparisonResult,
    PostGISDifference,
)
from geoagent_harness.postgis_inspection import (
    PostGISColumn,
    PostGISGeometryColumn,
    PostGISInspectionResult,
)
from geoagent_harness.skill_registry import load_skill_registry
from geoagent_harness.verifier.postgis import LayerExtent


def inspection(table: str) -> PostGISInspectionResult:
    return PostGISInspectionResult(
        status="inspected",
        target_schema="agent_sandbox",
        target_table=table,
        table_exists=True,
        row_count=2,
        columns=[
            PostGISColumn(
                ordinal_position=1,
                name="id",
                data_type="integer",
                nullable=False,
            )
        ],
        primary_key=None,
        unique_keys=[],
        geometry_columns=[
            PostGISGeometryColumn(
                name="geometry",
                declared_type="POINT",
                srid=4326,
                observed_types=["POINT"],
                null_count=0,
                invalid_count=0,
                extent=LayerExtent(
                    min_x=0,
                    min_y=0,
                    max_x=1,
                    max_y=1,
                ),
            )
        ],
        warnings=[],
    )


def comparison(
    *,
    candidate: PostGISInspectionResult | None = None,
    fields: tuple[str, ...] = (),
) -> PostGISComparisonResult:
    reference = inspection("reference_layer")
    selected = candidate or inspection("candidate_layer")
    differences = [
        PostGISDifference(
            field=field,
            reference="before",
            candidate="after",
        )
        for field in fields
    ]
    matches = not differences
    return PostGISComparisonResult(
        status="matched" if matches else "different",
        matches=matches,
        reference=reference,
        candidate=selected,
        differences=differences,
        warnings=[],
    )


def test_exact_match_is_compatible():
    result = assess_postgis_change(comparison())
    assert result.disposition == PostGISChangeDisposition.COMPATIBLE
    assert result.compatible is True
    assert result.operator_review_required is False
    assert result.findings == []
    assert result.promotion_authorized is False
    assert result.approval_created is False


def test_row_count_change_requires_review():
    candidate = inspection("candidate_layer").model_copy(
        update={"row_count": 3}
    )
    result = assess_postgis_change(comparison(
        candidate=candidate,
        fields=("row_count",),
    ))
    assert result.disposition == PostGISChangeDisposition.REVIEW_REQUIRED
    assert result.operator_review_required is True
    assert [item.code for item in result.findings] == [
        "row_count_changed"
    ]


@pytest.mark.parametrize(
    ("update", "code", "field"),
    [
        ({"srid": 3857}, "geometry_registration_changed", "geometry_columns"),
        (
            {"observed_types": ["LINESTRING"]},
            "geometry_type_changed",
            "geometry_columns",
        ),
        ({"invalid_count": 1}, "geometry_quality_changed", "geometry_columns"),
        ({"extent": None}, "extent_changed", "geometry_columns"),
    ],
)
def test_geometry_change_classification(update, code, field):
    candidate = inspection("candidate_layer")
    changed = candidate.geometry_columns[0].model_copy(update=update)
    candidate = candidate.model_copy(
        update={"geometry_columns": [changed]}
    )
    result = assess_postgis_change(comparison(
        candidate=candidate,
        fields=(field,),
    ))
    assert [item.code for item in result.findings] == [code]
    expected = (
        PostGISChangeDisposition.REVIEW_REQUIRED
        if code in {"geometry_quality_changed", "extent_changed"}
        else PostGISChangeDisposition.INCOMPATIBLE
    )
    assert result.disposition == expected


def test_column_change_is_incompatible():
    candidate = inspection("candidate_layer")
    candidate = candidate.model_copy(update={
        "columns": [
            PostGISColumn(
                ordinal_position=1,
                name="renamed_id",
                data_type="integer",
                nullable=False,
            )
        ]
    })
    result = assess_postgis_change(comparison(
        candidate=candidate,
        fields=("columns",),
    ))
    assert result.disposition == PostGISChangeDisposition.INCOMPATIBLE
    assert result.compatible is False
    assert result.operator_review_required is False


def test_incompatible_change_dominates_observational_drift():
    candidate = inspection("candidate_layer")
    candidate = candidate.model_copy(update={
        "row_count": 3,
        "columns": [],
    })
    result = assess_postgis_change(comparison(
        candidate=candidate,
        fields=("columns", "row_count"),
    ))
    assert result.disposition == PostGISChangeDisposition.INCOMPATIBLE
    assert {item.code for item in result.findings} == {
        "columns_changed",
        "row_count_changed",
    }


def test_schema_rejects_false_compatibility_claim():
    result = assess_postgis_change(comparison())
    payload = result.model_dump(mode="json")
    payload["compatible"] = False
    with pytest.raises(ValidationError, match="compatible claim"):
        PostGISChangeAssessment.model_validate(payload)


def test_skill_is_registered_read_only():
    project_root = Path(__file__).resolve().parents[1]
    skill = load_skill_registry(project_root).get_skill(
        "assess_postgis_change"
    )
    assert skill.kind.value == "validation"
    assert skill.access.value == "read_only"
    assert skill.approval_required is False
