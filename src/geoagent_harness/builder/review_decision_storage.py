"""Immutable storage for Builder human-review decisions."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from geoagent_harness.builder.review_storage import (
    BuilderReviewStorageError,
    load_builder_review_package,
)
from geoagent_harness.builder.schemas import (
    BuilderReviewDecision,
    BuilderReviewDecisionStorageResult,
)


DECISION_FILE_NAME = "DECISION.json"


class BuilderReviewDecisionStorageError(
    RuntimeError
):
    """Raised when a Builder decision cannot be stored."""


def canonical_builder_review_decision_json(
    decision: BuilderReviewDecision,
) -> str:
    """Return deterministic human-readable decision JSON."""

    return (
        json.dumps(
            decision.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_review_decision_sha256(
    decision: BuilderReviewDecision,
) -> str:
    """Hash the exact persisted decision content."""

    return hashlib.sha256(
        canonical_builder_review_decision_json(
            decision
        ).encode("utf-8")
    ).hexdigest()


def _decision_root_path(
    decision_root: Path,
) -> Path:
    if decision_root.is_symlink():
        raise BuilderReviewDecisionStorageError(
            "Builder decision root cannot be a symlink"
        )

    try:
        decision_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = decision_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderReviewDecisionStorageError(
            "Builder decision root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderReviewDecisionStorageError(
            "Builder decision root must be a directory"
        )

    return root


def persist_builder_review_decision(
    decision: BuilderReviewDecision,
    *,
    decision_root: Path,
    review_root: Path,
) -> BuilderReviewDecisionStorageResult:
    """Persist one decision bound to an unchanged review."""

    try:
        review, review_digest, safe_review_file = (
            load_builder_review_package(
                Path(decision.review_file),
                review_root=review_root,
            )
        )
    except BuilderReviewStorageError as exc:
        raise BuilderReviewDecisionStorageError(
            "Builder decision could not verify "
            "its review package"
        ) from exc

    if (
        review_digest
        != decision.review_package_sha256
    ):
        raise BuilderReviewDecisionStorageError(
            "Builder decision review digest does not match"
        )

    if (
        safe_review_file.as_posix()
        != decision.review_file
    ):
        raise BuilderReviewDecisionStorageError(
            "Builder decision review path does not match"
        )

    if (
        review.task_id != decision.task_id
        or review.generation_sha256
        != decision.generation_sha256
        or review.candidate_tree_sha256
        != decision.candidate_tree_sha256
    ):
        raise BuilderReviewDecisionStorageError(
            "Builder decision identities do not match review"
        )

    if (
        sorted(review.proposed_destinations)
        != sorted(decision.reviewed_paths)
    ):
        raise BuilderReviewDecisionStorageError(
            "Builder decision reviewed paths do not match"
        )

    root = _decision_root_path(
        decision_root
    )
    content = (
        canonical_builder_review_decision_json(
            decision
        )
    )
    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    decision_directory = (
        root
        / (
            f"{decision.decision_id}."
            f"{digest}.decision"
        )
    )

    if (
        decision_directory.exists()
        or decision_directory.is_symlink()
    ):
        raise BuilderReviewDecisionStorageError(
            "Builder decision already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-decision-",
            dir=root,
        )
    )
    staged = temporary_root / "decision"
    staged_file = staged / DECISION_FILE_NAME

    try:
        staged.mkdir()

        with staged_file.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)

        if (
            hashlib.sha256(
                staged_file.read_bytes()
            ).hexdigest()
            != digest
        ):
            raise BuilderReviewDecisionStorageError(
                "Builder decision file digest is inconsistent"
            )

        _, review_digest_after, _ = (
            load_builder_review_package(
                safe_review_file,
                review_root=review_root,
            )
        )

        if review_digest_after != review_digest:
            raise BuilderReviewDecisionStorageError(
                "Builder review changed during "
                "decision persistence"
            )

        os.replace(
            staged,
            decision_directory,
        )
        temporary_root.rmdir()
    except (
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )

        if isinstance(
            exc,
            BuilderReviewDecisionStorageError,
        ):
            raise

        raise BuilderReviewDecisionStorageError(
            "Builder decision could not be persisted"
        ) from exc

    final_file = (
        decision_directory / DECISION_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderReviewDecisionStorageError(
            "Persisted Builder decision could not "
            "be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderReviewDecisionStorageError(
            "Persisted Builder decision digest changed"
        )

    return BuilderReviewDecisionStorageResult(
        decision_id=decision.decision_id,
        task_id=decision.task_id,
        decision=decision.decision,
        review_package_sha256=review_digest,
        decision_sha256=digest,
        decision_directory=(
            decision_directory.as_posix()
        ),
        decision_file=final_file.as_posix(),
        approval_granted=(
            decision.approval_granted
        ),
        promotion_planning_authorized=(
            decision.promotion_planning_authorized
        ),
    )
