"""Tests for the shared failure taxonomy."""

from __future__ import annotations

import pytest

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    exit_code_for_category,
    failure_from_exception,
)


@pytest.mark.parametrize(
    ("category", "exit_code"),
    [
        (FailureCategory.INVALID_INPUT, 2),
        (FailureCategory.CONFIGURATION, 2),
        (FailureCategory.POLICY_DENIED, 2),
        (FailureCategory.APPROVAL_REJECTED, 2),
        (FailureCategory.NOT_FOUND, 2),
        (FailureCategory.CONFLICT, 2),
        (FailureCategory.TIMEOUT, 3),
        (FailureCategory.DEPENDENCY_UNAVAILABLE, 3),
        (FailureCategory.EXTERNAL_RESPONSE_INVALID, 4),
        (FailureCategory.EXECUTION_FAILED, 4),
        (FailureCategory.VALIDATION_FAILED, 1),
        (FailureCategory.CANCELLED, 130),
        (FailureCategory.INTERNAL_ERROR, 5),
    ],
)
def test_exit_code_policy(
    category: FailureCategory,
    exit_code: int,
) -> None:
    assert exit_code_for_category(category) == exit_code


def test_converts_typed_error_to_failure_record() -> None:
    error = GeoAgentError(
        "Internal MCP service is unavailable",
        code="mcp_unavailable",
        category=(
            FailureCategory.DEPENDENCY_UNAVAILABLE
        ),
        retry=RetryDisposition.SAFE_READ_ONLY,
    )

    failure = failure_from_exception(
        error,
        stage=FailureStage.MCP,
    )

    assert (
        failure.category
        == FailureCategory.DEPENDENCY_UNAVAILABLE
    )
    assert failure.code == "mcp_unavailable"
    assert failure.stage == FailureStage.MCP
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )
    assert failure.exit_code == 3
    assert failure.cause_type == "GeoAgentError"
    assert failure.secrets_redacted is True


def test_redacts_secret_from_failure_message() -> None:
    error = GeoAgentError(
        "POSTGRES_PASSWORD=do-not-expose",
        code="database_connection_failed",
        category=(
            FailureCategory.DEPENDENCY_UNAVAILABLE
        ),
        retry=RetryDisposition.MANUAL_REVIEW,
    )

    failure = failure_from_exception(
        error,
        stage=FailureStage.EXECUTION,
    )

    assert "do-not-expose" not in failure.message
    assert "POSTGRES_PASSWORD=[REDACTED]" in (
        failure.message
    )


def test_unclassified_error_fails_closed() -> None:
    failure = failure_from_exception(
        RuntimeError("unexpected failure"),
        stage=FailureStage.EXECUTION,
    )

    assert (
        failure.category
        == FailureCategory.INTERNAL_ERROR
    )
    assert failure.code == "unclassified_internal_error"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 5


def test_empty_error_message_is_replaced() -> None:
    failure = failure_from_exception(
        RuntimeError(),
        stage=FailureStage.REPORTING,
    )

    assert failure.message == (
        "Operation failed without an error message"
    )


def test_failure_record_is_json_serializable() -> None:
    error = GeoAgentError(
        "Shared model request timed out",
        code="model_timeout",
        category=FailureCategory.TIMEOUT,
        retry=RetryDisposition.SAFE_READ_ONLY,
    )

    failure = failure_from_exception(
        error,
        stage=FailureStage.MODEL,
    )

    payload = failure.model_dump(mode="json")

    assert payload == {
        "schema_version": "1.0",
        "category": "timeout",
        "code": "model_timeout",
        "stage": "model",
        "message": "Shared model request timed out",
        "retry": "safe_read_only",
        "exit_code": 3,
        "cause_type": "GeoAgentError",
        "secrets_redacted": True,
    }


def test_database_write_retry_requires_manual_review() -> None:
    error = GeoAgentError(
        "PostGIS execution was interrupted",
        code="postgis_execution_interrupted",
        category=FailureCategory.EXECUTION_FAILED,
        retry=RetryDisposition.MANUAL_REVIEW,
    )

    failure = failure_from_exception(
        error,
        stage=FailureStage.EXECUTION,
    )

    assert failure.retry == RetryDisposition.MANUAL_REVIEW
    assert failure.retry != (
        RetryDisposition.SAFE_READ_ONLY
    )