"""Tests for digest-bound Builder human-review packages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateTestRecord,
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    BuilderReviewError,
    assemble_builder_review_package,
    inspect_builder_candidate,
    materialize_builder_proposal,
)


def generation(
    *,
    task_id: str = "builder-review-test",
) -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id=task_id,
        summary="Propose one adapter and test.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/review_example.py"
                ),
                "purpose": "Propose adapter.",
            },
            {
                "kind": "test",
                "path": "tests/test_review_example.py",
                "purpose": "Propose test.",
            },
        ],
    )
    proposal = BuilderProposal(
        task_id=task_id,
        summary="Proposed review candidate.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/review_example.py"
                ),
                "content": (
                    '"""Untrusted review candidate."""\n'
                ),
            },
            {
                "kind": "test",
                "path": "tests/test_review_example.py",
                "content": (
                    "def test_review_example() -> None:\n"
                    "    assert True\n"
                ),
            },
        ],
    )

    return BuilderGenerationResult(
        model="builder-review-model",
        request=request,
        proposal=proposal,
    )


def prepare_review_inputs(
    tmp_path: Path,
) -> dict[str, Path]:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = (
        generation_root / "generation.json"
    )
    generation_file.write_text(
        json.dumps(
            generation().model_dump(mode="json"),
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
    test_record_path = (
        evidence_root / "record.json"
    )
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
    test_record_path.write_text(
        json.dumps(
            record.model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "generation_root": generation_root,
        "generation_file": generation_file,
        "candidate_root": candidate_root,
        "candidate": candidate,
        "evidence_root": evidence_root,
        "test_record": test_record_path,
    }


def test_assembles_exact_review_package(
    tmp_path: Path,
) -> None:
    paths = prepare_review_inputs(tmp_path)

    result = assemble_builder_review_package(
        generation_file=paths["generation_file"],
        generation_root=paths["generation_root"],
        candidate_path=paths["candidate"],
        candidate_root=paths["candidate_root"],
        test_record_path=paths["test_record"],
        evidence_root=paths["evidence_root"],
    )

    assert result.ready_for_human_review is True
    assert result.proposed_destinations == [
        (
            "src/geoagent_harness/"
            "skill_adapters/review_example.py"
        ),
        "tests/test_review_example.py",
    ]
    assert result.human_review_performed is False
    assert result.approval_granted is False
    assert result.files_copied is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_rejects_different_generation(
    tmp_path: Path,
) -> None:
    paths = prepare_review_inputs(tmp_path)

    other_file = (
        paths["generation_root"] / "other.json"
    )
    other_file.write_text(
        json.dumps(
            generation(
                task_id="different-review-task"
            ).model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderReviewError,
        match="task does not match",
    ):
        assemble_builder_review_package(
            generation_file=other_file,
            generation_root=paths["generation_root"],
            candidate_path=paths["candidate"],
            candidate_root=paths["candidate_root"],
            test_record_path=paths["test_record"],
            evidence_root=paths["evidence_root"],
        )


def test_review_package_contains_exact_evidence(
    tmp_path: Path,
) -> None:
    paths = prepare_review_inputs(tmp_path)

    result = assemble_builder_review_package(
        generation_file=paths["generation_file"],
        generation_root=paths["generation_root"],
        candidate_path=paths["candidate"],
        candidate_root=paths["candidate_root"],
        test_record_path=paths["test_record"],
        evidence_root=paths["evidence_root"],
    )

    assert (
        result.generation_sha256
        == result.candidate_manifest.generation_sha256
        == result.inspection.generation_sha256
        == result.test_assessment.generation_sha256
    )
    assert (
        result.candidate_tree_sha256
        == result.inspection.candidate_tree_sha256
        == result.test_assessment.candidate_tree_sha256
    )
