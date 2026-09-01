"""Immutable storage for Builder activation-review decisions."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.activation_review import (
    BuilderActivationReviewError,
    create_builder_activation_review_decision,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationReviewDecision,
    BuilderActivationReviewDecisionStorageResult,
)


ACTIVATION_DECISION_FILE_NAME = (
    "ACTIVATION_DECISION.json"
)
MAX_ACTIVATION_DECISION_BYTES = 500_000


class BuilderActivationReviewDecisionStorageError(
    RuntimeError
):
    """Raised when activation-review storage is unsafe."""


def canonical_builder_activation_review_json(
    decision: BuilderActivationReviewDecision,
) -> str:
    """Return deterministic activation-review JSON."""

    return (
        json.dumps(
            decision.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_activation_review_sha256(
    decision: BuilderActivationReviewDecision,
) -> str:
    """Hash exact canonical activation-review content."""

    return hashlib.sha256(
        canonical_builder_activation_review_json(
            decision
        ).encode("utf-8")
    ).hexdigest()


def _decision_root_path(
    decision_root: Path,
) -> Path:
    if decision_root.is_symlink():
        raise (
            BuilderActivationReviewDecisionStorageError(
                "Builder activation-decision root "
                "cannot be a symlink"
            )
        )

    try:
        decision_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = decision_root.resolve(strict=True)
    except OSError as exc:
        raise (
            BuilderActivationReviewDecisionStorageError(
                "Builder activation-decision root "
                "is unavailable"
            )
        ) from exc

    if not root.is_dir():
        raise (
            BuilderActivationReviewDecisionStorageError(
                "Builder activation-decision root "
                "must be a directory"
            )
        )

    return root


def _recreate_decision(
    decision: BuilderActivationReviewDecision,
    *,
    verification_root: Path,
    promotion_root: Path,
    plan_root: Path,
) -> BuilderActivationReviewDecision:
    try:
        return create_builder_activation_review_decision(
            verification_file=Path(
                decision.verification_file
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            plan_root=plan_root,
            decision_id=decision.decision_id,
            reviewer_id=decision.reviewer_id,
            decided_at=decision.decided_at,
            decision=decision.decision,
            rationale=decision.rationale,
        )
    except BuilderActivationReviewError as exc:
        raise (
            BuilderActivationReviewDecisionStorageError(
                "Builder activation decision could "
                "not be reverified"
            )
        ) from exc


def persist_builder_activation_review_decision(
    decision: BuilderActivationReviewDecision,
    *,
    decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    plan_root: Path,
) -> BuilderActivationReviewDecisionStorageResult:
    """Atomically persist one freshly reverified decision."""

    current = _recreate_decision(
        decision,
        verification_root=verification_root,
        promotion_root=promotion_root,
        plan_root=plan_root,
    )

    if current != decision:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation decision changed "
            "before persistence"
        )

    root = _decision_root_path(
        decision_root
    )
    content = (
        canonical_builder_activation_review_json(
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
            f"{digest}.activation-decision"
        )
    )

    if (
        decision_directory.exists()
        or decision_directory.is_symlink()
    ):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation decision already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-activation-",
            dir=root,
        )
    )
    staged = temporary_root / "decision"
    staged_file = (
        staged / ACTIVATION_DECISION_FILE_NAME
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
                BuilderActivationReviewDecisionStorageError(
                    "Builder activation-decision file "
                    "digest is inconsistent"
                )
            )

        current_after = _recreate_decision(
            decision,
            verification_root=verification_root,
            promotion_root=promotion_root,
            plan_root=plan_root,
        )

        if current_after != decision:
            raise (
                BuilderActivationReviewDecisionStorageError(
                    "Builder activation inputs changed "
                    "during decision persistence"
                )
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
            BuilderActivationReviewDecisionStorageError,
        ):
            raise

        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation decision could "
            "not be persisted"
        ) from exc

    final_file = (
        decision_directory
        / ACTIVATION_DECISION_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderActivationReviewDecisionStorageError(
            "Persisted Builder activation decision "
            "could not be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderActivationReviewDecisionStorageError(
            "Persisted Builder activation-decision "
            "digest changed"
        )

    return BuilderActivationReviewDecisionStorageResult(
        decision_id=decision.decision_id,
        task_id=decision.task_id,
        decision=decision.decision,
        verification_sha256=(
            decision.verification_sha256
        ),
        activation_decision_sha256=digest,
        decision_directory=(
            decision_directory.as_posix()
        ),
        decision_file=final_file.as_posix(),
        approval_granted=(
            decision.approval_granted
        ),
        activation_planning_authorized=(
            decision.activation_planning_authorized
        ),
    )


def load_builder_activation_review_decision(
    decision_file: Path,
    *,
    decision_root: Path,
) -> tuple[
    BuilderActivationReviewDecision,
    str,
    Path,
]:
    """Load and verify one immutable activation decision."""

    if decision_root.is_symlink():
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision root "
            "cannot be a symlink"
        )

    try:
        root = decision_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision root "
            "must be a directory"
        )

    unresolved = (
        decision_file
        if decision_file.is_absolute()
        else root / decision_file
    )

    if unresolved.is_symlink():
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file "
            "cannot be a symlink"
        )

    try:
        safe_file = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file "
            "is unavailable"
        ) from exc

    decision_directory = safe_file.parent

    if (
        decision_directory.parent != root
        or decision_directory.is_symlink()
    ):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation decision must be "
            "directly beneath its approved root"
        )

    if (
        safe_file.name
        != ACTIVATION_DECISION_FILE_NAME
        or not safe_file.is_file()
    ):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation decision must contain "
            "ACTIVATION_DECISION.json"
        )

    try:
        content = safe_file.read_bytes()
    except OSError as exc:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file "
            "could not be read"
        ) from exc

    size = len(content)

    if size < 1:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file is empty"
        )

    if size > MAX_ACTIVATION_DECISION_BYTES:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file exceeds "
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
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file is not "
            "valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file must "
            "contain an object"
        )

    try:
        decision = (
            BuilderActivationReviewDecision
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file failed "
            "schema validation"
        ) from exc

    expected_directory_name = (
        f"{decision.decision_id}."
        f"{digest}.activation-decision"
    )

    if (
        decision_directory.name
        != expected_directory_name
    ):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision directory "
            "digest is invalid"
        )

    if (
        canonical_builder_activation_review_json(
            decision
        ).encode("utf-8")
        != content
    ):
        raise BuilderActivationReviewDecisionStorageError(
            "Builder activation-decision file "
            "is not canonical"
        )

    return decision, digest, safe_file
