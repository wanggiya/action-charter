"""Strict schemas for immutable PostGIS rollback approvals."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROLLBACK_APPROVAL_STEP_IDS = ["step_4_restore_candidate", "step_5_restore_reference"]


class PostGISRollbackApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    approval_id: str = Field(pattern=r"^postgis-rollback-approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    rollback_plan_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approved_step_ids: list[Literal["step_4_restore_candidate", "step_5_restore_reference"]] = Field(max_length=2)
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    human_corrections: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(max_length=32)
    created_at: datetime
    expires_at: datetime | None = None
    secrets_redacted: Literal[True] = True
    approval_recorded: Literal[True] = True
    rollback_performed: Literal[False] = False
    database_modified: Literal[False] = False

    @model_validator(mode="after")
    def scope_is_exact(self):
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        if self.decision == "approved":
            if self.approved_step_ids != ROLLBACK_APPROVAL_STEP_IDS:
                raise ValueError("approved decision requires exact rollback scope")
            if self.human_corrections:
                raise ValueError("approved rollback cannot contain corrections")
        elif self.approved_step_ids:
            raise ValueError("denied decision cannot approve steps")
        return self


class PostGISRollbackApprovalStorageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    approval_id: str
    rollback_plan_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_directory: str
    approval_file: str
    decision: Literal["approved", "denied"]
    approved_step_ids: list[str]
    database_modified: Literal[False] = False
