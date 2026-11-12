from __future__ import annotations
import re
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from geoagent_harness.contracts.critic import CriticResult
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.contracts.actions import InterfaceApprovalDecision, InterfaceApprovalVerificationRequest, InterfaceExecutionPreviewRequest, InterfaceRecipeExecutionRequest, InterfaceReviewedPlanSaveRequest, InterfaceGeneratedPlanSaveRequest, InterfacePlanApprovalPreparationRequest, InterfacePlanApprovalDecisionRequest, InterfacePlanApprovalVerificationRequest, InterfacePlanExecutionPreviewRequest, InterfacePlanRecipeCompilationRequest, InterfacePlanRecipeSaveRequest


class InterfaceContextRetrievalRequest(BaseModel):
    """Read-only candidates from explicit task selection; not reviewed memory."""
    model_config = ConfigDict(extra="forbid")
    action: Literal["retrieve_task_context"]
    query: str = Field(min_length=1, max_length=1000)
    task_ids: list[str] = Field(min_length=1, max_length=5)


class InterfaceContextReviewRequest(InterfaceContextRetrievalRequest):
    action: Literal["review_task_context"]
    confirmed_context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


class InterfaceIntentRequest(BaseModel):
    """Reasoning-only current request and explicit answers, without hidden history."""
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["reason_task_intent"]
    review_filename: str | None = Field(pattern=r"^context-review\.[a-f0-9]{64}\.json$")
    request: str = Field(min_length=1, max_length=4000)
    selected_input_path: str | None = Field(default=None, min_length=1, max_length=960)
    clarification_answers: list[str] = Field(default_factory=list, max_length=5)


class InterfaceIntentInspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["inspect_intent_proposal"]
    intent: dict[str, Any]


class InterfaceIntentReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["review_task_intent"]
    intent: dict[str, Any]
    confirmed_intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


class InterfaceIntentHandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["plan_reviewed_intent"]
    review_filename: str = Field(pattern=r"^intent-review\.[a-f0-9]{64}\.json$")
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=1)


class InterfaceIntentPlanSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["save_reviewed_intent_plan"]
    review_filename: str = Field(pattern=r"^intent-review\.[a-f0-9]{64}\.json$")
    planner_result: PlannerResult
    confirmed_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceTaskEventRequest(BaseModel):
    """History entry only; no approval or execution authority is conferred."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["record_task_event"]
    task_id: str | None = Field(default=None, pattern=r"^task-[a-z0-9][a-z0-9_-]{0,63}$")
    event_type: Literal["request", "clarification", "selection", "decision", "outcome", "failure", "artifact_reference"]
    summary: str = Field(min_length=1, max_length=1000)
    details: str = Field(default="", max_length=8000)
    artifact_path: str | None = Field(default=None, max_length=240)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class InterfacePlanRequest(BaseModel):
    """One bounded natural-language request for the existing planner agent."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["plan_task"]
    request: str = Field(min_length=1, max_length=8000)
    allowed_skill_ids: list[str] = Field(min_length=1, max_length=64)
    input_paths: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("allowed_skill_ids")
    @classmethod
    def skill_ids_are_unique_and_safe(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("allowed skill IDs must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", item) for item in value):
            raise ValueError("allowed skill ID is invalid")
        return value

    @field_validator("input_paths")
    @classmethod
    def input_paths_are_bounded(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            if len(item) > 960:
                raise ValueError("input path is too long")
            item = item.strip()
            if "/" not in item:
                item = "data/input/" + item
            if (not re.fullmatch(r"data/input/[A-Za-z0-9._/-]+", item)
                    or any(part in {"", ".", ".."} for part in item.split("/"))):
                raise ValueError("input path is outside the governed input root")
            normalized.append(item)
        if len(normalized) != len(set(normalized)):
            raise ValueError("input paths must be unique after normalization")
        return normalized


class InterfaceRecipeTraceSaveRequest(BaseModel):
    """Exact adapted trace explicitly reviewed for immutable persistence."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["save_adapted_recipe_trace"]
    evidence_name: str = Field(
        pattern=r"^[a-z0-9][a-z0-9_-]{0,100}\.[a-f0-9]{64}\.json$"
    )
    confirmed_trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceCriticRunRequest(BaseModel):
    """Exact stored evidence selected for one in-memory Critic assessment."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["run_critic"]
    trace_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.json$")
    report_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.md$")
    confirmed_trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceCriticRecordRequest(InterfaceCriticRunRequest):
    """Exact validated Critic result selected for immutable recording."""

    action: Literal["record_critic_result"]
    confirmed_critic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result: CriticResult


class InterfaceRecipeReleaseRequest(BaseModel):
    """Exact recorded recipe-run evidence selected for release assessment."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["prepare_recipe_release"]
    release_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    trace_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.json$")
    report_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,80}\.md$")
    critic_record_file: str = Field(
        pattern=r"^critic-results/[A-Za-z0-9._-]+\.critic-result/CRITIC_RESULT\.json$"
    )
    confirmed_critic_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InterfaceRecipeReleaseCreationRequest(InterfaceRecipeReleaseRequest):
    """Exact assessed candidate explicitly confirmed for immutable release."""

    action: Literal["create_recipe_release"]
    confirmed_candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed_assessed_at: datetime
    confirmation: Literal["create_exact_release"]

    @field_validator("confirmed_assessed_at")
    @classmethod
    def assessed_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("confirmed assessment timestamp must include a timezone")
        return value


class InterfaceSnakemakeExportPreviewRequest(InterfaceApprovalVerificationRequest):
    """Exact approved recipe selected for a non-writing export preview."""

    action: Literal["preview_snakemake_export"]


class InterfaceSnakemakeExportRequest(InterfaceSnakemakeExportPreviewRequest):
    """Exact preview explicitly confirmed for immutable export generation."""

    action: Literal["export_snakemake"]
    confirmed_export_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: Literal["export_exact_approved_recipe"]
