"""Tests for the dedicated Executor MCP client."""

from __future__ import annotations

import asyncio

import pytest

from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
)
from geoagent_harness.mcp_client import (
    MCPClientError,
    MCPClientSettings,
    MCPExecutorClient,
)


def envelope() -> ExecutionEnvelope:
    return ExecutionEnvelope(
        plan_sha256="a" * 64,
        approval_id=(
            "approval-20260809t200000z-1234abcd"
        ),
        approved_step_ids=[
            "step_2",
            "step_4",
        ],
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        tool_arguments={
            "path": (
                "data/input/sample_points.geojson"
            ),
            "target_schema": "agent_sandbox",
            "target_table": "checkpoint5d_points",
            "original_request": "Test.",
            "task_id": "checkpoint5d-points",
        },
        execution_performed=False,
    )


def test_plan_filename_escape_is_rejected_before_network() -> None:
    client = MCPExecutorClient(
        MCPClientSettings(
            url="http://mcp-gis:8000/mcp",
            timeout_seconds=5,
        )
    )

    with pytest.raises(
        MCPClientError,
        match="plain JSON filename",
    ):
        asyncio.run(
            client.execute_approved_workflow(
                envelope=envelope(),
                plan_filename="../plan.json",
                approval_filename="approval.json",
            )
        )


def test_approval_filename_escape_is_rejected_before_network() -> None:
    client = MCPExecutorClient(
        MCPClientSettings(
            url="http://mcp-gis:8000/mcp",
            timeout_seconds=5,
        )
    )

    with pytest.raises(
        MCPClientError,
        match="plain JSON filename",
    ):
        asyncio.run(
            client.execute_approved_workflow(
                envelope=envelope(),
                plan_filename="plan.json",
                approval_filename="../approval.json",
            )
        )