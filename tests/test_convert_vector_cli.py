"""Tests for conversion-plan CLI registration."""

import json
from pathlib import Path

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (
    PROJECT_ROOT
    / "data"
    / "input"
    / "sample_points.geojson"
)


def test_plan_convert_help() -> None:
    result = runner.invoke(
        app,
        [
            "plan-convert-vector",
            "--help",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 0
    assert "--input-root" in output
    assert "--output-root" in output
    assert "--source-layer" in output
    assert "--target-layer" in output


def test_plan_convert_does_not_write(
    tmp_path: Path,
) -> None:
    target = tmp_path / "planned.geojson"

    result = runner.invoke(
        app,
        [
            "plan-convert-vector",
            str(SAMPLE),
            str(target),
            "--input-root",
            str(SAMPLE.parent),
            "--output-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["status"] == (
        "planned_not_executed"
    )
    assert payload["execution_allowed"] is False
    assert payload["approval_required"] is True
    assert target.exists() is False
