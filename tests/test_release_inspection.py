"""Tests for independent authoritative-release inspection."""

from pathlib import Path

from geoagent_harness.releases import (
    inspect_authoritative_release,
    persist_authoritative_release,
)
from tests.test_release_storage import NOW, ready_candidate


def test_inspects_verified_immutable_release(tmp_path: Path) -> None:
    stored = persist_authoritative_release(
        ready_candidate(tmp_path),
        project_root=tmp_path,
        release_root=tmp_path / "releases",
        released_at=NOW,
    )
    result = inspect_authoritative_release(
        Path(stored.release_manifest),
        release_root=tmp_path / "releases",
    )

    assert result.release_sha256 == stored.release_sha256
    assert result.candidate_sha256 == stored.candidate_sha256
    assert result.component_count == 6
    assert result.manifest_canonical is True
    assert result.directory_identity_verified is True
    assert result.candidate_verified is True
    assert result.exact_file_set_verified is True
    assert result.component_digests_verified is True
    assert result.release_verified is True
    assert result.files_modified is False
    assert result.registry_modified is False
    assert result.execution_performed is False
