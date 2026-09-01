"""Independent read-only verification of Builder bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.promotion import (
    PROMOTED_FILES_DIRECTORY,
    PROMOTION_MANIFEST_NAME,
)
from geoagent_harness.builder.promotion_plan_storage import (
    BuilderPromotionPlanStorageError,
    builder_promotion_plan_sha256,
    load_builder_promotion_plan,
)
from geoagent_harness.builder.schemas import (
    BuilderPromotionManifest,
    BuilderPromotionPlan,
    BuilderPromotionVerificationResult,
)


MAX_PROMOTION_MANIFEST_BYTES = 1_000_000


class BuilderPromotionVerificationError(
    RuntimeError
):
    """Raised when a promoted bundle fails verification."""


def canonical_builder_promotion_manifest_json(
    manifest: BuilderPromotionManifest,
) -> str:
    """Return the exact canonical manifest representation."""

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
        raise BuilderPromotionVerificationError(
            "Promoted Builder file could not be read"
        ) from exc


def _promotion_directory_path(
    promotion_directory: Path,
    *,
    promotion_root: Path,
) -> tuple[Path, Path]:
    """Resolve one direct non-symlink bundle beneath its root."""

    if promotion_root.is_symlink():
        raise BuilderPromotionVerificationError(
            "Builder promotion root cannot be a symlink"
        )

    try:
        root = promotion_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionVerificationError(
            "Builder promotion root must be a directory"
        )

    unresolved = (
        promotion_directory
        if promotion_directory.is_absolute()
        else root / promotion_directory
    )

    if unresolved.is_symlink():
        raise BuilderPromotionVerificationError(
            "Builder promotion directory cannot be a symlink"
        )

    try:
        bundle = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion directory is unavailable"
        ) from exc

    if bundle.parent != root:
        raise BuilderPromotionVerificationError(
            "Builder promotion directory escaped "
            "its approved root"
        )

    if not bundle.is_dir():
        raise BuilderPromotionVerificationError(
            "Builder promotion path must be a directory"
        )

    return root, bundle


def _manifest_path(bundle: Path) -> Path:
    unresolved = bundle / PROMOTION_MANIFEST_NAME

    if unresolved.is_symlink():
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest cannot be a symlink"
        )

    try:
        manifest = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest is unavailable"
        ) from exc

    if (
        manifest.parent != bundle
        or not manifest.is_file()
    ):
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest is unsafe"
        )

    return manifest


def _load_manifest(
    manifest_file: Path,
) -> tuple[BuilderPromotionManifest, bytes]:
    try:
        size = manifest_file.stat().st_size
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest metadata "
            "is unavailable"
        ) from exc

    if size < 1:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest is empty"
        )

    if size > MAX_PROMOTION_MANIFEST_BYTES:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest exceeds "
            "the size limit"
        )

    try:
        raw_bytes = manifest_file.read_bytes()
        raw = raw_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest is not UTF-8"
        ) from exc
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest could not be read"
        ) from exc

    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest contains "
            "invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest must contain "
            "one JSON object"
        )

    try:
        manifest = (
            BuilderPromotionManifest
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest failed "
            "schema validation"
        ) from exc

    canonical = (
        canonical_builder_promotion_manifest_json(
            manifest
        )
    )

    if raw != canonical:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest is not canonical"
        )

    return manifest, raw_bytes

def load_builder_promotion_manifest(
    promotion_directory: Path,
    *,
    promotion_root: Path,
) -> tuple[
    BuilderPromotionManifest,
    Path,
    Path,
]:
    """Securely load one canonical promotion manifest."""

    _, bundle = _promotion_directory_path(
        promotion_directory,
        promotion_root=promotion_root,
    )
    manifest_file = _manifest_path(bundle)
    manifest, _ = _load_manifest(
        manifest_file
    )

    return manifest, bundle, manifest_file

def _load_plan(
    plan_file: Path,
    *,
    plan_root: Path,
) -> BuilderPromotionPlan:
    try:
        return load_builder_promotion_plan(
            plan_file,
            plan_root=plan_root,
        )
    except BuilderPromotionPlanStorageError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion plan could not be loaded"
        ) from exc


def _expected_manifest_files(
    plan: BuilderPromotionPlan,
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


def _verify_manifest_against_plan(
    manifest: BuilderPromotionManifest,
    plan: BuilderPromotionPlan,
    *,
    promotion_plan_sha256: str,
) -> None:
    identity_pairs = (
        (
            manifest.task_id,
            plan.task_id,
            "task ID",
        ),
        (
            manifest.decision_id,
            plan.decision_id,
            "decision ID",
        ),
        (
            manifest.review_package_sha256,
            plan.review_package_sha256,
            "review-package digest",
        ),
        (
            manifest.decision_sha256,
            plan.decision_sha256,
            "decision digest",
        ),
        (
            manifest.generation_sha256,
            plan.generation_sha256,
            "generation digest",
        ),
        (
            manifest.candidate_tree_sha256,
            plan.candidate_tree_sha256,
            "candidate-tree digest",
        ),
        (
            manifest.promotion_plan_sha256,
            promotion_plan_sha256,
            "promotion-plan digest",
        ),
    )

    for actual, expected, label in identity_pairs:
        if actual != expected:
            raise BuilderPromotionVerificationError(
                f"Builder promotion {label} does not match"
            )

    actual_files = [
        item.model_dump(mode="json")
        for item in manifest.files
    ]

    if (
        actual_files
        != _expected_manifest_files(plan)
    ):
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest files "
            "do not match the plan"
        )


def _verify_directory_identity(
    bundle: Path,
    manifest: BuilderPromotionManifest,
) -> None:
    expected_name = (
        f"{manifest.task_id}."
        f"{manifest.promotion_plan_sha256}"
        ".promotion"
    )

    if bundle.name != expected_name:
        raise BuilderPromotionVerificationError(
            "Builder promotion directory identity "
            "does not match"
        )


def _expected_bundle_files(
    manifest: BuilderPromotionManifest,
) -> set[str]:
    return {
        PROMOTION_MANIFEST_NAME,
        *(
            (
                f"{PROMOTED_FILES_DIRECTORY}/"
                f"{item.destination_path}"
            )
            for item in manifest.files
        ),
    }


def _actual_bundle_files(
    bundle: Path,
) -> set[str]:
    actual: set[str] = set()

    try:
        entries = sorted(
            bundle.rglob("*"),
            key=lambda path: (
                path.relative_to(bundle).as_posix()
            ),
        )
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion bundle could not "
            "be enumerated"
        ) from exc

    for entry in entries:
        if entry.is_symlink():
            raise BuilderPromotionVerificationError(
                "Builder promotion bundle cannot "
                "contain symlinks"
            )

        if entry.is_file():
            actual.add(
                entry.relative_to(
                    bundle
                ).as_posix()
            )
        elif not entry.is_dir():
            raise BuilderPromotionVerificationError(
                "Builder promotion bundle contains "
                "an unsupported filesystem entry"
            )

    return actual


def _promoted_file_path(
    bundle: Path,
    destination_path: str,
) -> Path:
    files_root = (
        bundle / PROMOTED_FILES_DIRECTORY
    )

    if (
        files_root.is_symlink()
        or not files_root.is_dir()
    ):
        raise BuilderPromotionVerificationError(
            "Builder promoted-files directory "
            "is missing or unsafe"
        )

    unresolved = files_root / destination_path

    if unresolved.is_symlink():
        raise BuilderPromotionVerificationError(
            "Builder promoted file cannot be a symlink"
        )

    try:
        promoted = unresolved.resolve(strict=True)
        resolved_files_root = (
            files_root.resolve(strict=True)
        )
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promoted file is unavailable"
        ) from exc

    if (
        resolved_files_root
        not in promoted.parents
        or not promoted.is_file()
    ):
        raise BuilderPromotionVerificationError(
            "Builder promoted file escaped its bundle"
        )

    return promoted


def verify_builder_promotion_bundle(
    promotion_directory: Path,
    *,
    promotion_root: Path,
    plan_file: Path,
    plan_root: Path,
) -> BuilderPromotionVerificationResult:
    """Independently verify one promoted bundle read-only."""

    _, bundle = _promotion_directory_path(
        promotion_directory,
        promotion_root=promotion_root,
    )
    manifest_file = _manifest_path(bundle)

    manifest, manifest_bytes_before = (
        _load_manifest(manifest_file)
    )

    plan = _load_plan(
        plan_file,
        plan_root=plan_root,
    )
    plan_digest = (
        builder_promotion_plan_sha256(plan)
    )

    _verify_manifest_against_plan(
        manifest,
        plan,
        promotion_plan_sha256=plan_digest,
    )
    _verify_directory_identity(
        bundle,
        manifest,
    )

    expected_files = _expected_bundle_files(
        manifest
    )
    actual_files_before = _actual_bundle_files(
        bundle
    )

    if actual_files_before != expected_files:
        raise BuilderPromotionVerificationError(
            "Builder promotion bundle file set "
            "does not match"
        )

    verified_paths: list[str] = []
    verified_digests: dict[str, str] = {}

    for item in manifest.files:
        promoted = _promoted_file_path(
            bundle,
            item.destination_path,
        )
        digest = _file_sha256(promoted)

        if digest != item.sha256:
            raise BuilderPromotionVerificationError(
                "Builder promoted file digest "
                "does not match"
            )

        verified_digests[
            item.destination_path
        ] = digest
        verified_paths.append(
            item.destination_path
        )

    actual_files_after = _actual_bundle_files(
        bundle
    )

    if actual_files_after != actual_files_before:
        raise BuilderPromotionVerificationError(
            "Builder promotion bundle changed "
            "during verification"
        )

    try:
        manifest_bytes_after = (
            manifest_file.read_bytes()
        )
    except OSError as exc:
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest could not "
            "be rechecked"
        ) from exc

    if (
        manifest_bytes_after
        != manifest_bytes_before
    ):
        raise BuilderPromotionVerificationError(
            "Builder promotion manifest changed "
            "during verification"
        )

    for item in manifest.files:
        promoted = _promoted_file_path(
            bundle,
            item.destination_path,
        )

        if (
            _file_sha256(promoted)
            != verified_digests[
                item.destination_path
            ]
        ):
            raise BuilderPromotionVerificationError(
                "Builder promoted file changed "
                "during verification"
            )

    return BuilderPromotionVerificationResult(
        task_id=manifest.task_id,
        decision_id=manifest.decision_id,
        promotion_plan_sha256=(
            manifest.promotion_plan_sha256
        ),
        candidate_tree_sha256=(
            manifest.candidate_tree_sha256
        ),
        promotion_directory=bundle.as_posix(),
        promotion_manifest=(
            manifest_file.as_posix()
        ),
        plan_file=Path(
            plan_file
        ).resolve().as_posix(),
        verified_paths=verified_paths,
    )
