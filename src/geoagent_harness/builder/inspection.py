"""Deterministic static inspection of Builder candidates."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from geoagent_harness.builder.schemas import (
    BuilderCandidateInspectionResult,
    BuilderCandidateManifest,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)


MANIFEST_NAME = "BUILDER_CANDIDATE.json"
MAX_MANIFEST_BYTES = 1_000_000


class BuilderCandidateInspectionError(RuntimeError):
    """Raised when a Builder candidate fails static inspection."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _resolve_candidate(
    candidate_path: Path,
    *,
    candidate_root: Path,
) -> tuple[Path, Path]:
    if candidate_root.is_symlink():
        raise BuilderCandidateInspectionError(
            "Builder candidate root cannot be a symlink"
        )

    try:
        root = candidate_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderCandidateInspectionError(
            "Builder candidate root must be a directory"
        )

    unresolved = (
        candidate_path
        if candidate_path.is_absolute()
        else root / candidate_path
    )

    if unresolved.is_symlink():
        raise BuilderCandidateInspectionError(
            "Builder candidate cannot be a symlink"
        )

    try:
        candidate = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate is unavailable"
        ) from exc

    if not candidate.is_dir():
        raise BuilderCandidateInspectionError(
            "Builder candidate must be a directory"
        )

    if candidate.parent != root:
        raise BuilderCandidateInspectionError(
            "Builder candidate must be directly beneath its root"
        )

    return root, candidate


def _reject_symlinks(candidate: Path) -> None:
    for directory, directory_names, file_names in os.walk(
        candidate,
        followlinks=False,
    ):
        current = Path(directory)

        for name in [*directory_names, *file_names]:
            path = current / name

            if path.is_symlink():
                raise BuilderCandidateInspectionError(
                    "Builder candidate cannot contain symlinks"
                )


def load_builder_candidate_manifest(
    candidate: Path,
) -> BuilderCandidateManifest:
    """Load the strict manifest from one inspected candidate."""
    manifest_path = candidate / MANIFEST_NAME

    if manifest_path.is_symlink():
        raise BuilderCandidateInspectionError(
            "Builder candidate manifest cannot be a symlink"
        )

    try:
        if not manifest_path.is_file():
            raise BuilderCandidateInspectionError(
                "Builder candidate manifest is missing"
            )

        content = manifest_path.read_bytes()
    except OSError as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate manifest is unavailable"
        ) from exc

    if len(content) > MAX_MANIFEST_BYTES:
        raise BuilderCandidateInspectionError(
            "Builder candidate manifest exceeds byte limit"
        )

    try:
        payload = json.loads(content)
        return BuilderCandidateManifest.model_validate(
            payload
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
        TypeError,
        ValueError,
    ) as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate manifest is invalid"
        ) from exc


def _relative_file_set(candidate: Path) -> set[str]:
    paths: set[str] = set()

    for path in candidate.rglob("*"):
        if path.is_symlink():
            raise BuilderCandidateInspectionError(
                "Builder candidate cannot contain symlinks"
            )

        if path.is_file():
            paths.add(
                path.relative_to(candidate).as_posix()
            )

    return paths


def _verify_manifest_identity(
    candidate: Path,
    manifest: BuilderCandidateManifest,
) -> None:
    expected_name = (
        f"{manifest.task_id}."
        f"{manifest.generation_sha256}.candidate"
    )

    if candidate.name != expected_name:
        raise BuilderCandidateInspectionError(
            "Builder candidate directory identity is invalid"
        )


def _verify_declared_files(
    candidate: Path,
    manifest: BuilderCandidateManifest,
) -> list[str]:
    declared = {
        file.path
        for file in manifest.files
    }
    expected = declared | {MANIFEST_NAME}
    actual = _relative_file_set(candidate)

    if actual != expected:
        raise BuilderCandidateInspectionError(
            "Builder candidate file set does not match manifest"
        )

    checked: list[str] = []

    for declared_file in manifest.files:
        path = candidate / declared_file.path

        try:
            content = path.read_bytes()
        except OSError as exc:
            raise BuilderCandidateInspectionError(
                "Builder candidate file is unavailable"
            ) from exc

        if (
            _sha256_bytes(content)
            != declared_file.content_sha256
        ):
            raise BuilderCandidateInspectionError(
                "Builder candidate file digest does not match "
                "manifest"
            )

        checked.append(declared_file.path)

    checked.append(MANIFEST_NAME)
    return sorted(checked)


def _check_supported_syntax(
    candidate: Path,
    manifest: BuilderCandidateManifest,
) -> list[str]:
    checked: list[str] = []

    for declared_file in manifest.files:
        path = candidate / declared_file.path
        suffix = path.suffix.lower()

        try:
            if suffix == ".py":
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=declared_file.path,
                )
            elif suffix == ".json":
                json.loads(
                    path.read_text(encoding="utf-8")
                )
            elif suffix in {".yaml", ".yml"}:
                yaml.safe_load(
                    path.read_text(encoding="utf-8")
                )
            else:
                continue
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            json.JSONDecodeError,
            yaml.YAMLError,
        ) as exc:
            raise BuilderCandidateInspectionError(
                "Builder candidate contains invalid "
                f"{suffix or 'unknown'} syntax"
            ) from exc

        checked.append(declared_file.path)

    return sorted(checked)


def inspect_builder_candidate(
    *,
    candidate_path: Path,
    candidate_root: Path,
) -> BuilderCandidateInspectionResult:
    """Inspect one candidate without importing or executing it."""

    _, candidate = _resolve_candidate(
        candidate_path,
        candidate_root=candidate_root,
    )

    _reject_symlinks(candidate)

    try:
        digest_before = candidate_tree_sha256(
            candidate
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate could not be hashed"
        ) from exc

    manifest = load_builder_candidate_manifest(
        candidate
    )

    _verify_manifest_identity(
        candidate,
        manifest,
    )

    checked_files = _verify_declared_files(
        candidate,
        manifest,
    )
    syntax_checked_files = _check_supported_syntax(
        candidate,
        manifest,
    )

    try:
        digest_after = candidate_tree_sha256(
            candidate
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuilderCandidateInspectionError(
            "Builder candidate could not be rehashed"
        ) from exc

    if digest_after != digest_before:
        raise BuilderCandidateInspectionError(
            "Builder candidate changed during inspection"
        )

    return BuilderCandidateInspectionResult(
        task_id=manifest.task_id,
        model=manifest.model,
        generation_sha256=(
            manifest.generation_sha256
        ),
        candidate_tree_sha256=digest_before,
        candidate_tree_sha256_after=digest_after,
        candidate_path=str(candidate),
        checked_files=checked_files,
        syntax_checked_files=syntax_checked_files,
        checks=[
            "candidate_contained",
            "candidate_not_symlinked",
            "manifest_schema_valid",
            "candidate_identity_valid",
            "declared_file_set_exact",
            "declared_file_digests_match",
            "supported_syntax_valid",
            "candidate_digest_stable",
        ],
    )
