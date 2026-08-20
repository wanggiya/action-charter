"""Tests for proposal generation and compilation."""

from pathlib import Path

from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    propose_and_compile_recipe,
)


PROJECT_ROOT = Path(__file__).parents[1]

REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint9h.gpkg."
)


class FakeModelClient:
    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        assert request.json_mode is True

        return ModelResult(
            model="fake-qwen",
            finish_reason="stop",
            content=f"""
{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "{REQUEST}",
  "summary": "Inspect and convert the vector dataset.",
  "recipe_id_hint": "checkpoint9h",
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint9h.gpkg",
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
""".strip(),
        )


def test_pipeline_compiles_without_saving() -> None:
    result = propose_and_compile_recipe(
        original_request=REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(),
    )

    assert result.proposal_generated is True
    assert result.proposal_assessed is True
    assert result.compilation_performed is True

    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

    assert (
        result.generation.proposal
        .selection.template_id
        == "inspect_and_convert_vector"
    )

    recipe = result.compilation.recipe

    assert recipe.recipe_id == "checkpoint9h"
    assert recipe.execution_performed is False
    assert recipe.validation_performed is False

    assert [
        step.skill_id
        for step in recipe.steps
    ] == [
        "inspect_vector",
        "convert_vector",
    ]

    validation = (
        result.compilation.recipe_validation
    )

    assert validation.valid is True
    assert (
        validation.approval_required_step_ids
        == ["step_2"]
    )
    assert (
        validation.validation_required_step_ids
        == ["step_2"]
    )


def test_pipeline_preserves_authoritative_request() -> None:
    result = propose_and_compile_recipe(
        original_request=REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(),
    )

    assert (
        result.compilation.recipe.original_request
        == REQUEST
    )
    assert (
        result.generation.proposal.original_request
        == REQUEST
    )

