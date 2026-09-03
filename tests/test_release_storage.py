"""Tests for immutable authoritative release storage."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.releases import (
    AuthoritativeReleaseCandidate,
    AuthoritativeReleaseStorageError,
    load_authoritative_release,
    persist_authoritative_release,
)


NOW = datetime(2026, 9, 3, 8, tzinfo=timezone.utc)


def ready_candidate(tmp_path: Path) -> AuthoritativeReleaseCandidate:
    definitions = [
        ("approval", "approval", "approvals/approval.json"),
        ("plan", "plan", "plans/workflow.json"),
        ("critic_result", "critic_result", "critic/CRITIC_RESULT.json"),
        ("report", "report", "reports/workflow.md"),
        ("trace", "trace", "traces/workflow.json"),
        (
            "operational_history",
            "operational_history",
            "operational-history/workflow.events.jsonl",
        ),
    ]
    components = []
    for component_id, kind, relative in definitions:
        content = f"authoritative {component_id} evidence\n".encode()
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        components.append(
            {
                "component_id": component_id,
                "kind": kind,
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        )
    return AuthoritativeReleaseCandidate(
        release_id="release-storage-1",
        subject_type="workflow",
        subject_id="workflow-storage-1",
        deterministic_status="validated_success",
        lifecycle_state="validated",
        components=components,
        approval_complete=True,
        validation_complete=True,
        critic_complete=True,
        evidence_complete=True,
        ready_for_release=True,
        violations=[],
        assessed_at=NOW,
    )


def test_persists_and_loads_atomic_release(tmp_path: Path) -> None:
    candidate = ready_candidate(tmp_path)
    result = persist_authoritative_release(
        candidate,
        project_root=tmp_path,
        release_root=tmp_path / "releases",
        released_at=NOW,
    )

    assert result.release_created is True
    assert result.files_copied is True
    assert result.component_count == 6
    assert result.registry_modified is False
    assert result.execution_performed is False
    manifest = load_authoritative_release(
        Path(result.release_manifest),
        release_root=tmp_path / "releases",
    )
    assert manifest.release_id == candidate.release_id
    assert manifest.files_copied is True
    assert (Path(result.release_directory) / "CANDIDATE.json").is_file()
    for component in candidate.components:
        copied = (
            Path(result.release_directory) / "files" / component.path
        )
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == (
            component.sha256
        )


def test_refuses_non_ready_candidate(tmp_path: Path) -> None:
    payload = ready_candidate(tmp_path).model_dump(mode="json")
    payload.update(
        deterministic_status="incomplete_evidence",
        lifecycle_state="candidate",
        approval_complete=False,
        evidence_complete=False,
        ready_for_release=False,
        violations=["approval is incomplete"],
    )
    candidate = AuthoritativeReleaseCandidate.model_validate(payload)

    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="not ready",
    ):
        persist_authoritative_release(
            candidate,
            project_root=tmp_path,
            release_root=tmp_path / "releases",
            released_at=NOW,
        )


def test_refuses_changed_component(tmp_path: Path) -> None:
    candidate = ready_candidate(tmp_path)
    (tmp_path / candidate.components[0].path).write_text(
        "changed\n", encoding="utf-8"
    )
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="does not match",
    ):
        persist_authoritative_release(
            candidate,
            project_root=tmp_path,
            release_root=tmp_path / "releases",
            released_at=NOW,
        )


def test_refuses_duplicate_release_id(tmp_path: Path) -> None:
    candidate = ready_candidate(tmp_path)
    release_root = tmp_path / "releases"
    persist_authoritative_release(
        candidate,
        project_root=tmp_path,
        release_root=release_root,
        released_at=NOW,
    )
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="ID already exists",
    ):
        persist_authoritative_release(
            candidate,
            project_root=tmp_path,
            release_root=release_root,
            released_at=NOW,
        )


def test_loader_rejects_tampered_component(tmp_path: Path) -> None:
    result = persist_authoritative_release(
        ready_candidate(tmp_path),
        project_root=tmp_path,
        release_root=tmp_path / "releases",
        released_at=NOW,
    )
    copied = next((Path(result.release_directory) / "files").rglob("*.md"))
    copied.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="digest",
    ):
        load_authoritative_release(
            Path(result.release_manifest),
            release_root=tmp_path / "releases",
        )


def test_loader_rejects_unexpected_file(tmp_path: Path) -> None:
    result = persist_authoritative_release(
        ready_candidate(tmp_path),
        project_root=tmp_path,
        release_root=tmp_path / "releases",
        released_at=NOW,
    )
    (Path(result.release_directory) / "unexpected.txt").write_text(
        "unexpected", encoding="utf-8"
    )
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="unexpected file set",
    ):
        load_authoritative_release(
            Path(result.release_manifest),
            release_root=tmp_path / "releases",
        )


def test_loader_rejects_tampered_candidate(tmp_path: Path) -> None:
    result = persist_authoritative_release(
        ready_candidate(tmp_path),
        project_root=tmp_path,
        release_root=tmp_path / "releases",
        released_at=NOW,
    )
    candidate_file = Path(result.release_directory) / "CANDIDATE.json"
    candidate_file.write_text("{}", encoding="utf-8")
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="candidate file failed validation",
    ):
        load_authoritative_release(
            Path(result.release_manifest),
            release_root=tmp_path / "releases",
        )


def test_refuses_symlinked_release_root(tmp_path: Path) -> None:
    real = tmp_path / "real-releases"
    real.mkdir()
    linked = tmp_path / "linked-releases"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(
        AuthoritativeReleaseStorageError,
        match="root cannot be a symlink",
    ):
        persist_authoritative_release(
            ready_candidate(tmp_path),
            project_root=tmp_path,
            release_root=linked,
            released_at=NOW,
        )
