"""Tests for Builder candidate-test evidence storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderCandidateTestEvidenceError,
    BuilderCandidateTestRecord,
    load_builder_candidate_test_record,
)


def valid_record() -> BuilderCandidateTestRecord:
    return BuilderCandidateTestRecord(
        task_id="builder-evidence-test",
        generation_sha256="b" * 64,
        candidate_tree_sha256="a" * 64,
        candidate_tree_sha256_after="a" * 64,
        candidate_unchanged=True,
        pytest_exit_code=0,
        collected=1,
        passed_count=1,
        failed_count=0,
        skipped_count=0,
        error_count=0,
        passed=True,
    )


def write_record(root: Path) -> Path:
    path = root / "record.json"
    path.write_text(
        json.dumps(
            valid_record().model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_loads_valid_builder_test_record(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    path = write_record(root)

    loaded = load_builder_candidate_test_record(
        path,
        evidence_root=root,
    )

    assert loaded.passed is True
    assert loaded.network_available is False
    assert loaded.candidate_mount_read_only is True


def test_rejects_record_outside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        BuilderCandidateTestEvidenceError,
        match="escaped",
    ):
        load_builder_candidate_test_record(
            outside,
            evidence_root=root,
        )


def test_rejects_symlinked_record(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    target = write_record(root)
    link = root / "linked.json"
    link.symlink_to(target)

    with pytest.raises(
        BuilderCandidateTestEvidenceError,
        match="cannot be a symlink",
    ):
        load_builder_candidate_test_record(
            link,
            evidence_root=root,
        )


def test_rejects_invalid_record_schema(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    path = root / "record.json"
    path.write_text(
        '{"passed":true}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderCandidateTestEvidenceError,
        match="schema validation",
    ):
        load_builder_candidate_test_record(
            path,
            evidence_root=root,
        )
