"""Offline CLI tests for Builder review-package creation."""

from __future__ import annotations

import json

from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderReviewError,
    BuilderReviewStorageResult,
)
from geoagent_harness.cli import app


runner = CliRunner()


def storage_result(
) -> BuilderReviewStorageResult:
    return BuilderReviewStorageResult(
        task_id="builder-review-cli",
        generation_sha256="b" * 64,
        candidate_tree_sha256="a" * 64,
        review_package_sha256="c" * 64,
        review_directory=(
            "/approved/reviews/example.review"
        ),
        review_file=(
            "/approved/reviews/"
            "example.review/REVIEW.json"
        ),
    )


def test_cli_creates_review_package(
    monkeypatch,
) -> None:
    sentinel_review = object()

    def assemble(**kwargs):
        assert str(
            kwargs["generation_file"]
        ) == "generation.json"
        assert str(
            kwargs["candidate_path"]
        ) == "example.candidate"
        assert str(
            kwargs["test_record_path"]
        ) == "record.json"

        return sentinel_review

    def persist(review, **kwargs):
        assert review is sentinel_review
        assert str(
            kwargs["review_root"]
        ) == "builder-reviews"

        return storage_result()

    monkeypatch.setattr(
        builder,
        "assemble_builder_review_package",
        assemble,
    )
    monkeypatch.setattr(
        builder,
        "persist_builder_review_package",
        persist,
    )

    result = runner.invoke(
        app,
        [
            "create-builder-review-package",
            "generation.json",
            "example.candidate",
            "record.json",
            "--generation-root",
            "builder-generations",
            "--candidate-root",
            "builder-candidates",
            "--evidence-root",
            "builder-test-results",
            "--review-root",
            "builder-reviews",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["review_package_persisted"] is True
    assert payload["ready_for_human_review"] is True
    assert payload["human_review_performed"] is False
    assert payload["approval_granted"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_invalid_review_inputs(
    monkeypatch,
) -> None:
    def reject(**kwargs):
        raise BuilderReviewError(
            "Builder review inputs could not be verified"
        )

    monkeypatch.setattr(
        builder,
        "assemble_builder_review_package",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "create-builder-review-package",
            "generation.json",
            "example.candidate",
            "record.json",
        ],
    )

    assert result.exit_code == 2
    assert (
        "review inputs could not be verified"
        in result.output
    )
