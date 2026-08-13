"""Tests for durable workflow-state persistence."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.workflow_state import (
    StateTransition,
    TransitionActor,
    WorkflowState,
    WorkflowStateError,
    WorkflowStateRecord,
    create_initial_state,
    load_state,
    state_path,
    write_initial_state,
)


NOW = datetime(
    2026,
    8,
    12,
    12,
    0,
    tzinfo=timezone.utc,
)


def test_creates_initial_planned_state() -> None:
    state = create_initial_state(
        task_id="state-test",
        plan_sha256="a" * 64,
        occurred_at=NOW,
    )

    assert state.current_state == WorkflowState.PLANNED
    assert state.revision == 0
    assert state.approval_id is None
    assert state.failure is None
    assert len(state.transitions) == 1
    assert state.transitions[0].from_state is None
    assert (
        state.transitions[0].to_state
        == WorkflowState.PLANNED
    )


def test_initial_state_round_trip(
    tmp_path: Path,
) -> None:
    state = create_initial_state(
        task_id="round-trip",
        plan_sha256="b" * 64,
        occurred_at=NOW,
    )

    path = write_initial_state(
        state,
        state_root=tmp_path,
    )

    loaded = load_state(
        path,
        state_root=tmp_path,
    )

    assert loaded == state
    assert path.name == "round-trip.state.json"


def test_initial_state_cannot_be_overwritten(
    tmp_path: Path,
) -> None:
    state = create_initial_state(
        task_id="no-overwrite",
        plan_sha256="c" * 64,
        occurred_at=NOW,
    )

    write_initial_state(
        state,
        state_root=tmp_path,
    )

    with pytest.raises(
        WorkflowStateError,
        match="overwriting is blocked",
    ):
        write_initial_state(
            state,
            state_root=tmp_path,
        )


def test_state_path_cannot_escape_root(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / "outside.state.json"

    with pytest.raises(
        WorkflowStateError,
        match="escaped",
    ):
        load_state(
            outside,
            state_root=tmp_path,
        )


def test_rejects_non_contiguous_history() -> None:
    with pytest.raises(
        ValidationError,
        match="contiguous",
    ):
        WorkflowStateRecord(
            task_id="bad-history",
            plan_sha256="d" * 64,
            current_state=WorkflowState.APPROVED,
            revision=2,
            transitions=[
                StateTransition(
                    sequence=0,
                    from_state=None,
                    to_state=WorkflowState.PLANNED,
                    actor=TransitionActor.PLANNER,
                    reason="Plan created",
                    occurred_at=NOW,
                ),
                StateTransition(
                    sequence=2,
                    from_state=WorkflowState.PLANNED,
                    to_state=WorkflowState.APPROVED,
                    actor=TransitionActor.HUMAN,
                    reason="Plan approved",
                    occurred_at=NOW,
                ),
            ],
            created_at=NOW,
            updated_at=NOW,
        )


def test_rejects_unchained_history() -> None:
    with pytest.raises(
        ValidationError,
        match="not chained",
    ):
        WorkflowStateRecord(
            task_id="bad-chain",
            plan_sha256="e" * 64,
            current_state=WorkflowState.VALIDATING,
            revision=1,
            transitions=[
                StateTransition(
                    sequence=0,
                    from_state=None,
                    to_state=WorkflowState.PLANNED,
                    actor=TransitionActor.PLANNER,
                    reason="Plan created",
                    occurred_at=NOW,
                ),
                StateTransition(
                    sequence=1,
                    from_state=WorkflowState.EXECUTING,
                    to_state=WorkflowState.VALIDATING,
                    actor=TransitionActor.VERIFIER,
                    reason="Validation began",
                    occurred_at=NOW,
                ),
            ],
            created_at=NOW,
            updated_at=NOW,
        )


def test_failure_requires_terminal_failure_state() -> None:
    failure = failure_from_exception(
        GeoAgentError(
            "PostGIS result uncertain",
            code="postgis_result_uncertain",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        ),
        stage=FailureStage.EXECUTION,
    )

    with pytest.raises(
        ValidationError,
        match="failure evidence requires",
    ):
        WorkflowStateRecord(
            task_id="bad-failure",
            plan_sha256="f" * 64,
            current_state=WorkflowState.PLANNED,
            revision=0,
            transitions=[
                StateTransition(
                    sequence=0,
                    from_state=None,
                    to_state=WorkflowState.PLANNED,
                    actor=TransitionActor.PLANNER,
                    reason="Plan created",
                    occurred_at=NOW,
                ),
            ],
            failure=failure,
            created_at=NOW,
            updated_at=NOW,
        )


def test_loaded_state_rejects_unknown_fields(
    tmp_path: Path,
) -> None:
    state = create_initial_state(
        task_id="unknown-field",
        plan_sha256="1" * 64,
        occurred_at=NOW,
    )

    path = write_initial_state(
        state,
        state_root=tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    path.write_text(
        content.replace(
            '"schema_version": "1.0"',
            (
                '"schema_version": "1.0", '
                '"unexpected": true'
            ),
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        WorkflowStateError,
        match="schema validation",
    ):
        load_state(
            path,
            state_root=tmp_path,
        )
        
def test_state_file_is_readable_by_container_user(
    tmp_path: Path,
) -> None:
    state = create_initial_state(
        task_id="readable-state",
        plan_sha256="2" * 64,
        occurred_at=NOW,
    )

    path = write_initial_state(
        state,
        state_root=tmp_path,
    )

    mode = path.stat().st_mode & 0o777

    assert mode == 0o644
    