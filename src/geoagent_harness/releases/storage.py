"""Atomic immutable storage for authoritative release packages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.redaction import redact_value
from geoagent_harness.releases.assessment import (
    authoritative_release_candidate_sha256,
    canonical_authoritative_release_candidate_json,
)
from geoagent_harness.releases.schemas import (
    AuthoritativeReleaseCandidate,
    AuthoritativeReleaseInspectionResult,
    AuthoritativeReleaseManifest,
    AuthoritativeReleaseStorageResult,
    ReleaseLifecycleState,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    SchemaVersionError,
    require_supported_schema,
)


RELEASE_FILE_NAME = "RELEASE.json"
RELEASE_CANDIDATE_FILE_NAME = "CANDIDATE.json"
RELEASE_FILES_DIRECTORY = "files"
MAX_RELEASE_MANIFEST_BYTES = 1_000_000
MAX_RELEASE_COMPONENT_BYTES = 100_000_000
MAX_RELEASE_TOTAL_BYTES = 500_000_000


class AuthoritativeReleaseStorageError(RuntimeError):
    """Raised when an authoritative release cannot be stored safely."""


def canonical_authoritative_release_manifest_json(
    manifest: AuthoritativeReleaseManifest,
) -> str:
    """Return the canonical persisted release-manifest representation."""

    original = manifest.model_dump(mode="json")
    if redact_value(original) != original:
        raise AuthoritativeReleaseStorageError(
            "release manifest contains content requiring redaction"
        )
    return (
        json.dumps(
            original,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def authoritative_release_manifest_sha256(
    manifest: AuthoritativeReleaseManifest,
) -> str:
    """Digest the exact canonical persisted manifest."""

    return hashlib.sha256(
        canonical_authoritative_release_manifest_json(manifest).encode(
            "utf-8"
        )
    ).hexdigest()


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_RELEASE_COMPONENT_BYTES:
                    raise AuthoritativeReleaseStorageError(
                        "release component exceeds its size limit"
                    )
                digest.update(chunk)
    except OSError as exc:
        raise AuthoritativeReleaseStorageError(
            "release component could not be read"
        ) from exc
    return digest.hexdigest(), size


def _root(path: Path, *, create: bool, label: str) -> Path:
    if path.is_symlink():
        raise AuthoritativeReleaseStorageError(
            f"{label} root cannot be a symlink"
        )
    try:
        if create:
            path.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AuthoritativeReleaseStorageError(
            f"{label} root is unavailable"
        ) from exc
    if not resolved.is_dir():
        raise AuthoritativeReleaseStorageError(
            f"{label} root must be a directory"
        )
    return resolved


def _reject_symlink_parts(path: Path, root: Path) -> None:
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoritativeReleaseStorageError(
                "release component path cannot contain a symlink"
            )


def _source_file(path: str, *, project_root: Path) -> Path:
    candidate = project_root / path
    try:
        _reject_symlink_parts(candidate, project_root)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(project_root)
    except (OSError, ValueError) as exc:
        if isinstance(exc, AuthoritativeReleaseStorageError):
            raise
        raise AuthoritativeReleaseStorageError(
            "release component escaped the project root"
        ) from exc
    if not resolved.is_file():
        raise AuthoritativeReleaseStorageError(
            "release component must be a regular file"
        )
    return resolved


def _verify_candidate_sources(
    candidate: AuthoritativeReleaseCandidate,
    *,
    project_root: Path,
) -> list[tuple[Path, str, int]]:
    if (
        not candidate.ready_for_release
        or not candidate.evidence_complete
        or candidate.lifecycle_state != ReleaseLifecycleState.VALIDATED
        or candidate.violations
    ):
        raise AuthoritativeReleaseStorageError(
            "release candidate is not ready for release"
        )

    verified: list[tuple[Path, str, int]] = []
    total = 0
    for component in candidate.components:
        source = _source_file(
            component.path,
            project_root=project_root,
        )
        digest, size = _hash_file(source)
        if digest != component.sha256 or size != component.size_bytes:
            raise AuthoritativeReleaseStorageError(
                "release component does not match its candidate"
            )
        total += size
        if total > MAX_RELEASE_TOTAL_BYTES:
            raise AuthoritativeReleaseStorageError(
                "release components exceed the total size limit"
            )
        verified.append((source, digest, size))
    return verified


def persist_authoritative_release(
    candidate: AuthoritativeReleaseCandidate,
    *,
    project_root: Path,
    release_root: Path,
    released_at: datetime,
) -> AuthoritativeReleaseStorageResult:
    """Copy one verified candidate into a write-once atomic package."""

    safe_project_root = _root(
        project_root,
        create=False,
        label="project",
    )
    sources = _verify_candidate_sources(
        candidate,
        project_root=safe_project_root,
    )
    candidate_sha256 = authoritative_release_candidate_sha256(candidate)
    candidate_content = canonical_authoritative_release_candidate_json(
        candidate
    )
    manifest = AuthoritativeReleaseManifest(
        release_id=candidate.release_id,
        subject_type=candidate.subject_type,
        subject_id=candidate.subject_id,
        candidate_sha256=candidate_sha256,
        components=candidate.components,
        released_at=released_at,
    )
    manifest_content = canonical_authoritative_release_manifest_json(
        manifest
    )
    release_sha256 = hashlib.sha256(
        manifest_content.encode("utf-8")
    ).hexdigest()
    safe_release_root = _root(
        release_root,
        create=True,
        label="release",
    )
    if any(
        safe_release_root.glob(f"{candidate.release_id}.*.release")
    ):
        raise AuthoritativeReleaseStorageError(
            "authoritative release ID already exists"
        )
    final_directory = safe_release_root / (
        f"{candidate.release_id}.{release_sha256}.release"
    )
    if final_directory.exists() or final_directory.is_symlink():
        raise AuthoritativeReleaseStorageError(
            "authoritative release package already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(prefix=".geoagent-release-", dir=safe_release_root)
    )
    staged = temporary_root / "release"
    try:
        staged.mkdir()
        staged_files = staged / RELEASE_FILES_DIRECTORY
        staged_files.mkdir()
        for component, (source, expected_digest, expected_size) in zip(
            candidate.components,
            sources,
            strict=True,
        ):
            destination = staged_files / component.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as source_stream, destination.open(
                "xb"
            ) as destination_stream:
                shutil.copyfileobj(source_stream, destination_stream)
                destination_stream.flush()
                os.fsync(destination_stream.fileno())
            staged_digest, staged_size = _hash_file(destination)
            source_digest_after, source_size_after = _hash_file(source)
            if (
                staged_digest != expected_digest
                or staged_size != expected_size
                or source_digest_after != expected_digest
                or source_size_after != expected_size
            ):
                raise AuthoritativeReleaseStorageError(
                    "release component changed during staging"
                )

        candidate_file = staged / RELEASE_CANDIDATE_FILE_NAME
        with candidate_file.open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(candidate_content)
            stream.flush()
            os.fsync(stream.fileno())
        if _hash_file(candidate_file)[0] != candidate_sha256:
            raise AuthoritativeReleaseStorageError(
                "staged release candidate digest is inconsistent"
            )

        manifest_file = staged / RELEASE_FILE_NAME
        with manifest_file.open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(manifest_content)
            stream.flush()
            os.fsync(stream.fileno())
        if _hash_file(manifest_file)[0] != release_sha256:
            raise AuthoritativeReleaseStorageError(
                "staged release manifest digest is inconsistent"
            )

        # Reverify all authoritative sources immediately before finalization.
        _verify_candidate_sources(
            candidate,
            project_root=safe_project_root,
        )
        os.replace(staged, final_directory)
        temporary_root.rmdir()
    except (OSError, RuntimeError, ValueError) as exc:
        shutil.rmtree(temporary_root, ignore_errors=True)
        if isinstance(exc, AuthoritativeReleaseStorageError):
            raise
        raise AuthoritativeReleaseStorageError(
            "authoritative release package could not be persisted"
        ) from exc

    final_manifest = final_directory / RELEASE_FILE_NAME
    loaded = load_authoritative_release(
        final_manifest,
        release_root=safe_release_root,
    )
    if loaded != manifest:
        raise AuthoritativeReleaseStorageError(
            "persisted release manifest changed"
        )
    return AuthoritativeReleaseStorageResult(
        release_id=manifest.release_id,
        subject_type=manifest.subject_type,
        subject_id=manifest.subject_id,
        candidate_sha256=candidate_sha256,
        release_sha256=release_sha256,
        release_directory=final_directory.as_posix(),
        release_manifest=final_manifest.as_posix(),
        component_count=len(manifest.components),
    )


def load_authoritative_release(
    manifest_file: Path,
    *,
    release_root: Path,
) -> AuthoritativeReleaseManifest:
    """Securely load and independently verify one release package."""

    root = _root(release_root, create=False, label="release")
    candidate = (
        manifest_file if manifest_file.is_absolute() else root / manifest_file
    )
    if candidate.is_symlink() or candidate.parent.is_symlink():
        raise AuthoritativeReleaseStorageError(
            "release package path cannot contain a symlink"
        )
    try:
        safe_manifest = candidate.resolve(strict=True)
        directory = safe_manifest.parent
        if directory.parent != root:
            raise ValueError
    except (OSError, ValueError) as exc:
        raise AuthoritativeReleaseStorageError(
            "release manifest escaped its approved package"
        ) from exc
    if safe_manifest.name != RELEASE_FILE_NAME or not safe_manifest.is_file():
        raise AuthoritativeReleaseStorageError(
            "release manifest path is invalid"
        )
    try:
        size = safe_manifest.stat().st_size
        raw = safe_manifest.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuthoritativeReleaseStorageError(
            "release manifest could not be read"
        ) from exc
    if size < 1 or size > MAX_RELEASE_MANIFEST_BYTES:
        raise AuthoritativeReleaseStorageError(
            "release manifest has an invalid size"
        )
    try:
        payload: Any = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError
        require_supported_schema(
            payload,
            artifact_type=ArtifactType.AUTHORITATIVE_RELEASE_MANIFEST,
        )
        manifest = AuthoritativeReleaseManifest.model_validate(payload)
    except (
        json.JSONDecodeError,
        SchemaVersionError,
        ValidationError,
        ValueError,
    ) as exc:
        raise AuthoritativeReleaseStorageError(
            "release manifest failed schema validation"
        ) from exc
    canonical = canonical_authoritative_release_manifest_json(manifest)
    if raw != canonical:
        raise AuthoritativeReleaseStorageError(
            "release manifest is not canonical"
        )
    release_sha256 = authoritative_release_manifest_sha256(manifest)
    if directory.name != (
        f"{manifest.release_id}.{release_sha256}.release"
    ):
        raise AuthoritativeReleaseStorageError(
            "release directory identity is invalid"
        )

    candidate_file = directory / RELEASE_CANDIDATE_FILE_NAME
    if candidate_file.is_symlink() or not candidate_file.is_file():
        raise AuthoritativeReleaseStorageError(
            "release candidate file is invalid"
        )
    try:
        candidate_size = candidate_file.stat().st_size
        if candidate_size < 1 or candidate_size > MAX_RELEASE_MANIFEST_BYTES:
            raise AuthoritativeReleaseStorageError(
                "release candidate file has an invalid size"
            )
        candidate_raw = candidate_file.read_text(encoding="utf-8")
        candidate_payload: Any = json.loads(candidate_raw)
        if not isinstance(candidate_payload, dict):
            raise ValueError
        require_supported_schema(
            candidate_payload,
            artifact_type=ArtifactType.AUTHORITATIVE_RELEASE_CANDIDATE,
        )
        stored_candidate = AuthoritativeReleaseCandidate.model_validate(
            candidate_payload
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        SchemaVersionError,
        ValidationError,
        ValueError,
    ) as exc:
        raise AuthoritativeReleaseStorageError(
            "release candidate file failed validation"
        ) from exc
    candidate_canonical = canonical_authoritative_release_candidate_json(
        stored_candidate
    )
    if candidate_raw != candidate_canonical:
        raise AuthoritativeReleaseStorageError(
            "release candidate file is not canonical"
        )
    if (
        hashlib.sha256(candidate_raw.encode("utf-8")).hexdigest()
        != manifest.candidate_sha256
        or not stored_candidate.ready_for_release
        or stored_candidate.lifecycle_state
        != ReleaseLifecycleState.VALIDATED
        or stored_candidate.release_id != manifest.release_id
        or stored_candidate.subject_type != manifest.subject_type
        or stored_candidate.subject_id != manifest.subject_id
        or stored_candidate.components != manifest.components
    ):
        raise AuthoritativeReleaseStorageError(
            "release candidate does not match its manifest"
        )

    expected = {
        RELEASE_FILE_NAME,
        RELEASE_CANDIDATE_FILE_NAME,
        RELEASE_FILES_DIRECTORY,
    }
    total = 0
    files_root = directory / RELEASE_FILES_DIRECTORY
    if files_root.is_symlink() or not files_root.is_dir():
        raise AuthoritativeReleaseStorageError(
            "release files directory is invalid"
        )
    for component in manifest.components:
        path = files_root / component.path
        try:
            _reject_symlink_parts(path, directory)
            safe_path = path.resolve(strict=True)
            safe_path.relative_to(files_root)
        except (OSError, ValueError) as exc:
            if isinstance(exc, AuthoritativeReleaseStorageError):
                raise
            raise AuthoritativeReleaseStorageError(
                "release component escaped its package"
            ) from exc
        if not safe_path.is_file():
            raise AuthoritativeReleaseStorageError(
                "release component is unavailable"
            )
        digest, component_size = _hash_file(safe_path)
        digest_after, size_after = _hash_file(safe_path)
        if (
            digest != component.sha256
            or digest_after != component.sha256
            or component_size != component.size_bytes
            or size_after != component.size_bytes
        ):
            raise AuthoritativeReleaseStorageError(
                "release component digest is invalid"
            )
        total += component_size
        if total > MAX_RELEASE_TOTAL_BYTES:
            raise AuthoritativeReleaseStorageError(
                "release components exceed the total size limit"
            )
        relative_component = (
            Path(RELEASE_FILES_DIRECTORY) / component.path
        )
        expected.add(relative_component.as_posix())
        expected.update(
            parent.as_posix()
            for parent in relative_component.parents
            if parent.as_posix() != "."
        )

    actual: set[str] = set()
    try:
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise AuthoritativeReleaseStorageError(
                    "release package cannot contain symlinks"
                )
            actual.add(path.relative_to(directory).as_posix())
    except OSError as exc:
        raise AuthoritativeReleaseStorageError(
            "release package file set could not be verified"
        ) from exc
    if actual != expected:
        raise AuthoritativeReleaseStorageError(
            "release package contains an unexpected file set"
        )
    try:
        if safe_manifest.read_text(encoding="utf-8") != raw:
            raise AuthoritativeReleaseStorageError(
                "release manifest changed during verification"
            )
    except (OSError, UnicodeError) as exc:
        raise AuthoritativeReleaseStorageError(
            "release manifest could not be reverified"
        ) from exc
    try:
        if candidate_file.read_text(encoding="utf-8") != candidate_raw:
            raise AuthoritativeReleaseStorageError(
                "release candidate changed during verification"
            )
    except (OSError, UnicodeError) as exc:
        raise AuthoritativeReleaseStorageError(
            "release candidate could not be reverified"
        ) from exc
    return manifest


def inspect_authoritative_release(
    manifest_file: Path,
    *,
    release_root: Path,
) -> AuthoritativeReleaseInspectionResult:
    """Independently verify and summarize one immutable release."""

    manifest = load_authoritative_release(
        manifest_file,
        release_root=release_root,
    )
    root = _root(release_root, create=False, label="release")
    candidate = manifest_file if manifest_file.is_absolute() else (
        root / manifest_file
    )
    safe_manifest = candidate.resolve(strict=True)
    return AuthoritativeReleaseInspectionResult(
        release_id=manifest.release_id,
        subject_type=manifest.subject_type,
        subject_id=manifest.subject_id,
        candidate_sha256=manifest.candidate_sha256,
        release_sha256=authoritative_release_manifest_sha256(manifest),
        release_directory=safe_manifest.parent.as_posix(),
        release_manifest=safe_manifest.as_posix(),
        component_count=len(manifest.components),
    )
