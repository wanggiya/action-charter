"""Offline CLI tests for recipe operator review."""

from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.model import (
    ModelResult,
)
import geoagent_harness.recipe_proposals.runtime as proposal_runtime


runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[1]

READY_REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10b.gpkg."
)

INCOMPLETE_REQUEST = (
    "Convert my vector dataset."
)


class FakeSharedModelClient:
    content: str = ""

    def __init__(
        self,
        _settings,
    ) -> None:
        pass

    def complete(self, _request):
        return ModelResult(
            model="fake-qwen",
            content=self.content,
            finish_reason="stop",
        )


def ready_content() -> str:
    return f"""
{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "{READY_REQUEST}",
  "summary": "Inspect and convert the vector dataset.",
  "recipe_id_hint": "checkpoint10b",
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint10b.gpkg",
      "target_layer": null,
      "target_format": "geopackage"
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
""".strip()


def incomplete_content() -> str:
    return f"""
{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "{INCOMPLETE_REQUEST}",
  "summary": "Convert a vector dataset.",
  "recipe_id_hint": null,
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": null,
      "source_layer": null,
      "target_path": null,
      "target_layer": null,
      "target_format": null
    }}
  }},
  "assumptions": [],
  "missing_information": [
    "The input and output paths are required."
  ],
  "warnings": [],
  "compilation_performed": false,
  "execution_requested": false,
  "approval_performed": false,
  "execution_performed": false
}}
""".strip()


def install_fake_model(
    monkeypatch,
    *,
    content: str,
) -> None:
    FakeSharedModelClient.content = content

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


def test_ready_review_is_returned(
    monkeypatch,
) -> None:
    install_fake_model(
        monkeypatch,
        content=ready_content(),
    )

    result = runner.invoke(
        app,
        [
            "review-recipe-request",
            READY_REQUEST,
            "--project-root",
            str(PROJECT_ROOT),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )

    import json

    payload = json.loads(result.stdout)

    assert payload["status"] == (
        "ready_for_operator_review"
    )
    assert (
        payload["assessment"]
        ["ready_for_compilation"]
        is True
    )
    assert payload["compilation"] is not None

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


def test_clarification_is_valid_cli_outcome(
    monkeypatch,
) -> None:
    install_fake_model(
        monkeypatch,
        content=incomplete_content(),
    )

    result = runner.invoke(
        app,
        [
            "review-recipe-request",
            INCOMPLETE_REQUEST,
            "--project-root",
            str(PROJECT_ROOT),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )

    import json

    payload = json.loads(result.stdout)

    assert payload["status"] == (
        "clarification_required"
    )
    assert payload["compilation"] is None
    assert (
        payload["compilation_performed"]
        is False
    )
    assert len(
        payload["clarification_questions"]
    ) >= 1

    assert payload["recipe_saved"] is False
    assert (
        payload["approval_performed"]
        is False
    )
    assert (
        payload["execution_performed"]
        is False
    )

def test_ready_summary_is_human_readable(
    monkeypatch,
) -> None:
    install_fake_model(
        monkeypatch,
        content=ready_content(),
    )

    result = runner.invoke(
        app,
        [
            "review-recipe-request",
            READY_REQUEST,
            "--project-root",
            str(PROJECT_ROOT),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
            "--output-format",
            "summary",
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )
    assert (
        "Status: ready_for_operator_review"
        in result.stdout
    )
    assert "Recipe ID: checkpoint10b" in (
        result.stdout
    )
    assert (
        "Approval-required steps: step_2"
        in result.stdout
    )
    assert "Recipe saved: no" in result.stdout
    assert (
        "Execution performed: no"
        in result.stdout
    )


def test_unknown_output_format_is_rejected(
    monkeypatch,
) -> None:
    install_fake_model(
        monkeypatch,
        content=ready_content(),
    )

    result = runner.invoke(
        app,
        [
            "review-recipe-request",
            READY_REQUEST,
            "--project-root",
            str(PROJECT_ROOT),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
            "--output-format",
            "html",
        ],
    )

    assert result.exit_code == 2
    assert (
        "output format must be"
        in result.output
    )

