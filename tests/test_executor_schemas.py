"""Tests for typed execution-envelope schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
)

from geoagent_harness.executor.schemas import (
    ExecutorRunResult,
)

def test_executor_result_requires_real_execution() -> None:
    payload = {
        "agent_id": "executor",
        "plan_sha256": "a" * 64,
        "approval_id": (
            "approval-20260809t200000z-1234abcd"
        ),
        "tool_name": (
            "run_approved_vector_postgis_workflow"
        ),
        "execution_performed": False,
        "workflow": {
            "task_id": "test-task",
            "final_status": "validated_success",
            "validation_passed": True,
            "report_path": "reports/test-task.md",
            "trace_path": "traces/test-task.json",
            "warnings": [],
        },
    }

    with pytest.raises(ValidationError):
        ExecutorRunResult.model_validate(payload)

def valid_envelope() -> dict:
    return {
        "schema_version": "1.0",
        "plan_sha256": "a" * 64,
        "approval_id": (
            "approval-20260809t183930z-6100744a"
        ),
        "approved_step_ids": [
            "step_2",
            "step_4",
        ],
        "selected_skills": [
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        "tool_name": (
            "run_vector_postgis_workflow"
        ),
        "tool_arguments": {
            "path": (
                "data/input/sample_points.geojson"
            ),
            "source_layer": None,
            "target_schema": "agent_sandbox",
            "target_table": "checkpoint5b_points",
            "original_request": (
                "Inspect, load, validate, and report "
                "the sample dataset."
            ),
            "task_id": "checkpoint5b-points",
            "context_references": [
                "context/PROJECT_SUMMARY.md",
            ],
            "human_corrections": [],
        },
        "execution_performed": False,
    }


def test_valid_execution_envelope() -> None:
    envelope = ExecutionEnvelope.model_validate(
        valid_envelope()
    )

    assert envelope.execution_performed is False
    assert envelope.tool_name == (
        "run_vector_postgis_workflow"
    )


def test_execution_cannot_be_claimed() -> None:
    payload = valid_envelope()
    payload["execution_performed"] = True

    with pytest.raises(ValidationError):
        ExecutionEnvelope.model_validate(payload)


def test_arbitrary_tool_name_is_rejected() -> None:
    payload = valid_envelope()
    payload["tool_name"] = "run_shell"

    with pytest.raises(ValidationError):
        ExecutionEnvelope.model_validate(payload)


def test_arbitrary_tool_arguments_are_rejected() -> None:
    payload = valid_envelope()
    payload["tool_arguments"]["sql"] = (
        "select * from secrets"
    )

    with pytest.raises(ValidationError):
        ExecutionEnvelope.model_validate(payload)


def test_invalid_plan_digest_is_rejected() -> None:
    payload = valid_envelope()
    payload["plan_sha256"] = "not-a-digest"

    with pytest.raises(ValidationError):
        ExecutionEnvelope.model_validate(payload)