"""Tests for deterministic Snakemake export planning."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.recipes import (
    WorkflowRecipe,
    build_recipe_execution_envelope,
    create_recipe_approval,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.snakemake_export import (
    SnakemakeExportPolicyError,
    plan_snakemake_recipe_export,
)


PROJECT_ROOT = Path(__file__).parents[1]


def approved_recipe(
    tmp_path: Path,
):
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    recipe = WorkflowRecipe.model_validate(
        {
            "recipe_id": "snakemake-test",
            "summary": "Inspect and convert vector data.",
            "original_request": (
                "Convert the sample vector dataset."
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
                            "snakemake-test.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )

    approval, approval_path = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved export test.",
        approval_root=tmp_path / "approvals",
        now=datetime(
            2026,
            8,
            22,
            tzinfo=timezone.utc,
        ),
    )

    recipe_path = (
        tmp_path
        / "recipes"
        / "snakemake-test.json"
    )

    return (
        recipe,
        approval,
        registry,
        recipe_path,
        approval_path,
    )


def test_approved_recipe_export_is_planned(
    tmp_path: Path,
) -> None:
    (
        recipe,
        approval,
        registry,
        recipe_path,
        approval_path,
    ) = approved_recipe(tmp_path)

    plan = plan_snakemake_recipe_export(
        recipe=recipe,
        approval=approval,
        registry=registry,
        recipe_path=recipe_path,
        approval_path=approval_path,
    )

    envelope = build_recipe_execution_envelope(
        recipe=recipe,
        approval=approval,
        registry=registry,
    )

    assert plan.recipe_id == envelope.recipe_id
    assert (
        plan.recipe_sha256
        == envelope.recipe_sha256
    )
    assert (
        plan.approval_id
        == envelope.approval_id
    )
    assert plan.approved_step_ids == [
        "step_2"
    ]
    assert plan.topological_step_ids == [
        "step_1",
        "step_2",
    ]

    assert plan.export_performed is False
    assert plan.workflow_executed is False
    assert (
        plan.recipe_execution_performed
        is False
    )
    assert plan.approval_modified is False
    assert plan.recipe_modified is False


def test_denied_approval_cannot_be_exported(
    tmp_path: Path,
) -> None:
    (
        recipe,
        approval,
        registry,
        recipe_path,
        approval_path,
    ) = approved_recipe(tmp_path)

    denied = approval.model_copy(
        update={
            "decision": "denied"
        }
    )

    with pytest.raises(
        SnakemakeExportPolicyError,
        match="failed export policy",
    ):
        plan_snakemake_recipe_export(
            recipe=recipe,
            approval=denied,
            registry=registry,
            recipe_path=recipe_path,
            approval_path=approval_path,
        )


def test_export_plan_uses_only_basenames(
    tmp_path: Path,
) -> None:
    (
        recipe,
        approval,
        registry,
        recipe_path,
        approval_path,
    ) = approved_recipe(tmp_path)

    plan = plan_snakemake_recipe_export(
        recipe=recipe,
        approval=approval,
        registry=registry,
        recipe_path=recipe_path,
        approval_path=approval_path,
    )

    assert plan.recipe_filename == (
        "snakemake-test.json"
    )
    assert "/" not in plan.recipe_filename
    assert "/" not in plan.approval_filename

