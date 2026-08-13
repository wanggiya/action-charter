"""Tests for deterministic workflow-state transitions."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.workflow_state import (
    TransitionActor,
    WorkflowState,
    WorkflowStateError,
    create_initial_state,
    load_state,
    transition_state,
    write_initial_state,
    write_updated_state,
)


NOW = datetime(
    2026,
    8,
    13,
    12,
    0,
    tzinfo=timezone.utc,
)


def initial_state():
    return create_initial_state(
        task_id="transition-test",
        plan_sha256="a" * 64,
        occurred_at=NOW,
    )


def approve(state):
    return transition_state(
        state,
        to_state=WorkflowState.APPROVED,
        actor=TransitionActor.HUMAN,
        reason="Exact plan approved",
        approval_id=(
            "approval-20260813t120000z-1234abcd"
        ),
        occurred_at=NOW + timedelta(seconds=1),
    )


def test_transitions_through_success() -> None:
    planned = initial_state()
    approved = approve(planned)

    executing = transition_state(
        approved,
        to_state=WorkflowState.EXECUTING,
        actor=TransitionActor.EXECUTOR,
        reason="Approved execution began",
        occurred_at=NOW + timedelta(seconds=2),
    )

    validating = transition_state(
        executing,
        to_state=WorkflowState.VALIDATING,
        actor=TransitionActor.VERIFIER,
        reason="Deterministic validation began",
        occurred_at=NOW + timedelta(seconds=3),
    )

    completed = transition_state(
        validating,
        to_state=WorkflowState.VALIDATED_SUCCESS,
        actor=TransitionActor.VERIFIER,
        reason="All deterministic checks passed",
        occurred_at=NOW + timedelta(seconds=4),
        trace_path="traces/transition-test.json",
        report_path="reports/transition-test.md",
    )

    assert completed.revision == 4
    assert completed.current_state == (
        WorkflowState.VALIDATED_SUCCESS
    )
    assert len(completed.transitions) == 5
    assert completed.failure is None


def test_rejects_skipping_approval() -> None:
    with pytest.raises(
        WorkflowStateError,
        match="not allowed",
    ):
        transition_state(
            initial_state(),
            to_state=WorkflowState.EXECUTING,
            actor=TransitionActor.EXECUTOR,
            reason="Unsafe skip",
            occurred_at=NOW + timedelta(seconds=1),
        )


def test_only_human_can_approve() -> None:
    with pytest.raises(
        WorkflowStateError,
        match="only a human",
    ):
        transition_state(
            initial_state(),
            to_state=WorkflowState.APPROVED,
            actor=TransitionActor.EXECUTOR,
            reason="Invalid actor",
            approval_id=(
                "approval-20260813t120000z-1234abcd"
            ),
            occurred_at=NOW + timedelta(seconds=1),
        )


def test_failure_state_requires_evidence() -> None:
    executing = transition_state(
        approve(initial_state()),
        to_state=WorkflowState.EXECUTING,
        actor=TransitionActor.EXECUTOR,
        reason="Execution began",
        occurred_at=NOW + timedelta(seconds=2),
    )

    with pytest.raises(
        WorkflowStateError,
        match="requires failure evidence",
    ):
        transition_state(
            executing,
            to_state=WorkflowState.EXECUTION_FAILED,
            actor=TransitionActor.EXECUTOR,
            reason="Execution failed",
            occurred_at=NOW + timedelta(seconds=3),
        )


def test_execution_failure_requires_manual_review() -> None:
    executing = transition_state(
        approve(initial_state()),
        to_state=WorkflowState.EXECUTING,
        actor=TransitionActor.EXECUTOR,
        reason="Execution began",
        occurred_at=NOW + timedelta(seconds=2),
    )

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
        executing,
        to_state=WorkflowState.EXECUTION_FAILED,
        actor=TransitionActor.EXECUTOR,
        reason="Execution outcome requires review",
        failure=failure,
        occurred_at=NOW + timedelta(seconds=3),
    )

    assert failed.failure is not None
    assert failed.failure.retry == (
        RetryDisposition.MANUAL_REVIEW
    )


def test_terminal_state_cannot_transition() -> None:
    executing = transition_state(
        approve(initial_state()),
        to_state=WorkflowState.EXECUTING,
        actor=TransitionActor.EXECUTOR,
        reason="Execution began",
        occurred_at=NOW + timedelta(seconds=2),
    )

    failure = failure_from_exception(
        GeoAgentError(
            "Execution failed",
            code="execution_failed",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.EXECUTION,
    )

    failed = transition_state(
        executing,
        to_state=WorkflowState.EXECUTION_FAILED,
        actor=TransitionActor.EXECUTOR,
        reason="Execution failed",
        failure=failure,
        occurred_at=NOW + timedelta(seconds=3),
    )

    with pytest.raises(
        WorkflowStateError,
        match="not allowed",
    ):
        transition_state(
            failed,
            to_state=WorkflowState.EXECUTING,
            actor=TransitionActor.EXECUTOR,
            reason="Unsafe retry",
            occurred_at=NOW + timedelta(seconds=4),
        )


def test_atomic_revision_update(
    tmp_path: Path,
) -> None:
    planned = initial_state()

    path = write_initial_state(
        planned,
        state_root=tmp_path,
    )

    approved = approve(planned)

    write_updated_state(
        approved,
        state_root=tmp_path,
        expected_revision=0,
    )

    loaded = load_state(
        path,
        state_root=tmp_path,
    )

    assert loaded.current_state == WorkflowState.APPROVED
    assert loaded.revision == 1


def test_stale_revision_is_rejected(
    tmp_path: Path,
) -> None:
    planned = initial_state()

    write_initial_state(
        planned,
        state_root=tmp_path,
    )

    approved = approve(planned)

    write_updated_state(
        approved,
        state_root=tmp_path,
        expected_revision=0,
    )

    with pytest.raises(
        WorkflowStateError,
        match="revision conflict",
    ):
        write_updated_state(
            approved,
            state_root=tmp_path,
            expected_revision=0,
        )
        
def test_updated_state_remains_container_readable(
    tmp_path: Path,
) -> None:
    planned = initial_state()

    path = write_initial_state(
        planned,
        state_root=tmp_path,
    )

    approved = approve(planned)

    write_updated_state(
        approved,
        state_root=tmp_path,
        expected_revision=0,
    )

    mode = path.stat().st_mode & 0o777

    assert mode == 0o644
