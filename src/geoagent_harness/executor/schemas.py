"""Typed schemas for deterministic execution handoff."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkflowToolArguments(BaseModel):
    """Arguments for the approved composite workflow tool."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    source_layer: str | None = None
    target_schema: str = Field(min_length=1)
    target_table: str = Field(min_length=1)
    original_request: str = Field(
        min_length=1,
        max_length=8000,
    )
    task_id: str = Field(min_length=1)
    context_references: list[str] = Field(
        default_factory=list
    )
    human_corrections: list[str] = Field(
        default_factory=list
    )


class ExecutionEnvelope(BaseModel):
    """Approved tool request that has not been executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    plan_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str = Field(min_length=1)
    approved_step_ids: list[str] = Field(
        min_length=1
    )
    selected_skills: list[str] = Field(
        min_length=1
    )
    tool_name: Literal[
        "run_vector_postgis_workflow"
    ] = "run_vector_postgis_workflow"
    tool_arguments: WorkflowToolArguments
    execution_performed: Literal[False] = False