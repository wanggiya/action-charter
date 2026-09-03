"""Tests for trusted operational-history observers."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.operational_history import (
    AgentRole,
    OperationalEventType,
    OperationalHistoryError,
    OperationalIdentity,
    load_operational_events,
    record_critic_history,
    record_executor_history,
    record_gis_workflow_history,
    record_planner_history,
)
from geoagent_harness.critic.schemas import (
    CriticAssessment,
    CriticResult,
    EvidenceReference,
)
from geoagent_harness.executor.schemas import (
    ExecutorRunResult,
    WorkflowExecutionResult,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)
from geoagent_harness.reporting import write_report
from geoagent_harness.trace import (
    TraceTimestamps,
    WorkflowTrace,
    write_trace,
)


NOW = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)


def write_evidence(
    tmp_path: Path,
    *,
    task_id: str = "observed-workflow",
) -> tuple[Path, Path, Path, Path]:
    trace_root = tmp_path / "traces"
    report_root = tmp_path / "reports"
    trace = WorkflowTrace(
        task_id=task_id,
        original_request="Load and validate sample points.",
        context_references=[],
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
        ],
        plan_sha256="a" * 64,
        approval_id="approval-observer-1",
        approved_step_ids=["step_1"],
        tool_arguments={},
        tool_results={},
        validation_results={
            "passed": True,
            "table_exists": True,
            "geometry_column_exists": True,
            "row_count": 2,
            "srid": 4326,
            "geometry_type": "POINT",
            "invalid_geometry_count": 0,
            "null_geometry_count": 0,
            "extent": {
                "min_x": -71.1,
                "min_y": 42.3,
                "max_x": -71.0,
                "max_y": 42.4,
            },
            "checks": [],
            "warnings": [],
        },
        artifacts=[],
        warnings=[],
        final_status="validated_success",
        timestamps=TraceTimestamps(
            started_at=NOW,
            finished_at=NOW,
        ),
        versions={"harness": "0.1.0"},
    )
    report = write_report(trace, report_root=report_root)
    trace_path = write_trace(trace, trace_root=trace_root)
    return trace_path, report, trace_root, report_root


def gis_identity(
    *,
    task_id: str = "observed-workflow",
) -> OperationalIdentity:
    return OperationalIdentity(
        agent_id=AgentRole.GIS,
        agent_instance_id="gis-instance-1",
        agent_run_id="gis-run-1",
        task_id=task_id,
        correlation_id="correlation-observer-1",
        parent_run_id=None,
    )


def test_records_successful_gis_history_from_evidence(
    tmp_path: Path,
) -> None:
    trace, report, trace_root, report_root = (
        write_evidence(tmp_path)
    )
    event_root = tmp_path / "events"

    recorded = record_gis_workflow_history(
        trace_path=trace,
        report_path=report,
        trace_root=trace_root,
        report_root=report_root,
        event_root=event_root,
        identity=gis_identity(),
    )

    assert [event.event_type for event in recorded] == [
        OperationalEventType.RUN_STARTED,
        OperationalEventType.APPROVAL_VERIFIED,
        OperationalEventType.VALIDATION_COMPLETED,
        OperationalEventType.EVIDENCE_PERSISTED,
        OperationalEventType.RUN_COMPLETED,
    ]
    assert recorded[-1].status == "validated_success"
    assert recorded[-2].artifact_digests.keys() == {
        "trace",
        "report",
    }

    loaded = load_operational_events(
        event_root
        / "correlation-observer-1.events.jsonl",
        event_root=event_root,
    )
    assert loaded == recorded


def test_rejects_caller_task_mismatch(
    tmp_path: Path,
) -> None:
    trace, report, trace_root, report_root = (
        write_evidence(tmp_path)
    )

    with pytest.raises(
        OperationalHistoryError,
        match="task identity",
    ):
        record_gis_workflow_history(
            trace_path=trace,
            report_path=report,
            trace_root=trace_root,
            report_root=report_root,
            event_root=tmp_path / "events",
            identity=gis_identity(task_id="different-task"),
        )


def test_rejects_non_gis_role(
    tmp_path: Path,
) -> None:
    trace, report, trace_root, report_root = (
        write_evidence(tmp_path)
    )
    identity = gis_identity().model_copy(
        update={"agent_id": AgentRole.PLANNER}
    )

    with pytest.raises(
        OperationalHistoryError,
        match="gis agent role",
    ):
        record_gis_workflow_history(
            trace_path=trace,
            report_path=report,
            trace_root=trace_root,
            report_root=report_root,
            event_root=tmp_path / "events",
            identity=identity,
        )


def test_rejects_unverified_workflow_evidence(
    tmp_path: Path,
) -> None:
    trace, report, trace_root, report_root = (
        write_evidence(tmp_path)
    )
    trace.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        OperationalHistoryError,
        match="could not be verified",
    ):
        record_gis_workflow_history(
            trace_path=trace,
            report_path=report,
            trace_root=trace_root,
            report_root=report_root,
            event_root=tmp_path / "events",
            identity=gis_identity(),
        )


def agent_identity(
    role: AgentRole,
    run_id: str,
    *,
    parent_run_id: str | None = None,
) -> OperationalIdentity:
    return OperationalIdentity(
        agent_id=role,
        agent_instance_id=f"{role.value}-instance-1",
        agent_run_id=run_id,
        task_id="correlated-task",
        correlation_id="correlated-history",
        parent_run_id=parent_run_id,
    )


def planner_result() -> PlannerResult:
    return PlannerResult(
        model="qwen-local",
        original_request="Inspect the approved dataset.",
        context_references=["context/SKILLS_INDEX.yaml"],
        plan=WorkflowPlan(
            summary="Inspect and validate the dataset.",
            steps=[
                {
                    "step_id": "step_1",
                    "skill": "inspect_vector",
                    "purpose": "Inspect the approved input.",
                    "requires_approval": False,
                    "validation_required": True,
                },
            ],
        ),
    )


def executor_result(
    *,
    status: str = "validated_success",
) -> ExecutorRunResult:
    return ExecutorRunResult(
        plan_sha256="a" * 64,
        approval_id="approval-correlated-1",
        tool_name="run_approved_vector_postgis_workflow",
        workflow=WorkflowExecutionResult(
            task_id="correlated-task",
            final_status=status,
            validation_passed=(status == "validated_success"),
            report_path="reports/correlated-task.md",
            trace_path="traces/correlated-task.json",
            warnings=[],
        ),
    )


def critic_result() -> CriticResult:
    return CriticResult(
        model="qwen-local",
        task_id="correlated-task",
        deterministic_status="validated_success",
        evidence_references=[
            EvidenceReference(
                path="traces/correlated-task.json",
                sha256="b" * 64,
            ),
        ],
        evidence_gaps=[],
        workflow_warnings=[],
        human_corrections=[],
        assessment=CriticAssessment(
            deterministic_status="validated_success",
            conclusion="supported",
            success_claimed=True,
            summary="Deterministic evidence supports success.",
        ),
    )


def test_records_correlated_planner_executor_and_critic_runs(
    tmp_path: Path,
) -> None:
    event_root = tmp_path / "events"
    planner_identity = agent_identity(
        AgentRole.PLANNER,
        "planner-run-1",
    )
    executor_identity = agent_identity(
        AgentRole.EXECUTOR,
        "executor-run-1",
        parent_run_id="planner-run-1",
    )
    critic_identity = agent_identity(
        AgentRole.CRITIC,
        "critic-run-1",
        parent_run_id="executor-run-1",
    )

    planner_events = record_planner_history(
        result=planner_result(),
        identity=planner_identity,
        started_at=NOW,
        finished_at=NOW,
        event_root=event_root,
    )
    executor_events = record_executor_history(
        result=executor_result(),
        identity=executor_identity,
        started_at=NOW,
        finished_at=NOW,
        event_root=event_root,
    )
    critic_events = record_critic_history(
        result=critic_result(),
        identity=critic_identity,
        started_at=NOW,
        finished_at=NOW,
        event_root=event_root,
    )

    assert [event.event_type for event in planner_events] == [
        OperationalEventType.RUN_STARTED,
        OperationalEventType.INPUT_VALIDATED,
        OperationalEventType.PROPOSAL_GENERATED,
        OperationalEventType.RUN_COMPLETED,
    ]
    assert executor_events[-1].event_type == (
        OperationalEventType.RUN_COMPLETED
    )
    assert critic_events[-1].status == "assessment_completed"
    assert critic_events[2].facts["deterministic_status"] == (
        "validated_success"
    )

    loaded = load_operational_events(
        event_root / "correlated-history.events.jsonl",
        event_root=event_root,
    )
    assert len(loaded) == 14
    assert {
        event.identity.agent_id for event in loaded
    } == {
        AgentRole.PLANNER,
        AgentRole.EXECUTOR,
        AgentRole.CRITIC,
    }


def test_executor_failure_is_recorded_as_terminal_failure(
    tmp_path: Path,
) -> None:
    result = executor_result(status="execution_failed")

    events = record_executor_history(
        result=result,
        identity=agent_identity(
            AgentRole.EXECUTOR,
            "executor-run-1",
        ),
        started_at=NOW,
        finished_at=NOW,
        event_root=tmp_path / "events",
    )

    assert events[-1].event_type == OperationalEventType.RUN_FAILED
    assert events[-1].failure_code == (
        "executor_execution_failed"
    )


@pytest.mark.parametrize(
    ("observer", "result", "role"),
    [
        (record_planner_history, planner_result(), AgentRole.EXECUTOR),
        (record_executor_history, executor_result(), AgentRole.PLANNER),
        (record_critic_history, critic_result(), AgentRole.EXECUTOR),
    ],
)
def test_agent_observers_reject_incorrect_roles(
    tmp_path: Path,
    observer,
    result,
    role: AgentRole,
) -> None:
    with pytest.raises(
        OperationalHistoryError,
        match="requires the",
    ):
        observer(
            result=result,
            identity=agent_identity(role, "wrong-role-run"),
            started_at=NOW,
            finished_at=NOW,
            event_root=tmp_path / "events",
        )


def test_agent_observer_rejects_unaware_timestamps(
    tmp_path: Path,
) -> None:
    unaware = datetime(2026, 9, 3, 12)

    with pytest.raises(
        OperationalHistoryError,
        match="timezone",
    ):
        record_planner_history(
            result=planner_result(),
            identity=agent_identity(
                AgentRole.PLANNER,
                "planner-run-1",
            ),
            started_at=unaware,
            finished_at=unaware,
            event_root=tmp_path / "events",
        )
