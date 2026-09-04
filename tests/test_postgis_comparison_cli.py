import json

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.postgis_comparison import (
    PostGISComparisonResult,
    PostGISDifference,
)
from geoagent_harness.postgis_inspection import PostGISInspectionResult


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


def result(*, matches: bool) -> PostGISComparisonResult:
    differences = []
    if not matches:
        differences = [
            PostGISDifference(
                field="row_count",
                reference=2,
                candidate=3,
            )
        ]
    return PostGISComparisonResult(
        status="matched" if matches else "different",
        matches=matches,
        reference=inspection("reference_layer"),
        candidate=inspection("candidate_layer"),
        differences=differences,
        warnings=[],
    )


def test_cli_match_exits_zero(monkeypatch):
    import geoagent_harness.postgis_comparison as module

    monkeypatch.setattr(
        module,
        "compare_postgis_tables",
        lambda **kwargs: result(matches=True),
    )
    invoked = CliRunner().invoke(
        app,
        [
            "compare-postgis-tables",
            "--reference-table",
            "reference_layer",
            "--candidate-table",
            "candidate_layer",
        ],
    )
    assert invoked.exit_code == 0
    assert json.loads(invoked.stdout)["matches"] is True


def test_cli_difference_exits_one(monkeypatch):
    import geoagent_harness.postgis_comparison as module

    monkeypatch.setattr(
        module,
        "compare_postgis_tables",
        lambda **kwargs: result(matches=False),
    )
    invoked = CliRunner().invoke(
        app,
        [
            "compare-postgis-tables",
            "--reference-table",
            "reference_layer",
            "--candidate-table",
            "candidate_layer",
        ],
    )
    assert invoked.exit_code == 1
    assert json.loads(invoked.stdout)["matches"] is False

