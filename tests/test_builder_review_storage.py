"""Tests for immutable Builder review-package storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateInspectionResult,
    BuilderCandidateManifest,
    BuilderCandidateTestAssessment,
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    BuilderReviewPackage,
    BuilderReviewStorageError,
    builder_review_sha256,
    persist_builder_review_package,
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


def test_persists_digest_addressed_review(
    tmp_path: Path,
) -> None:
    review = review_package(tmp_path)

    result = persist_builder_review_package(
        review,
        review_root=tmp_path / "reviews",
    )

    review_file = Path(result.review_file)

    assert review_file.is_file()
    assert review_file.name == "REVIEW.json"
    assert (
        result.review_package_sha256
        == builder_review_sha256(review)
    )
    assert (
        result.review_package_sha256
        in Path(result.review_directory).name
    )
    assert result.ready_for_human_review is True
    assert result.human_review_performed is False
    assert result.approval_granted is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False


def test_refuses_existing_review_package(
    tmp_path: Path,
) -> None:
    review = review_package(tmp_path)
    root = tmp_path / "reviews"

    persist_builder_review_package(
        review,
        review_root=root,
    )

    with pytest.raises(
        BuilderReviewStorageError,
        match="already exists",
    ):
        persist_builder_review_package(
            review,
            review_root=root,
        )


def test_rejects_changed_candidate(
    tmp_path: Path,
) -> None:
    review = review_package(tmp_path)

    (
        Path(review.candidate_path) / "example.py"
    ).write_text(
        '"""Changed candidate."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderReviewStorageError,
        match="changed before persistence",
    ):
        persist_builder_review_package(
            review,
            review_root=tmp_path / "reviews",
        )


def test_rejects_symlinked_review_root(
    tmp_path: Path,
) -> None:
    real_root = tmp_path / "real-reviews"
    real_root.mkdir()
    linked_root = tmp_path / "linked-reviews"
    linked_root.symlink_to(real_root)

    with pytest.raises(
        BuilderReviewStorageError,
        match="root cannot be a symlink",
    ):
        persist_builder_review_package(
            review_package(tmp_path),
            review_root=linked_root,
        )
