"""Tests for structured failure evidence in traces."""

from datetime import datetime, timezone

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.reporting import render_report
from geoagent_harness.trace import (
    TraceTimestamps,
    WorkflowTrace,
)


def make_trace(
    *,
    failure=None,
    final_status="execution_failed",
) -> WorkflowTrace:
    now = datetime.now(timezone.utc)

    return WorkflowTrace(
        task_id="failure-trace-test",
        original_request="Test failure evidence.",
        context_references=[
            "context/PROJECT_SUMMARY.md",
        ],
        selected_skills=[
            "inspect_vector",
        ],
        tool_arguments={},
        tool_results={},
        validation_results=None,
        failure=failure,
        artifacts=[],
        warnings=[],
        final_status=final_status,
        human_corrections=[],
        timestamps=TraceTimestamps(
            started_at=now,
            finished_at=now,
        ),
        versions={
            "python": "test",
        },
    )


def test_successful_trace_has_no_failure() -> None:
    trace = make_trace(
        failure=None,
        final_status="validated_success",
    )

    payload = trace.model_dump(mode="json")

    assert payload["failure"] is None


def test_trace_contains_structured_failure() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "PostGIS operation failed",
            code="postgis_operation_failed",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.EXECUTION,
    )

    trace = make_trace(failure=failure)
    payload = trace.model_dump(mode="json")

    assert payload["failure"]["category"] == (
        "execution_failed"
    )
    assert payload["failure"]["code"] == (
        "postgis_operation_failed"
    )
    assert payload["failure"]["stage"] == "execution"
    assert payload["failure"]["retry"] == (
        "manual_review"
    )
    assert payload["failure"]["exit_code"] == 4
    assert payload["failure"]["secrets_redacted"] is True


def test_failure_message_is_redacted() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "POSTGRES_PASSWORD=do-not-expose",
            code="database_connection_failed",
            category=(
                FailureCategory.DEPENDENCY_UNAVAILABLE
            ),
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.EXECUTION,
    )

    trace = make_trace(failure=failure)
    payload = trace.model_dump(mode="json")

    message = payload["failure"]["message"]

    assert "do-not-expose" not in message
    assert "[REDACTED]" in message


def test_report_contains_failure_evidence() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "Deterministic validation did not pass",
            code="postgis_validation_failed",
            category=FailureCategory.VALIDATION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.VALIDATION,
    )

    report = render_report(
        make_trace(
            failure=failure,
            final_status="validation_failed",
        )
    )

    assert "## Failure evidence" in report
    assert "validation_failed" in report
    assert "postgis_validation_failed" in report
    assert "manual_review" in report


def test_success_report_says_no_failure() -> None:
    report = render_report(
        make_trace(
            failure=None,
            final_status="validated_success",
        )
    )

    section = report.split(
        "## Failure evidence",
        maxsplit=1,
    )[1].split(
        "## Artifacts",
        maxsplit=1,
    )[0]

    assert "- None" in section