"""Tests for deterministic operator-review rendering."""

from pathlib import Path

from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    render_recipe_operator_review,
    review_recipe_request,
)


PROJECT_ROOT = Path(__file__).parents[1]

READY_REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10c.gpkg."
)

INCOMPLETE_REQUEST = (
    "Convert my vector dataset."
)


class FakeModelClient:
    def __init__(
        self,
        *,
        content: str,
    ) -> None:
        self.content = content

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        assert request.json_mode is True

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
  "summary": "Inspect and convert a vector dataset.",
  "recipe_id_hint": "checkpoint10c",
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint10c.gpkg",
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


def test_ready_review_summary() -> None:
    review = review_recipe_request(
        original_request=READY_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            content=ready_content()
        ),
    )

    rendered = render_recipe_operator_review(
        review
    )

    assert (
        "Status: ready_for_operator_review"
        in rendered
    )
    assert "Recipe ID: checkpoint10c" in rendered
    assert (
        "- step_1: inspect_vector "
        "(depends on: none)"
        in rendered
    )
    assert (
        "- step_2: convert_vector "
        "(depends on: step_1)"
        in rendered
    )
    assert (
        "Approval-required steps: step_2"
        in rendered
    )
    assert "Recipe saved: no" in rendered
    assert "Execution performed: no" in rendered


def test_clarification_summary() -> None:
    review = review_recipe_request(
        original_request=INCOMPLETE_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            content=incomplete_content()
        ),
    )

    rendered = render_recipe_operator_review(
        review
    )

    assert (
        "Status: clarification_required"
        in rendered
    )
    assert "Clarification required:" in rendered
    assert (
        "Which approved input dataset"
        in rendered
    )
    assert "Compilation performed: no" in rendered
    assert "Recipe saved: no" in rendered
    assert "Execution performed: no" in rendered
