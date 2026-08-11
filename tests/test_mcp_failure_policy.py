"""Tests for structured MCP failure policy."""

from __future__ import annotations

import asyncio

import pytest

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.mcp_client.client import (
    MCPClientError,
    MCPReadOnlyClient,
)
from geoagent_harness.mcp_client.settings import (
    MCPClientSettings,
)


def classify(error: MCPClientError):
    return failure_from_exception(
        error,
        stage=FailureStage.MCP,
    )


def test_read_timeout_is_safe_to_retry() -> None:
    failure = classify(
        MCPClientError.read_timeout()
    )

    assert failure.category == FailureCategory.TIMEOUT
    assert failure.code == "mcp_read_timeout"
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )
    assert failure.exit_code == 3


def test_execution_timeout_requires_review() -> None:
    failure = classify(
        MCPClientError.execution_timeout()
    )

    assert failure.category == FailureCategory.TIMEOUT
    assert failure.code == "mcp_execution_timeout"
    assert (
        failure.retry
        == RetryDisposition.MANUAL_REVIEW
    )
    assert failure.exit_code == 3


def test_read_unavailable_is_safe_to_retry() -> None:
    failure = classify(
        MCPClientError.read_unavailable()
    )

    assert (
        failure.category
        == FailureCategory.DEPENDENCY_UNAVAILABLE
    )
    assert failure.code == "mcp_read_unavailable"
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )


def test_execution_unavailable_requires_review() -> None:
    failure = classify(
        MCPClientError.execution_unavailable()
    )

    assert (
        failure.category
        == FailureCategory.DEPENDENCY_UNAVAILABLE
    )
    assert failure.code == "mcp_execution_unavailable"
    assert (
        failure.retry
        == RetryDisposition.MANUAL_REVIEW
    )


def test_execution_tool_error_requires_review() -> None:
    failure = classify(
        MCPClientError.execution_tool_error()
    )

    assert (
        failure.category
        == FailureCategory.EXECUTION_FAILED
    )
    assert failure.code == "mcp_execution_tool_error"
    assert (
        failure.retry
        == RetryDisposition.MANUAL_REVIEW
    )
    assert failure.exit_code == 4


def test_invalid_mcp_response_is_not_retried() -> None:
    failure = classify(
        MCPClientError.invalid_response(
            "MCP returned malformed evidence"
        )
    )

    assert (
        failure.category
        == FailureCategory.EXTERNAL_RESPONSE_INVALID
    )
    assert failure.code == "mcp_invalid_response"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 4


def test_invalid_filename_is_invalid_input() -> None:
    failure = classify(
        MCPClientError.invalid_filename(
            label="plan_filename"
        )
    )

    assert (
        failure.category
        == FailureCategory.INVALID_INPUT
    )
    assert failure.code == "mcp_invalid_filename"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 2


def test_read_only_client_rejects_unapproved_tool() -> None:
    settings = MCPClientSettings(
        url="http://mcp-gis:8000/mcp",
        timeout_seconds=10,
    )
    client = MCPReadOnlyClient(settings)

    with pytest.raises(MCPClientError) as captured:
        asyncio.run(
            client.call_tool(
                "run_approved_vector_postgis_workflow"
            )
        )

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.POLICY_DENIED
    )
    assert failure.code == "mcp_tool_not_allowed"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 2