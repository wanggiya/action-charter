"""Existing immutable-artifact action contracts, shared across transports."""
from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from geoagent_harness.contracts.planning import PlannerResult


class InterfaceApprovalDecision(BaseModel):
    """Exact human decision accepted by the local interface boundary."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["record_recipe_approval"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    valid_for_minutes: int | None = Field(default=None, ge=1, le=1440)


class InterfaceApprovalVerificationRequest(BaseModel):
    """Exact recorded decision selected for independent verification."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["verify_recipe_approval"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")


class InterfaceExecutionPreviewRequest(BaseModel):
    """Exact verified artifacts selected for a non-executing preview."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["prepare_execution_preview"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")


class InterfaceRecipeExecutionRequest(BaseModel):
    """One explicit confirmation of an exact previewed execution."""

    model_config = ConfigDict(extra="forbid")

    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    action: Literal["execute_exact_preview"]
    recipe_filename: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$")
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^recipe-approval-[a-z0-9-]+\.json$")
    confirmed_execution_preview_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: Literal["execute_exact_preview"]


class InterfaceReviewedPlanSaveRequest(BaseModel):
    """Exact validated Planner result selected for immutable storage."""

    model_config = ConfigDict(extra="forbid")

    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    action: Literal["save_reviewed_plan"]
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=64)
    planner_result: PlannerResult

    @field_validator("allowed_skill_ids")
    @classmethod
    def skill_ids_are_unique_and_safe(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("allowed skill IDs must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in value):
            raise ValueError("allowed skill ID is invalid")
        return value


class InterfaceGeneratedPlanSaveRequest(InterfaceReviewedPlanSaveRequest):
    """Storage of a generated proposal is not human review or approval."""

    action: Literal["save_generated_plan"]


class InterfacePlanApprovalPreparationRequest(BaseModel):
    """Exact immutable plan selected for non-writing approval preparation."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["prepare_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfacePlanApprovalDecisionRequest(BaseModel):
    """One explicit human decision bound to an exact prepared plan request."""

    model_config = ConfigDict(extra="forbid")

    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    action: Literal["record_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    valid_for_minutes: int | None = Field(default=None, ge=1, le=1440)


class InterfacePlanApprovalVerificationRequest(BaseModel):
    """Exact recorded plan decision selected for independent verification."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["verify_plan_approval"]
    plan_filename: str = Field(pattern=r"^planner-plan\.[a-f0-9]{64}\.json$")
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_approval_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_filename: str = Field(pattern=r"^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}\.json$")


class InterfacePlanExecutionPreviewRequest(InterfacePlanApprovalVerificationRequest):
    """Exact verified evidence selected for non-executing envelope preview."""

    action: Literal["preview_plan_execution"]


class InterfacePlanRecipeCompilationRequest(InterfacePlanApprovalVerificationRequest):
    """Exact verified plan selected for non-writing recipe compilation."""

    action: Literal["compile_plan_recipe"]


class InterfacePlanRecipeSaveRequest(InterfacePlanApprovalVerificationRequest):
    """Exact reviewed Planner-derived recipe selected for immutable storage."""

    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    action: Literal["save_reviewed_plan_recipe"]
    confirmed_recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class EditRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['validate_plan_edit']
    planner_result: PlannerResult
