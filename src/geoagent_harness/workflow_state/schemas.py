"""Schemas for durable workflow state."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from geoagent_harness.failures import FailureRecord


_TASK_ID = re.compile(
    r"^[a-z0-9][a-z0-9_-]{0,80}$"
)


class WorkflowState(str, Enum):
    """Stable lifecycle states for one workflow."""

    PLANNED = "planned"
    APPROVED = "approved"
    EXECUTING = "executing"
    VALIDATING = "validating"
    VALIDATED_SUCCESS = "validated_success"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    CANCELLED = "cancelled"


class TransitionActor(str, Enum):
    """Trusted component responsible for a transition."""

    HARNESS = "harness"
    PLANNER = "planner"
    HUMAN = "human"
    EXECUTOR = "executor"
    VERIFIER = "verifier"
    OPERATOR = "operator"


class StateTransition(BaseModel):
    """One immutable entry in the transition history."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=0)
    from_state: WorkflowState | None
    to_state: WorkflowState
    actor: TransitionActor
    reason: str = Field(
        min_length=1,
        max_length=2000,
    )
    occurred_at: datetime
    failure: FailureRecord | None = None

    @field_validator("occurred_at")
    @classmethod
    def timestamp_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "occurred_at must include a timezone"
            )

        return value


class WorkflowStateRecord(BaseModel):
    """Durable state for one exact planned workflow."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    plan_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str | None = None

    current_state: WorkflowState
    revision: int = Field(ge=0)

    transitions: list[StateTransition] = Field(
        min_length=1
    )

    trace_path: str | None = None
    report_path: str | None = None

    failure: FailureRecord | None = None

    created_at: datetime
    updated_at: datetime

    secrets_redacted: Literal[True] = True

    @field_validator("task_id")
    @classmethod
    def task_id_is_safe(
        cls,
        value: str,
    ) -> str:
        if not _TASK_ID.fullmatch(value):
            raise ValueError(
                "task_id contains unsafe characters"
            )

        return value

    @field_validator(
        "created_at",
        "updated_at",
    )
    @classmethod
    def timestamps_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "state timestamps must include a timezone"
            )

        return value

    @model_validator(mode="after")
    def history_is_consistent(
        self,
    ) -> "WorkflowStateRecord":
        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at cannot precede created_at"
            )

        expected_sequences = list(
            range(len(self.transitions))
        )

        actual_sequences = [
            transition.sequence
            for transition in self.transitions
        ]

        if actual_sequences != expected_sequences:
            raise ValueError(
                "transition sequences must be contiguous"
            )

        if self.revision != len(self.transitions) - 1:
            raise ValueError(
                "revision must match the last transition"
            )

        first = self.transitions[0]

        if first.from_state is not None:
            raise ValueError(
                "initial transition must have no "
                "from_state"
            )

        if first.to_state != WorkflowState.PLANNED:
            raise ValueError(
                "initial transition must enter planned"
            )

        previous = first

        for transition in self.transitions[1:]:
            if transition.from_state != previous.to_state:
                raise ValueError(
                    "transition history is not chained"
                )

            if (
                transition.occurred_at
                < previous.occurred_at
            ):
                raise ValueError(
                    "transition timestamps are not "
                    "monotonic"
                )

            previous = transition

        if previous.to_state != self.current_state:
            raise ValueError(
                "current_state does not match history"
            )

        if self.updated_at != previous.occurred_at:
            raise ValueError(
                "updated_at must match the latest "
                "transition"
            )

        if (
            self.failure is not None
            and self.current_state
            not in {
                WorkflowState.VALIDATION_FAILED,
                WorkflowState.EXECUTION_FAILED,
                WorkflowState.CANCELLED,
            }
        ):
            raise ValueError(
                "failure evidence requires a failed "
                "or cancelled state"
            )

        return self