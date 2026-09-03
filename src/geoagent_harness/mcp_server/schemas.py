"""Structured results for Checkpoint 2 MCP tools."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from geoagent_harness.schemas import InspectVectorResult
from geoagent_harness.spatial_contracts import (
    SpatialDataContractAssessment,
)


class HealthCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    write_tools_enabled: bool
    overwrite_enabled: bool
    input_root: str
    tools: list[str]


class InspectVectorToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["inspected"] = "inspected"
    result: InspectVectorResult


class LoadVectorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "planned_not_executed"
    ] = "planned_not_executed"

    source: str
    source_driver: str
    source_layers: list[str]

    target_schema: str
    target_table: str

    operation: Literal["create_table"] = "create_table"

    # These are deliberately fixed values.
    execution_allowed: Literal[False] = False
    approval_required: Literal[True] = True

    warnings: list[str]


class AssessSpatialDataContractToolResult(BaseModel):
    """Read-only deterministic spatial-contract result."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["assessed"] = "assessed"
    result: SpatialDataContractAssessment
