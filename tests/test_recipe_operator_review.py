"""Tests for the operator recipe-review boundary."""

from pathlib import Path

from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    review_recipe_request,
)


PROJECT_ROOT = Path(__file__).parents[1]

READY_REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10a.gpkg."
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
  "recipe_id_hint": "checkpoint10a",
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint10a.gpkg",
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


def test_ready_request_reaches_review() -> None:
    result = review_recipe_request(
        original_request=READY_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            content=ready_content()
        ),
    )

    assert result.status == (
        "ready_for_operator_review"
    )
    assert result.assessment.ready_for_compilation
    assert result.compilation is not None
    assert result.compilation_performed is True

    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

    assert [
        step.skill_id
        for step in result.compilation.recipe.steps
    ] == [
        "inspect_vector",
        "convert_vector",
    ]


def test_incomplete_request_requests_clarification() -> None:
    result = review_recipe_request(
        original_request=INCOMPLETE_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            content=incomplete_content()
        ),
    )

    assert result.status == (
        "clarification_required"
    )
    assert (
        result.assessment.ready_for_compilation
        is False
    )
    assert result.compilation is None
    assert result.compilation_performed is False

    assert result.clarification_questions == [
        (
            "Which approved input dataset should "
            "the recipe use?"
        ),
        (
            "Which new output path beneath the "
            "approved output root should be used?"
        ),
        (
            "The input and output paths are "
            "required."
        ),
    ]

    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

