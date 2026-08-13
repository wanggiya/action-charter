"""Safe persistence for durable workflow state."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.redaction import redact_value
from geoagent_harness.workflow_state.schemas import (
    StateTransition,
    TransitionActor,
    WorkflowState,
    WorkflowStateRecord,
)
from geoagent_harness.failures import (
    FailureRecord,
)


_MAX_STATE_BYTES = 1_000_000

_ALLOWED_TRANSITIONS: dict[
    WorkflowState,
    frozenset[WorkflowState],
] = {
    WorkflowState.PLANNED: frozenset(
        {
            WorkflowState.APPROVED,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.APPROVED: frozenset(
        {
            WorkflowState.EXECUTING,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.EXECUTING: frozenset(
        {
            WorkflowState.VALIDATING,
            WorkflowState.EXECUTION_FAILED,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.VALIDATING: frozenset(
        {
            WorkflowState.VALIDATED_SUCCESS,
            WorkflowState.VALIDATION_FAILED,
            WorkflowState.EXECUTION_FAILED,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.VALIDATED_SUCCESS: frozenset(),
    WorkflowState.VALIDATION_FAILED: frozenset(),
    WorkflowState.EXECUTION_FAILED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
}


class WorkflowStateError(RuntimeError):
    """Raised when workflow state cannot be handled safely."""


def state_path(
    *,
    state_root: Path,
    task_id: str,
) -> Path:
    """Resolve one state file beneath its trusted root."""
    root = state_root.resolve()

    candidate = (
        root / f"{task_id}.state.json"
    ).resolve()

    if candidate.parent != root:
        raise WorkflowStateError(
            "workflow state path escaped its "
            "approved root"
        )

    return candidate


def create_initial_state(
    *,
    task_id: str,
    plan_sha256: str,
    occurred_at: datetime | None = None,
) -> WorkflowStateRecord:
    """Create an in-memory initial planned state."""
    active_time = (
        occurred_at
        or datetime.now(timezone.utc)
    )

    initial_transition = StateTransition(
        sequence=0,
        from_state=None,
        to_state=WorkflowState.PLANNED,
        actor=TransitionActor.PLANNER,
        reason="Validated plan was created",
        occurred_at=active_time,
    )

    return WorkflowStateRecord(
        task_id=task_id,
        plan_sha256=plan_sha256,
        current_state=WorkflowState.PLANNED,
        revision=0,
        transitions=[initial_transition],
        created_at=active_time,
        updated_at=active_time,
    )


def write_initial_state(
    state: WorkflowStateRecord,
    *,
    state_root: Path,
) -> Path:
    """Atomically create state without overwriting."""
    if state.revision != 0:
        raise WorkflowStateError(
            "initial state must have revision zero"
        )

    root = state_root.resolve()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = state_path(
        state_root=root,
        task_id=state.task_id,
    )

    payload = redact_value(
        state.model_dump(mode="json")
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{state.task_id}.",
        suffix=".tmp",
        dir=root,
    )

    temporary_path = Path(temporary_name)

    try:
        os.fchmod(
            descriptor,
            0o644,
        )
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(
                payload,
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        try:
            os.link(
                temporary_path,
                path,
            )
        except FileExistsError as exc:
            raise WorkflowStateError(
                "workflow state already exists; "
                "overwriting is blocked"
            ) from exc

        directory_descriptor = os.open(
            root,
            os.O_RDONLY,
        )

        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)

    except WorkflowStateError:
        raise
    except OSError as exc:
        raise WorkflowStateError(
            "workflow state could not be written"
        ) from exc
    finally:
        temporary_path.unlink(
            missing_ok=True,
        )

    return path


def load_state(
    path: Path,
    *,
    state_root: Path,
) -> WorkflowStateRecord:
    """Load and validate state beneath a trusted root."""
    root = state_root.resolve()
    resolved = path.resolve()

    if resolved.parent != root:
        raise WorkflowStateError(
            "workflow state path escaped its "
            "approved root"
        )

    if not resolved.is_file():
        raise WorkflowStateError(
            "workflow state file does not exist"
        )

    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise WorkflowStateError(
            "workflow state could not be inspected"
        ) from exc

    if size > _MAX_STATE_BYTES:
        raise WorkflowStateError(
            "workflow state exceeds the size limit"
        )

    try:
        payload = json.loads(
            resolved.read_text(encoding="utf-8")
        )

        return WorkflowStateRecord.model_validate(
            payload
        )
    except UnicodeDecodeError as exc:
        raise WorkflowStateError(
            "workflow state is not UTF-8"
        ) from exc
    except json.JSONDecodeError as exc:
        raise WorkflowStateError(
            "workflow state is not valid JSON"
        ) from exc
    except ValidationError as exc:
        raise WorkflowStateError(
            "workflow state failed schema validation"
        ) from exc
    except OSError as exc:
        raise WorkflowStateError(
            "workflow state could not be read"
        ) from exc
        
def transition_state(
    state: WorkflowStateRecord,
    *,
    to_state: WorkflowState,
    actor: TransitionActor,
    reason: str,
    occurred_at: datetime | None = None,
    approval_id: str | None = None,
    failure: FailureRecord | None = None,
    trace_path: str | None = None,
    report_path: str | None = None,
) -> WorkflowStateRecord:
    """Create the next state after deterministic policy checks."""
    allowed = _ALLOWED_TRANSITIONS[
        state.current_state
    ]

    if to_state not in allowed:
        raise WorkflowStateError(
            "transition is not allowed: "
            f"{state.current_state.value} -> "
            f"{to_state.value}"
        )

    active_time = (
        occurred_at
        or datetime.now(timezone.utc)
    )

    if active_time < state.updated_at:
        raise WorkflowStateError(
            "transition timestamp cannot precede "
            "the current state"
        )

    active_approval_id = (
        approval_id
        if approval_id is not None
        else state.approval_id
    )

    if (
        to_state
        in {
            WorkflowState.APPROVED,
            WorkflowState.EXECUTING,
            WorkflowState.VALIDATING,
            WorkflowState.VALIDATED_SUCCESS,
            WorkflowState.VALIDATION_FAILED,
            WorkflowState.EXECUTION_FAILED,
        }
        and active_approval_id is None
    ):
        raise WorkflowStateError(
            "approval_id is required for this "
            "transition"
        )

    failed_states = {
        WorkflowState.VALIDATION_FAILED,
        WorkflowState.EXECUTION_FAILED,
        WorkflowState.CANCELLED,
    }

    if to_state in failed_states and failure is None:
        raise WorkflowStateError(
            "failed or cancelled state requires "
            "failure evidence"
        )

    if to_state not in failed_states and failure is not None:
        raise WorkflowStateError(
            "failure evidence is allowed only for "
            "failed or cancelled states"
        )

    if (
        to_state == WorkflowState.APPROVED
        and actor != TransitionActor.HUMAN
    ):
        raise WorkflowStateError(
            "only a human actor may approve a plan"
        )

    if (
        to_state == WorkflowState.EXECUTING
        and actor != TransitionActor.EXECUTOR
    ):
        raise WorkflowStateError(
            "only the executor may begin execution"
        )

    if (
        to_state
        in {
            WorkflowState.VALIDATING,
            WorkflowState.VALIDATED_SUCCESS,
            WorkflowState.VALIDATION_FAILED,
        }
        and actor != TransitionActor.VERIFIER
    ):
        raise WorkflowStateError(
            "only the verifier may record validation "
            "transitions"
        )

    if (
        to_state == WorkflowState.CANCELLED
        and actor != TransitionActor.OPERATOR
    ):
        raise WorkflowStateError(
            "only the operator may cancel a workflow"
        )

    transition = StateTransition(
        sequence=state.revision + 1,
        from_state=state.current_state,
        to_state=to_state,
        actor=actor,
        reason=reason,
        occurred_at=active_time,
        failure=failure,
    )

    return state.model_copy(
        update={
            "approval_id": active_approval_id,
            "current_state": to_state,
            "revision": state.revision + 1,
            "transitions": [
                *state.transitions,
                transition,
            ],
            "trace_path": (
                trace_path
                if trace_path is not None
                else state.trace_path
            ),
            "report_path": (
                report_path
                if report_path is not None
                else state.report_path
            ),
            "failure": failure,
            "updated_at": active_time,
        }
    )


def write_updated_state(
    state: WorkflowStateRecord,
    *,
    state_root: Path,
    expected_revision: int,
) -> Path:
    """Atomically replace the expected prior state revision."""
    root = state_root.resolve()

    path = state_path(
        state_root=root,
        task_id=state.task_id,
    )

    current = load_state(
        path,
        state_root=root,
    )

    if current.task_id != state.task_id:
        raise WorkflowStateError(
            "workflow state task identity changed"
        )

    if current.plan_sha256 != state.plan_sha256:
        raise WorkflowStateError(
            "workflow state plan identity changed"
        )

    if current.revision != expected_revision:
        raise WorkflowStateError(
            "workflow state revision conflict"
        )

    if state.revision != expected_revision + 1:
        raise WorkflowStateError(
            "updated state revision is invalid"
        )

    payload = redact_value(
        state.model_dump(mode="json")
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{state.task_id}.",
        suffix=".tmp",
        dir=root,
    )

    temporary_path = Path(temporary_name)

    try:
        os.fchmod(
            descriptor,
            0o644,
        )
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(
                payload,
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(
            temporary_path,
            path,
        )

        directory_descriptor = os.open(
            root,
            os.O_RDONLY,
        )

        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)

    except OSError as exc:
        raise WorkflowStateError(
            "updated workflow state could not "
            "be written"
        ) from exc
    finally:
        temporary_path.unlink(
            missing_ok=True,
        )

    return path