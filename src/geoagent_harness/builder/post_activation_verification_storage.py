"""Immutable storage for Builder trust evidence."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.post_activation_verification import (
    BuilderPostActivationVerificationError,
    verify_builder_activation,
)
from geoagent_harness.builder.schemas import (
    BuilderPostActivationVerificationResult,
    BuilderPostActivationVerificationStorageResult,
)


TRUST_EVIDENCE_FILE_NAME = (
    "POST_ACTIVATION_VERIFICATION.json"
)
MAX_TRUST_EVIDENCE_BYTES = 500_000


class BuilderPostActivationVerificationStorageError(
    RuntimeError
):
    """Raised when Builder trust evidence is unsafe."""


def canonical_builder_trust_evidence_json(
    verification: BuilderPostActivationVerificationResult,
) -> str:
    """Return deterministic post-activation evidence."""

    return (
        json.dumps(
            verification.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_trust_evidence_sha256(
    verification: BuilderPostActivationVerificationResult,
) -> str:
    """Hash exact canonical trust evidence."""

    return hashlib.sha256(
        canonical_builder_trust_evidence_json(
            verification
        ).encode("utf-8")
    ).hexdigest()


def _evidence_root_path(
    evidence_root: Path,
) -> Path:
    if evidence_root.is_symlink():
        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust-evidence root "
                "cannot be a symlink"
            )
        )

    try:
        evidence_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = evidence_root.resolve(strict=True)
    except OSError as exc:
        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust-evidence root "
                "is unavailable"
            )
        ) from exc

    if not root.is_dir():
        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust-evidence root "
                "must be a directory"
            )
        )

    return root


def _reverify(
    verification: BuilderPostActivationVerificationResult,
    *,
    activation_root: Path,
    activation_plan_root: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderPostActivationVerificationResult:
    try:
        return verify_builder_activation(
            activation_directory=Path(
                verification.activation_directory
            ),
            activation_root=activation_root,
            activation_plan_file=Path(
                verification.activation_plan_file
            ),
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except BuilderPostActivationVerificationError as exc:
        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust evidence could "
                "not be reverified"
            )
        ) from exc


def persist_builder_trust_evidence(
    verification: BuilderPostActivationVerificationResult,
    *,
    evidence_root: Path,
    activation_root: Path,
    activation_plan_root: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderPostActivationVerificationStorageResult:
    """Persist one freshly reverified trust result."""

    current = _reverify(
        verification,
        activation_root=activation_root,
        activation_plan_root=activation_plan_root,
        activation_decision_root=(
            activation_decision_root
        ),
        verification_root=verification_root,
        promotion_root=promotion_root,
        promotion_plan_root=promotion_plan_root,
        project_root=project_root,
    )

    if current != verification:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust evidence changed "
            "before persistence"
        )

    root = _evidence_root_path(
        evidence_root
    )
    content = (
        canonical_builder_trust_evidence_json(
            verification
        )
    )
    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    evidence_directory = (
        root
        / (
            f"{verification.task_id}."
            f"{digest}.post-activation-verification"
        )
    )

    if (
        evidence_directory.exists()
        or evidence_directory.is_symlink()
    ):
        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust evidence already exists"
            )
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-trust-",
            dir=root,
        )
    )
    staged = temporary_root / "evidence"
    staged_file = (
        staged / TRUST_EVIDENCE_FILE_NAME
    )

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
            raise (
                BuilderPostActivationVerificationStorageError(
                    "Builder trust-evidence file "
                    "digest is inconsistent"
                )
            )

        current_after = _reverify(
            verification,
            activation_root=activation_root,
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )

        if current_after != verification:
            raise (
                BuilderPostActivationVerificationStorageError(
                    "Builder activated files changed "
                    "during trust-evidence persistence"
                )
            )

        os.replace(
            staged,
            evidence_directory,
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
            BuilderPostActivationVerificationStorageError,
        ):
            raise

        raise (
            BuilderPostActivationVerificationStorageError(
                "Builder trust evidence could "
                "not be persisted"
            )
        ) from exc

    final_file = (
        evidence_directory
        / TRUST_EVIDENCE_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Persisted Builder trust evidence "
            "could not be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderPostActivationVerificationStorageError(
            "Persisted Builder trust-evidence "
            "digest changed"
        )

    return BuilderPostActivationVerificationStorageResult(
        task_id=verification.task_id,
        activation_decision_id=(
            verification.activation_decision_id
        ),
        activation_plan_sha256=(
            verification.activation_plan_sha256
        ),
        candidate_tree_sha256=(
            verification.candidate_tree_sha256
        ),
        trust_evidence_sha256=digest,
        evidence_directory=(
            evidence_directory.as_posix()
        ),
        evidence_file=final_file.as_posix(),
    )


def load_builder_trust_evidence(
    evidence_file: Path,
    *,
    evidence_root: Path,
) -> tuple[
    BuilderPostActivationVerificationResult,
    str,
    Path,
]:
    """Load canonical digest-addressed trust evidence."""

    if evidence_root.is_symlink():
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence root "
            "cannot be a symlink"
        )

    try:
        root = evidence_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence root "
            "is unavailable"
        ) from exc

    unresolved = (
        evidence_file
        if evidence_file.is_absolute()
        else root / evidence_file
    )

    if (
        unresolved.is_symlink()
        or unresolved.parent.is_symlink()
    ):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust evidence cannot be a symlink"
        )

    try:
        safe_file = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file is unavailable"
        ) from exc

    evidence_directory = safe_file.parent

    if (
        evidence_directory.parent != root
        or not evidence_directory.is_dir()
    ):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust evidence escaped "
            "its approved root"
        )

    if (
        safe_file.name != TRUST_EVIDENCE_FILE_NAME
        or not safe_file.is_file()
    ):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust evidence must contain "
            "POST_ACTIVATION_VERIFICATION.json"
        )

    try:
        content = safe_file.read_bytes()
    except OSError as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file "
            "could not be read"
        ) from exc

    if len(content) < 1:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file is empty"
        )

    if len(content) > MAX_TRUST_EVIDENCE_BYTES:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file exceeds "
            "the size limit"
        )

    digest = hashlib.sha256(
        content
    ).hexdigest()

    try:
        payload: Any = json.loads(
            content.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file is not "
            "valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file must "
            "contain an object"
        )

    try:
        verification = (
            BuilderPostActivationVerificationResult
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file failed "
            "schema validation"
        ) from exc

    expected_directory_name = (
        f"{verification.task_id}."
        f"{digest}.post-activation-verification"
    )

    if (
        evidence_directory.name
        != expected_directory_name
    ):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence directory "
            "digest is invalid"
        )

    if (
        canonical_builder_trust_evidence_json(
            verification
        ).encode("utf-8")
        != content
    ):
        raise BuilderPostActivationVerificationStorageError(
            "Builder trust-evidence file "
            "is not canonical"
        )

    return verification, digest, safe_file
