"""Schemas for concise, task-specific context packs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContextReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str


class DatasetContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    path: str
    format: str
    purpose: str
    read_only: bool


class SkillContext(BaseModel):
    """Implemented skill supplied to the Planner."""
    model_config = ConfigDict(extra="forbid")

    id: str
    status: Literal["implemented"]
    version: str | None = None
    entrypoint: str | None = None
    verifier: str | None = None


class DecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    decision: str
    status: Literal["accepted"]


class TaskContextPack(BaseModel):
    """Trusted context supplied to the Planner Agent."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    original_request: str = Field(min_length=1, max_length=8000)
    project_summary: str
    architecture: str
    current_status: str
    datasets: list[DatasetContext]
    available_skills: list[SkillContext]
    decisions: list[DecisionContext]
    context_references: list[ContextReference]
    warnings: list[str] = Field(default_factory=list)

    def as_prompt_payload(self) -> dict[str, Any]:
        """Return JSON-compatible content for a model prompt."""

        return self.model_dump(mode="json")