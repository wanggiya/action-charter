import json

from typer.testing import CliRunner

from geoagent_harness.apps.cli.main import app
from geoagent_harness.data.databases.postgis.change_assessment.schemas import PostGISChangeDisposition
from geoagent_harness.data.databases.postgis.change_assessment.service import assess_postgis_change
from geoagent_harness.data.databases.postgis.comparison.schemas import PostGISComparisonResult, PostGISDifference
from geoagent_harness.data.databases.postgis.inspection.schemas import PostGISInspectionResult


def inspection(table: str) -> PostGISInspectionResult:
    return PostGISInspectionResult(
        status="inspected",
        target_schema="agent_sandbox",
        target_table=table,
        table_exists=True,
        row_count=2,
        columns=[],
        primary_key=None,
        unique_keys=[],
        geometry_columns=[],
        warnings=[],
    )


def comparison(
    *,
    candidate: PostGISInspectionResult | None = None,
    changed: bool = False,
) -> PostGISComparisonResult:
    differences = []
    if changed:
        differences = [
            PostGISDifference(
                field="row_count",
                reference=2,
                candidate=3,
            )
        ]
    return PostGISComparisonResult(
        status="different" if changed else "matched",
        matches=not changed,
        reference=inspection("reference_layer"),
        candidate=candidate or inspection("candidate_layer"),
        differences=differences,
        warnings=[],
    )


def test_cli_compatible_exits_zero(monkeypatch):
    import geoagent_harness.data.databases.postgis.change_assessment as assessment_module
    import geoagent_harness.data.databases.postgis.comparison as comparison_module

    monkeypatch.setattr(
        comparison_module,
        "compare_postgis_tables",
        lambda **kwargs: comparison(),
    )
    monkeypatch.setattr(
        assessment_module,
        "assess_postgis_change",
        assess_postgis_change,
    )
    result = CliRunner().invoke(
        app,
        [
            "assess-postgis-change",
            "--reference-table",
            "reference_layer",
            "--candidate-table",
            "candidate_layer",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["disposition"] == "compatible"
    assert payload["promotion_authorized"] is False


def test_cli_review_required_exits_one(monkeypatch):
    import geoagent_harness.data.databases.postgis.comparison as comparison_module

    candidate = inspection("candidate_layer").model_copy(
        update={"row_count": 3}
    )
    evidence = comparison(
        candidate=candidate,
        changed=True,
    )
    monkeypatch.setattr(
        comparison_module,
        "compare_postgis_tables",
        lambda **kwargs: evidence,
    )
    result = CliRunner().invoke(
        app,
        [
            "assess-postgis-change",
            "--reference-table",
            "reference_layer",
            "--candidate-table",
            "candidate_layer",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["disposition"] == (
        PostGISChangeDisposition.REVIEW_REQUIRED.value
    )
