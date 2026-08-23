"""Tests for the trusted raster-inspection recipe template."""

from pathlib import Path

from geoagent_harness.recipe_proposals import (
    RecipeProposal,
    assess_recipe_proposal,
    compile_recipe_proposal,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]


def raster_proposal(
    *,
    path: str | None,
) -> RecipeProposal:
    """Build one non-executable raster proposal."""

    return RecipeProposal.model_validate(
        {
            "original_request": (
                "Inspect the sample raster."
            ),
            "summary": (
                "Inspect trusted raster metadata."
            ),
            "recipe_id_hint": (
                "inspect-sample-raster"
            ),
            "selection": {
                "template_id": (
                    "inspect_raster"
                ),
                "parameters": {
                    "path": path,
                },
            },
        }
    )


def test_raster_proposal_is_ready() -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    assessment = assess_recipe_proposal(
        raster_proposal(
            path=(
                "data/input/sample_dem.tif"
            )
        ),
        registry=registry,
    )

    assert assessment.template_id == (
        "inspect_raster"
    )
    assert assessment.ready_for_compilation
    assert assessment.required_fields == [
        "path"
    ]
    assert assessment.missing_fields == []
    assert assessment.compilation_performed is False
    assert assessment.execution_performed is False


def test_raster_proposal_requires_path() -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    assessment = assess_recipe_proposal(
        raster_proposal(path=None),
        registry=registry,
    )

    assert not assessment.ready_for_compilation
    assert assessment.missing_fields == [
        "path"
    ]
    assert assessment.clarification_questions == [
        (
            "Which approved input dataset should "
            "the recipe use?"
        )
    ]


def test_raster_proposal_compiles_without_execution(
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    result = compile_recipe_proposal(
        raster_proposal(
            path=(
                "data/input/sample_dem.tif"
            )
        ),
        registry=registry,
    )

    recipe = result.recipe

    assert recipe.recipe_id == (
        "inspect-sample-raster"
    )
    assert len(recipe.steps) == 1

    step = recipe.steps[0]

    assert step.step_id == "step_1"
    assert step.skill_id == "inspect_raster"
    assert step.depends_on == []
    assert step.arguments == {
        "path": (
            "data/input/sample_dem.tif"
        )
    }
    assert step.output_ids == [
        "raster_metadata"
    ]

    assert (
        result.recipe_validation
        .approval_required_step_ids
        == []
    )
    assert result.compilation_performed is True
    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

