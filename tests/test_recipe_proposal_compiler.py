"""Tests for deterministic recipe-proposal compilation."""

from pathlib import Path

import pytest

from geoagent_harness.recipe_proposals import (
    RecipeCompilationError,
    RecipeProposal,
    compile_recipe_proposal,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]


def registry():
    return load_skill_registry(
        PROJECT_ROOT
    )


def conversion_proposal(
    *,
    recipe_id_hint: str | None = (
        "checkpoint9c-conversion"
    ),
) -> RecipeProposal:
    return RecipeProposal.model_validate(
        {
            "original_request": (
                "Convert the sample points to "
                "GeoPackage."
            ),
            "summary": (
                "Inspect and convert sample points."
            ),
            "recipe_id_hint": recipe_id_hint,
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
                        "checkpoint9c.gpkg"
                    ),
                    "target_format": (
                        "geopackage"
                    ),
                },
            },
        }
    )


def test_conversion_compiles_to_fixed_recipe() -> None:
    result = compile_recipe_proposal(
        conversion_proposal(),
        registry=registry(),
    )

    assert result.compilation_performed is True
    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

    assert result.recipe.recipe_id == (
        "checkpoint9c-conversion"
    )
    assert result.recipe.status == "planned"
    assert result.recipe.execution_performed is False
    assert result.recipe.validation_performed is False

    assert [
        step.skill_id
        for step in result.recipe.steps
    ] == [
        "inspect_vector",
        "convert_vector",
    ]

    assert result.recipe.steps[0].step_id == (
        "step_1"
    )
    assert result.recipe.steps[0].depends_on == []

    assert result.recipe.steps[1].step_id == (
        "step_2"
    )
    assert result.recipe.steps[1].depends_on == [
        "step_1"
    ]

    assert (
        result.recipe.steps[1]
        .arguments["target_path"]
        == "data/output/checkpoint9c.gpkg"
    )


def test_compiled_recipe_passes_policy() -> None:
    result = compile_recipe_proposal(
        conversion_proposal(),
        registry=registry(),
    )

    assert result.recipe_validation.valid is True
    assert (
        result.recipe_validation
        .topological_step_ids
        == [
            "step_1",
            "step_2",
        ]
    )
    assert (
        result.recipe_validation
        .approval_required_step_ids
        == [
            "step_2",
        ]
    )
    assert (
        result.recipe_validation
        .validation_required_step_ids
        == [
            "step_2",
        ]
    )


def test_missing_parameter_blocks_compilation() -> None:
    proposal = RecipeProposal.model_validate(
        {
            "original_request": (
                "Convert a vector dataset."
            ),
            "summary": "Convert a vector.",
            "selection": {
                "template_id": (
                    "inspect_and_convert_vector"
                ),
                "parameters": {
                    "path": (
                        "data/input/"
                        "sample_points.geojson"
                    ),
                    "target_path": None,
                },
            },
        }
    )

    with pytest.raises(
        RecipeCompilationError,
        match="not ready",
    ):
        compile_recipe_proposal(
            proposal,
            registry=registry(),
        )


def test_generated_recipe_id_is_deterministic() -> None:
    proposal = conversion_proposal(
        recipe_id_hint=None
    )

    first = compile_recipe_proposal(
        proposal,
        registry=registry(),
    )
    second = compile_recipe_proposal(
        proposal,
        registry=registry(),
    )

    assert (
        first.recipe.recipe_id
        == second.recipe.recipe_id
    )
    assert first.recipe.recipe_id.startswith(
        "recipe-"
    )


def test_target_format_is_not_model_execution() -> None:
    result = compile_recipe_proposal(
        conversion_proposal(),
        registry=registry(),
    )

    conversion = result.recipe.steps[1]

    # target_format is used during proposal assessment.
    # The trusted conversion implementation derives the
    # actual driver from the target extension.
    assert "target_format" not in (
        conversion.arguments
    )

    assert result.recipe_saved is False
    assert result.execution_performed is False

