"""Structured, deterministic evidence supplied to the Critic Agent."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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