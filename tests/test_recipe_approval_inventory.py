"""Tests for deterministic recipe approval inventory."""

from datetime import datetime, timezone
from pathlib import Path

from geoagent_harness.recipes import (
    WorkflowRecipe,
    build_recipe_approval_inventory,
    create_recipe_approval,
    save_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


def recipe() -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "recipe_id": "inventory-test",
            "summary": "Inspect and convert data.",
            "original_request": (
                "Convert the sample dataset."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "arguments": {
                        "path": "data/input/sample.geojson"
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
                        "path": "data/input/sample.geojson",
                        "target_path": (
                            "data/output/sample.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )


def test_inventory_finds_exact_valid_match(
    tmp_path: Path,
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )
    recipe_root = tmp_path / "recipes"
    approval_root = tmp_path / "approvals"

    stored_recipe, recipe_path = save_recipe(
        recipe(),
        recipe_root=recipe_root,
    )

    approval, approval_path = create_recipe_approval(
        recipe=stored_recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved inventory test.",
        approval_root=approval_root,
        now=NOW,
    )

    result = build_recipe_approval_inventory(
        recipe_root=recipe_root,
        approval_root=approval_root,
        registry=registry,
        now=NOW,
    )

    assert result.recipe_count == 1
    assert result.approval_count == 1
    assert result.valid_match_count == 1
    assert len(result.matches) == 1

    match = result.matches[0]

    assert match.recipe_id == "inventory-test"
    assert match.recipe_filename == (
        recipe_path.name
    )
    assert match.approval_filename == (
        approval_path.name
    )
    assert match.approval_id == (
        approval.approval_id
    )
    assert match.approved is True
    assert match.approved_step_ids == [
        "step_2"
    ]

    assert (
        result.recipes_without_matching_approval
        == []
    )
    assert (
        result.approvals_without_matching_recipe
        == []
    )


def test_inventory_reports_recipe_without_approval(
    tmp_path: Path,
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )
    recipe_root = tmp_path / "recipes"
    approval_root = tmp_path / "approvals"

    _, recipe_path = save_recipe(
        recipe(),
        recipe_root=recipe_root,
    )
    approval_root.mkdir()

    result = build_recipe_approval_inventory(
        recipe_root=recipe_root,
        approval_root=approval_root,
        registry=registry,
        now=NOW,
    )

    assert result.valid_match_count == 0
    assert result.matches == []
    assert (
        result.recipes_without_matching_approval
        == [recipe_path.name]
    )

def test_inventory_ignores_non_recipe_approvals(
    tmp_path: Path,
) -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )
    recipe_root = tmp_path / "recipes"
    approval_root = tmp_path / "approvals"

    stored_recipe, _ = save_recipe(
        recipe(),
        recipe_root=recipe_root,
    )

    create_recipe_approval(
        recipe=stored_recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved inventory test.",
        approval_root=approval_root,
        now=NOW,
    )

    unrelated = (
        approval_root
        / "approval-unrelated.json"
    )
    unrelated.write_text(
        '{"schema_version":"1.0"}\n',
        encoding="utf-8",
    )

    result = build_recipe_approval_inventory(
        recipe_root=recipe_root,
        approval_root=approval_root,
        registry=registry,
        now=NOW,
    )

    assert result.approval_count == 1
    assert result.valid_match_count == 1
