"""Tests that registered models emit current versions."""

from datetime import datetime, timezone

from geoagent_harness.approvals.schemas import (
    ApprovalRecord,
)
from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
    WorkflowToolArguments,
)
from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.planner.schemas import (
    PlanStep,
    WorkflowPlan,
)
from geoagent_harness.trace import (
    TraceTimestamps,
    WorkflowTrace,
)
from geoagent_harness.workflow_state import (
    create_initial_state,
)


NOW = datetime.now(timezone.utc)


def test_workflow_plan_emits_version_1() -> None:
    plan = WorkflowPlan(
        summary="Inspect the dataset.",
        steps=[
            PlanStep(
                step_id="step_1",
                skill="inspect_vector",
                purpose="Inspect approved input.",
            )
        ],
    )

    assert plan.schema_version == "1.0"


def test_approval_emits_version_1() -> None:
    approval = ApprovalRecord(
        approval_id=(
            "approval-20260813t180000z-1234abcd"
        ),
        plan_sha256="a" * 64,
        decision="approved",
        step_ids=["step_1"],
        approver="test-operator",
        reason="Test approval",
        created_at=NOW,
    )

    assert approval.schema_version == "1.0"


def test_execution_envelope_emits_version_1() -> None:
    envelope = ExecutionEnvelope(
        plan_sha256="b" * 64,
        approval_id=(
            "approval-20260813t180000z-1234abcd"
        ),
        approved_step_ids=["step_1"],
        selected_skills=["inspect_vector"],
        tool_arguments=WorkflowToolArguments(
            path="data/input/sample_points.geojson",
            target_schema="agent_sandbox",
            target_table="sample_points",
            original_request="Inspect sample points.",
            task_id="schema-envelope-test",
        ),
    )

    assert envelope.schema_version == "1.0"


def test_failure_emits_version_1() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "Test failure",
            code="test_failure",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.NEVER,
        ),
        stage=FailureStage.EXECUTION,
    )

    assert failure.schema_version == "1.0"


def test_trace_emits_version_1() -> None:
    trace = WorkflowTrace(
        task_id="schema-trace-test",
        original_request="Test trace version.",
        context_references=[],
        selected_skills=[],
        tool_arguments={},
        tool_results={},
        validation_results=None,
        artifacts=[],
        warnings=[],
        final_status="execution_failed",
        timestamps=TraceTimestamps(
            started_at=NOW,
            finished_at=NOW,
        ),
        versions={},
    )

    assert trace.schema_version == "1.0"


def test_workflow_state_emits_version_1() -> None:
    state = create_initial_state(
        task_id="schema-state-test",
        plan_sha256="c" * 64,
        occurred_at=NOW,
    )

    assert state.schema_version == "1.0"
