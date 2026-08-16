"""Tests for approved recipe execution handoff."""

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest

from geoagent_harness.recipes import (
    RecipeExecutionPolicyError,
    WorkflowRecipe,
    build_recipe_execution_envelope,
    create_recipe_approval,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    16,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_recipe() -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "recipe_id": "execution-envelope-test",
            "summary": "Convert sample points.",
            "original_request": (
                "Convert sample points."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
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
                            "execution-test.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )


def make_approval(
    tmp_path: Path,
):
    recipe = make_recipe()
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    approval, _ = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved execution handoff.",
        approval_root=tmp_path,
        now=NOW,
    )

    return recipe, registry, approval


def test_builds_nonexecuted_envelope(
    tmp_path: Path,
) -> None:
    recipe, registry, approval = (
        make_approval(tmp_path)
    )

    envelope = (
        build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
    )

    assert envelope.recipe_id == (
        "execution-envelope-test"
    )
    assert envelope.approved_step_ids == [
        "step_2"
    ]
    assert envelope.topological_step_ids == [
        "step_1",
        "step_2",
    ]
    assert [
        step.step_id
        for step in envelope.steps
    ] == [
        "step_1",
        "step_2",
    ]
    assert envelope.tool_name == (
        "run_approved_recipe"
    )
    assert envelope.execution_performed is False


def test_changed_recipe_cannot_build_envelope(
    tmp_path: Path,
) -> None:
    recipe, registry, approval = (
        make_approval(tmp_path)
    )

    recipe.summary = "Changed after approval."

    with pytest.raises(
        RecipeExecutionPolicyError,
        match="approval is not valid",
    ):
        build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )


def test_denied_recipe_cannot_build_envelope(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    approval, _ = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="denied",
        approver="test-operator",
        reason="Denied.",
        approval_root=tmp_path,
        now=NOW,
    )

    with pytest.raises(
        RecipeExecutionPolicyError,
        match="approval is not valid",
    ):
        build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
