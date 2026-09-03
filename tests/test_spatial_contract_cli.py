"""CLI tests for read-only spatial-data contract assessment."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app


PROJECT_ROOT = Path(__file__).parents[1]
BENCHMARK_ROOT = (
    PROJECT_ROOT / "benchmarks" / "spatial-contracts" / "vector"
)
DATA_ROOT = BENCHMARK_ROOT / "data"
runner = CliRunner()


def test_cli_assesses_clean_dataset() -> None:
    result = runner.invoke(
        app,
        [
            "assess-spatial-data-contract",
            "clean.geojson",
            "contract.yaml",
            "--input-root",
            str(DATA_ROOT),
            "--contract-root",
            str(BENCHMARK_ROOT),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["assessment_performed"] is True
    assert payload["filesystem_modified"] is False
    assert payload["database_modified"] is False
    assert payload["execution_performed"] is False


def test_cli_returns_one_for_contract_violation() -> None:
    result = runner.invoke(
        app,
        [
            "assess-spatial-data-contract",
            "invalid_geometry.geojson",
            "contract.yaml",
            "--input-root",
            str(DATA_ROOT),
            "--contract-root",
            str(BENCHMARK_ROOT),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert any(
        check["check_id"] == "invalid_geometry"
        and check["passed"] is False
        for check in payload["checks"]
    )


def test_cli_returns_two_for_unsafe_input() -> None:
    result = runner.invoke(
        app,
        [
            "assess-spatial-data-contract",
            "../outside.geojson",
            "contract.yaml",
            "--input-root",
            str(DATA_ROOT),
            "--contract-root",
            str(BENCHMARK_ROOT),
        ],
    )

    assert result.exit_code == 2
    assert "Error:" in result.output
