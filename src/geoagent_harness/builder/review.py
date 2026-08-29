"""Assemble exact Builder evidence for human review."""

from __future__ import annotations

import hashlib
from pathlib import Path

from geoagent_harness.builder.inspection import (
    BuilderCandidateInspectionError,
    inspect_builder_candidate,
    load_builder_candidate_manifest,
)
from geoagent_harness.builder.schemas import (
    BuilderReviewPackage,
)
from geoagent_harness.builder.storage import (
    BuilderGenerationStorageError,
    builder_generation_sha256,
    load_builder_generation,
)
from geoagent_harness.builder.testing import (
    BuilderCandidateTestingError,
    assess_builder_candidate_tests,
)


class BuilderReviewError(RuntimeError):
    """Raised when a Builder review package is inconsistent."""


def _content_sha256(content: str) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def assemble_builder_review_package(
    *,
    generation_file: Path,
    generation_root: Path,
    candidate_path: Path,
    candidate_root: Path,
    test_record_path: Path,
    evidence_root: Path,
) -> BuilderReviewPackage:
    """Assemble verified evidence without approving or writing."""

    try:
        generation = load_builder_generation(
            generation_file,
            generation_root=generation_root,
        )
        generation_digest = (
            builder_generation_sha256(generation)
        )
        inspection = inspect_builder_candidate(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
        )
        test_assessment = (
            assess_builder_candidate_tests(
                candidate_path=candidate_path,
                candidate_root=candidate_root,
                test_record_path=test_record_path,
                evidence_root=evidence_root,
            )
        )
        manifest = load_builder_candidate_manifest(
            Path(inspection.candidate_path)
        )
    except (
        BuilderCandidateInspectionError,
        BuilderCandidateTestingError,
        BuilderGenerationStorageError,
        OSError,
        ValueError,
    ) as exc:
        raise BuilderReviewError(
            "Builder review inputs could not be verified"
        ) from exc

    if (
        generation.request.task_id
        != inspection.task_id
    ):
        raise BuilderReviewError(
            "Builder generation task does not match candidate"
        )

    if generation.model != inspection.model:
        raise BuilderReviewError(
            "Builder generation model does not match candidate"
        )

    if (
        generation_digest
        != inspection.generation_sha256
    ):
        raise BuilderReviewError(
            "Builder generation digest does not "
            "match candidate"
        )

    proposed = {
        file.path: (
            file.kind,
            _content_sha256(file.content),
        )
        for file in generation.proposal.files
    }
    manifested = {
        file.path: (
            file.kind,
            file.content_sha256,
        )
        for file in manifest.files
    }

    if proposed != manifested:
        raise BuilderReviewError(
            "Builder proposal files do not match "
            "candidate manifest"
        )

    destinations = sorted(proposed)

    return BuilderReviewPackage(
        task_id=generation.request.task_id,
        model=generation.model,
        generation_sha256=generation_digest,
        candidate_tree_sha256=(
            inspection.candidate_tree_sha256
        ),
        generation=generation,
        candidate_manifest=manifest,
        inspection=inspection,
        test_assessment=test_assessment,
        candidate_path=inspection.candidate_path,
        test_record_path=(
            test_assessment.test_record_path
        ),
        proposed_destinations=destinations,
        warnings=sorted(
            {
                *generation.proposal.warnings,
                (
                    "Candidate paths are proposals only; "
                    "no trusted destination has been "
                    "approved."
                ),
                (
                    "Passing isolated tests does not grant "
                    "implementation trust."
                ),
            }
        ),
    )
