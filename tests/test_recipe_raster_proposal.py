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

def raster_conversion_proposal(
    *,
    path: str | None,
    target_path: str | None,
    target_crs: str | None,
) -> RecipeProposal:
    """Build one non-executable raster conversion proposal."""

    return RecipeProposal.model_validate(
        {
            "original_request": (
                "Reproject the sample raster."
            ),
            "summary": (
                "Inspect and convert one raster."
            ),
            "recipe_id_hint": (
                "convert-sample-raster"
            ),
            "selection": {
                "template_id": (
                    "inspect_and_convert_raster"
                ),
                "parameters": {
                    "path": path,
                    "target_path": target_path,
                    "target_crs": target_crs,
                    "resampling": "bilinear",
                },
            },
        }
    )


def test_raster_conversion_proposal_is_ready(
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    assessment = assess_recipe_proposal(
        raster_conversion_proposal(
            path="data/input/sample_dem.tif",
            target_path=(
                "data/output/reprojected_dem.tif"
            ),
            target_crs="EPSG:3857",
        ),
        registry=registry,
    )

    assert assessment.ready_for_compilation
    assert assessment.required_fields == [
        "path",
        "target_path",
        "target_crs",
    ]
    assert assessment.missing_fields == []
    assert assessment.policy_conflicts == []


def test_raster_conversion_requires_target_crs(
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    assessment = assess_recipe_proposal(
        raster_conversion_proposal(
            path="data/input/sample_dem.tif",
            target_path=(
                "data/output/reprojected_dem.tif"
            ),
            target_crs=None,
        ),
        registry=registry,
    )

    assert not assessment.ready_for_compilation
    assert assessment.missing_fields == [
        "target_crs"
    ]


def test_raster_conversion_rejects_non_tiff_target(
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    assessment = assess_recipe_proposal(
        raster_conversion_proposal(
            path="data/input/sample_dem.tif",
            target_path=(
                "data/output/reprojected_dem.png"
            ),
            target_crs="EPSG:3857",
        ),
        registry=registry,
    )

    assert not assessment.ready_for_compilation
    assert assessment.policy_conflicts == [
        "raster target_path must end with .tif"
    ]


def test_raster_conversion_compiles_for_approval(
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    result = compile_recipe_proposal(
        raster_conversion_proposal(
            path="data/input/sample_dem.tif",
            target_path=(
                "data/output/reprojected_dem.tif"
            ),
            target_crs="EPSG:3857",
        ),
        registry=registry,
    )

    recipe = result.recipe

    assert len(recipe.steps) == 2

    inspection = recipe.steps[0]
    conversion = recipe.steps[1]

    assert inspection.step_id == "step_1"
    assert inspection.skill_id == (
        "inspect_raster"
    )
    assert inspection.depends_on == []

    assert conversion.step_id == "step_2"
    assert conversion.skill_id == (
        "convert_raster"
    )
    assert conversion.depends_on == [
        "step_1"
    ]
    assert conversion.arguments == {
        "path": "data/input/sample_dem.tif",
        "target_path": (
            "data/output/reprojected_dem.tif"
        ),
        "target_crs": "EPSG:3857",
        "resampling": "bilinear",
    }

    assert (
        result.recipe_validation
        .approval_required_step_ids
        == ["step_2"]
    )

    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

