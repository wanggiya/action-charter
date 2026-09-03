"""Offline CLI tests for authoritative-release inspection."""

import json

from typer.testing import CliRunner

import geoagent_harness.releases as releases
from geoagent_harness.cli import app
from geoagent_harness.releases import (
    AuthoritativeReleaseInspectionResult,
    AuthoritativeReleaseStorageError,
)


runner = CliRunner()


def inspection_result() -> AuthoritativeReleaseInspectionResult:
    return AuthoritativeReleaseInspectionResult(
        release_id="release-cli-1",
        subject_type="workflow",
        subject_id="workflow-cli-1",
        candidate_sha256="a" * 64,
        release_sha256="b" * 64,
        release_directory="releases/release-cli-1.release",
        release_manifest="releases/release-cli-1.release/RELEASE.json",
        component_count=6,
    )


def test_cli_inspects_release(monkeypatch) -> None:
    def inspect(manifest_file, **kwargs):
        assert str(manifest_file) == "release/RELEASE.json"
        assert str(kwargs["release_root"]) == "releases"
        return inspection_result()

    monkeypatch.setattr(
        releases, "inspect_authoritative_release", inspect
    )
    result = runner.invoke(
        app,
        ["inspect-authoritative-release", "release/RELEASE.json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["release_verified"] is True
    assert payload["files_modified"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_invalid_release(monkeypatch) -> None:
    def reject(*args, **kwargs):
        raise AuthoritativeReleaseStorageError(
            "release component digest is invalid"
        )

    monkeypatch.setattr(
        releases, "inspect_authoritative_release", reject
    )
    result = runner.invoke(
        app,
        ["inspect-authoritative-release", "release/RELEASE.json"],
    )

    assert result.exit_code == 2
    assert "component digest is invalid" in result.output
