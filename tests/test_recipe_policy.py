"""Tests for reusable recipe policy."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.recipes import (
    RecipePolicyError,
    WorkflowRecipe,
    recipe_sha256,
    validate_recipe_policy,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]


def conversion_recipe() -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "schema_version": "1.0",
            "recipe_id": "convert-sample-points",
            "status": "planned",
            "summary": (
                "Convert sample points to GeoPackage."
            ),
            "original_request": (
                "Convert sample_points.geojson "
                "to GeoPackage."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "depends_on": [],
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        )
                    },
                    "output_ids": [
                        "source_metadata"
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_vector",
                    "depends_on": [
                        "step_1"
                    ],
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_path": (
                            "data/output/"
                            "sample_points.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
            "execution_performed": False,
            "validation_performed": False,
        }
    )


def test_valid_conversion_recipe() -> None:
    recipe = conversion_recipe()
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    result = validate_recipe_policy(
        recipe,
        registry=registry,
    )

    assert result.valid is True
    assert result.topological_step_ids == [
        "step_1",
        "step_2",
    ]
    assert result.approval_required_step_ids == [
        "step_2"
    ]
    assert result.write_step_ids == [
        "step_2"
    ]
    assert result.validation_required_step_ids == [
        "step_2"
    ]
    assert result.execution_performed is False


def test_recipe_digest_is_deterministic() -> None:
    first = conversion_recipe()
    second = conversion_recipe()

    assert recipe_sha256(first) == (
        recipe_sha256(second)
    )


def test_unknown_skill_is_rejected() -> None:
    recipe = conversion_recipe()
    recipe.steps[0].skill_id = "unknown_skill"

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    with pytest.raises(
        RecipePolicyError,
        match="unknown skill",
    ):
        validate_recipe_policy(
            recipe,
            registry=registry,
        )


def test_unknown_dependency_is_rejected() -> None:
    recipe = conversion_recipe()
    recipe.steps[1].depends_on = [
        "step_999"
    ]

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    with pytest.raises(
        RecipePolicyError,
        match="unknown dependencies",
    ):
        validate_recipe_policy(
            recipe,
            registry=registry,
        )


def test_dependency_cycle_is_rejected() -> None:
    recipe = conversion_recipe()

    recipe.steps[0].depends_on = [
        "step_2"
    ]
    recipe.steps[1].depends_on = [
        "step_1"
    ]

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    with pytest.raises(
        RecipePolicyError,
        match="cycle",
    ):
        validate_recipe_policy(
            recipe,
            registry=registry,
        )


def test_write_step_requires_output() -> None:
    recipe = conversion_recipe()
    recipe.steps[1].output_ids = []

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    with pytest.raises(
        RecipePolicyError,
        match="logical output",
    ):
        validate_recipe_policy(
            recipe,
            registry=registry,
        )


def test_duplicate_dependencies_are_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="must not contain duplicates",
    ):
        WorkflowRecipe.model_validate(
            {
                "schema_version": "1.0",
                "recipe_id": "duplicate-dependency",
                "status": "planned",
                "summary": "Invalid recipe.",
                "original_request": (
                    "Test duplicate dependencies."
                ),
                "steps": [
                    {
                        "step_id": "step_1",
                        "skill_id": "inspect_vector",
                        "depends_on": [],
                        "arguments": {},
                        "output_ids": [
                            "metadata"
                        ],
                    },
                    {
                        "step_id": "step_2",
                        "skill_id": "convert_vector",
                        "depends_on": [
                            "step_1",
                            "step_1",
                        ],
                        "arguments": {},
                        "output_ids": [
                            "converted"
                        ],
                    },
                ],
            }
        )


def test_recipe_cannot_claim_execution() -> None:
    payload = conversion_recipe().model_dump(
        mode="json"
    )
    payload["execution_performed"] = True

    with pytest.raises(ValidationError):
        WorkflowRecipe.model_validate(payload)
