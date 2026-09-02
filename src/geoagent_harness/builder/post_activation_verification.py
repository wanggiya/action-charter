"""Independent verification of activated Builder files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.activation import (
    ACTIVATION_MANIFEST_NAME,
)
from geoagent_harness.builder.activation_plan_storage import (
    BuilderActivationPlanStorageError,
    load_builder_activation_plan,
)
from geoagent_harness.builder.activation_review_storage import (
    BuilderActivationReviewDecisionStorageError,
    load_builder_activation_review_decision,
)
from geoagent_harness.builder.promotion_verification import (
    BuilderPromotionVerificationError,
    verify_builder_promotion_bundle,
)
from geoagent_harness.builder.promotion_verification_storage import (
    BuilderPromotionVerificationStorageError,
    builder_promotion_verification_sha256,
    load_builder_promotion_verification,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationManifest,
    BuilderActivationPlan,
    BuilderPostActivationVerificationResult,
)


MAX_ACTIVATION_MANIFEST_BYTES = 1_000_000


class BuilderPostActivationVerificationError(
    RuntimeError
):
    """Raised when activated Builder files are invalid."""


def canonical_builder_activation_manifest_json(
    manifest: BuilderActivationManifest,
) -> str:
    """Return the exact canonical activation manifest."""

    return (
        json.dumps(
            manifest.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_sha256(path: Path) -> str:
    try:
        return _sha256_bytes(
            path.read_bytes()
        )
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Activated Builder file could not be read"
        ) from exc


def _activation_directory_path(
    activation_directory: Path,
    *,
    activation_root: Path,
) -> tuple[Path, Path]:
    if activation_root.is_symlink():
        raise BuilderPostActivationVerificationError(
            "Builder activation root cannot be a symlink"
        )

    try:
        root = activation_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation root is unavailable"
        ) from exc

    unresolved = (
        activation_directory
        if activation_directory.is_absolute()
        else root / activation_directory
    )

    if unresolved.is_symlink():
        raise BuilderPostActivationVerificationError(
            "Builder activation directory "
            "cannot be a symlink"
        )

    try:
        activation = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation directory "
            "is unavailable"
        ) from exc

    if (
        activation.parent != root
        or not activation.is_dir()
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation directory escaped "
            "its approved root"
        )

    return root, activation


def _manifest_path(
    activation: Path,
) -> Path:
    unresolved = (
        activation / ACTIVATION_MANIFEST_NAME
    )

    if unresolved.is_symlink():
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest "
            "cannot be a symlink"
        )

    try:
        manifest_file = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest is unavailable"
        ) from exc

    if (
        manifest_file.parent != activation
        or not manifest_file.is_file()
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest is unsafe"
        )

    return manifest_file


def _load_manifest(
    manifest_file: Path,
) -> tuple[
    BuilderActivationManifest,
    bytes,
]:
    try:
        content = manifest_file.read_bytes()
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest "
            "could not be read"
        ) from exc

    if len(content) < 1:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest is empty"
        )

    if len(content) > MAX_ACTIVATION_MANIFEST_BYTES:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest exceeds "
            "the size limit"
        )

    try:
        raw = content.decode("utf-8")
        payload: Any = json.loads(raw)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest is not "
            "valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest must "
            "contain an object"
        )

    try:
        manifest = (
            BuilderActivationManifest
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest failed "
            "schema validation"
        ) from exc

    if (
        canonical_builder_activation_manifest_json(
            manifest
        ).encode("utf-8")
        != content
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest is not canonical"
        )

    return manifest, content


def _project_root_path(
    project_root: Path,
) -> Path:
    if project_root.is_symlink():
        raise BuilderPostActivationVerificationError(
            "Builder verification project root "
            "cannot be a symlink"
        )

    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder verification project root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPostActivationVerificationError(
            "Builder verification project root "
            "must be a directory"
        )

    return root


def _destination_path(
    project: Path,
    relative_path: str,
) -> Path:
    unresolved = project / relative_path
    current = project

    for part in Path(relative_path).parts:
        current = current / part

        if current.is_symlink():
            raise BuilderPostActivationVerificationError(
                "Activated Builder path contains "
                "a symlink"
            )

    try:
        destination = unresolved.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderPostActivationVerificationError(
            "Activated Builder file is unavailable"
        ) from exc

    if (
        project not in destination.parents
        or not destination.is_file()
    ):
        raise BuilderPostActivationVerificationError(
            "Activated Builder file escaped "
            "the project root"
        )

    return destination


def _expected_manifest_files(
    plan: BuilderActivationPlan,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": item.kind.value,
            "source_path": item.source_path,
            "destination_path": (
                item.destination_path
            ),
            "sha256": item.sha256,
        }
        for item in plan.files
    ]


def verify_builder_activation(
    *,
    activation_directory: Path,
    activation_root: Path,
    activation_plan_file: Path,
    activation_plan_root: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderPostActivationVerificationResult:
    """Verify exact activated bytes without executing them."""

    _, activation = _activation_directory_path(
        activation_directory,
        activation_root=activation_root,
    )
    manifest_file = _manifest_path(
        activation
    )
    manifest, manifest_content = (
        _load_manifest(manifest_file)
    )

    try:
        (
            plan,
            plan_digest,
            safe_plan_file,
        ) = load_builder_activation_plan(
            activation_plan_file,
            plan_root=activation_plan_root,
        )
        (
            decision,
            decision_digest,
            _,
        ) = load_builder_activation_review_decision(
            Path(plan.activation_decision_file),
            decision_root=activation_decision_root,
        )
        verification = (
            load_builder_promotion_verification(
                Path(plan.verification_file),
                verification_root=verification_root,
            )
        )
    except (
        BuilderActivationPlanStorageError,
        BuilderActivationReviewDecisionStorageError,
        BuilderPromotionVerificationStorageError,
    ) as exc:
        raise BuilderPostActivationVerificationError(
            "Builder post-activation evidence "
            "could not be loaded"
        ) from exc

    verification_digest = (
        builder_promotion_verification_sha256(
            verification
        )
    )

    if (
        manifest.task_id != plan.task_id
        or manifest.activation_decision_id
        != plan.activation_decision_id
        or manifest.activation_plan_sha256
        != plan_digest
        or manifest.activation_decision_sha256
        != decision_digest
        or manifest.verification_sha256
        != verification_digest
        or manifest.promotion_plan_sha256
        != plan.promotion_plan_sha256
        or manifest.candidate_tree_sha256
        != plan.candidate_tree_sha256
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation identities do not match"
        )

    if (
        decision.decision != "approved"
        or not decision.approval_granted
        or not decision.activation_planning_authorized
        or decision.verification_sha256
        != verification_digest
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation approval is invalid"
        )

    if (
        plan.activation_decision_sha256
        != decision_digest
        or plan.verification_sha256
        != verification_digest
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation plan evidence "
            "does not match"
        )

    try:
        current_verification = (
            verify_builder_promotion_bundle(
                promotion_directory=Path(
                    verification.promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=Path(
                    verification.plan_file
                ),
                plan_root=promotion_plan_root,
            )
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderPostActivationVerificationError(
            "Builder promoted bundle could not "
            "be reverified"
        ) from exc

    if current_verification != verification:
        raise BuilderPostActivationVerificationError(
            "Builder promotion verification changed"
        )

    project = _project_root_path(project_root)

    if (
        project.as_posix() != plan.project_root
        or manifest.project_root != plan.project_root
        or manifest.promotion_directory
        != plan.promotion_directory
        or manifest.activation_plan_file
        != safe_plan_file.as_posix()
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation paths do not match"
        )

    expected_directory_name = (
        f"{plan.task_id}.{plan_digest}.activation"
    )

    if activation.name != expected_directory_name:
        raise BuilderPostActivationVerificationError(
            "Builder activation directory identity "
            "is invalid"
        )

    entries = sorted(
        path.relative_to(activation).as_posix()
        for path in activation.rglob("*")
    )

    if entries != [ACTIVATION_MANIFEST_NAME]:
        raise BuilderPostActivationVerificationError(
            "Builder activation evidence contains "
            "unexpected entries"
        )

    actual_manifest_files = [
        item.model_dump(mode="json")
        for item in manifest.files
    ]
    expected_manifest_files = (
        _expected_manifest_files(plan)
    )

    if actual_manifest_files != expected_manifest_files:
        raise BuilderPostActivationVerificationError(
            "Builder activation manifest files "
            "do not match the plan"
        )

    first_digests: dict[str, str] = {}

    for item in plan.files:
        destination = _destination_path(
            project,
            item.destination_path,
        )
        digest = _file_sha256(destination)

        if digest != item.sha256:
            raise BuilderPostActivationVerificationError(
                "Activated Builder file digest "
                "does not match"
            )

        first_digests[
            item.destination_path
        ] = digest

    try:
        verification_after = (
            verify_builder_promotion_bundle(
                promotion_directory=Path(
                    verification.promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=Path(
                    verification.plan_file
                ),
                plan_root=promotion_plan_root,
            )
        )
        manifest_content_after = (
            manifest_file.read_bytes()
        )
    except (
        BuilderPromotionVerificationError,
        OSError,
    ) as exc:
        raise BuilderPostActivationVerificationError(
            "Builder activation evidence changed "
            "during verification"
        ) from exc

    if (
        verification_after != verification
        or manifest_content_after
        != manifest_content
    ):
        raise BuilderPostActivationVerificationError(
            "Builder activation evidence changed "
            "during verification"
        )

    for item in plan.files:
        destination = _destination_path(
            project,
            item.destination_path,
        )
        digest = _file_sha256(destination)

        if (
            digest != item.sha256
            or digest
            != first_digests[item.destination_path]
        ):
            raise BuilderPostActivationVerificationError(
                "Activated Builder files changed "
                "during verification"
            )

    return BuilderPostActivationVerificationResult(
        task_id=plan.task_id,
        activation_decision_id=(
            plan.activation_decision_id
        ),
        verification_sha256=(
            verification_digest
        ),
        activation_decision_sha256=(
            decision_digest
        ),
        promotion_plan_sha256=(
            plan.promotion_plan_sha256
        ),
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        activation_plan_sha256=plan_digest,
        activation_directory=(
            activation.as_posix()
        ),
        activation_manifest=(
            manifest_file.as_posix()
        ),
        activation_plan_file=(
            safe_plan_file.as_posix()
        ),
        project_root=project.as_posix(),
        verified_paths=[
            item.destination_path
            for item in plan.files
        ],
    )
