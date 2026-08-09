"""Schemas for human approval records."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_APPROVAL_ID = re.compile(
    r"^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$"
)

_SHA256 = re.compile(r"^[a-f0-9]{64}$")

_STEP_ID = re.compile(r"^step_[1-9][0-9]*$")


class ApprovalRecord(BaseModel):
    """One append-only decision for an exact plan digest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    approval_id: str
    plan_sha256: str
    decision: Literal["approved", "denied"]
    step_ids: list[str] = Field(min_length=1)
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    human_corrections: list[str] = Field(
        default_factory=list
    )
    created_at: datetime
    expires_at: datetime | None = None
    secrets_redacted: Literal[True] = True

    @field_validator("approval_id")
    @classmethod
    def validate_approval_id(
        cls,
        value: str,
    ) -> str:
        if not _APPROVAL_ID.fullmatch(value):
            raise ValueError(
                "approval_id has an invalid format"
            )

        return value

    @field_validator("plan_sha256")
    @classmethod
    def validate_plan_sha256(
        cls,
        value: str,
    ) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError(
                "plan_sha256 must be a SHA-256 digest"
            )

        return value

    @field_validator("step_ids")
    @classmethod
    def validate_step_ids(
        cls,
        values: list[str],
    ) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError(
                "step_ids must not contain duplicates"
            )

        if not all(
            _STEP_ID.fullmatch(value)
            for value in values
        ):
            raise ValueError(
                "step_ids contain an invalid step ID"
            )

        return values

    @model_validator(mode="after")
    def validate_expiration(
        self,
    ) -> "ApprovalRecord":
        if (
            self.expires_at is not None
            and self.expires_at <= self.created_at
        ):
            raise ValueError(
                "expires_at must be later than created_at"
            )

        return self


class ApprovalVerification(BaseModel):
    """Result of deterministic approval verification."""

    model_config = ConfigDict(extra="forbid")

    approved: bool
    approval_id: str | None = None
    plan_sha256: str
    approved_step_ids: list[str] = Field(
        default_factory=list
    )
    reason: str