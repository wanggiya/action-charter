"""Tests for vector-conversion execution CLI."""

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


def test_convert_vector_help() -> None:
    result = runner.invoke(
        app,
        [
            "convert-vector",
            "--help",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 0
    assert "--source-layer" in output
    assert "--target-layer" in output
    assert "--pretty" in output


def test_cli_rejects_disabled_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "disabled.geojson"

    monkeypatch.setenv(
        "GEOAGENT_INPUT_ROOT",
        str(SAMPLE.parent),
    )
    monkeypatch.setenv(
        "GEOAGENT_OUTPUT_ROOT",
        str(tmp_path),
    )
    monkeypatch.setenv(
        "ENABLE_WRITE_TOOLS",
        "false",
    )

    result = runner.invoke(
        app,
        [
            "convert-vector",
            str(SAMPLE),
            str(target),
        ],
    )

    assert result.exit_code == 2
    assert "write tools are disabled" in result.output
    assert target.exists() is False


def test_cli_writes_pending_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "cli_converted.gpkg"

    monkeypatch.setenv(
        "GEOAGENT_INPUT_ROOT",
        str(SAMPLE.parent),
    )
    monkeypatch.setenv(
        "GEOAGENT_OUTPUT_ROOT",
        str(tmp_path),
    )
    monkeypatch.setenv(
        "ENABLE_WRITE_TOOLS",
        "true",
    )
    monkeypatch.setenv(
        "ALLOW_OVERWRITE",
        "false",
    )

    result = runner.invoke(
        app,
        [
            "convert-vector",
            str(SAMPLE),
            str(target),
            "--target-layer",
            "cli_converted",
        ],
    )

    assert result.exit_code == 0
    assert target.is_file()

    payload = json.loads(result.stdout)

    assert payload["status"] == (
        "converted_pending_validation"
    )
    assert payload["validation_required"] is True
    assert payload["validation_performed"] is False
    assert payload["final_success_claimed"] is False
