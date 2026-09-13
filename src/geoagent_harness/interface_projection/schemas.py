"""Strict browser-safe workflow projection schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InterfaceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$", max_length=80)
    title: str = Field(min_length=1, max_length=80)
    subtitle: str = Field(min_length=1, max_length=120)
    kind: Literal["input", "agent", "policy", "approval", "tool", "evidence"]
    category: Literal["input", "planning", "policy", "approval", "execution", "tool", "validation", "evidence"]
    group: Literal["intake", "planning", "governance", "execution", "assurance"]
    x: int = Field(ge=0, le=4000)
    y: int = Field(ge=0, le=4000)
    status: Literal["verified", "approved", "complete", "failed", "pending"]
    authority: str = Field(min_length=1, max_length=120)
    performed_by: str = Field(alias="performedBy", min_length=1, max_length=80)
    evidence: str = Field(min_length=1, max_length=160)
    details: "InterfaceNodeDetails | None" = None


class InterfaceObservedFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=50)
    value: str = Field(min_length=1, max_length=120)


class InterfaceEvidencePreview(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: str = Field(min_length=1, max_length=80)
    category: Literal["trace", "plan", "approval", "validation", "artifact"]
    status: Literal["verified", "recorded", "pending", "failed"]
    reference: str = Field(min_length=1, max_length=120)
    digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    facts: list[InterfaceObservedFact] = Field(default_factory=list, max_length=6)


class InterfaceNodeDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    summary: str = Field(min_length=1, max_length=240)
    observed_facts: list[InterfaceObservedFact] = Field(default_factory=list, alias="observedFacts", max_length=10)
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    duration_ms: int | None = Field(default=None, alias="durationMs", ge=0)
    findings: list[str] = Field(default_factory=list, max_length=10)
    evidence_previews: list[InterfaceEvidencePreview] = Field(
        default_factory=list,
        alias="evidencePreviews",
        max_length=8,
    )


class InterfaceEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_: str = Field(alias="from", pattern=r"^[a-z][a-z0-9_-]*$")
    to: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")


class InterfaceWorkflowProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal["1.0"] = Field(default="1.0", alias="schemaVersion")
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", max_length=81)
    title: str = Field(min_length=1, max_length=100)
    correlation_id: str = Field(alias="correlationId", min_length=1, max_length=81)
    read_only: Literal[True] = Field(default=True, alias="readOnly")
    source: Literal["validated_trace"] = "validated_trace"
    nodes: list[InterfaceNode] = Field(min_length=1, max_length=100)
    edges: list[InterfaceEdge] = Field(max_length=200)

    @model_validator(mode="after")
    def graph_references_must_be_closed(self) -> "InterfaceWorkflowProjection":
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("interface node IDs must be unique")
        known = set(ids)
        if any(edge.from_ not in known or edge.to not in known for edge in self.edges):
            raise ValueError("interface edge references an unknown node")
        return self


class InterfaceWorkflowSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    task_id: str = Field(alias="taskId", pattern=r"^[a-z0-9][a-z0-9_-]*$", max_length=81)
    status: Literal["validated_success", "validation_failed", "execution_failed"]
    finished_at: datetime = Field(alias="finishedAt")
    projection_path: str = Field(alias="projectionPath", pattern=r"^/runtime/[a-z0-9][a-z0-9_-]*\.json$")


class InterfaceWorkflowCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal["1.0"] = Field(default="1.0", alias="schemaVersion")
    read_only: Literal[True] = Field(default=True, alias="readOnly")
    workflows: list[InterfaceWorkflowSummary] = Field(max_length=50)


class InterfaceProjectionExportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal["exported"] = "exported"
    workflow_count: int = Field(ge=0, le=50)
    catalog_file: Literal["catalog.json"] = "catalog.json"
    projection_files: list[str] = Field(max_length=50)
    source_modified: Literal[False] = False
    execution_performed: Literal[False] = False
