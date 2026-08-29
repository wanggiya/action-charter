"""Tests for trusted Builder candidate materialization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderGenerationResult,
    BuilderMaterializationError,
    BuilderProposal,
    BuilderRequest,
    materialize_builder_proposal,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)


def generation() -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id="builder-materialization-test",
        summary="Propose one adapter and one test.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose the adapter.",
            },
            {
                "kind": "test",
                "path": "tests/test_example.py",
                "purpose": "Propose the test.",
            },
        ],
    )

    proposal = BuilderProposal(
        task_id="builder-materialization-test",
        summary="Proposed untrusted candidate files.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": (
                    '"""Untrusted adapter candidate."""\n'
                ),
            },
            {
                "kind": "test",
                "path": "tests/test_example.py",
                "content": (
                    "def test_example() -> None:\n"
                    "    assert True\n"
                ),
            },
        ],
    )

    return BuilderGenerationResult(
        model="builder-test-model",
        request=request,
        proposal=proposal,
    )


def write_generation(root: Path) -> Path:
    path = root / "generation.json"
    path.write_text(
        json.dumps(
            generation().model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_materializes_separate_untrusted_candidate(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )
    original = generation_file.read_bytes()

    result = materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=tmp_path / "candidates",
    )

    candidate = Path(result.candidate_path)

    assert candidate.is_dir()
    assert (
        candidate
        / "src"
        / "geoagent_harness"
        / "skill_adapters"
        / "example.py"
    ).is_file()
    assert (
        candidate / "tests" / "test_example.py"
    ).is_file()
    assert (
        candidate / "BUILDER_CANDIDATE.json"
    ).is_file()

    assert generation_file.read_bytes() == original
    assert result.source_generation_modified is False
    assert result.tests_performed is False
    assert result.validation_performed is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False
    assert result.candidate_tree_sha256 == (
        candidate_tree_sha256(candidate)
    )


def test_candidate_is_immutable(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )
    candidate_root = tmp_path / "candidates"

    materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=candidate_root,
    )

    with pytest.raises(
        BuilderMaterializationError,
        match="already exists",
    ):
        materialize_builder_proposal(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_root=candidate_root,
        )


def test_symlinked_candidate_root_is_rejected(
    tmp_path: Path,
) -> None:
    real_root = tmp_path / "real-candidates"
    real_root.mkdir()
    linked_root = tmp_path / "linked-candidates"
    linked_root.symlink_to(real_root)

    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )

    with pytest.raises(
        BuilderMaterializationError,
        match="root cannot be a symlink",
    ):
        materialize_builder_proposal(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_root=linked_root,
        )


def test_materialization_does_not_modify_source(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )

    before = generation_file.stat()

    materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=tmp_path / "candidates",
    )

    after = generation_file.stat()

    assert before.st_size == after.st_size
    assert before.st_mtime_ns == after.st_mtime_ns
