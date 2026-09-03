"""Offline CLI tests for workflow release assessment."""

import json
from datetime import datetime, timezone

from typer.testing import CliRunner

import geoagent_harness.releases as releases
from geoagent_harness.cli import app
from geoagent_harness.releases import (
    AuthoritativeReleaseCandidate,
    ReleaseAssessmentError,
)
from tests.test_release_schemas import components


runner = CliRunner()
NOW = datetime(2026, 9, 3, 7, tzinfo=timezone.utc)


def incomplete_candidate() -> AuthoritativeReleaseCandidate:
    return AuthoritativeReleaseCandidate(
        release_id="release-cli-1",
        subject_type="workflow",
        subject_id="workflow-cli-1",
        deterministic_status="incomplete_evidence",
        lifecycle_state="candidate",
        components=components(),
        approval_complete=False,
        validation_complete=True,
        critic_complete=True,
        evidence_complete=False,
        ready_for_release=False,
        violations=["approval evidence is incomplete"],
        assessed_at=NOW,
    )


def test_cli_reports_non_ready_candidate(monkeypatch) -> None:
    def assess(**kwargs):
        assert kwargs["release_id"] == "release-cli-1"
        assert str(kwargs["trace_file"]) == "task.json"
        assert str(kwargs["critic_record_file"]) == (
            "record/CRITIC_RESULT.json"
        )
        assert kwargs["plan_file"] is None
        assert kwargs["approval_file"] is None
        return incomplete_candidate()

    monkeypatch.setattr(
        releases,
        "assess_workflow_release_candidate",
        assess,
    )

    result = runner.invoke(
        app,
        [
            "assess-workflow-release",
            "release-cli-1",
            "task.json",
            "task.md",
            "record/CRITIC_RESULT.json",
            "task.events.jsonl",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert len(payload["candidate_sha256"]) == 64
    assert payload["candidate"]["lifecycle_state"] == "candidate"
    assert payload["candidate"]["ready_for_release"] is False
    assert payload["candidate"]["release_created"] is False


def test_cli_reports_unverifiable_release_evidence(
    monkeypatch,
) -> None:
    def reject(**kwargs):
        raise ReleaseAssessmentError(
            "release evidence could not be verified"
        )

    monkeypatch.setattr(
        releases,
        "assess_workflow_release_candidate",
        reject,
    )
    result = runner.invoke(
        app,
        [
            "assess-workflow-release",
            "release-cli-1",
            "task.json",
            "task.md",
            "record/CRITIC_RESULT.json",
            "task.events.jsonl",
        ],
    )

    assert result.exit_code == 2
    assert "could not be verified" in result.output
