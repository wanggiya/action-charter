"""Offline CLI tests for authoritative workflow release creation."""

import json
from datetime import datetime, timezone

from typer.testing import CliRunner

import geoagent_harness.releases as releases
from geoagent_harness.cli import app
from geoagent_harness.releases import (
    AuthoritativeReleaseStorageResult,
)
from tests.test_release_assessment_cli import incomplete_candidate
from tests.test_release_schemas import candidate_payload


runner = CliRunner()
NOW = datetime(2026, 9, 3, 9, tzinfo=timezone.utc)


def command() -> list[str]:
    return [
        "create-workflow-release",
        "release-cli-1",
        "task.json",
        "task.md",
        "record/CRITIC_RESULT.json",
        "task.events.jsonl",
        "--plan-file",
        "workflow.json",
        "--approval-file",
        "approval.json",
    ]


def test_cli_creates_ready_release(monkeypatch) -> None:
    candidate = releases.AuthoritativeReleaseCandidate.model_validate(
        candidate_payload()
    )

    def assess(**kwargs):
        assert kwargs["release_id"] == "release-cli-1"
        return candidate.model_copy(update={"release_id": "release-cli-1"})

    def persist(active_candidate, **kwargs):
        assert active_candidate.ready_for_release is True
        assert str(kwargs["release_root"]) == "releases"
        return AuthoritativeReleaseStorageResult(
            release_id="release-cli-1",
            subject_type="workflow",
            subject_id="workflow-test-1",
            candidate_sha256="a" * 64,
            release_sha256="b" * 64,
            release_directory="releases/release-cli-1.release",
            release_manifest=(
                "releases/release-cli-1.release/RELEASE.json"
            ),
            component_count=6,
        )

    monkeypatch.setattr(
        releases, "assess_workflow_release_candidate", assess
    )
    monkeypatch.setattr(
        releases, "persist_authoritative_release", persist
    )
    result = runner.invoke(app, command())

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["release_created"] is True
    assert payload["files_copied"] is True
    assert payload["execution_performed"] is False


def test_cli_refuses_non_ready_release(monkeypatch) -> None:
    monkeypatch.setattr(
        releases,
        "assess_workflow_release_candidate",
        lambda **kwargs: incomplete_candidate(),
    )
    result = runner.invoke(app, command())

    assert result.exit_code == 2
    assert "not ready for release" in result.output
