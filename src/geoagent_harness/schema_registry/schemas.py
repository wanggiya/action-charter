"""Schemas for artifact-version compatibility policy."""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


_VERSION = re.compile(
    r"^(?:0|[1-9][0-9]*)\.[0-9]+$"
)


class ArtifactType(str, Enum):
    """Stable identifiers for versioned artifact schemas."""

    CONTEXT_PACK = "context_pack"
    WORKFLOW_PLAN = "workflow_plan"
    APPROVAL_RECORD = "approval_record"
    EXECUTION_ENVELOPE = "execution_envelope"
    FAILURE_RECORD = "failure_record"
    WORKFLOW_TRACE = "workflow_trace"
    CRITIC_ASSESSMENT = "critic_assessment"
    CRITIC_EVIDENCE_PACK = "critic_evidence_pack"
    WORKFLOW_STATE = "workflow_state"
    RESUME_ASSESSMENT = "resume_assessment"
    VECTOR_CONVERSION_PLAN = (
        "vector_conversion_plan"
    )
    VECTOR_CONVERSION_RESULT = (
        "vector_conversion_result"
    )
    RECIPE = "recipe"
    RECIPE_VALIDATION = "recipe_validation"
    RECIPE_APPROVAL = "recipe_approval"
    RECIPE_EXECUTION_ENVELOPE = (
        "recipe_execution_envelope"
    )
    RECIPE_STEP_EXECUTION_RESULT = (
        "recipe_step_execution_result"
    )
    RECIPE_RUN_EVIDENCE = (
        "recipe_run_evidence"
    )
    RECIPE_RUN_RESULT = (
        "recipe_run_result"
    )
    RECIPE_EXECUTION_RECORD = (
        "recipe_execution_record"
    )
    PERSISTED_RECIPE_EXECUTION_RESULT = (
        "persisted_recipe_execution_result"
    )
    RECIPE_PROPOSAL = "recipe_proposal"
    RECIPE_PROPOSAL_ASSESSMENT = (
        "recipe_proposal_assessment"
    )
    RECIPE_COMPILATION_RESULT = (
        "recipe_compilation_result"
    )
    RECIPE_PROPOSAL_GENERATION_RESULT = (
        "recipe_proposal_generation_result"
    )
    RECIPE_PROPOSAL_PIPELINE_RESULT = (
        "recipe_proposal_pipeline_result"
    )
    RECIPE_OPERATOR_REVIEW = (
        "recipe_operator_review"
    )
    RECIPE_OPERATOR_SAVE_RESULT = (
        "recipe_operator_save_result"
    )
    SKILL_SCAFFOLD_REQUEST = (
        "skill_scaffold_request"
    )
    SKILL_SCAFFOLD_PLAN = (
        "skill_scaffold_plan"
    )
    SKILL_SCAFFOLD_GENERATION_RESULT = (
        "skill_scaffold_generation_result"
    )
    SKILL_SCAFFOLD_CONTRACT_RESULT = (
        "skill_scaffold_contract_result"
    )
    SNAKEMAKE_RECIPE_EXPORT_PLAN = (
        "snakemake_recipe_export_plan"
    )
    SNAKEMAKE_RECIPE_EXPORT_RESULT = (
        "snakemake_recipe_export_result"
    )
    SNAKEMAKE_EXPORT_CONTRACT_RESULT = (
        "snakemake_export_contract_result"
    )
    SNAKEMAKE_REPLAY_CONFIGURATION = (
        "snakemake_replay_configuration"
    )
    SNAKEMAKE_REPLAY_COMPLETION = (
        "snakemake_replay_completion"
    )
    RECIPE_APPROVAL_INVENTORY = (
        "recipe_approval_inventory"
    )
    


class CompatibilityDisposition(str, Enum):
    """Result of comparing an artifact version with policy."""

    CURRENT = "current"
    SUPPORTED_READ = "supported_read"
    MIGRATION_REQUIRED = "migration_required"
    UNSUPPORTED_OLDER = "unsupported_older"
    UNSUPPORTED_FUTURE = "unsupported_future"
    INVALID_VERSION = "invalid_version"


class SchemaPolicy(BaseModel):
    """Version policy for one artifact type."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    artifact_type: ArtifactType
    current_version: str
    writable_version: str
    supported_read_versions: tuple[str, ...] = Field(
        min_length=1
    )
    migration_sources: tuple[str, ...] = ()

    @field_validator(
        "current_version",
        "writable_version",
    )
    @classmethod
    def version_is_valid(
        cls,
        value: str,
    ) -> str:
        if not _VERSION.fullmatch(value):
            raise ValueError(
                "schema version must use major.minor format"
            )

        return value

    @field_validator(
        "supported_read_versions",
        "migration_sources",
    )
    @classmethod
    def versions_are_valid(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError(
                "schema version lists must not "
                "contain duplicates"
            )

        if not all(
            _VERSION.fullmatch(value)
            for value in values
        ):
            raise ValueError(
                "schema versions must use "
                "major.minor format"
            )

        return values


class CompatibilityAssessment(BaseModel):
    """Read-only assessment of one artifact version."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    artifact_type: ArtifactType
    artifact_version: str
    current_version: str
    writable_version: str

    disposition: CompatibilityDisposition
    readable: bool
    writable: bool
    migration_required: bool

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    artifact_modified: Literal[False] = False
