"""Trusted assessment of isolated Builder candidate tests."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.builder.inspection import (
    BuilderCandidateInspectionError,
    inspect_builder_candidate,
)
from geoagent_harness.builder.schemas import (
    BuilderCandidateTestAssessment,
)
from geoagent_harness.builder.test_evidence import (
    BuilderCandidateTestEvidenceError,
    load_builder_candidate_test_record,
)


class BuilderCandidateTestingError(RuntimeError):
    """Raised when Builder test evidence is not acceptable."""


def assess_builder_candidate_tests(
    *,
    candidate_path: Path,
    candidate_root: Path,
    test_record_path: Path,
    evidence_root: Path,
) -> BuilderCandidateTestAssessment:
    """Bind successful isolated tests to an exact candidate."""

    try:
        inspection = inspect_builder_candidate(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
        )
        record = load_builder_candidate_test_record(
            test_record_path,
            evidence_root=evidence_root,
        )
    except (
        BuilderCandidateInspectionError,
        BuilderCandidateTestEvidenceError,
    ) as exc:
        raise BuilderCandidateTestingError(
            "Builder candidate test evidence "
            "could not be assessed"
        ) from exc

    if record.task_id != inspection.task_id:
        raise BuilderCandidateTestingError(
            "Builder test task ID does not match candidate"
        )

    if (
        record.generation_sha256
        != inspection.generation_sha256
    ):
        raise BuilderCandidateTestingError(
            "Builder test generation digest does not "
            "match candidate"
        )

    if (
        record.candidate_tree_sha256
        != inspection.candidate_tree_sha256
        or record.candidate_tree_sha256_after
        != inspection.candidate_tree_sha256
    ):
        raise BuilderCandidateTestingError(
            "Builder test evidence does not match the "
            "inspected candidate digest"
        )

    if not record.candidate_unchanged:
        raise BuilderCandidateTestingError(
            "Builder candidate changed during tests"
        )

    if not record.passed:
        raise BuilderCandidateTestingError(
            "Builder candidate tests did not pass"
        )

    if record.network_available:
        raise BuilderCandidateTestingError(
            "Builder candidate tests reported network access"
        )

    if not record.candidate_mount_read_only:
        raise BuilderCandidateTestingError(
            "Builder candidate was not mounted read-only"
        )

    return BuilderCandidateTestAssessment(
        task_id=inspection.task_id,
        generation_sha256=(
            inspection.generation_sha256
        ),
        candidate_tree_sha256=(
            inspection.candidate_tree_sha256
        ),
        candidate_path=inspection.candidate_path,
        test_record_path=str(
            (
                test_record_path
                if test_record_path.is_absolute()
                else evidence_root / test_record_path
            ).resolve()
        ),
        collected=record.collected,
        passed_count=record.passed_count,
        failed_count=record.failed_count,
        skipped_count=record.skipped_count,
        error_count=record.error_count,
    )

