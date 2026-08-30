"""Tests for read-only Builder promotion planning."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateTestRecord,
    BuilderGenerationResult,
    BuilderPromotionPlanError,
    BuilderProposal,
    BuilderRequest,
    assemble_builder_review_package,
    create_builder_review_decision,
    inspect_builder_candidate,
    materialize_builder_proposal,
    persist_builder_review_decision,
    persist_builder_review_package,
    plan_builder_promotion,
    BuilderPromotionPlanStorageError,
    builder_promotion_plan_sha256,
    persist_builder_promotion_plan,
)


def prepared_promotion(
    tmp_path: Path,
    *,
    approved: bool = True,
) -> dict[str, Path]:
    request = BuilderRequest(
        task_id="builder-promotion-plan",
        summary="Propose an adapter and test.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/"
                    "promotion_example.py"
                ),
                "purpose": "Propose adapter.",
            },
            {
                "kind": "test",
                "path": (
                    "tests/test_promotion_example.py"
                ),
                "purpose": "Propose test.",
            },
        ],
    )
    proposal = BuilderProposal(
        task_id=request.task_id,
        summary="Proposed promotion candidate.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/"
                    "promotion_example.py"
                ),
                "content": (
                    '"""Promotion candidate."""\n'
                ),
            },
            {
                "kind": "test",
                "path": (
                    "tests/test_promotion_example.py"
                ),
                "content": (
                    "def test_promotion_example() -> None:\n"
                    "    assert True\n"
                ),
            },
        ],
    )
    generation = BuilderGenerationResult(
        model="builder-promotion-model",
        request=request,
        proposal=proposal,
    )

    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = (
        generation_root / "generation.json"
    )
    generation_file.write_text(
        json.dumps(
            generation.model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_root = tmp_path / "candidates"
    materialized = materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=candidate_root,
    )
    candidate = Path(materialized.candidate_path)

    inspection = inspect_builder_candidate(
        candidate_path=candidate,
        candidate_root=candidate_root,
    )

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    record_path = evidence_root / "record.json"
    record = BuilderCandidateTestRecord(
        task_id=inspection.task_id,
        generation_sha256=(
            inspection.generation_sha256
        ),
        candidate_tree_sha256=(
            inspection.candidate_tree_sha256
        ),
        candidate_tree_sha256_after=(
            inspection.candidate_tree_sha256
        ),
        candidate_unchanged=True,
        pytest_exit_code=0,
        collected=1,
        passed_count=1,
        failed_count=0,
        skipped_count=0,
        error_count=0,
        passed=True,
    )
    record_path.write_text(
        json.dumps(
            record.model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    review = assemble_builder_review_package(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record_path=record_path,
        evidence_root=evidence_root,
    )

    review_root = tmp_path / "reviews"
    persisted_review = (
        persist_builder_review_package(
            review,
            review_root=review_root,
        )
    )

    decision = create_builder_review_decision(
        review_file=Path(
            persisted_review.review_file
        ),
        review_root=review_root,
        decision_id="builder-promotion-decision",
        reviewer_id="operator@example.com",
        decided_at=datetime.now(timezone.utc),
        decision=(
            "approved"
            if approved
            else "rejected"
        ),
        approved_paths=(
            sorted(review.proposed_destinations)
            if approved
            else []
        ),
        rationale=(
            "Approved exact files."
            if approved
            else "Rejected candidate."
        ),
    )

    decision_root = tmp_path / "decisions"
    persisted_decision = (
        persist_builder_review_decision(
            decision,
            decision_root=decision_root,
            review_root=review_root,
        )
    )

    project_root = tmp_path / "project"
    project_root.mkdir()

    return {
        "candidate": candidate,
        "candidate_root": candidate_root,
        "review_root": review_root,
        "decision_root": decision_root,
        "decision_file": Path(
            persisted_decision.decision_file
        ),
        "project_root": project_root,
    }


def test_plans_exact_approved_files_without_writes(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    result = plan_builder_promotion(
        decision_file=paths["decision_file"],
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )

    assert [
        file.destination_path
        for file in result.files
    ] == [
        (
            "src/geoagent_harness/"
            "skill_adapters/promotion_example.py"
        ),
        "tests/test_promotion_example.py",
    ]
    assert result.human_approval_verified is True
    assert result.candidate_inspection_passed is True
    assert result.promotion_ready is True
    assert result.files_copied is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False

    assert not (
        paths["project_root"]
        / "src"
        / "geoagent_harness"
        / "skill_adapters"
        / "promotion_example.py"
    ).exists()


def test_rejects_rejected_decision(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(
        tmp_path,
        approved=False,
    )

    with pytest.raises(
        BuilderPromotionPlanError,
        match="does not authorize",
    ):
        plan_builder_promotion(
            decision_file=paths["decision_file"],
            decision_root=paths["decision_root"],
            review_root=paths["review_root"],
            candidate_root=paths["candidate_root"],
            project_root=paths["project_root"],
        )


def test_rejects_existing_destination(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    destination = (
        paths["project_root"]
        / "tests"
        / "test_promotion_example.py"
    )
    destination.parent.mkdir(parents=True)
    destination.write_text(
        "existing\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanError,
        match="destination already exists",
    ):
        plan_builder_promotion(
            decision_file=paths["decision_file"],
            decision_root=paths["decision_root"],
            review_root=paths["review_root"],
            candidate_root=paths["candidate_root"],
            project_root=paths["project_root"],
        )


def test_rejects_changed_candidate(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    (
        paths["candidate"]
        / "tests"
        / "test_promotion_example.py"
    ).write_text(
        "def changed():\n"
        "    return False\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionPlanError,
        match="inputs could not be verified",
    ):
        plan_builder_promotion(
            decision_file=paths["decision_file"],
            decision_root=paths["decision_root"],
            review_root=paths["review_root"],
            candidate_root=paths["candidate_root"],
            project_root=paths["project_root"],
        )

def test_persists_reverified_promotion_plan(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    plan = plan_builder_promotion(
        decision_file=paths["decision_file"],
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )

    result = persist_builder_promotion_plan(
        plan,
        plan_root=tmp_path / "plans",
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )

    plan_file = Path(result.plan_file)

    assert plan_file.is_file()
    assert plan_file.name == "PLAN.json"
    assert (
        result.promotion_plan_sha256
        == builder_promotion_plan_sha256(plan)
    )
    assert (
        result.promotion_plan_sha256
        in Path(result.plan_directory).name
    )
    assert result.plan_persisted is True
    assert result.files_copied is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False


def test_refuses_existing_promotion_plan(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    plan = plan_builder_promotion(
        decision_file=paths["decision_file"],
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )
    plan_root = tmp_path / "plans"

    persist_builder_promotion_plan(
        plan,
        plan_root=plan_root,
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="already exists",
    ):
        persist_builder_promotion_plan(
            plan,
            plan_root=plan_root,
            decision_root=paths["decision_root"],
            review_root=paths["review_root"],
            candidate_root=paths["candidate_root"],
            project_root=paths["project_root"],
        )


def test_rejects_changed_plan_before_persistence(
    tmp_path: Path,
) -> None:
    paths = prepared_promotion(tmp_path)

    plan = plan_builder_promotion(
        decision_file=paths["decision_file"],
        decision_root=paths["decision_root"],
        review_root=paths["review_root"],
        candidate_root=paths["candidate_root"],
        project_root=paths["project_root"],
    )

    changed = plan.model_copy(
        update={
            "reviewer_id": "different-reviewer",
        }
    )

    with pytest.raises(
        BuilderPromotionPlanStorageError,
        match="changed before persistence",
    ):
        persist_builder_promotion_plan(
            changed,
            plan_root=tmp_path / "plans",
            decision_root=paths["decision_root"],
            review_root=paths["review_root"],
            candidate_root=paths["candidate_root"],
            project_root=paths["project_root"],
        )
