"""Structured schemas for Planner Agent output."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class PlanStep(BaseModel):
    """One proposed, non-executed workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(
        pattern=r"^step_[1-9][0-9]*$"
    )
    skill: str = Field(
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    purpose: str = Field(min_length=1, max_length=1000)
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    expected_artifacts: list[str] = Field(default_factory=list)
    validation_required: bool = False


class WorkflowPlan(BaseModel):
    """A structured plan that has not been executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal["planned"] = "planned"
    summary: str = Field(min_length=1, max_length=2000)
    steps: list[PlanStep] = Field(min_length=1, max_length=20)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    execution_performed: Literal[False] = False
    validation_performed: Literal[False] = False

    @field_validator("steps")
    @classmethod
    def step_ids_must_be_sequential(
        cls,
        steps: list[PlanStep],
    ) -> list[PlanStep]:
        expected = [
            f"step_{number}"
            for number in range(1, len(steps) + 1)
        ]
        actual = [step.step_id for step in steps]

        if actual != expected:
            raise ValueError(
                "step IDs must be sequential starting at step_1"
            )

        return steps


class PlannerResult(BaseModel):
    """Validated result returned by the Planner Agent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: Literal["planner"] = "planner"
    model: str
    context_references: list[str]
    plan: WorkflowPlan
    warnings: list[str] = Field(default_factory=list)