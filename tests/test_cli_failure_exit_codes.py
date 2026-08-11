"""Tests for stable typed CLI failure exit codes."""

from __future__ import annotations

# from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness import critic
from geoagent_harness import planner
from geoagent_harness.cli import app
from geoagent_harness.executor import service as executor_service
from geoagent_harness.mcp_client import (
    MCPClientError,
)
from geoagent_harness.model import (
    ModelClientError,
)

runner = CliRunner()


def test_planner_timeout_uses_exit_code_3(
    monkeypatch,
) -> None:
    def fail_plan(**kwargs):
        raise ModelClientError.timeout()

    monkeypatch.setattr(
        planner,
        "plan_task",
        fail_plan,
    )

    result = runner.invoke(
        app,
        [
            "plan-task",
            "--request",
            "Inspect the approved dataset.",
        ],
    )

    assert result.exit_code == 3
    assert "model_timeout" in result.output
    assert (
        "Shared model request timed out"
        in result.output
    )


def test_planner_invalid_response_uses_exit_code_4(
    monkeypatch,
) -> None:
    def fail_plan(**kwargs):
        raise ModelClientError.invalid_response()

    monkeypatch.setattr(
        planner,
        "plan_task",
        fail_plan,
    )

    result = runner.invoke(
        app,
        [
            "plan-task",
            "--request",
            "Inspect the approved dataset.",
        ],
    )

    assert result.exit_code == 4
    assert "model_invalid_response" in result.output


def test_critic_unavailable_uses_exit_code_3(
    monkeypatch,
) -> None:
    def fail_critique(**kwargs):
        raise ModelClientError.unavailable()

    monkeypatch.setattr(
        critic,
        "critique_task",
        fail_critique,
    )

    result = runner.invoke(
        app,
        [
            "critique-task",
            "traces/example.json",
            "reports/example.md",
        ],
    )

    assert result.exit_code == 3
    assert "model_unavailable" in result.output


def test_executor_mcp_failure_uses_exit_code_4(
    monkeypatch,
) -> None:
    async def fail_execution(**kwargs):
        raise MCPClientError.execution_tool_error()

    monkeypatch.setattr(
        executor_service,
        "execute_approved_plan",
        fail_execution,
    )

    result = runner.invoke(
        app,
        [
            "execute-approved-plan",
            "example-plan.json",
            "example-approval.json",
        ],
    )

    assert result.exit_code == 4
    assert (
        "mcp_execution_tool_error"
        in result.output
    )


def test_executor_timeout_uses_exit_code_3(
    monkeypatch,
) -> None:
    async def timeout_execution(**kwargs):
        raise MCPClientError.execution_timeout()

    monkeypatch.setattr(
        executor_service,
        "execute_approved_plan",
        timeout_execution,
    )

    result = runner.invoke(
        app,
        [
            "execute-approved-plan",
            "example-plan.json",
            "example-approval.json",
        ],
    )

    assert result.exit_code == 3
    assert "mcp_execution_timeout" in result.output
    assert "timed out" in result.output.lower()