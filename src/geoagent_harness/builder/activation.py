"""Explicit transactional activation of Builder bundles."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from geoagent_harness.builder.activation_plan import (
    BuilderActivationPlanError,
    plan_builder_activation,
)
from geoagent_harness.builder.activation_plan_storage import (
    BuilderActivationPlanStorageError,
    builder_activation_plan_sha256,
    load_builder_activation_plan,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationPlan,
    BuilderActivationResult,
)


ACTIVATION_MANIFEST_NAME = "ACTIVATION.json"


class BuilderActivationError(RuntimeError):
    """Raised when explicit Builder activation is unsafe."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_bytes(
    path: Path,
    *,
    label: str,
) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise BuilderActivationError(
            f"{label} could not be read"
        ) from exc


def _project_root_path(
    project_root: Path,
) -> Path:
    if project_root.is_symlink():
        raise BuilderActivationError(
            "Builder activation project root "
            "cannot be a symlink"
        )

    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationError(
            "Builder activation project root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationError(
            "Builder activation project root "
            "must be a directory"
        )

    return root


def _activation_root_path(
    activation_root: Path,
) -> Path:
    if activation_root.is_symlink():
        raise BuilderActivationError(
            "Builder activation evidence root "
            "cannot be a symlink"
        )

    try:
        activation_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = activation_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationError(
            "Builder activation evidence root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationError(
            "Builder activation evidence root "
            "must be a directory"
        )

    return root


def _source_path(
    plan: BuilderActivationPlan,
    relative_path: str,
) -> Path:
    promotion_directory = Path(
        plan.promotion_directory
    )

    unresolved = (
        promotion_directory / relative_path
    )

    if unresolved.is_symlink():
        raise BuilderActivationError(
            "Builder activation source "
            "cannot be a symlink"
        )

    try:
        source = unresolved.resolve(strict=True)
        promotion = promotion_directory.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderActivationError(
            "Builder activation source is unavailable"
        ) from exc

    if (
        promotion not in source.parents
        or not source.is_file()
    ):
        raise BuilderActivationError(
            "Builder activation source escaped "
            "the promoted bundle"
        )

    return source


def _destination_path(
    project: Path,
    relative_path: str,
) -> Path:
    unresolved = project / relative_path

    if unresolved.is_symlink():
        raise BuilderActivationError(
            "Builder activation destination "
            "cannot be a symlink"
        )

    destination = unresolved.resolve()

    if project not in destination.parents:
        raise BuilderActivationError(
            "Builder activation destination "
            "escaped project root"
        )

    return destination


def _stage_bytes(
    *,
    destination: Path,
    content: bytes,
) -> Path:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=(
            f".{destination.name}."
            "geoagent-activation-"
        ),
        dir=destination.parent,
    )
    temporary = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            "wb",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(temporary, 0o644)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise

    return temporary


def _remove_new_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # Preserve the original activation failure.
        pass


def _remove_empty_directories(
    directories: list[Path],
) -> None:
    for directory in reversed(directories):
        try:
            directory.rmdir()
        except OSError:
            pass


def _new_parent_directories(
    destination: Path,
    *,
    project: Path,
) -> list[Path]:
    missing: list[Path] = []
    current = destination.parent

    while (
        current != project
        and project in current.parents
        and not current.exists()
    ):
        missing.append(current)
        current = current.parent

    return list(reversed(missing))


def _canonical_manifest_json(
    payload: dict[str, Any],
) -> str:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def _manifest_payload(
    plan: BuilderActivationPlan,
    *,
    activation_plan_sha256: str,
    activation_plan_file: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "task_id": plan.task_id,
        "activation_decision_id": (
            plan.activation_decision_id
        ),
        "verification_sha256": (
            plan.verification_sha256
        ),
        "activation_decision_sha256": (
            plan.activation_decision_sha256
        ),
        "promotion_plan_sha256": (
            plan.promotion_plan_sha256
        ),
        "candidate_tree_sha256": (
            plan.candidate_tree_sha256
        ),
        "activation_plan_sha256": (
            activation_plan_sha256
        ),
        "project_root": plan.project_root,
        "promotion_directory": (
            plan.promotion_directory
        ),
        "activation_plan_file": (
            activation_plan_file.as_posix()
        ),
        "files": [
            {
                "kind": item.kind.value,
                "source_path": item.source_path,
                "destination_path": (
                    item.destination_path
                ),
                "sha256": item.sha256,
            }
            for item in plan.files
        ],
        "human_approval_verified": True,
        "bundle_reverified": True,
        "files_copied": True,
        "activation_performed": True,
        "post_activation_verified": False,
        "registry_modified": False,
        "implementation_trusted": False,
        "promotion_performed": True,
        "execution_performed": False,
    }


def activate_builder_bundle(
    plan_file: Path,
    *,
    activation_plan_root: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
    activation_root: Path,
    confirm_activation_decision_id: str,
    confirm_activation_plan_sha256: str,
) -> BuilderActivationResult:
    """Install exact approved bytes with rollback on failure."""

    try:
        (
            plan,
            plan_digest,
            safe_plan_file,
        ) = load_builder_activation_plan(
            plan_file,
            plan_root=activation_plan_root,
        )
    except BuilderActivationPlanStorageError as exc:
        raise BuilderActivationError(
            "Builder activation plan could not be loaded"
        ) from exc

    if (
        confirm_activation_decision_id
        != plan.activation_decision_id
    ):
        raise BuilderActivationError(
            "Builder activation-decision confirmation "
            "does not match"
        )

    if (
        confirm_activation_plan_sha256
        != plan_digest
    ):
        raise BuilderActivationError(
            "Builder activation-plan confirmation "
            "does not match"
        )

    if (
        builder_activation_plan_sha256(plan)
        != plan_digest
    ):
        raise BuilderActivationError(
            "Builder activation-plan digest "
            "is inconsistent"
        )

    project = _project_root_path(
        project_root
    )
    root = _activation_root_path(
        activation_root
    )

    activation_directory = (
        root
        / (
            f"{plan.task_id}."
            f"{plan_digest}.activation"
        )
    )

    if (
        activation_directory.exists()
        or activation_directory.is_symlink()
    ):
        raise BuilderActivationError(
            "Builder activation evidence already exists"
        )

    try:
        current_plan = plan_builder_activation(
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
            project_root=project,
        )
    except BuilderActivationPlanError as exc:
        raise BuilderActivationError(
            "Builder activation inputs could not "
            "be reverified"
        ) from exc

    if current_plan != plan:
        raise BuilderActivationError(
            "Builder activation plan changed "
            "before activation"
        )

    staged_files: list[
        tuple[Path, Path, str]
    ] = []
    installed_files: list[Path] = []
    created_directories: list[Path] = []
    activated_paths: list[str] = []

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-activation-",
            dir=root,
        )
    )
    staged_evidence = (
        temporary_root / "activation"
    )
    staged_manifest = (
        staged_evidence
        / ACTIVATION_MANIFEST_NAME
    )
    evidence_finalized = False

    try:
        staged_evidence.mkdir()

        for item in plan.files:
            source = _source_path(
                plan,
                item.source_path,
            )
            destination = _destination_path(
                project,
                item.destination_path,
            )

            if destination.exists():
                raise BuilderActivationError(
                    "Builder activation destination "
                    "already exists"
                )

            content = _read_bytes(
                source,
                label="Builder activation source",
            )

            if (
                _sha256_bytes(content)
                != item.sha256
            ):
                raise BuilderActivationError(
                    "Builder activation source digest "
                    "changed"
                )

            for directory in (
                _new_parent_directories(
                    destination,
                    project=project,
                )
            ):
                if directory not in created_directories:
                    created_directories.append(
                        directory
                    )

            temporary = _stage_bytes(
                destination=destination,
                content=content,
            )

            if (
                _sha256_bytes(
                    _read_bytes(
                        temporary,
                        label=(
                            "Staged Builder activation"
                        ),
                    )
                )
                != item.sha256
            ):
                raise BuilderActivationError(
                    "Staged Builder activation digest "
                    "changed"
                )

            staged_files.append(
                (
                    temporary,
                    destination,
                    item.sha256,
                )
            )
            activated_paths.append(
                item.destination_path
            )

        manifest_payload = _manifest_payload(
            plan,
            activation_plan_sha256=plan_digest,
            activation_plan_file=safe_plan_file,
        )

        with staged_manifest.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                _canonical_manifest_json(
                    manifest_payload
                )
            )

        try:
            current_after = (
                plan_builder_activation(
                    activation_decision_file=Path(
                        plan.activation_decision_file
                    ),
                    activation_decision_root=(
                        activation_decision_root
                    ),
                    verification_root=(
                        verification_root
                    ),
                    promotion_root=promotion_root,
                    promotion_plan_root=(
                        promotion_plan_root
                    ),
                    project_root=project,
                )
            )
        except BuilderActivationPlanError as exc:
            raise BuilderActivationError(
                "Builder activation inputs could not "
                "be reverified after staging"
            ) from exc

        if current_after != plan:
            raise BuilderActivationError(
                "Builder activation inputs changed "
                "during staging"
            )

        for temporary, destination, digest in (
            staged_files
        ):
            if destination.exists():
                raise BuilderActivationError(
                    "Builder activation destination "
                    "appeared during commit"
                )

            if (
                _sha256_bytes(
                    _read_bytes(
                        temporary,
                        label=(
                            "Staged Builder activation"
                        ),
                    )
                )
                != digest
            ):
                raise BuilderActivationError(
                    "Staged Builder activation changed "
                    "before commit"
                )

            os.replace(
                temporary,
                destination,
            )
            installed_files.append(
                destination
            )

        for (
            _temporary,
            destination,
            digest,
        ) in staged_files:
            if (
                _sha256_bytes(
                    _read_bytes(
                        destination,
                        label=(
                            "Installed Builder activation"
                        ),
                    )
                )
                != digest
            ):
                raise BuilderActivationError(
                    "Installed Builder activation digest "
                    "changed"
                )

        if (
            activation_directory.exists()
            or activation_directory.is_symlink()
        ):
            raise BuilderActivationError(
                "Builder activation evidence destination "
                "appeared during commit"
            )

        os.replace(
            staged_evidence,
            activation_directory,
        )
        evidence_finalized = True
        temporary_root.rmdir()
    except (
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        for temporary, _destination, _digest in (
            staged_files
        ):
            temporary.unlink(missing_ok=True)

        for destination in reversed(
            installed_files
        ):
            _remove_new_file(destination)

        if evidence_finalized:
            shutil.rmtree(
                activation_directory,
                ignore_errors=True,
            )

        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )
        _remove_empty_directories(
            created_directories
        )

        if isinstance(
            exc,
            BuilderActivationError,
        ):
            raise

        raise BuilderActivationError(
            "Builder activation transaction failed"
        ) from exc

    return BuilderActivationResult(
        task_id=plan.task_id,
        activation_decision_id=(
            plan.activation_decision_id
        ),
        activation_plan_sha256=plan_digest,
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        activation_directory=(
            activation_directory.as_posix()
        ),
        activation_manifest=(
            activation_directory
            / ACTIVATION_MANIFEST_NAME
        ).as_posix(),
        activated_paths=activated_paths,
    )
