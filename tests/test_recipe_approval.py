"""Tests for exact reusable-recipe approvals."""

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

import pytest

from geoagent_harness.recipes import (
    RecipeApprovalError,
    WorkflowRecipe,
    create_recipe_approval,
    load_recipe_approval,
    verify_recipe_approval,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)

from geoagent_harness.recipes import RecipeStep


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    16,
    4,
    0,
    tzinfo=timezone.utc,
)


def make_recipe() -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "recipe_id": "approved-conversion",
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
                            "approved.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )


def create_approved(
    tmp_path: Path,
):
    return create_recipe_approval(
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved conversion test.",
        approval_root=tmp_path,
        now=NOW,
        approval_id=(
            "recipe-approval-"
            "20260816t040000z-1234abcd"
        ),
    )


def test_recipe_approval_round_trip(
    tmp_path: Path,
) -> None:
    record, path = create_approved(
        tmp_path
    )

    loaded = load_recipe_approval(
        path,
        approval_root=tmp_path,
    )

    assert loaded == record


def test_exact_recipe_approval_passes(
    tmp_path: Path,
) -> None:
    record, _ = create_approved(
        tmp_path
    )

    result = verify_recipe_approval(
        approval=record,
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        now=NOW,
    )

    assert result.approved is True
    assert result.required_step_ids == [
        "step_2"
    ]
    assert result.missing_step_ids == []


def test_changed_recipe_is_rejected(
    tmp_path: Path,
) -> None:
    record, _ = create_approved(
        tmp_path
    )

    changed = make_recipe()
    changed.summary = "Changed after approval."

    result = verify_recipe_approval(
        approval=record,
        recipe=changed,
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        now=NOW,
    )

    assert result.approved is False
    assert "exact recipe" in result.reason


def test_incomplete_approval_is_rejected(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()

    recipe.steps.append(
        RecipeStep.model_validate(
            {
                "step_id": "step_3",
                "skill_id": "convert_vector",
                "depends_on": ["step_2"],
                "arguments": {
                    "path": (
                        "data/input/"
                        "sample_points.geojson"
                    ),
                    "target_path": (
                        "data/output/second.gpkg"
                    ),
                },
                "output_ids": ["second_vector"],
            }
        )
    )

    record, _ = create_recipe_approval(
        recipe=recipe,
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Partial approval.",
        approval_root=tmp_path,
        now=NOW,
    )

    result = verify_recipe_approval(
        approval=record,
        recipe=recipe,
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        now=NOW,
    )

    assert result.approved is False
    assert result.missing_step_ids == [
        "step_3"
    ]


def test_denied_recipe_is_rejected(
    tmp_path: Path,
) -> None:
    record, _ = create_recipe_approval(
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        step_ids=["step_2"],
        decision="denied",
        approver="test-operator",
        reason="Conversion denied.",
        approval_root=tmp_path,
        now=NOW,
    )

    result = verify_recipe_approval(
        approval=record,
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        now=NOW,
    )

    assert result.approved is False
    assert result.reason == (
        "approval decision is denied"
    )


def test_expired_recipe_approval_is_rejected(
    tmp_path: Path,
) -> None:
    record, _ = create_recipe_approval(
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Temporary approval.",
        approval_root=tmp_path,
        now=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )

    result = verify_recipe_approval(
        approval=record,
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        now=NOW + timedelta(minutes=6),
    )

    assert result.approved is False
    assert result.reason == (
        "recipe approval has expired"
    )


def test_read_only_step_cannot_be_approved(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RecipeApprovalError,
        match="do not require approval",
    ):
        create_recipe_approval(
            recipe=make_recipe(),
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            step_ids=["step_1"],
            decision="approved",
            approver="test-operator",
            reason="Invalid scope.",
            approval_root=tmp_path,
            now=NOW,
        )


def test_recipe_approval_overwrite_is_blocked(
    tmp_path: Path,
) -> None:
    create_approved(tmp_path)

    with pytest.raises(
        RecipeApprovalError,
        match="overwriting is blocked",
    ):
        create_approved(tmp_path)


def test_recipe_approval_is_redacted(
    tmp_path: Path,
) -> None:
    record, path = create_recipe_approval(
        recipe=make_recipe(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        step_ids=["step_2"],
        decision="approved",
        approver=(
            "operator token=do-not-expose"
        ),
        reason=(
            "password=do-not-expose"
        ),
        approval_root=tmp_path,
        now=NOW,
    )

    content = path.read_text(
        encoding="utf-8"
    )

    assert "do-not-expose" not in content
    assert "do-not-expose" not in record.reason
