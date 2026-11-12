"""Compatibility handoff exports and the recipe-specific Executor result."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.contracts.execution import WorkflowToolArguments, ExecutionEnvelope, WorkflowExecutionResult, ExecutorRunResult
from geoagent_harness.contracts.recipes import RecipeRunResult
from geoagent_harness.contracts.recipe_evidence import RecipeExecutionRecord


class ExecutorRecipeRunResult(BaseModel):
    """Recipe result returned by the independent Executor Agent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: Literal["executor"] = "executor"

    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    tool_name: Literal[
        "run_approved_recipe"
    ] = "run_approved_recipe"

    execution_performed: Literal[True] = True

    recipe: RecipeRunResult
    execution_record: RecipeExecutionRecord
