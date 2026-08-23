"""Tests for candidate-test evidence storage."""

import json
from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    SkillCandidateTestEvidenceError,
    load_skill_candidate_test_record,
)


DIGEST = "a" * 64


def valid_payload() -> dict:
    return {
        "schema_version": "1.0",
        "skill_id": "inspect_raster",
        "candidate_tree_sha256": DIGEST,
        "candidate_tree_sha256_after": DIGEST,
        "candidate_unchanged": True,
        "pytest_exit_code": 0,
        "collected": 6,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "passed": True,
        "network_available": False,
        "candidate_mount_read_only": True,
        "tests_executed": True,
        "implementation_executed": True,
        "registry_modified": False,
        "promotion_performed": False,
    }


def test_loads_valid_candidate_test_record(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(valid_payload()),
        encoding="utf-8",
    )

    result = load_skill_candidate_test_record(
        path,
        evidence_root=tmp_path,
    )

    assert result.passed is True
    assert result.collected == 6
    assert result.registry_modified is False
    assert result.promotion_performed is False


def test_inconsistent_success_is_rejected(
    tmp_path: Path,
) -> None:
    payload = valid_payload()
    payload["failed_count"] = 1

    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        SkillCandidateTestEvidenceError,
        match="schema validation",
    ):
        load_skill_candidate_test_record(
            path,
            evidence_root=tmp_path,
        )


def test_record_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    outside = tmp_path / "outside.json"
    outside.write_text(
        json.dumps(valid_payload()),
        encoding="utf-8",
    )

    with pytest.raises(
        SkillCandidateTestEvidenceError,
        match="escaped",
    ):
        load_skill_candidate_test_record(
            outside,
            evidence_root=root,
        )

