"""Typed schemas for reusable workflow recipes."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


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
