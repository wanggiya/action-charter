"""Typed schemas for reusable workflow recipes."""

from __future__ import annotations

from typing import Any, Literal

import re
from datetime import datetime


from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_RECIPE_APPROVAL_ID = re.compile(
    r"^recipe-approval-"
    r"[0-9]{8}t[0-9]{6}z-"
    r"[a-f0-9]{8}$"
)

_SHA256 = re.compile(
    r"^[a-f0-9]{64}$"
)

_STEP_ID = re.compile(
    r"^step_[1-9][0-9]*$"
)

class RecipeExecutionStep(BaseModel):
    """Trusted recipe step prepared for execution."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(
        pattern=r"^step_[1-9][0-9]*$"
    )
    skill_id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$"
    )

    depends_on: list[str] = Field(
        default_factory=list
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict
    )
    output_ids: list[str] = Field(
        default_factory=list
    )


class RecipeExecutionEnvelope(BaseModel):
    """Approved recipe request that has not executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    approval_id: str
    approved_step_ids: list[str] = Field(
        min_length=1
    )
    topological_step_ids: list[str] = Field(
        min_length=1
    )

    steps: list[RecipeExecutionStep] = Field(
        min_length=1
    )

    tool_name: Literal[
        "run_approved_recipe"
    ] = "run_approved_recipe"

    execution_performed: Literal[False] = False
    
class InspectVectorRecipeArguments(BaseModel):
    """Allowlisted recipe arguments for vector inspection."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)

class InspectRasterRecipeArguments(BaseModel):
    """Arguments for one read-only raster inspection."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        min_length=1,
        max_length=2000,
    )

class ConvertVectorRecipeArguments(BaseModel):
    """Allowlisted recipe arguments for vector conversion."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    target_path: str = Field(min_length=1)

    source_layer: str | None = None
    target_layer: str | None = None


class RecipeStepExecutionResult(BaseModel):
    """Result of one hard-coded recipe step dispatch."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    step_id: str
    skill_id: str

    status: Literal[
        "completed",
        "completed_pending_validation",
    ]

    output_ids: list[str]
    result: dict[str, Any]

    execution_performed: Literal[True] = True
    validation_performed: bool    

class RecipeStepRunResult(BaseModel):
    """Execution and validation result for one recipe step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    skill_id: str

    status: Literal[
        "completed",
        "validated_success",
        "validation_failed",
    ]

    execution: RecipeStepExecutionResult
    validation_result: dict[str, Any] | None = None

    execution_performed: Literal[True] = True
    validation_performed: bool


class RecipeRunResult(BaseModel):
    """Final result of one approved recipe run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    final_status: Literal[
        "validated_success",
        "validation_failed",
    ]

    step_results: list[RecipeStepRunResult] = Field(
        min_length=1
    )

    failed_step_id: str | None = None
    warnings: list[str] = Field(
        default_factory=list
    )

    execution_performed: Literal[True] = True
    validation_performed: bool

class RecipeApprovalRecord(BaseModel):
    """Append-only approval for one exact recipe."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    approval_id: str
    recipe_sha256: str
    decision: Literal["approved", "denied"]

    step_ids: list[str] = Field(
        min_length=1
    )

    approver: str = Field(
        min_length=1,
        max_length=200,
    )
    reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    human_corrections: list[str] = Field(
        default_factory=list
    )

    created_at: datetime
    expires_at: datetime | None = None

    secrets_redacted: Literal[True] = True

    @field_validator("approval_id")
    @classmethod
    def approval_id_is_valid(
        cls,
        value: str,
    ) -> str:
        if not _RECIPE_APPROVAL_ID.fullmatch(
            value
        ):
            raise ValueError(
                "recipe approval ID has an "
                "invalid format"
            )

        return value

    @field_validator("recipe_sha256")
    @classmethod
    def digest_is_valid(
        cls,
        value: str,
    ) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError(
                "recipe_sha256 must be a "
                "SHA-256 digest"
            )

        return value

    @field_validator("step_ids")
    @classmethod
    def step_ids_are_valid(
        cls,
        values: list[str],
    ) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError(
                "approval step IDs must not "
                "contain duplicates"
            )

        if not all(
            _STEP_ID.fullmatch(value)
            for value in values
        ):
            raise ValueError(
                "approval contains an invalid "
                "step ID"
            )

        return values

    @field_validator(
        "created_at",
        "expires_at",
    )
    @classmethod
    def timestamps_are_aware(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "approval timestamps must include "
                "a timezone"
            )

        return value

    @model_validator(mode="after")
    def expiration_is_valid(
        self,
    ) -> "RecipeApprovalRecord":
        if (
            self.expires_at is not None
            and self.expires_at <= self.created_at
        ):
            raise ValueError(
                "expires_at must be later than "
                "created_at"
            )

        return self


class RecipeApprovalVerification(BaseModel):
    """Deterministic recipe-approval verification."""

    model_config = ConfigDict(extra="forbid")

    approved: bool
    approval_id: str | None = None
    recipe_sha256: str

    required_step_ids: list[str] = Field(
        default_factory=list
    )
    approved_step_ids: list[str] = Field(
        default_factory=list
    )
    missing_step_ids: list[str] = Field(
        default_factory=list
    )

    reason: str
 
class RecipeApprovalMatch(BaseModel):
    """One deterministic recipe and approval pairing."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    recipe_filename: str

    approval_id: str
    approval_filename: str
    decision: Literal[
        "approved",
        "denied",
    ]

    approved: bool
    required_step_ids: list[str] = Field(
        default_factory=list
    )
    approved_step_ids: list[str] = Field(
        default_factory=list
    )
    missing_step_ids: list[str] = Field(
        default_factory=list
    )

    created_at: datetime
    expires_at: datetime | None = None
    reason: str


class RecipeApprovalInventory(BaseModel):
    """Read-only inventory of recipe and approval matches."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    matches: list[RecipeApprovalMatch] = Field(
        default_factory=list
    )
    recipes_without_matching_approval: list[str] = Field(
        default_factory=list
    )
    approvals_without_matching_recipe: list[str] = Field(
        default_factory=list
    )

    recipe_count: int = Field(ge=0)
    approval_count: int = Field(ge=0)
    valid_match_count: int = Field(ge=0)

    inventory_performed: Literal[True] = True
    recipe_modified: Literal[False] = False
    approval_modified: Literal[False] = False
    execution_performed: Literal[False] = False  

class RecipeStep(BaseModel):
    """One non-executed step in a reusable recipe."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(
        pattern=r"^step_[1-9][0-9]*$"
    )
    skill_id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$"
    )

    depends_on: list[str] = Field(
        default_factory=list
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict
    )
    output_ids: list[str] = Field(
        default_factory=list
    )

    @field_validator("depends_on")
    @classmethod
    def dependencies_are_unique(
        cls,
        values: list[str],
    ) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError(
                "depends_on must not contain duplicates"
            )

        return values

    @field_validator("output_ids")
    @classmethod
    def outputs_are_safe_and_unique(
        cls,
        values: list[str],
    ) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError(
                "output_ids must not contain duplicates"
            )

        for value in values:
            if not value:
                raise ValueError(
                    "output IDs cannot be empty"
                )

            if not value.replace("_", "").isalnum():
                raise ValueError(
                    "output IDs must contain only "
                    "letters, numbers, and underscores"
                )

            if not value[0].isalpha():
                raise ValueError(
                    "output IDs must begin with a letter"
                )

        return values


class WorkflowRecipe(BaseModel):
    """A reusable workflow that has not executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    status: Literal["planned"] = "planned"

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )
    original_request: str = Field(
        min_length=1,
        max_length=8000,
    )

    steps: list[RecipeStep] = Field(
        min_length=1,
        max_length=100,
    )

    execution_performed: Literal[False] = False
    validation_performed: Literal[False] = False

    @field_validator("steps")
    @classmethod
    def step_ids_are_unique(
        cls,
        steps: list[RecipeStep],
    ) -> list[RecipeStep]:
        step_ids = [
            step.step_id
            for step in steps
        ]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "recipe step IDs must be unique"
            )

        return steps


class RecipeValidation(BaseModel):
    """Deterministic policy result for one recipe."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    valid: Literal[True] = True
    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    topological_step_ids: list[str]
    approval_required_step_ids: list[str]
    write_step_ids: list[str]
    validation_required_step_ids: list[str]

    execution_performed: Literal[False] = False
