"""Tests for digest-bound Builder candidate-test assessment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateTestRecord,
    BuilderCandidateTestingError,
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    assess_builder_candidate_tests,
    inspect_builder_candidate,
    materialize_builder_proposal,
)


def prepared_candidate(
    tmp_path: Path,
) -> tuple[Path, Path]:
    request = BuilderRequest(
        task_id="builder-testing",
        summary="Propose one adapter and test.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose adapter.",
            },
            {
                "kind": "test",
                "path": "tests/test_example.py",
                "purpose": "Propose test.",
            },
        ],
    )
    proposal = BuilderProposal(
        task_id=request.task_id,
        summary="Proposed candidate.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": '"""Candidate adapter."""\n',
            },
            {
                "kind": "test",
                "path": "tests/test_example.py",
                "content": (
                    "def test_example() -> None:\n"
                    "    assert True\n"
                ),
            },
        ],
    )
    generation = BuilderGenerationResult(
        model="builder-test-model",
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

    return (
        candidate_root,
        Path(materialized.candidate_path),
    )


def write_test_record(
    *,
    evidence_root: Path,
    candidate_root: Path,
    candidate: Path,
    digest: str | None = None,
    passed: bool = True,
) -> Path:
    inspection = inspect_builder_candidate(
        candidate_path=candidate,
        candidate_root=candidate_root,
    )
    bound_digest = (
        inspection.candidate_tree_sha256
        if digest is None
        else digest
    )

    record = BuilderCandidateTestRecord(
        task_id=inspection.task_id,
        generation_sha256=(
            inspection.generation_sha256
        ),
        candidate_tree_sha256=bound_digest,
        candidate_tree_sha256_after=bound_digest,
        candidate_unchanged=True,
        pytest_exit_code=0 if passed else 1,
        collected=1,
        passed_count=1 if passed else 0,
        failed_count=0 if passed else 1,
        skipped_count=0,
        error_count=0,
        passed=passed,
    )

    evidence_root.mkdir()
    path = evidence_root / "record.json"
    path.write_text(
        json.dumps(
            record.model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_accepts_digest_bound_successful_tests(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )
    evidence_root = tmp_path / "evidence"
    record_path = write_test_record(
        evidence_root=evidence_root,
        candidate_root=candidate_root,
        candidate=candidate,
    )

    result = assess_builder_candidate_tests(
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record_path=record_path,
        evidence_root=evidence_root,
    )

    assert result.static_inspection_passed is True
    assert result.isolated_tests_passed is True
    assert result.digest_bound is True
    assert result.tests_performed is True
    assert result.implementation_executed is True
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_rejects_test_record_for_other_digest(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )
    evidence_root = tmp_path / "evidence"
    record_path = write_test_record(
        evidence_root=evidence_root,
        candidate_root=candidate_root,
        candidate=candidate,
        digest="c" * 64,
    )

    with pytest.raises(
        BuilderCandidateTestingError,
        match="does not match the inspected",
    ):
        assess_builder_candidate_tests(
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record_path=record_path,
            evidence_root=evidence_root,
        )


def test_rejects_failed_tests(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )
    evidence_root = tmp_path / "evidence"
    record_path = write_test_record(
        evidence_root=evidence_root,
        candidate_root=candidate_root,
        candidate=candidate,
        passed=False,
    )

    with pytest.raises(
        BuilderCandidateTestingError,
        match="tests did not pass",
    ):
        assess_builder_candidate_tests(
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record_path=record_path,
            evidence_root=evidence_root,
        )
