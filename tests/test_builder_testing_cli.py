"""Offline CLI tests for Builder test assessment."""

from __future__ import annotations

import json

from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderCandidateTestAssessment,
    BuilderCandidateTestingError,
)
from geoagent_harness.cli import app


runner = CliRunner()


def successful_assessment(
) -> BuilderCandidateTestAssessment:
    return BuilderCandidateTestAssessment(
        task_id="builder-cli-assessment",
        generation_sha256="b" * 64,
        candidate_tree_sha256="a" * 64,
        candidate_path=(
            "/approved/candidates/example.candidate"
        ),
        test_record_path=(
            "/approved/evidence/example.json"
        ),
        collected=2,
        passed_count=2,
        failed_count=0,
        skipped_count=0,
        error_count=0,
    )


def test_cli_assesses_builder_test_evidence(
    monkeypatch,
) -> None:
    def assess(**kwargs):
        assert str(
            kwargs["candidate_path"]
        ) == "example.candidate"
        assert str(
            kwargs["test_record_path"]
        ) == "example.json"

        return successful_assessment()

    monkeypatch.setattr(
        builder,
        "assess_builder_candidate_tests",
        assess,
    )

    result = runner.invoke(
        app,
        [
            "assess-builder-candidate-tests",
            "example.candidate",
            "example.json",
            "--candidate-root",
            "builder-candidates",
            "--evidence-root",
            "builder-test-results",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["static_inspection_passed"] is True
    assert payload["isolated_tests_passed"] is True
    assert payload["digest_bound"] is True
    assert payload["tests_performed"] is True
    assert payload["implementation_executed"] is True
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_unacceptable_test_evidence(
    monkeypatch,
) -> None:
    def reject(**kwargs):
        raise BuilderCandidateTestingError(
            "Builder test evidence does not match "
            "the inspected candidate digest"
        )

    monkeypatch.setattr(
        builder,
        "assess_builder_candidate_tests",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "assess-builder-candidate-tests",
            "example.candidate",
            "example.json",
        ],
    )

    assert result.exit_code == 2
    assert (
        "does not match the inspected candidate digest"
        in result.output
    )
