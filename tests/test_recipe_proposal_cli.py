"""CLI tests for deterministic proposal compilation."""

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[1]


def test_cli_compiles_without_execution(
    tmp_path: Path,
) -> None:
    proposal_file = (
        tmp_path / "proposal.json"
    )

    proposal_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "original_request": (
                    "Convert sample points."
                ),
                "summary": (
                    "Inspect and convert "
                    "sample points."
                ),
                "recipe_id_hint": (
                    "checkpoint9d-cli"
                ),
                "selection": {
                    "template_id": (
                        "inspect_and_convert_vector"
                    ),
                    "parameters": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_path": (
                            "data/output/"
                            "checkpoint9d-cli.gpkg"
                        ),
                        "target_format": (
                            "geopackage"
                        ),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "compile-recipe-proposal",
            str(proposal_file),
            "--proposal-root",
            str(tmp_path),
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )

    payload = json.loads(result.stdout)

    assert (
        payload["compilation_performed"]
        is True
    )
    assert payload["recipe_saved"] is False
    assert (
        payload["approval_performed"]
        is False
    )
    assert (
        payload["execution_performed"]
        is False
    )

    assert payload["recipe"]["recipe_id"] == (
        "checkpoint9d-cli"
    )
    assert [
        step["skill_id"]
        for step in payload["recipe"]["steps"]
    ] == [
        "inspect_vector",
        "convert_vector",
    ]

