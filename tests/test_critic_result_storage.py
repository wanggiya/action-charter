"""Tests for immutable Critic-result record storage."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.critic import (
    CriticResultStorageError,
    build_critic_result_record,
    critic_result_record_sha256,
    load_critic_result_record,
    persist_critic_result_record,
)
from tests.test_critic_result_records import critic_result


NOW = datetime(2026, 9, 3, 4, tzinfo=timezone.utc)


def record():
    return build_critic_result_record(
        result=critic_result(),
        recorded_at=NOW,
    )


def test_persists_and_loads_canonical_critic_record(
    tmp_path: Path,
) -> None:
    active_record = record()
    result = persist_critic_result_record(
        active_record,
        record_root=tmp_path,
    )

    assert result.critic_record_sha256 == (
        critic_result_record_sha256(active_record)
    )
    assert result.authoritative_status_changed is False
    assert result.release_created is False
    loaded = load_critic_result_record(
        Path(result.record_file),
        record_root=tmp_path,
    )
    assert loaded == active_record


def test_refuses_duplicate_critic_record(
    tmp_path: Path,
) -> None:
    active_record = record()
    persist_critic_result_record(active_record, record_root=tmp_path)

    with pytest.raises(
        CriticResultStorageError,
        match="already exists",
    ):
        persist_critic_result_record(
            active_record,
            record_root=tmp_path,
        )


def test_rejects_tampered_record(
    tmp_path: Path,
) -> None:
    result = persist_critic_result_record(
        record(),
        record_root=tmp_path,
    )
    path = Path(result.record_file)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["critic_result"]["workflow_warnings"].append("changed")
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CriticResultStorageError):
        load_critic_result_record(path, record_root=tmp_path)


def test_rejects_noncanonical_record(
    tmp_path: Path,
) -> None:
    result = persist_critic_result_record(
        record(),
        record_root=tmp_path,
    )
    path = Path(result.record_file)
    payload = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(
        CriticResultStorageError,
        match="not canonical",
    ):
        load_critic_result_record(path, record_root=tmp_path)


def test_rejects_unexpected_package_file(
    tmp_path: Path,
) -> None:
    result = persist_critic_result_record(
        record(),
        record_root=tmp_path,
    )
    path = Path(result.record_file)
    (path.parent / "unexpected.txt").write_text(
        "unexpected", encoding="utf-8"
    )

    with pytest.raises(
        CriticResultStorageError,
        match="unexpected files",
    ):
        load_critic_result_record(path, record_root=tmp_path)


def test_rejects_symlinked_record_root(
    tmp_path: Path,
) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(
        CriticResultStorageError,
        match="root cannot be a symlink",
    ):
        persist_critic_result_record(
            record(),
            record_root=linked_root,
        )


def test_rejects_record_outside_approved_root(
    tmp_path: Path,
) -> None:
    approved = tmp_path / "approved"
    result = persist_critic_result_record(
        record(),
        record_root=tmp_path / "outside",
    )
    approved.mkdir()

    with pytest.raises(
        CriticResultStorageError,
        match="escaped",
    ):
        load_critic_result_record(
            Path(result.record_file),
            record_root=approved,
        )
