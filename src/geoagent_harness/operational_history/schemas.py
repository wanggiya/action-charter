"""Typed identities and operational-history records."""

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


_IDENTIFIER = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)
_FACT_KEY = re.compile(
    r"^[a-z][a-z0-9_]{0,63}$"
)
_VERSION_KEY = re.compile(
    r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$"
)


class AgentRole(str, Enum):
    """Stable logical roles that may emit operational facts."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"
    BUILDER = "builder"
    GIS = "gis"
    WORKFLOW_RUNNER = "workflow_runner"
    HARNESS = "harness"


class OperationalEventType(str, Enum):
    """Bounded event vocabulary for observable lifecycle facts."""

    RUN_STARTED = "run_started"
    INPUT_VALIDATED = "input_validated"
    PROPOSAL_GENERATED = "proposal_generated"
    POLICY_ASSESSED = "policy_assessed"
    APPROVAL_VERIFIED = "approval_verified"
    TOOL_REQUESTED = "tool_requested"
    TOOL_COMPLETED = "tool_completed"
    VALIDATION_COMPLETED = "validation_completed"
    EVIDENCE_PERSISTED = "evidence_persisted"
    RUN_FAILED = "run_failed"
    RUN_COMPLETED = "run_completed"


class OperationalIdentity(BaseModel):
    """Identity shared by every event from one agent invocation."""

    model_config = ConfigDict(extra="forbid")

    agent_id: AgentRole
    agent_instance_id: str
    agent_run_id: str
    task_id: str
    correlation_id: str
    parent_run_id: str | None = None

    @field_validator(
        "agent_instance_id",
        "agent_run_id",
        "task_id",
        "correlation_id",
        "parent_run_id",
    )
    @classmethod
    def identifiers_must_be_safe(
        cls,
        value: str | None,
    ) -> str | None:
        if value is not None and not _IDENTIFIER.fullmatch(
            value
        ):
            raise ValueError(
                "operational identifiers contain unsafe characters"
            )

        return value

    @model_validator(mode="after")
    def parent_must_be_distinct(
        self,
    ) -> "OperationalIdentity":
        if self.parent_run_id == self.agent_run_id:
            raise ValueError(
                "an agent run cannot be its own parent"
            )

        return self


class OperationalEvent(BaseModel):
    """One immutable, secret-redacted operational fact."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    event_id: str
    sequence: int = Field(ge=0)
    identity: OperationalIdentity
    event_type: OperationalEventType
    occurred_at: datetime

    status: str | None = Field(
        default=None,
        max_length=120,
    )
    recipe_id: str | None = None
    skill_id: str | None = None
    tool_name: str | None = None
    policy_decision: str | None = Field(
        default=None,
        max_length=500,
    )
    failure_code: str | None = None

    artifact_digests: dict[str, str] = Field(
        default_factory=dict,
        max_length=20,
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    versions: dict[str, str] = Field(
        default_factory=dict,
        max_length=20,
    )
    facts: dict[
        str,
        str | int | float | bool | None,
    ] = Field(
        default_factory=dict,
        max_length=20,
    )

    previous_event_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    secrets_redacted: Literal[True] = True
    private_reasoning_recorded: Literal[False] = False

    @field_validator(
        "event_id",
        "recipe_id",
        "skill_id",
        "tool_name",
        "failure_code",
    )
    @classmethod
    def optional_identifiers_must_be_safe(
        cls,
        value: str | None,
    ) -> str | None:
        if value is not None and not _IDENTIFIER.fullmatch(
            value
        ):
            raise ValueError(
                "event identifiers contain unsafe characters"
            )

        return value

    @field_validator("occurred_at")
    @classmethod
    def timestamp_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "operational event timestamp must include a timezone"
            )

        return value

    @field_validator("artifact_digests")
    @classmethod
    def artifact_digests_must_be_bounded(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        for name, digest in value.items():
            if not _FACT_KEY.fullmatch(name):
                raise ValueError(
                    "artifact digest names must be safe identifiers"
                )
            if not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise ValueError(
                    "artifact digests must be lowercase SHA-256"
                )

        return value

    @field_validator("evidence_references")
    @classmethod
    def evidence_references_must_be_safe(
        cls,
        value: list[str],
    ) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError(
                "evidence references must be unique"
            )

        for reference in value:
            if (
                not reference
                or len(reference) > 500
                or "\x00" in reference
                or "\n" in reference
                or "\r" in reference
            ):
                raise ValueError(
                    "evidence references must be bounded single lines"
                )

        return value

    @field_validator("versions")
    @classmethod
    def versions_must_be_bounded(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        for name, version in value.items():
            if not _VERSION_KEY.fullmatch(name):
                raise ValueError(
                    "version names must be safe identifiers"
                )
            if not version or len(version) > 200:
                raise ValueError(
                    "versions must contain bounded values"
                )

        return value

    @field_validator("facts")
    @classmethod
    def facts_must_be_bounded(
        cls,
        value: dict[
            str,
            str | int | float | bool | None,
        ],
    ) -> dict[
        str,
        str | int | float | bool | None,
    ]:
        forbidden_fragments = (
            "secret",
            "password",
            "token",
            "credential",
            "chain_of_thought",
            "reasoning",
        )

        for name, fact in value.items():
            if not _FACT_KEY.fullmatch(name):
                raise ValueError(
                    "operational fact names must be safe identifiers"
                )
            if any(
                fragment in name
                for fragment in forbidden_fragments
            ):
                raise ValueError(
                    "operational facts cannot contain sensitive fields"
                )
            if isinstance(fact, str) and len(fact) > 1000:
                raise ValueError(
                    "operational fact values exceed the size limit"
                )

        return value

    @model_validator(mode="after")
    def sequence_and_outcome_are_consistent(
        self,
    ) -> "OperationalEvent":
        if self.sequence == 0:
            if self.event_type != OperationalEventType.RUN_STARTED:
                raise ValueError(
                    "the first run event must be run_started"
                )
            if self.previous_event_sha256 is not None:
                raise ValueError(
                    "the first run event cannot reference a predecessor"
                )
        elif self.previous_event_sha256 is None:
            raise ValueError(
                "later run events require a predecessor digest"
            )

        if (
            self.event_type == OperationalEventType.RUN_FAILED
            and self.failure_code is None
        ):
            raise ValueError(
                "run_failed requires a failure code"
            )

        if (
            self.event_type != OperationalEventType.RUN_FAILED
            and self.failure_code is not None
        ):
            raise ValueError(
                "failure codes are allowed only on run_failed"
            )

        return self


class OperationalTimeline(BaseModel):
    """Deterministic correlated view of validated events."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    correlation_id: str
    agent_ids: list[AgentRole] = Field(min_length=1)
    agent_run_ids: list[str] = Field(min_length=1)
    started_at: datetime
    finished_at: datetime
    events: list[OperationalEvent] = Field(min_length=1)
    event_count: int = Field(ge=1)
    failed_run_ids: list[str] = Field(default_factory=list)
    history_validated: Literal[True] = True
    secrets_redacted: Literal[True] = True
    private_reasoning_recorded: Literal[False] = False

    @model_validator(mode="after")
    def summary_must_match_events(
        self,
    ) -> "OperationalTimeline":
        if self.event_count != len(self.events):
            raise ValueError(
                "timeline event count is inconsistent"
            )
        if self.started_at > self.finished_at:
            raise ValueError(
                "timeline timestamps are inconsistent"
            )

        return self
