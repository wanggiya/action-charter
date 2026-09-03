"""Trusted observers that derive events from validated artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from geoagent_harness.critic.schemas import CriticResult
from geoagent_harness.executor.schemas import ExecutorRunResult
from geoagent_harness.planner.schemas import PlannerResult

from geoagent_harness.critic.evidence import (
    CriticEvidenceError,
    build_critic_evidence,
)
from geoagent_harness.operational_history.schemas import (
    AgentRole,
    OperationalEvent,
    OperationalEventType,
    OperationalIdentity,
)
from geoagent_harness.operational_history.service import (
    OperationalHistoryError,
    append_operational_events,
    create_operational_event,
)


def _aware_timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise OperationalHistoryError(
            "workflow evidence contains an invalid timestamp"
        ) from exc

    if (
        timestamp.tzinfo is None
        or timestamp.utcoffset() is None
    ):
        raise OperationalHistoryError(
            "workflow evidence timestamp lacks a timezone"
        )

    return timestamp


def _validated_digest(value: BaseModel) -> str:
    """Hash one complete validated model without persisting it."""

    content = json.dumps(
        value.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _validate_observer_inputs(
    *,
    identity: OperationalIdentity,
    expected_role: AgentRole,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    if identity.agent_id != expected_role:
        raise OperationalHistoryError(
            f"observer requires the {expected_role.value} agent role"
        )
    if (
        started_at.tzinfo is None
        or started_at.utcoffset() is None
        or finished_at.tzinfo is None
        or finished_at.utcoffset() is None
    ):
        raise OperationalHistoryError(
            "observer timestamps must include a timezone"
        )
    if finished_at < started_at:
        raise OperationalHistoryError(
            "observer timestamps are not monotonic"
        )


def _append_derived_run(
    *,
    identity: OperationalIdentity,
    event_root: Path,
    specifications: list[
        tuple[OperationalEventType, datetime, dict[str, object]]
    ],
) -> list[OperationalEvent]:
    events: list[OperationalEvent] = []

    for event_type, occurred_at, values in specifications:
        event = create_operational_event(
            identity=identity,
            event_type=event_type,
            previous_event=(events[-1] if events else None),
            occurred_at=occurred_at,
            **values,
        )
        events.append(event)

    append_operational_events(events, event_root=event_root)
    return events


def record_planner_history(
    *,
    result: PlannerResult,
    identity: OperationalIdentity,
    started_at: datetime,
    finished_at: datetime,
    event_root: Path,
) -> list[OperationalEvent]:
    """Record observable facts from one validated Planner result."""

    _validate_observer_inputs(
        identity=identity,
        expected_role=AgentRole.PLANNER,
        started_at=started_at,
        finished_at=finished_at,
    )

    approval_steps = sum(
        step.requires_approval for step in result.plan.steps
    )
    validation_steps = sum(
        step.validation_required for step in result.plan.steps
    )

    return _append_derived_run(
        identity=identity,
        event_root=event_root,
        specifications=[
            (
                OperationalEventType.RUN_STARTED,
                started_at,
                {
                    "status": "planning",
                    "versions": {"model": result.model},
                },
            ),
            (
                OperationalEventType.INPUT_VALIDATED,
                started_at,
                {
                    "status": "validated",
                    "facts": {
                        "context_reference_count": len(
                            result.context_references
                        ),
                    },
                },
            ),
            (
                OperationalEventType.PROPOSAL_GENERATED,
                finished_at,
                {
                    "status": result.plan.status,
                    "artifact_digests": {
                        "planner_result": _validated_digest(result),
                        "plan": _validated_digest(result.plan),
                    },
                    "facts": {
                        "step_count": len(result.plan.steps),
                        "approval_step_count": approval_steps,
                        "validation_step_count": validation_steps,
                        "warning_count": len(result.warnings),
                    },
                },
            ),
            (
                OperationalEventType.RUN_COMPLETED,
                finished_at,
                {"status": "planned"},
            ),
        ],
    )


def record_executor_history(
    *,
    result: ExecutorRunResult,
    identity: OperationalIdentity,
    started_at: datetime,
    finished_at: datetime,
    event_root: Path,
) -> list[OperationalEvent]:
    """Record one validated Executor result without replaying it."""

    _validate_observer_inputs(
        identity=identity,
        expected_role=AgentRole.EXECUTOR,
        started_at=started_at,
        finished_at=finished_at,
    )
    if result.workflow.task_id != identity.task_id:
        raise OperationalHistoryError(
            "Executor result task identity does not match"
        )

    successful = (
        result.workflow.final_status == "validated_success"
    )
    terminal_type = (
        OperationalEventType.RUN_COMPLETED
        if successful
        else OperationalEventType.RUN_FAILED
    )
    terminal_values: dict[str, object] = {
        "status": result.workflow.final_status,
    }
    if not successful:
        terminal_values["failure_code"] = (
            f"executor_{result.workflow.final_status}"
        )

    return _append_derived_run(
        identity=identity,
        event_root=event_root,
        specifications=[
            (
                OperationalEventType.RUN_STARTED,
                started_at,
                {"status": "executing"},
            ),
            (
                OperationalEventType.APPROVAL_VERIFIED,
                started_at,
                {
                    "status": "approved",
                    "artifact_digests": {
                        "plan": result.plan_sha256,
                    },
                    "facts": {"approval_id": result.approval_id},
                },
            ),
            (
                OperationalEventType.TOOL_REQUESTED,
                started_at,
                {
                    "status": "requested",
                    "tool_name": result.tool_name,
                },
            ),
            (
                OperationalEventType.TOOL_COMPLETED,
                finished_at,
                {
                    "status": result.workflow.final_status,
                    "tool_name": result.tool_name,
                    "facts": {
                        "execution_performed": (
                            result.execution_performed
                        ),
                    },
                },
            ),
            (
                OperationalEventType.VALIDATION_COMPLETED,
                finished_at,
                {
                    "status": (
                        "passed"
                        if result.workflow.validation_passed
                        else "failed"
                    ),
                    "facts": {
                        "validation_passed": (
                            result.workflow.validation_passed
                        ),
                        "warning_count": len(
                            result.workflow.warnings
                        ),
                    },
                },
            ),
            (terminal_type, finished_at, terminal_values),
        ],
    )


def record_critic_history(
    *,
    result: CriticResult,
    identity: OperationalIdentity,
    started_at: datetime,
    finished_at: datetime,
    event_root: Path,
) -> list[OperationalEvent]:
    """Record one validated Critic assessment as separate evidence."""

    _validate_observer_inputs(
        identity=identity,
        expected_role=AgentRole.CRITIC,
        started_at=started_at,
        finished_at=finished_at,
    )
    if result.task_id != identity.task_id:
        raise OperationalHistoryError(
            "Critic result task identity does not match"
        )

    references = [item.path for item in result.evidence_references]
    digests = {
        f"evidence_{index}": item.sha256
        for index, item in enumerate(
            result.evidence_references,
            start=1,
        )
    }

    return _append_derived_run(
        identity=identity,
        event_root=event_root,
        specifications=[
            (
                OperationalEventType.RUN_STARTED,
                started_at,
                {
                    "status": "reviewing",
                    "versions": {"model": result.model},
                },
            ),
            (
                OperationalEventType.INPUT_VALIDATED,
                started_at,
                {
                    "status": "validated",
                    "artifact_digests": digests,
                    "evidence_references": references,
                    "facts": {
                        "evidence_gap_count": len(
                            result.evidence_gaps
                        ),
                        "workflow_warning_count": len(
                            result.workflow_warnings
                        ),
                    },
                },
            ),
            (
                OperationalEventType.POLICY_ASSESSED,
                finished_at,
                {
                    "status": result.assessment.conclusion,
                    "policy_decision": (
                        result.assessment.conclusion
                    ),
                    "artifact_digests": {
                        "critic_result": _validated_digest(result),
                    },
                    "facts": {
                        "deterministic_status": (
                            result.deterministic_status
                        ),
                        "success_claimed": (
                            result.assessment.success_claimed
                        ),
                        "risk_count": len(
                            result.assessment.additional_risks
                        ),
                    },
                },
            ),
            (
                OperationalEventType.RUN_COMPLETED,
                finished_at,
                {"status": "assessment_completed"},
            ),
        ],
    )


def record_gis_workflow_history(
    *,
    trace_path: Path,
    report_path: Path,
    trace_root: Path,
    report_root: Path,
    event_root: Path,
    identity: OperationalIdentity,
) -> list[OperationalEvent]:
    """Record one GIS run from existing validated evidence.

    This observer does not import or execute implementation code. It
    accepts identity only from its trusted caller and derives outcome,
    approval, validation, timestamps, and digests from the existing
    trace/report verification boundary.
    """

    if identity.agent_id != AgentRole.GIS:
        raise OperationalHistoryError(
            "GIS workflow history requires the gis agent role"
        )

    try:
        evidence = build_critic_evidence(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
        )
    except CriticEvidenceError as exc:
        raise OperationalHistoryError(
            "GIS workflow evidence could not be verified"
        ) from exc

    if evidence.task_id != identity.task_id:
        raise OperationalHistoryError(
            "GIS workflow task identity does not match"
        )

    started_at = _aware_timestamp(
        evidence.timestamps["started_at"]
    )
    finished_at = _aware_timestamp(
        evidence.timestamps["finished_at"]
    )

    if finished_at < started_at:
        raise OperationalHistoryError(
            "GIS workflow timestamps are not monotonic"
        )

    references = [
        reference.path
        for reference in evidence.evidence_references
    ]
    digests = {
        (
            "trace"
            if reference.path.endswith(".json")
            else "report"
        ): reference.sha256
        for reference in evidence.evidence_references
    }

    events: list[OperationalEvent] = []

    def record(
        event_type: OperationalEventType,
        *,
        occurred_at: datetime,
        **values: object,
    ) -> OperationalEvent:
        previous = events[-1] if events else None
        event = create_operational_event(
            identity=identity,
            event_type=event_type,
            previous_event=previous,
            occurred_at=occurred_at,
            **values,
        )
        events.append(event)
        return event

    record(
        OperationalEventType.RUN_STARTED,
        occurred_at=started_at,
        status="executing",
        versions=evidence.versions,
    )

    if evidence.approval.complete:
        record(
            OperationalEventType.APPROVAL_VERIFIED,
            occurred_at=started_at,
            status="approved",
            artifact_digests={
                "plan": evidence.approval.plan_sha256,
            },
            facts={
                "approval_id": evidence.approval.approval_id,
                "approved_step_count": len(
                    evidence.approval.approved_step_ids
                ),
            },
        )

    if evidence.validation.passed is not None:
        record(
            OperationalEventType.VALIDATION_COMPLETED,
            occurred_at=finished_at,
            status=(
                "passed"
                if evidence.validation.passed
                else "failed"
            ),
            facts={
                "validation_passed": (
                    evidence.validation.passed
                ),
                "failed_check_count": len(
                    evidence.validation.failed_checks
                ),
            },
        )

    record(
        OperationalEventType.EVIDENCE_PERSISTED,
        occurred_at=finished_at,
        status="persisted",
        artifact_digests=digests,
        evidence_references=references,
    )

    if evidence.deterministic_status == "validated_success":
        record(
            OperationalEventType.RUN_COMPLETED,
            occurred_at=finished_at,
            status="validated_success",
        )
    else:
        record(
            OperationalEventType.RUN_FAILED,
            occurred_at=finished_at,
            status=evidence.deterministic_status,
            failure_code=(
                "workflow_"
                f"{evidence.deterministic_status}"
            ),
        )

    append_operational_events(
        events,
        event_root=event_root,
    )

    return events
