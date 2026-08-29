"""Offline CLI tests for Builder human decisions."""

from __future__ import annotations

import json
from datetime import datetime

from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderReviewDecisionStorageResult,
)
from geoagent_harness.cli import app


runner = CliRunner()


def persisted_result(
) -> BuilderReviewDecisionStorageResult:
    return BuilderReviewDecisionStorageResult(
        decision_id="decision-cli-001",
        task_id="builder-review-cli",
        decision="approved",
        review_package_sha256="a" * 64,
        decision_sha256="b" * 64,
        decision_directory=(
            "/approved/decisions/example.decision"
        ),
        decision_file=(
            "/approved/decisions/"
            "example.decision/DECISION.json"
        ),
        approval_granted=True,
        promotion_planning_authorized=True,
    )


def test_cli_records_approved_decision(
    monkeypatch,
) -> None:
    sentinel_decision = object()

    def create(**kwargs):
        assert kwargs["decision"] == "approved"
        assert kwargs["reviewer_id"] == (
            "operator@example.com"
        )
        assert kwargs["approved_paths"] == [
            (
                "src/geoagent_harness/"
                "skill_adapters/example.py"
            ),
        ]
        assert isinstance(
            kwargs["decided_at"],
            datetime,
        )
        assert (
            kwargs["decided_at"].tzinfo
            is not None
        )

        return sentinel_decision

    def persist(decision, **kwargs):
        assert decision is sentinel_decision
        assert str(
            kwargs["decision_root"]
        ) == "builder-decisions"

        return persisted_result()

    monkeypatch.setattr(
        builder,
        "create_builder_review_decision",
        create,
    )
    monkeypatch.setattr(
        builder,
        "persist_builder_review_decision",
        persist,
    )

    result = runner.invoke(
        app,
        [
            "record-builder-review-decision",
            "example.review/REVIEW.json",
            "--decision-id",
            "decision-cli-001",
            "--reviewer-id",
            "operator@example.com",
            "--decided-at",
            "2026-08-29T18:30:00-04:00",
            "--decision",
            "approved",
            "--rationale",
            "Reviewed exact candidate and evidence.",
            "--approved-path",
            (
                "src/geoagent_harness/"
                "skill_adapters/example.py"
            ),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["decision_persisted"] is True
    assert payload["human_review_performed"] is True
    assert payload["approval_granted"] is True
    assert (
        payload["promotion_planning_authorized"]
        is True
    )
    assert payload["files_copied"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_unknown_decision(
    monkeypatch,
) -> None:
    result = runner.invoke(
        app,
        [
            "record-builder-review-decision",
            "example.review/REVIEW.json",
            "--decision-id",
            "decision-cli-002",
            "--reviewer-id",
            "operator@example.com",
            "--decided-at",
            "2026-08-29T18:30:00-04:00",
            "--decision",
            "maybe",
            "--rationale",
            "Invalid decision.",
        ],
    )

    assert result.exit_code == 2
    assert (
        "decision must be approved or rejected"
        in result.output
    )


def test_cli_rejects_invalid_timestamp(
    monkeypatch,
) -> None:
    result = runner.invoke(
        app,
        [
            "record-builder-review-decision",
            "example.review/REVIEW.json",
            "--decision-id",
            "decision-cli-003",
            "--reviewer-id",
            "operator@example.com",
            "--decided-at",
            "not-a-timestamp",
            "--decision",
            "rejected",
            "--rationale",
            "Invalid timestamp.",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid isoformat string" in result.output
