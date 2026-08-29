"""Trusted atomic materialization of Builder proposals."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from geoagent_harness.builder.schemas import (
    BuilderGenerationResult,
    BuilderMaterializationResult,
)
from geoagent_harness.builder.storage import (
    builder_generation_sha256,
    load_builder_generation,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)


class BuilderMaterializationError(RuntimeError):
    """Raised when Builder candidate creation is unsafe."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_generation_path(
    generation_file: Path,
    *,
    generation_root: Path,
) -> Path:
    root = generation_root.resolve(strict=True)

    candidate = (
        generation_file
        if generation_file.is_absolute()
        else root / generation_file
    )

    return candidate.resolve(strict=True)


def _candidate_root_path(candidate_root: Path) -> Path:
    if candidate_root.is_symlink():
        raise BuilderMaterializationError(
            "Builder candidate root cannot be a symlink"
        )

    try:
        candidate_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = candidate_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderMaterializationError(
            "Builder candidate root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderMaterializationError(
            "Builder candidate root must be a directory"
        )

    return root


def _contained_target(
    candidate: Path,
    relative_path: str,
) -> Path:
    target = (candidate / relative_path).resolve()

    if (
        target == candidate
        or candidate not in target.parents
    ):
        raise BuilderMaterializationError(
            "Builder candidate file escaped its bundle"
        )

    if target.is_symlink():
        raise BuilderMaterializationError(
            "Builder candidate file cannot be a symlink"
        )

    return target


def _write_new_text(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise BuilderMaterializationError(
            "Builder candidate file already exists"
        ) from exc


def _candidate_manifest(
    generation: BuilderGenerationResult,
    *,
    generation_digest: str,
) -> str:
    files = [
        {
            "kind": proposed.kind.value,
            "path": proposed.path,
            "content_sha256": _sha256_bytes(
                proposed.content.encode("utf-8")
            ),
        }
        for proposed in generation.proposal.files
    ]

    payload = {
        "schema_version": "1.0",
        "task_id": generation.request.task_id,
        "model": generation.model,
        "generation_sha256": generation_digest,
        "files": files,
        "candidate_materialized": True,
        "tests_performed": False,
        "validation_performed": False,
        "implementation_trusted": False,
        "promotion_performed": False,
        "execution_performed": False,
    }

    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def materialize_builder_proposal(
    *,
    generation_file: Path,
    generation_root: Path,
    candidate_root: Path,
) -> BuilderMaterializationResult:
    """Atomically create one isolated untrusted candidate."""

    try:
        generation = load_builder_generation(
            generation_file,
            generation_root=generation_root,
        )
        source = _source_generation_path(
            generation_file,
            generation_root=generation_root,
        )
        source_bytes_before = source.read_bytes()
    except (OSError, ValueError, RuntimeError) as exc:
        raise BuilderMaterializationError(
            "Builder generation could not be loaded"
        ) from exc

    source_digest = _sha256_bytes(
        source_bytes_before
    )
    generation_digest = (
        builder_generation_sha256(generation)
    )

    root = _candidate_root_path(candidate_root)

    candidate = (
        root
        / (
            f"{generation.request.task_id}."
            f"{generation_digest}.candidate"
        )
    )

    if candidate.exists() or candidate.is_symlink():
        raise BuilderMaterializationError(
            "Builder candidate already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-",
            dir=root,
        )
    )
    staged = temporary_root / "candidate"
    materialized: list[str] = []

    try:
        staged.mkdir()

        for proposed in generation.proposal.files:
            target = _contained_target(
                staged,
                proposed.path,
            )
            _write_new_text(
                target,
                proposed.content,
            )
            materialized.append(proposed.path)

        manifest_path = _contained_target(
            staged,
            "BUILDER_CANDIDATE.json",
        )
        _write_new_text(
            manifest_path,
            _candidate_manifest(
                generation,
                generation_digest=generation_digest,
            ),
        )
        materialized.append("BUILDER_CANDIDATE.json")

        staged_digest = candidate_tree_sha256(
            staged
        )

        if (
            _sha256_bytes(source.read_bytes())
            != source_digest
        ):
            raise BuilderMaterializationError(
                "Builder generation changed during "
                "materialization"
            )

        os.replace(staged, candidate)
        temporary_root.rmdir()

        final_digest = candidate_tree_sha256(
            candidate
        )

        if final_digest != staged_digest:
            shutil.rmtree(
                candidate,
                ignore_errors=True,
            )
            raise BuilderMaterializationError(
                "Builder candidate digest changed "
                "during finalization"
            )
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
            BuilderMaterializationError,
        ):
            raise

        raise BuilderMaterializationError(
            "Builder candidate could not be materialized"
        ) from exc

    return BuilderMaterializationResult(
        task_id=generation.request.task_id,
        model=generation.model,
        generation_sha256=generation_digest,
        source_file_sha256=source_digest,
        candidate_tree_sha256=final_digest,
        source_generation_path=str(source),
        candidate_path=str(candidate),
        materialized_files=sorted(materialized),
    )
