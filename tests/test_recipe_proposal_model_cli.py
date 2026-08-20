"""Offline CLI tests for proposal generation."""

from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.model import (
    ModelResult,
)
import geoagent_harness.recipe_proposals.runtime as proposal_runtime


runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[1]

REQUEST = (
    "Inspect data/input/sample_points.geojson."
)


class FakeSharedModelClient:
    def __init__(
        self,
        _settings,
    ) -> None:
        pass

    def complete(self, _request):
        return ModelResult(
            model="fake-qwen",
            content=f"""
{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "{REQUEST}",
  "summary": "Inspect the vector dataset.",
  "recipe_id_hint": "checkpoint9f-cli",
  "selection": {{
    "template_id": "inspect_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null
    }}
  }},
  "assumptions": [],
  "missing_information": [],
  "warnings": [],
  "compilation_performed": false,
  "execution_requested": false,
  "approval_performed": false,
  "execution_performed": false
}}
""".strip(),
        )


def test_cli_generates_proposal_without_network(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        proposal_runtime,
        "SharedModelClient",
        FakeSharedModelClient,
    )
    monkeypatch.setattr(
        proposal_runtime,
        "load_model_settings",
        lambda: object(),
    )

    result = runner.invoke(
        app,
        [
            "propose-recipe",
            REQUEST,
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )

    import json

    payload = json.loads(result.stdout)

    assert payload["model"] == "fake-qwen"
    assert (
        payload["proposal"]
        ["selection"]["template_id"]
        == "inspect_vector"
    )

    assert (
        payload["proposal_schema_validated"]
        is True
    )
    assert (
        payload["compilation_performed"]
        is False
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

