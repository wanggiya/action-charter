"""Tests for digest-bound Builder review decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderReviewDecisionError,
    create_builder_review_decision,
)
from geoagent_harness.builder import (
    persist_builder_review_package,
)
from geoagent_harness.builder import (
    BuilderCandidateInspectionResult,
    BuilderCandidateManifest,
    BuilderCandidateTestAssessment,
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    BuilderReviewPackage,
    # BuilderReviewStorageError,
    builder_review_sha256,
    persist_builder_review_package,
    BuilderReviewDecisionStorageError,
    builder_review_decision_sha256,
    persist_builder_review_decision,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)

def review_package(
    tmp_path: Path,
) -> BuilderReviewPackage:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    candidate_file = candidate / "example.py"
    candidate_file.write_text(
        '"""Candidate."""\n',
        encoding="utf-8",
    )
    digest = candidate_tree_sha256(candidate)

    request = BuilderRequest(
        task_id="builder-review-storage",
        summary="Propose one adapter.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose adapter.",
            },
        ],
    )
    proposal = BuilderProposal(
        task_id=request.task_id,
        summary="Proposed adapter.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": '"""Candidate."""\n',
            },
        ],
    )
    generation = BuilderGenerationResult(
        model="builder-review-model",
        request=request,
        proposal=proposal,
    )
    generation_digest = "b" * 64

    manifest = BuilderCandidateManifest(
        task_id=request.task_id,
        model=generation.model,
        generation_sha256=generation_digest,
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content_sha256": (
                    "c" * 64
                ),
            },
        ],
    )
    inspection = BuilderCandidateInspectionResult(
        task_id=request.task_id,
        model=generation.model,
        generation_sha256=generation_digest,
        candidate_tree_sha256=digest,
        candidate_tree_sha256_after=digest,
        candidate_path=candidate.as_posix(),
        checked_files=["example.py"],
        checks=["test_fixture"],
    )
    assessment = BuilderCandidateTestAssessment(
        task_id=request.task_id,
        generation_sha256=generation_digest,
        candidate_tree_sha256=digest,
        candidate_path=candidate.as_posix(),
        test_record_path=(
            tmp_path / "record.json"
        ).as_posix(),
        collected=1,
        passed_count=1,
        failed_count=0,
        skipped_count=0,
        error_count=0,
    )

    return BuilderReviewPackage(
        task_id=request.task_id,
        model=generation.model,
        generation_sha256=generation_digest,
        candidate_tree_sha256=digest,
        generation=generation,
        candidate_manifest=manifest,
        inspection=inspection,
        test_assessment=assessment,
        candidate_path=candidate.as_posix(),
        test_record_path=assessment.test_record_path,
        proposed_destinations=[
            (
                "src/geoagent_harness/"
                "skill_adapters/example.py"
            ),
        ],
    )



def persisted_review(
    tmp_path: Path,
) -> tuple[Path, Path]:
    review = review_package(tmp_path)
    review_root = tmp_path / "reviews"

    result = persist_builder_review_package(
        review,
        review_root=review_root,
    )

    return review_root, Path(result.review_file)


def test_approves_reviewed_subset(
    tmp_path: Path,
) -> None:
    review_root, review_file = persisted_review(
        tmp_path
    )

    result = create_builder_review_decision(
        review_file=review_file,
        review_root=review_root,
        decision_id="review-decision-001",
        reviewer_id="operator@example.com",
        decided_at=datetime.now(timezone.utc),
        decision="approved",
        approved_paths=[
            (
                "src/geoagent_harness/"
                "skill_adapters/example.py"
            ),
        ],
        rationale="Reviewed exact candidate and evidence.",
    )

    assert result.decision == "approved"
    assert result.approval_granted is True
    assert (
        result.promotion_planning_authorized
        is True
    )
    assert result.human_review_performed is True
    assert result.files_copied is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False


def test_records_rejection_without_paths(
    tmp_path: Path,
) -> None:
    review_root, review_file = persisted_review(
        tmp_path
    )

    result = create_builder_review_decision(
        review_file=review_file,
        review_root=review_root,
        decision_id="review-decision-002",
        reviewer_id="operator@example.com",
        decided_at=datetime.now(timezone.utc),
        decision="rejected",
        approved_paths=[],
        rationale="Candidate requires revision.",
    )

    assert result.decision == "rejected"
    assert result.approved_paths == []
    assert result.approval_granted is False
    assert (
        result.promotion_planning_authorized
        is False
    )


def test_rejects_unreviewed_path(
    tmp_path: Path,
) -> None:
    review_root, review_file = persisted_review(
        tmp_path
    )

    with pytest.raises(
        BuilderReviewDecisionError,
        match="were not reviewed",
    ):
        create_builder_review_decision(
            review_file=review_file,
            review_root=review_root,
            decision_id="review-decision-003",
            reviewer_id="operator@example.com",
            decided_at=datetime.now(timezone.utc),
            decision="approved",
            approved_paths=["src/unreviewed.py"],
            rationale="Invalid selection.",
        )


def test_rejects_naive_timestamp(
    tmp_path: Path,
) -> None:
    review_root, review_file = persisted_review(
        tmp_path
    )

    with pytest.raises(
        BuilderReviewDecisionError,
        match="failed validation",
    ):
        create_builder_review_decision(
            review_file=review_file,
            review_root=review_root,
            decision_id="review-decision-004",
            reviewer_id="operator@example.com",
            decided_at=datetime.now(),
            decision="approved",
            approved_paths=[
                (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
            ],
            rationale="Timestamp lacks timezone.",
        )

def approved_decision(
    tmp_path: Path,
):
    review_root, review_file = persisted_review(
        tmp_path
    )

    decision = create_builder_review_decision(
        review_file=review_file,
        review_root=review_root,
        decision_id="review-decision-storage",
        reviewer_id="operator@example.com",
        decided_at=datetime.now(timezone.utc),
        decision="approved",
        approved_paths=[
            (
                "src/geoagent_harness/"
                "skill_adapters/example.py"
            ),
        ],
        rationale="Approved exact reviewed adapter.",
    )

    return review_root, decision


def test_persists_digest_addressed_decision(
    tmp_path: Path,
) -> None:
    review_root, decision = approved_decision(
        tmp_path
    )

    result = persist_builder_review_decision(
        decision,
        decision_root=tmp_path / "decisions",
        review_root=review_root,
    )

    decision_file = Path(result.decision_file)

    assert decision_file.is_file()
    assert decision_file.name == "DECISION.json"
    assert (
        result.decision_sha256
        == builder_review_decision_sha256(
            decision
        )
    )
    assert (
        result.decision_sha256
        in Path(result.decision_directory).name
    )
    assert result.approval_granted is True
    assert (
        result.promotion_planning_authorized
        is True
    )
    assert result.files_copied is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False


def test_refuses_existing_decision(
    tmp_path: Path,
) -> None:
    review_root, decision = approved_decision(
        tmp_path
    )
    decision_root = tmp_path / "decisions"

    persist_builder_review_decision(
        decision,
        decision_root=decision_root,
        review_root=review_root,
    )

    with pytest.raises(
        BuilderReviewDecisionStorageError,
        match="already exists",
    ):
        persist_builder_review_decision(
            decision,
            decision_root=decision_root,
            review_root=review_root,
        )


def test_rejects_decision_with_wrong_review_digest(
    tmp_path: Path,
) -> None:
    review_root, decision = approved_decision(
        tmp_path
    )

    changed = decision.model_copy(
        update={
            "review_package_sha256": "f" * 64,
        }
    )

    with pytest.raises(
        BuilderReviewDecisionStorageError,
        match="review digest does not match",
    ):
        persist_builder_review_decision(
            changed,
            decision_root=tmp_path / "decisions",
            review_root=review_root,
        )


def test_rejects_symlinked_decision_root(
    tmp_path: Path,
) -> None:
    review_root, decision = approved_decision(
        tmp_path
    )
    real_root = tmp_path / "real-decisions"
    real_root.mkdir()
    linked_root = tmp_path / "linked-decisions"
    linked_root.symlink_to(real_root)

    with pytest.raises(
        BuilderReviewDecisionStorageError,
        match="root cannot be a symlink",
    ):
        persist_builder_review_decision(
            decision,
            decision_root=linked_root,
            review_root=review_root,
        )
