"""Read-only assessment of durable workflow state."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from geoagent_harness.failures import (
    RetryDisposition,
)
from geoagent_harness.workflow_state.schemas import (
    WorkflowState,
    WorkflowStateRecord,
)


class ResumeDisposition(str, Enum):
    """Deterministic resume recommendation."""

    RESUME_ALLOWED = "resume_allowed"
    MANUAL_REVIEW_REQUIRED = (
        "manual_review_required"
    )
    TERMINAL = "terminal"


class ResumeAssessment(BaseModel):
    """Read-only resume assessment for one workflow."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    plan_sha256: str
    current_state: WorkflowState
    revision: int = Field(ge=0)

    disposition: ResumeDisposition
    reason: str = Field(
        min_length=1,
        max_length=2000,
    )
    next_action: str = Field(
        min_length=1,
        max_length=2000,
    )

    database_write_may_have_started: bool
    automatic_execution_allowed: Literal[False] = False
    state_modified: Literal[False] = False


def _execution_may_have_started(
    state: WorkflowStateRecord,
) -> bool:
    """Return whether history entered execution."""
    execution_states = {
        WorkflowState.EXECUTING,
        WorkflowState.VALIDATING,
        WorkflowState.VALIDATED_SUCCESS,
        WorkflowState.VALIDATION_FAILED,
        WorkflowState.EXECUTION_FAILED,
    }

    return any(
        transition.to_state in execution_states
        for transition in state.transitions
    )


def assess_resume(
    state: WorkflowStateRecord,
) -> ResumeAssessment:
    """Assess state without executing or modifying it."""
    current = state.current_state

    write_may_have_started = (
        _execution_may_have_started(state)
    )

    if current == WorkflowState.PLANNED:
        disposition = (
            ResumeDisposition.RESUME_ALLOWED
        )
        reason = (
            "The workflow has not been approved or "
            "executed."
        )
        next_action = (
            "Obtain an exact-plan human approval "
            "before execution."
        )

    elif current == WorkflowState.APPROVED:
        disposition = (
            ResumeDisposition.RESUME_ALLOWED
        )
        reason = (
            "The exact plan is approved and no "
            "execution transition is recorded."
        )
        next_action = (
            "The Executor may begin the approved "
            "workflow after revalidating the plan "
            "and approval."
        )

    elif current in {
        WorkflowState.EXECUTING,
        WorkflowState.VALIDATING,
        WorkflowState.EXECUTION_FAILED,
        WorkflowState.VALIDATION_FAILED,
    }:
        disposition = (
            ResumeDisposition.MANUAL_REVIEW_REQUIRED
        )
        reason = (
            "A PostGIS write may have started; "
            "automatic retry could duplicate or "
            "conflict with existing data."
        )
        next_action = (
            "Inspect the target PostGIS table, trace, "
            "report, and approval evidence before "
            "choosing any recovery action."
        )

    elif current == WorkflowState.CANCELLED:
        if write_may_have_started:
            disposition = (
                ResumeDisposition
                .MANUAL_REVIEW_REQUIRED
            )
            reason = (
                "Cancellation occurred after execution "
                "may have started, so the database "
                "outcome is uncertain."
            )
            next_action = (
                "Inspect PostGIS and existing artifacts "
                "before creating a new approved task."
            )
        else:
            disposition = ResumeDisposition.TERMINAL
            reason = (
                "The workflow was cancelled before "
                "execution began."
            )
            next_action = (
                "Create a new plan and approval if the "
                "task should be attempted again."
            )

    elif current == WorkflowState.VALIDATED_SUCCESS:
        disposition = ResumeDisposition.TERMINAL
        reason = (
            "The workflow completed with deterministic "
            "validation success."
        )
        next_action = (
            "Use the recorded report and trace; no "
            "resume action is required."
        )

    else:
        raise ValueError(
            f"unsupported workflow state: {current}"
        )

    if (
        state.failure is not None
        and state.failure.retry
        == RetryDisposition.MANUAL_REVIEW
    ):
        disposition = (
            ResumeDisposition.MANUAL_REVIEW_REQUIRED
        )

        if not write_may_have_started:
            reason = (
                "The recorded failure explicitly "
                "requires manual review."
            )
            next_action = (
                "Review the structured failure and "
                "workflow evidence before proceeding."
            )

    return ResumeAssessment(
        task_id=state.task_id,
        plan_sha256=state.plan_sha256,
        current_state=current,
        revision=state.revision,
        disposition=disposition,
        reason=reason,
        next_action=next_action,
        database_write_may_have_started=(
            write_may_have_started
        ),
        automatic_execution_allowed=False,
        state_modified=False,
    )