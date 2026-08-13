"""Tests for read-only workflow resume assessment."""

from datetime import datetime, timedelta, timezone

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.workflow_state import (
    ResumeDisposition,
    TransitionActor,
    WorkflowState,
    assess_resume,
    create_initial_state,
    transition_state,
)


NOW = datetime(
    2026,
    8,
    13,
    14,
    0,
    tzinfo=timezone.utc,
)

APPROVAL_ID = (
    "approval-20260813t140000z-1234abcd"
)


def planned():
    return create_initial_state(
        task_id="resume-test",
        plan_sha256="a" * 64,
        occurred_at=NOW,
    )


def approved():
    return transition_state(
        planned(),
        to_state=WorkflowState.APPROVED,
        actor=TransitionActor.HUMAN,
        reason="Exact plan approved",
        approval_id=APPROVAL_ID,
        occurred_at=NOW + timedelta(seconds=1),
    )


def executing():
    return transition_state(
        approved(),
        to_state=WorkflowState.EXECUTING,
        actor=TransitionActor.EXECUTOR,
        reason="Approved execution began",
        occurred_at=NOW + timedelta(seconds=2),
    )


def validating():
    return transition_state(
        executing(),
        to_state=WorkflowState.VALIDATING,
        actor=TransitionActor.VERIFIER,
        reason="Deterministic validation began",
        occurred_at=NOW + timedelta(seconds=3),
    )


def test_planned_state_can_continue_to_approval() -> None:
    state = planned()
    original = state.model_dump_json()

    assessment = assess_resume(state)

    assert assessment.disposition == (
        ResumeDisposition.RESUME_ALLOWED
    )
    assert (
        assessment.database_write_may_have_started
        is False
    )
    assert assessment.automatic_execution_allowed is False
    assert assessment.state_modified is False
    assert state.model_dump_json() == original


def test_approved_state_can_continue_to_executor() -> None:
    assessment = assess_resume(approved())

    assert assessment.disposition == (
        ResumeDisposition.RESUME_ALLOWED
    )
    assert (
        assessment.database_write_may_have_started
        is False
    )
    assert "Executor" in assessment.next_action


def test_executing_requires_manual_review() -> None:
    assessment = assess_resume(executing())

    assert assessment.disposition == (
        ResumeDisposition.MANUAL_REVIEW_REQUIRED
    )
    assert (
        assessment.database_write_may_have_started
        is True
    )
    assert assessment.automatic_execution_allowed is False


def test_validating_requires_manual_review() -> None:
    assessment = assess_resume(validating())

    assert assessment.disposition == (
        ResumeDisposition.MANUAL_REVIEW_REQUIRED
    )
    assert (
        assessment.database_write_may_have_started
        is True
    )


def test_validated_success_is_terminal() -> None:
    completed = transition_state(
        validating(),
        to_state=WorkflowState.VALIDATED_SUCCESS,
        actor=TransitionActor.VERIFIER,
        reason="All deterministic checks passed",
        occurred_at=NOW + timedelta(seconds=4),
    )

    assessment = assess_resume(completed)

    assert assessment.disposition == (
        ResumeDisposition.TERMINAL
    )
    assert (
        assessment.database_write_may_have_started
        is True
    )


def test_execution_failure_requires_review() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "PostGIS write outcome is uncertain",
            code="postgis_write_uncertain",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.EXECUTION,
    )

    failed = transition_state(
        executing(),
        to_state=WorkflowState.EXECUTION_FAILED,
        actor=TransitionActor.EXECUTOR,
        reason="Execution outcome is uncertain",
        failure=failure,
        occurred_at=NOW + timedelta(seconds=3),
    )

    assessment = assess_resume(failed)

    assert assessment.disposition == (
        ResumeDisposition.MANUAL_REVIEW_REQUIRED
    )
    assert (
        assessment.database_write_may_have_started
        is True
    )


def test_cancellation_before_execution_is_terminal() -> None:
    failure = failure_from_exception(
        KeyboardInterrupt(),
        stage=FailureStage.APPROVAL,
    )

    cancelled = transition_state(
        planned(),
        to_state=WorkflowState.CANCELLED,
        actor=TransitionActor.OPERATOR,
        reason="Operator cancelled before approval",
        failure=failure,
        occurred_at=NOW + timedelta(seconds=1),
    )

    assessment = assess_resume(cancelled)

    assert assessment.disposition == (
        ResumeDisposition.TERMINAL
    )
    assert (
        assessment.database_write_may_have_started
        is False
    )


def test_cancellation_after_execution_requires_review() -> None:
    failure = failure_from_exception(
        KeyboardInterrupt(),
        stage=FailureStage.EXECUTION,
    )

    cancelled = transition_state(
        executing(),
        to_state=WorkflowState.CANCELLED,
        actor=TransitionActor.OPERATOR,
        reason="Operator interrupted execution",
        failure=failure,
        occurred_at=NOW + timedelta(seconds=3),
    )

    assessment = assess_resume(cancelled)

    assert assessment.disposition == (
        ResumeDisposition.MANUAL_REVIEW_REQUIRED
    )
    assert (
        assessment.database_write_may_have_started
        is True
    )