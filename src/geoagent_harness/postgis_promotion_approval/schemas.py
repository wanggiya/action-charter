"""Strict schemas for immutable PostGIS promotion approvals."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


APPROVAL_STEP_IDS = [
    "step_4_archive_reference",
    "step_5_promote_candidate",
]


class PostGISPromotionApproval(BaseModel):
    """One human decision bound to an exact promotion plan."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    approval_id: str = Field(
        pattern=(
            r"^postgis-promotion-approval-"
            r"[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$"
        )
    )
    plan_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$", max_length=100)
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assessment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approved_step_ids: list[Literal[
        "step_4_archive_reference",
        "step_5_promote_candidate",
    ]] = Field(max_length=2)
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    human_corrections: list[
        Annotated[str, Field(min_length=1, max_length=500)]
    ] = Field(max_length=32)
    created_at: datetime
    expires_at: datetime | None = None
    secrets_redacted: Literal[True] = True
    approval_recorded: Literal[True] = True
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False
    database_modified: Literal[False] = False

    @model_validator(mode="after")
    def decision_scope_is_exact(self) -> "PostGISPromotionApproval":
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        if self.decision == "approved":
            if self.approved_step_ids != APPROVAL_STEP_IDS:
                raise ValueError("approved decision requires exact mutation scope")
            if self.human_corrections:
                raise ValueError(
                    "approved plan cannot contain human corrections; regenerate it"
                )
        elif self.approved_step_ids:
            raise ValueError("denied decision cannot approve steps")
        return self


class PostGISPromotionApprovalStorageResult(BaseModel):
    """Verified location and identity of an immutable approval."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    approval_id: str
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_directory: str
    approval_file: str
    decision: Literal["approved", "denied"]
    approved_step_ids: list[str]
    approval_recorded: Literal[True] = True
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False
    database_modified: Literal[False] = False
