"""Immutable storage for Builder activation plans."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.activation_plan import (
    BuilderActivationPlanError,
    plan_builder_activation,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationPlan,
    BuilderActivationPlanStorageResult,
)


ACTIVATION_PLAN_FILE_NAME = (
    "ACTIVATION_PLAN.json"
)
MAX_ACTIVATION_PLAN_BYTES = 1_000_000


class BuilderActivationPlanStorageError(
    RuntimeError
):
    """Raised when Builder activation-plan storage is unsafe."""


def canonical_builder_activation_plan_json(
    plan: BuilderActivationPlan,
) -> str:
    """Return deterministic activation-plan JSON."""

    return (
        json.dumps(
            plan.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_activation_plan_sha256(
    plan: BuilderActivationPlan,
) -> str:
    """Hash exact canonical activation-plan content."""

    return hashlib.sha256(
        canonical_builder_activation_plan_json(
            plan
        ).encode("utf-8")
    ).hexdigest()


def _plan_root_path(
    plan_root: Path,
) -> Path:
    if plan_root.is_symlink():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "cannot be a symlink"
        )

    try:
        plan_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = plan_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "must be a directory"
        )

    return root


def _recreate_plan(
    plan: BuilderActivationPlan,
    *,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderActivationPlan:
    try:
        return plan_builder_activation(
            activation_decision_file=Path(
                plan.activation_decision_file
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
    except BuilderActivationPlanError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation plan could not "
            "be reverified"
        ) from exc


def persist_builder_activation_plan(
    plan: BuilderActivationPlan,
    *,
    plan_root: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderActivationPlanStorageResult:
    """Persist one freshly reverified non-writing plan."""

    current = _recreate_plan(
        plan,
        activation_decision_root=(
            activation_decision_root
        ),
        verification_root=verification_root,
        promotion_root=promotion_root,
        promotion_plan_root=promotion_plan_root,
        project_root=project_root,
    )

    if current != plan:
        raise BuilderActivationPlanStorageError(
            "Builder activation plan changed "
            "before persistence"
        )

    root = _plan_root_path(plan_root)
    content = (
        canonical_builder_activation_plan_json(
            plan
        )
    )
    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    plan_directory = (
        root
        / (
            f"{plan.task_id}."
            f"{digest}.activation-plan"
        )
    )

    if (
        plan_directory.exists()
        or plan_directory.is_symlink()
    ):
        raise BuilderActivationPlanStorageError(
            "Builder activation plan already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-activation-plan-",
            dir=root,
        )
    )
    staged = temporary_root / "plan"
    staged_file = (
        staged / ACTIVATION_PLAN_FILE_NAME
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
            raise BuilderActivationPlanStorageError(
                "Builder activation-plan file digest "
                "is inconsistent"
            )

        current_after = _recreate_plan(
            plan,
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

        if current_after != plan:
            raise BuilderActivationPlanStorageError(
                "Builder activation inputs changed "
                "during plan persistence"
            )

        os.replace(
            staged,
            plan_directory,
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
            BuilderActivationPlanStorageError,
        ):
            raise

        raise BuilderActivationPlanStorageError(
            "Builder activation plan could "
            "not be persisted"
        ) from exc

    final_file = (
        plan_directory
        / ACTIVATION_PLAN_FILE_NAME
    )

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderActivationPlanStorageError(
            "Persisted Builder activation plan "
            "could not be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderActivationPlanStorageError(
            "Persisted Builder activation-plan "
            "digest changed"
        )

    return BuilderActivationPlanStorageResult(
        task_id=plan.task_id,
        activation_decision_id=(
            plan.activation_decision_id
        ),
        verification_sha256=(
            plan.verification_sha256
        ),
        activation_decision_sha256=(
            plan.activation_decision_sha256
        ),
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        activation_plan_sha256=digest,
        plan_directory=(
            plan_directory.as_posix()
        ),
        plan_file=final_file.as_posix(),
    )


def load_builder_activation_plan(
    plan_file: Path,
    *,
    plan_root: Path,
) -> tuple[
    BuilderActivationPlan,
    str,
    Path,
]:
    """Load one canonical digest-addressed activation plan."""

    if plan_root.is_symlink():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "cannot be a symlink"
        )

    try:
        root = plan_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan root "
            "must be a directory"
        )

    unresolved = (
        plan_file
        if plan_file.is_absolute()
        else root / plan_file
    )

    if unresolved.is_symlink():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file "
            "cannot be a symlink"
        )

    if unresolved.parent.is_symlink():
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan directory "
            "cannot be a symlink"
        )

    try:
        safe_file = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file "
            "is unavailable"
        ) from exc

    plan_directory = safe_file.parent

    if plan_directory.parent != root:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file escaped "
            "its approved root"
        )

    if (
        safe_file.name
        != ACTIVATION_PLAN_FILE_NAME
        or not safe_file.is_file()
    ):
        raise BuilderActivationPlanStorageError(
            "Builder activation plan must contain "
            "ACTIVATION_PLAN.json"
        )

    try:
        content = safe_file.read_bytes()
    except OSError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file "
            "could not be read"
        ) from exc

    size = len(content)

    if size < 1:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file is empty"
        )

    if size > MAX_ACTIVATION_PLAN_BYTES:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file exceeds "
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
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file is not "
            "valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file must "
            "contain an object"
        )

    try:
        plan = BuilderActivationPlan.model_validate(
            payload
        )
    except ValidationError as exc:
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file failed "
            "schema validation"
        ) from exc

    expected_directory_name = (
        f"{plan.task_id}."
        f"{digest}.activation-plan"
    )

    if (
        plan_directory.name
        != expected_directory_name
    ):
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan directory "
            "digest is invalid"
        )

    if (
        canonical_builder_activation_plan_json(
            plan
        ).encode("utf-8")
        != content
    ):
        raise BuilderActivationPlanStorageError(
            "Builder activation-plan file "
            "is not canonical"
        )

    return plan, digest, safe_file
