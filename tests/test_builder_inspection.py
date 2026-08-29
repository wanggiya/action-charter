"""Tests for deterministic Builder candidate inspection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateInspectionError,
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    inspect_builder_candidate,
    materialize_builder_proposal,
)


def generation() -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id="builder-inspection-test",
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
        task_id="builder-inspection-test",
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


def prepared_candidate(
    tmp_path: Path,
) -> tuple[Path, Path]:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()

    generation_file = (
        generation_root / "generation.json"
    )
    generation_file.write_text(
        json.dumps(
            generation().model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_root = tmp_path / "candidates"

    result = materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=candidate_root,
    )

    return candidate_root, Path(result.candidate_path)


def test_inspects_exact_candidate_without_execution(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    result = inspect_builder_candidate(
        candidate_path=candidate,
        candidate_root=candidate_root,
    )

    assert result.passed is True
    assert result.candidate_tree_sha256 == (
        result.candidate_tree_sha256_after
    )
    assert result.checked_files == [
        "BUILDER_CANDIDATE.json",
        (
            "src/geoagent_harness/"
            "skill_adapters/example.py"
        ),
        "tests/test_example.py",
    ]
    assert result.syntax_checked_files == [
        (
            "src/geoagent_harness/"
            "skill_adapters/example.py"
        ),
        "tests/test_example.py",
    ]
    assert result.candidate_modified is False
    assert result.files_imported is False
    assert result.files_executed is False
    assert result.tests_performed is False
    assert result.validation_performed is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_changed_candidate_file_is_rejected(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    target = (
        candidate
        / "src"
        / "geoagent_harness"
        / "skill_adapters"
        / "example.py"
    )
    target.write_text(
        "raise RuntimeError('changed')\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderCandidateInspectionError,
        match="digest does not match",
    ):
        inspect_builder_candidate(
            candidate_path=candidate,
            candidate_root=candidate_root,
        )


def test_undeclared_file_is_rejected(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    (candidate / "unexpected.txt").write_text(
        "undeclared\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderCandidateInspectionError,
        match="file set does not match",
    ):
        inspect_builder_candidate(
            candidate_path=candidate,
            candidate_root=candidate_root,
        )


def test_invalid_python_syntax_is_rejected(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    target = candidate / "tests" / "test_example.py"
    target.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    manifest_path = (
        candidate / "BUILDER_CANDIDATE.json"
    )
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    import hashlib

    manifest["files"][1]["content_sha256"] = (
        hashlib.sha256(
            target.read_bytes()
        ).hexdigest()
    )
    manifest_path.write_text(
        json.dumps(
            manifest,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderCandidateInspectionError,
        match="invalid .py syntax",
    ):
        inspect_builder_candidate(
            candidate_path=candidate,
            candidate_root=candidate_root,
        )


def test_symlinked_file_is_rejected(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    target = candidate / "tests" / "test_example.py"
    target.unlink()
    target.symlink_to(
        candidate
        / "src"
        / "geoagent_harness"
        / "skill_adapters"
        / "example.py"
    )

    with pytest.raises(
        BuilderCandidateInspectionError,
        match="cannot contain symlinks",
    ):
        inspect_builder_candidate(
            candidate_path=candidate,
            candidate_root=candidate_root,
        )


def test_candidate_outside_root_is_rejected(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )
    other_root = tmp_path / "other-candidates"
    other_root.mkdir()

    with pytest.raises(
        BuilderCandidateInspectionError,
        match="directly beneath",
    ):
        inspect_builder_candidate(
            candidate_path=candidate,
            candidate_root=other_root,
        )
