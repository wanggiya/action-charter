"""Tests for immutable Builder promotion-plan loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderPromotionPlan,
    BuilderPromotionPlanStorageError,
    builder_promotion_plan_sha256,
    canonical_builder_promotion_plan_json,
    load_builder_promotion_plan,
)


DIGEST = "a" * 64


def promotion_plan(
    *,
    task_id: str = "builder-plan-storage-test",
) -> BuilderPromotionPlan:
    """Create one valid non-writing promotion plan."""

    return BuilderPromotionPlan(
        task_id=task_id,
        decision_id="builder-decision-test",
        reviewer_id="reviewer-test",
        review_package_sha256=DIGEST,
        decision_sha256=DIGEST,
        generation_sha256=DIGEST,
        candidate_tree_sha256=DIGEST,
        candidate_path=(
            "/workspace/builder-candidates/"
            "builder-plan-storage-test.candidate"
        ),
        project_root="/workspace/project",
        review_file=(
            "/workspace/builder-reviews/"
            "builder-plan-storage-test.review/"
            "REVIEW.json"
        ),
        decision_file=(
            "/workspace/builder-decisions/"
            "builder-decision-test.decision/"
            "DECISION.json"
        ),
        files=[
            {
                "kind": "adapter",
                "source_path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "destination_path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "sha256": DIGEST,
                "destination_exists": False,
            }
        ],
    )


def write_plan(
    root: Path,
    plan: BuilderPromotionPlan,
) -> Path:
    """Write one correctly addressed canonical plan."""

    digest = builder_promotion_plan_sha256(
        plan
    )
    directory = (
        root
        / (
            f"{plan.task_id}."
            f"{digest}.promotion-plan"
        )
    )
    directory.mkdir()

    path = directory / "PLAN.json"
    path.write_text(
        canonical_builder_promotion_plan_json(
            plan
        ),
        encoding="utf-8",
    )

    return path


def test_loads_canonical_digest_addressed_plan(
    tmp_path: Path,
) -> None:
    plan = promotion_plan()
    path = write_plan(tmp_path, plan)

    loaded = load_builder_promotion_plan(
        path,
        plan_root=tmp_path,
    )

    assert loaded == plan
    assert loaded.files_copied is False
    assert loaded.registry_modified is False
    assert loaded.implementation_trusted is False
    assert loaded.promotion_performed is False
    assert loaded.execution_performed is False


def test_noncanonical_plan_is_rejected(
    tmp_path: Path,
) -> None:
    plan = promotion_plan()
    digest = builder_promotion_plan_sha256(
        plan
    )
    directory = (
        tmp_path
        / (
            f"{plan.task_id}."
            f"{digest}.promotion-plan"
        )
    )
    directory.mkdir()

    path = directory / "PLAN.json"
    path.write_text(
        json.dumps(
            plan.model_dump(mode="json")
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="not canonical",
    ):
        load_builder_promotion_plan(
            path,
            plan_root=tmp_path,
        )


def test_wrong_digest_directory_is_rejected(
    tmp_path: Path,
) -> None:
    plan = promotion_plan()
    directory = (
        tmp_path
        / (
            f"{plan.task_id}."
            f"{'b' * 64}.promotion-plan"
        )
    )
    directory.mkdir()

    path = directory / "PLAN.json"
    path.write_text(
        canonical_builder_promotion_plan_json(
            plan
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="does not match its content digest",
    ):
        load_builder_promotion_plan(
            path,
            plan_root=tmp_path,
        )


def test_plan_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "plans"
    root.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()
    path = outside / "PLAN.json"
    path.write_text(
        canonical_builder_promotion_plan_json(
            promotion_plan()
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="escaped",
    ):
        load_builder_promotion_plan(
            path,
            plan_root=root,
        )


def test_symlinked_plan_directory_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "plans"
    root.mkdir()

    plan = promotion_plan()
    real_directory = tmp_path / "real-plan"
    real_directory.mkdir()

    real_file = real_directory / "PLAN.json"
    real_file.write_text(
        canonical_builder_promotion_plan_json(
            plan
        ),
        encoding="utf-8",
    )

    linked_directory = (
        root
        / (
            f"{plan.task_id}."
            f"{builder_promotion_plan_sha256(plan)}"
            ".promotion-plan"
        )
    )
    linked_directory.symlink_to(
        real_directory,
        target_is_directory=True,
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="directory cannot be a symlink",
    ):
        load_builder_promotion_plan(
            linked_directory / "PLAN.json",
            plan_root=root,
        )


def test_wrong_plan_filename_is_rejected(
    tmp_path: Path,
) -> None:
    plan = promotion_plan()
    digest = builder_promotion_plan_sha256(
        plan
    )
    directory = (
        tmp_path
        / (
            f"{plan.task_id}."
            f"{digest}.promotion-plan"
        )
    )
    directory.mkdir()

    path = directory / "OTHER.json"
    path.write_text(
        canonical_builder_promotion_plan_json(
            plan
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="filename must be PLAN.json",
    ):
        load_builder_promotion_plan(
            path,
            plan_root=tmp_path,
        )
