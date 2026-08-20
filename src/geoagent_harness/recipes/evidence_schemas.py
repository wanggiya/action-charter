"""Typed artifact and lineage evidence for recipe runs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from geoagent_harness.recipes.schemas import (
    RecipeRunResult,
)


class ArtifactRole(str, Enum):
    """Role of one physical artifact in a recipe run."""

    INPUT = "input"
    OUTPUT = "output"


class ArtifactReference(BaseModel):
    """Cryptographic reference to one trusted artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(
        pattern=r"^[a-z][a-z0-9_-]{0,100}$"
    )
    role: ArtifactRole

    path: str = Field(
        min_length=1,
        max_length=2000,
    )
    sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    size_bytes: int = Field(ge=0)

    media_type: str | None = Field(
        default=None,
        max_length=200,
    )

    producer_step_id: str | None = Field(
        default=None,
        pattern=r"^step_[1-9][0-9]*$",
    )

    @model_validator(mode="after")
    def producer_matches_role(
        self,
    ) -> "ArtifactReference":
        if (
            self.role == ArtifactRole.INPUT
            and self.producer_step_id is not None
        ):
            raise ValueError(
                "input artifact cannot have a "
                "producer step"
            )

        if (
            self.role == ArtifactRole.OUTPUT
            and self.producer_step_id is None
        ):
            raise ValueError(
                "output artifact requires a "
                "producer step"
            )

        return self


class LineageEdge(BaseModel):
    """One deterministic derivation between artifacts."""

    model_config = ConfigDict(extra="forbid")

    source_artifact_id: str = Field(
        pattern=r"^[a-z][a-z0-9_-]{0,100}$"
    )
    target_artifact_id: str = Field(
        pattern=r"^[a-z][a-z0-9_-]{0,100}$"
    )

    step_id: str = Field(
        pattern=r"^step_[1-9][0-9]*$"
    )
    skill_id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$"
    )

    relationship: Literal[
        "derived_from"
    ] = "derived_from"


class RecipeRunEvidence(BaseModel):
    """Authoritative evidence for one completed recipe run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str = Field(
        pattern=r"^[a-z0-9][a-z0-9_-]{0,100}$"
    )
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    final_status: Literal[
        "validated_success",
        "validation_failed",
    ]

    run_result: RecipeRunResult

    artifacts: list[ArtifactReference] = Field(
        min_length=1
    )
    lineage: list[LineageEdge] = Field(
        default_factory=list
    )

    skill_versions: dict[str, str] = Field(
        default_factory=dict
    )
    warnings: list[str] = Field(
        default_factory=list
    )

    recorded_at: datetime

    secrets_redacted: Literal[True] = True

    @field_validator("recorded_at")
    @classmethod
    def recorded_at_is_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "recorded_at must include a timezone"
            )

        return value

    @model_validator(mode="after")
    def evidence_is_consistent(
        self,
    ) -> "RecipeRunEvidence":
        if self.recipe_id != self.run_result.recipe_id:
            raise ValueError(
                "evidence recipe ID conflicts with "
                "the run result"
            )

        if (
            self.recipe_sha256
            != self.run_result.recipe_sha256
        ):
            raise ValueError(
                "evidence recipe digest conflicts "
                "with the run result"
            )

        if (
            self.approval_id
            != self.run_result.approval_id
        ):
            raise ValueError(
                "evidence approval ID conflicts "
                "with the run result"
            )

        if (
            self.final_status
            != self.run_result.final_status
        ):
            raise ValueError(
                "evidence final status conflicts "
                "with the run result"
            )

        artifact_ids = [
            artifact.artifact_id
            for artifact in self.artifacts
        ]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(
                "artifact IDs must be unique"
            )

        artifacts_by_id = {
            artifact.artifact_id: artifact
            for artifact in self.artifacts
        }

        steps_by_id = {
            step.step_id: step
            for step in self.run_result.step_results
        }

        for artifact in self.artifacts:
            if (
                artifact.producer_step_id is not None
                and artifact.producer_step_id
                not in steps_by_id
            ):
                raise ValueError(
                    "artifact producer step is not "
                    "present in the run result"
                )

        for edge in self.lineage:
            if (
                edge.source_artifact_id
                not in artifacts_by_id
                or edge.target_artifact_id
                not in artifacts_by_id
            ):
                raise ValueError(
                    "lineage references an unknown "
                    "artifact"
                )

            if edge.step_id not in steps_by_id:
                raise ValueError(
                    "lineage references an unknown "
                    "recipe step"
                )

            step = steps_by_id[edge.step_id]

            if edge.skill_id != step.skill_id:
                raise ValueError(
                    "lineage skill conflicts with "
                    "the run result"
                )

            source = artifacts_by_id[
                edge.source_artifact_id
            ]
            target = artifacts_by_id[
                edge.target_artifact_id
            ]

            if source.role != ArtifactRole.INPUT:
                raise ValueError(
                    "lineage source must be an "
                    "input artifact"
                )

            if target.role != ArtifactRole.OUTPUT:
                raise ValueError(
                    "lineage target must be an "
                    "output artifact"
                )

            if target.producer_step_id != edge.step_id:
                raise ValueError(
                    "lineage step does not match "
                    "the output producer"
                )

        return self

class RecipeExecutionRecord(BaseModel):
    """Durable references for one completed recipe run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str = Field(
        pattern=r"^[a-z0-9][a-z0-9_-]{0,100}$"
    )
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str = Field(min_length=1)

    final_status: Literal[
        "validated_success",
        "validation_failed",
    ]

    run_result_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    run_result_path: str = Field(min_length=1)

    evidence_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    evidence_path: str = Field(min_length=1)

    report_path: str = Field(min_length=1)

    execution_performed: Literal[True] = True
    evidence_recorded: Literal[True] = True
    report_written: Literal[True] = True


class PersistedRecipeExecutionResult(BaseModel):
    """Completed recipe result with durable evidence references."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    run_result: RecipeRunResult
    execution_record: RecipeExecutionRecord

    @model_validator(mode="after")
    def identities_must_match(
        self,
    ) -> "PersistedRecipeExecutionResult":
        result = self.run_result
        record = self.execution_record

        if result.recipe_id != record.recipe_id:
            raise ValueError(
                "recipe result and execution record "
                "recipe IDs do not match"
            )

        if (
            result.recipe_sha256
            != record.recipe_sha256
        ):
            raise ValueError(
                "recipe result and execution record "
                "digests do not match"
            )

        if (
            result.approval_id
            != record.approval_id
        ):
            raise ValueError(
                "recipe result and execution record "
                "approval IDs do not match"
            )

        if (
            result.final_status
            != record.final_status
        ):
            raise ValueError(
                "recipe result and execution record "
                "statuses do not match"
            )

        return self
