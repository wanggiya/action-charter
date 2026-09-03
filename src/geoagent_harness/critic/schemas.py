"""Structured, deterministic evidence supplied to the Critic Agent."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

class CriticAssessment(BaseModel):
    """Schema-constrained assessment produced by the model."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]

    conclusion: Literal[
        "supported",
        "not_supported",
        "incomplete",
    ]

    success_claimed: bool

    summary: str = Field(
        min_length=1,
        max_length=3000,
    )
    validation_basis: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    additional_risks: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    recommendations: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    edits_performed: Literal[False] = False
    database_actions_performed: Literal[False] = False


class CriticResult(BaseModel):
    """Validated in-memory result returned by the Critic Agent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: Literal["critic"] = "critic"
    model: str
    task_id: str

    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]

    evidence_references: list[EvidenceReference]
    evidence_gaps: list[str]
    workflow_warnings: list[str]
    human_corrections: list[str]

    assessment: CriticAssessment


class CriticResultRecord(BaseModel):
    """Immutable wrapper for one validated Critic result."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    record_type: Literal[
        "critic_result_record"
    ] = "critic_result_record"

    task_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]
    critic_result_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    critic_result: CriticResult
    recorded_at: datetime

    critic_result_recorded: Literal[True] = True
    authoritative_status_changed: Literal[False] = False
    release_created: Literal[False] = False
    filesystem_artifacts_modified: Literal[False] = False
    database_modified: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("recorded_at")
    @classmethod
    def recorded_at_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Critic record timestamp must include a timezone"
            )
        return value

    @model_validator(mode="after")
    def identities_and_outcome_must_match(
        self,
    ) -> "CriticResultRecord":
        result = self.critic_result
        statuses = {
            self.deterministic_status,
            result.deterministic_status,
            result.assessment.deterministic_status,
        }
        if len(statuses) != 1:
            raise ValueError(
                "Critic record deterministic statuses do not match"
            )
        if self.task_id != result.task_id:
            raise ValueError(
                "Critic record task identities do not match"
            )

        expected = {
            "validated_success": ("supported", True),
            "validation_failed": ("not_supported", False),
            "execution_failed": ("not_supported", False),
            "incomplete_evidence": ("incomplete", False),
        }
        conclusion, success_claimed = expected[
            self.deterministic_status
        ]
        if (
            result.assessment.conclusion != conclusion
            or result.assessment.success_claimed
            is not success_claimed
        ):
            raise ValueError(
                "Critic record conclusion conflicts with "
                "deterministic status"
            )
        return self


class CriticResultStorageResult(BaseModel):
    """Result of immutable Critic-record persistence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]
    critic_result_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    critic_record_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    record_directory: str
    record_file: str

    critic_result_recorded: Literal[True] = True
    authoritative_status_changed: Literal[False] = False
    release_created: Literal[False] = False
    execution_performed: Literal[False] = False

class EvidenceReference(BaseModel):
    """Cryptographic reference to one trusted evidence file."""

    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ValidationEvidence(BaseModel):
    """Important deterministic PostGIS validation facts."""

    model_config = ConfigDict(extra="forbid")

    passed: bool | None = None
    table_exists: bool | None = None
    geometry_column_exists: bool | None = None
    row_count: int | None = None
    srid: int | None = None
    geometry_type: str | None = None
    invalid_geometry_count: int | None = None
    null_geometry_count: int | None = None
    extent: Any | None = None
    failed_checks: list[str] = Field(default_factory=list)


class ApprovalEvidence(BaseModel):
    """Approval facts associated with the exact planned workflow."""

    model_config = ConfigDict(extra="forbid")

    approval_id: str | None = None
    plan_sha256: str | None = None
    approved_step_ids: list[str] = Field(default_factory=list)
    complete: bool = False


class CriticEvidencePack(BaseModel):
    """Concise, secret-redacted evidence for one critic invocation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    original_request: str

    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]
    trace_final_status: str
    validation_passed: bool | None

    selected_skills: list[str]
    validation: ValidationEvidence
    approval: ApprovalEvidence

    artifacts: list[str]
    warnings: list[str]
    human_corrections: list[str]
    evidence_gaps: list[str]

    timestamps: dict[str, str]
    versions: dict[str, str]

    report_excerpt: str
    evidence_references: list[EvidenceReference]

    def as_prompt_payload(self) -> dict[str, Any]:
        """Return JSON-compatible content for a model prompt."""

        return self.model_dump(mode="json")
