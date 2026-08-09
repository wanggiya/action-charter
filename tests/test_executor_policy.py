"""Tests for deterministic execution-envelope construction."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from geoagent_harness.approvals import (
    ApprovalRecord,
    plan_sha256,
)
from geoagent_harness.executor import (
    ExecutorPolicyError,
    build_execution_envelope,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)

NOW = datetime(
    2026,
    8,
    9,
    18,
    0,
    tzinfo=timezone.utc,
)


def planner_result() -> PlannerResult:
    plan = WorkflowPlan.model_validate(
        {
            "schema_version": "1.0",
            "status": "planned",
            "summary": (
                "Inspect, load, validate, and report."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill": "inspect_vector",
                    "purpose": "Inspect input.",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
                {
                    "step_id": "step_2",
                    "skill": "load_vector_to_postgis",
                    "purpose": "Load input.",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_schema": (
                            "agent_sandbox"
                        ),
                        "target_table": (
                            "checkpoint5b_points"
                        ),
                    },
                    "requires_approval": True,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
                {
                    "step_id": "step_3",
                    "skill": (
                        "validate_postgis_layer"
                    ),
                    "purpose": "Validate output.",
                    "arguments": {
                        "target_schema": (
                            "agent_sandbox"
                        ),
                        "target_table": (
                            "checkpoint5b_points"
                        ),
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": True,
                },
                {
                    "step_id": "step_4",
                    "skill": "generate_report",
                    "purpose": "Generate report.",
                    "arguments": {
                        "task_id": (
                            "checkpoint5b-points"
                        ),
                    },
                    "requires_approval": True,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
            ],
            "assumptions": [],
            "risks": [],
            "execution_performed": False,
            "validation_performed": False,
        }
    )

    return PlannerResult(
        model="qwen-test",
        original_request=(
            "Inspect, load, validate, and report."
        ),
        context_references=[
            "context/PROJECT_SUMMARY.md",
        ],
        plan=plan,
    )


def approval_for(
    result: PlannerResult,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=(
            "approval-20260809t180000z-1234abcd"
        ),
        plan_sha256=plan_sha256(result.plan),
        decision="approved",
        step_ids=["step_2", "step_4"],
        approver="local-user",
        reason="Approved controlled writes.",
        created_at=NOW,
        secrets_redacted=True,
    )


def test_builds_approved_execution_envelope() -> None:
    result = planner_result()

    envelope = build_execution_envelope(
        planner_result=result,
        approval=approval_for(result),
        allowed_schemas={"agent_sandbox"},
    )

    assert envelope.execution_performed is False
    assert envelope.tool_name == (
        "run_vector_postgis_workflow"
    )
    assert envelope.tool_arguments.path == (
        "data/input/sample_points.geojson"
    )
    assert envelope.tool_arguments.target_table == (
        "checkpoint5b_points"
    )


def test_changed_plan_invalidates_approval() -> None:
    result = planner_result()
    approval = approval_for(result)

    result.plan.steps[1].arguments[
        "target_table"
    ] = "changed_table"
    result.plan.steps[2].arguments[
        "target_table"
    ] = "changed_table"

    with pytest.raises(
        ExecutorPolicyError,
        match="approval failed",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )


def test_mismatched_targets_are_rejected() -> None:
    result = planner_result()
    approval = approval_for(result)

    result.plan.steps[2].arguments[
        "target_table"
    ] = "different_table"

    with pytest.raises(
        ExecutorPolicyError,
        match="targets do not match",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )


def test_path_outside_input_is_rejected() -> None:
    result = planner_result()
    approval = approval_for(result)

    result.plan.steps[0].arguments[
        "path"
    ] = "../private.geojson"
    result.plan.steps[1].arguments[
        "path"
    ] = "../private.geojson"

    with pytest.raises(
        ExecutorPolicyError,
        match="data/input",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )


def test_unapproved_schema_is_rejected() -> None:
    result = planner_result()
    approval = approval_for(result)

    result.plan.steps[1].arguments[
        "target_schema"
    ] = "public"
    result.plan.steps[2].arguments[
        "target_schema"
    ] = "public"

    with pytest.raises(
        ExecutorPolicyError,
        match="schema is not allowed",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )


def test_unsupported_arguments_are_rejected() -> None:
    result = planner_result()
    approval = approval_for(result)

    result.plan.steps[0].arguments[
        "recursive"
    ] = True

    with pytest.raises(
        ExecutorPolicyError,
        match="unsupported arguments",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )


def test_denied_approval_is_rejected() -> None:
    result = planner_result()
    approval = approval_for(result)
    approval.decision = "denied"

    with pytest.raises(
        ExecutorPolicyError,
        match="approval failed",
    ):
        build_execution_envelope(
            planner_result=result,
            approval=approval,
            allowed_schemas={"agent_sandbox"},
        )