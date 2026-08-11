"""Tests for deterministic operator cancellation."""

from click import unstyle
from typer.testing import CliRunner

import geoagent_harness.planner as planner
from geoagent_harness.cli import app
from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    RetryDisposition,
    failure_from_exception,
)


runner = CliRunner()


def test_planning_cancellation_is_not_retryable() -> None:
    failure = failure_from_exception(
        KeyboardInterrupt(),
        stage=FailureStage.PLANNING,
    )

    assert failure.category == FailureCategory.CANCELLED
    assert failure.code == "operator_cancelled"
    assert failure.exit_code == 130
    assert failure.retry == RetryDisposition.NEVER
    assert failure.cause_type == "KeyboardInterrupt"
    assert failure.message == (
        "Operation cancelled by operator"
    )


def test_execution_cancellation_requires_review() -> None:
    failure = failure_from_exception(
        KeyboardInterrupt(),
        stage=FailureStage.EXECUTION,
    )

    assert failure.category == FailureCategory.CANCELLED
    assert failure.exit_code == 130
    assert failure.retry == (
        RetryDisposition.MANUAL_REVIEW
    )


def test_plan_task_cancellation_exits_130(
    monkeypatch,
) -> None:
    def interrupt_plan(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        planner,
        "plan_task",
        interrupt_plan,
    )

    result = runner.invoke(
        app,
        [
            "plan-task",
            "--request",
            "Plan a test task.",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 130
    assert "operator_cancelled" in output
    assert "Operation cancelled by operator" in output
    assert "Traceback" not in output