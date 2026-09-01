"""Immutable storage for Builder promotion verification."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.builder.promotion_verification import (
    BuilderPromotionVerificationError,
    verify_builder_promotion_bundle,
)
from geoagent_harness.builder.schemas import (
    BuilderPromotionVerificationResult,
    BuilderPromotionVerificationStorageResult,
)


VERIFICATION_FILE_NAME = "VERIFICATION.json"
MAX_VERIFICATION_FILE_BYTES = 250_000


class BuilderPromotionVerificationStorageError(
    RuntimeError
):
    """Raised when verification evidence is unsafe."""


def canonical_builder_promotion_verification_json(
    verification: BuilderPromotionVerificationResult,
) -> str:
    """Return deterministic persisted verification JSON."""

    return (
        json.dumps(
            verification.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_promotion_verification_sha256(
    verification: BuilderPromotionVerificationResult,
) -> str:
    """Hash the exact canonical verification evidence."""

    return hashlib.sha256(
        canonical_builder_promotion_verification_json(
            verification
        ).encode("utf-8")
    ).hexdigest()


def _verification_root_path(
    verification_root: Path,
) -> Path:
    if verification_root.is_symlink():
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification root "
            "cannot be a symlink"
        )

    try:
        verification_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = verification_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification root "
            "must be a directory"
        )

    return root


def persist_builder_promotion_verification(
    verification: BuilderPromotionVerificationResult,
    *,
    verification_root: Path,
    promotion_root: Path,
    plan_root: Path,
) -> BuilderPromotionVerificationStorageResult:
    """Persist one freshly reverified result atomically."""

    try:
        current = verify_builder_promotion_bundle(
            promotion_directory=Path(
                verification.promotion_directory
            ),
            promotion_root=promotion_root,
            plan_file=Path(
                verification.plan_file
            ),
            plan_root=plan_root,
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification could "
            "not be reverified"
        ) from exc

    if current != verification:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification changed "
            "before persistence"
        )

    root = _verification_root_path(
        verification_root
    )
    content = (
        canonical_builder_promotion_verification_json(
            verification
        )
    )
    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    verification_directory = (
        root
        / (
            f"{verification.task_id}."
            f"{digest}.verification"
        )
    )

    if (
        verification_directory.exists()
        or verification_directory.is_symlink()
    ):
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification "
            "already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-verification-",
            dir=root,
        )
    )
    staged = temporary_root / "verification"
    staged_file = (
        staged / VERIFICATION_FILE_NAME
    )

    try:
        staged.mkdir()

        with staged_file.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)

        staged_digest = hashlib.sha256(
            staged_file.read_bytes()
        ).hexdigest()

        if staged_digest != digest:
            raise BuilderPromotionVerificationStorageError(
                "Builder promotion-verification "
                "file digest is inconsistent"
            )

        current_after = (
            verify_builder_promotion_bundle(
                promotion_directory=Path(
                    verification.promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=Path(
                    verification.plan_file
                ),
                plan_root=plan_root,
            )
        )

        if current_after != verification:
            raise BuilderPromotionVerificationStorageError(
                "Builder promotion bundle changed "
                "during verification persistence"
            )

        os.replace(
            staged,
            verification_directory,
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
            BuilderPromotionVerificationStorageError,
        ):
            raise

        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification could "
            "not be persisted"
        ) from exc

    final_file = (
        verification_directory
        / VERIFICATION_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Persisted Builder promotion verification "
            "could not be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderPromotionVerificationStorageError(
            "Persisted Builder promotion-verification "
            "digest changed"
        )

    return BuilderPromotionVerificationStorageResult(
        task_id=verification.task_id,
        decision_id=verification.decision_id,
        promotion_plan_sha256=(
            verification.promotion_plan_sha256
        ),
        candidate_tree_sha256=(
            verification.candidate_tree_sha256
        ),
        verification_sha256=digest,
        verification_directory=(
            verification_directory.as_posix()
        ),
        verification_file=final_file.as_posix(),
    )


def load_builder_promotion_verification(
    verification_file: Path,
    *,
    verification_root: Path,
) -> BuilderPromotionVerificationResult:
    """Load canonical verification evidence beneath its root."""

    if verification_root.is_symlink():
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification root "
            "cannot be a symlink"
        )

    try:
        root = verification_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification root "
            "is unavailable"
        ) from exc

    candidate = (
        verification_file
        if verification_file.is_absolute()
        else root / verification_file
    )

    if candidate.is_symlink():
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "cannot be a symlink"
        )

    try:
        safe_file = candidate.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "is unavailable"
        ) from exc

    if not safe_file.is_file():
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification path "
            "must be a regular file"
        )

    if root not in safe_file.parents:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "escaped its root"
        )

    if safe_file.name != VERIFICATION_FILE_NAME:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification filename "
            "must be VERIFICATION.json"
        )

    try:
        size = safe_file.stat().st_size
    except OSError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification metadata "
            "is unavailable"
        ) from exc

    if size < 1:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file is empty"
        )

    if size > MAX_VERIFICATION_FILE_BYTES:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "exceeds the size limit"
        )

    try:
        raw = safe_file.read_text(
            encoding="utf-8"
        )
        payload = json.loads(raw)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification must "
            "contain one JSON object"
        )

    try:
        verification = (
            BuilderPromotionVerificationResult
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion verification failed "
            "schema validation"
        ) from exc

    if (
        canonical_builder_promotion_verification_json(
            verification
        )
        != raw
    ):
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification file "
            "is not canonical"
        )

    expected_directory = (
        f"{verification.task_id}."
        f"{builder_promotion_verification_sha256(verification)}"
        ".verification"
    )

    if safe_file.parent.name != expected_directory:
        raise BuilderPromotionVerificationStorageError(
            "Builder promotion-verification directory "
            "identity is invalid"
        )

    return verification
