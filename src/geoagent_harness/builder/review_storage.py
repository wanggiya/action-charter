"""Immutable storage for Builder human-review packages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.schemas import (
    BuilderReviewPackage,
    BuilderReviewStorageResult,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)


REVIEW_FILE_NAME = "REVIEW.json"
MAX_REVIEW_FILE_BYTES = 2_000_000


class BuilderReviewStorageError(RuntimeError):
    """Raised when a review package cannot be stored safely."""


def canonical_builder_review_json(
    review: BuilderReviewPackage,
) -> str:
    """Return deterministic human-readable review JSON."""

    return (
        json.dumps(
            review.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_review_sha256(
    review: BuilderReviewPackage,
) -> str:
    """Hash the exact persisted review-package content."""

    return hashlib.sha256(
        canonical_builder_review_json(
            review
        ).encode("utf-8")
    ).hexdigest()


def _review_root_path(review_root: Path) -> Path:
    if review_root.is_symlink():
        raise BuilderReviewStorageError(
            "Builder review root cannot be a symlink"
        )

    try:
        review_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = review_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderReviewStorageError(
            "Builder review root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderReviewStorageError(
            "Builder review root must be a directory"
        )

    return root


def persist_builder_review_package(
    review: BuilderReviewPackage,
    *,
    review_root: Path,
) -> BuilderReviewStorageResult:
    """Atomically persist one digest-addressed review package."""

    root = _review_root_path(review_root)
    review_content = canonical_builder_review_json(
        review
    )
    review_digest = hashlib.sha256(
        review_content.encode("utf-8")
    ).hexdigest()

    review_directory = (
        root
        / (
            f"{review.task_id}."
            f"{review_digest}.review"
        )
    )

    if (
        review_directory.exists()
        or review_directory.is_symlink()
    ):
        raise BuilderReviewStorageError(
            "Builder review package already exists"
        )

    candidate = Path(review.candidate_path)

    try:
        candidate_digest_before = (
            candidate_tree_sha256(candidate)
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuilderReviewStorageError(
            "Builder review candidate could not be hashed"
        ) from exc

    if (
        candidate_digest_before
        != review.candidate_tree_sha256
    ):
        raise BuilderReviewStorageError(
            "Builder review candidate changed before "
            "persistence"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-review-",
            dir=root,
        )
    )
    staged = temporary_root / "review"
    staged_file = staged / REVIEW_FILE_NAME

    try:
        staged.mkdir()

        with staged_file.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(review_content)

        if (
            hashlib.sha256(
                staged_file.read_bytes()
            ).hexdigest()
            != review_digest
        ):
            raise BuilderReviewStorageError(
                "Builder review file digest is inconsistent"
            )

        candidate_digest_after = (
            candidate_tree_sha256(candidate)
        )

        if (
            candidate_digest_after
            != candidate_digest_before
        ):
            raise BuilderReviewStorageError(
                "Builder review candidate changed during "
                "persistence"
            )

        os.replace(
            staged,
            review_directory,
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
            BuilderReviewStorageError,
        ):
            raise

        raise BuilderReviewStorageError(
            "Builder review package could not be persisted"
        ) from exc

    final_file = (
        review_directory / REVIEW_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderReviewStorageError(
            "Persisted Builder review could not be verified"
        ) from exc

    if final_digest != review_digest:
        raise BuilderReviewStorageError(
            "Persisted Builder review digest changed"
        )

    return BuilderReviewStorageResult(
        task_id=review.task_id,
        generation_sha256=(
            review.generation_sha256
        ),
        candidate_tree_sha256=(
            review.candidate_tree_sha256
        ),
        review_package_sha256=review_digest,
        review_directory=(
            review_directory.as_posix()
        ),
        review_file=final_file.as_posix(),
    )

def load_builder_review_package(
    review_file: Path,
    *,
    review_root: Path,
) -> tuple[BuilderReviewPackage, str, Path]:
    """Load and verify one immutable review package."""

    if review_root.is_symlink():
        raise BuilderReviewStorageError(
            "Builder review root cannot be a symlink"
        )

    try:
        root = review_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderReviewStorageError(
            "Builder review root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderReviewStorageError(
            "Builder review root must be a directory"
        )

    unresolved = (
        review_file
        if review_file.is_absolute()
        else root / review_file
    )

    if unresolved.is_symlink():
        raise BuilderReviewStorageError(
            "Builder review file cannot be a symlink"
        )

    try:
        safe_file = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderReviewStorageError(
            "Builder review file is unavailable"
        ) from exc

    review_directory = safe_file.parent

    if (
        review_directory.parent != root
        or review_directory.is_symlink()
    ):
        raise BuilderReviewStorageError(
            "Builder review package must be directly "
            "beneath its approved root"
        )

    if (
        safe_file.name != REVIEW_FILE_NAME
        or not safe_file.is_file()
    ):
        raise BuilderReviewStorageError(
            "Builder review package must contain REVIEW.json"
        )

    try:
        size = safe_file.stat().st_size
        content = safe_file.read_bytes()
    except OSError as exc:
        raise BuilderReviewStorageError(
            "Builder review file could not be read"
        ) from exc

    if size < 1:
        raise BuilderReviewStorageError(
            "Builder review file is empty"
        )

    if size > MAX_REVIEW_FILE_BYTES:
        raise BuilderReviewStorageError(
            "Builder review file exceeds the size limit"
        )

    digest = hashlib.sha256(content).hexdigest()

    try:
        payload: Any = json.loads(
            content.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise BuilderReviewStorageError(
            "Builder review file is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderReviewStorageError(
            "Builder review file must contain an object"
        )

    try:
        review = BuilderReviewPackage.model_validate(
            payload
        )
    except ValidationError as exc:
        raise BuilderReviewStorageError(
            "Builder review file failed schema validation"
        ) from exc

    expected_directory_name = (
        f"{review.task_id}.{digest}.review"
    )

    if (
        review_directory.name
        != expected_directory_name
    ):
        raise BuilderReviewStorageError(
            "Builder review directory digest is invalid"
        )

    if (
        canonical_builder_review_json(review)
        .encode("utf-8")
        != content
    ):
        raise BuilderReviewStorageError(
            "Builder review file is not canonical"
        )

    return review, digest, safe_file
