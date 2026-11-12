"""Typed schemas for non-executing Snakemake exports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class SnakemakeRecipeExportPlan(BaseModel):
    """Plan for exporting one exact approved recipe."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    recipe_filename: str = Field(
        pattern=r"^[^/\\]+\.json$"
    )
    approval_filename: str = Field(
        pattern=r"^[^/\\]+\.json$"
    )

    approved_step_ids: list[str] = Field(
        min_length=1
    )
    topological_step_ids: list[str] = Field(
        min_length=1
    )

    replay_entrypoint: Literal[
        "geoagent_harness.snakemake_export."
        "replay:run_approved_recipe_replay"
    ] = (
        "geoagent_harness.snakemake_export."
        "replay:run_approved_recipe_replay"
    )

    workflow_filename: Literal[
        "Snakefile"
    ] = "Snakefile"

    configuration_filename: Literal[
        "geoagent-replay.json"
    ] = "geoagent-replay.json"

    manifest_filename: Literal[
        "snakemake-export-manifest.json"
    ] = "snakemake-export-manifest.json"

    warnings: list[str] = Field(
        default_factory=list
    )

    export_performed: Literal[False] = False
    workflow_executed: Literal[False] = False
    recipe_execution_performed: Literal[False] = False
    approval_modified: Literal[False] = False
    recipe_modified: Literal[False] = False

    @model_validator(mode="after")
    def step_scope_is_consistent(
        self,
    ) -> "SnakemakeRecipeExportPlan":
        if len(self.approved_step_ids) != len(
            set(self.approved_step_ids)
        ):
            raise ValueError(
                "approved step IDs must be unique"
            )

        if len(self.topological_step_ids) != len(
            set(self.topological_step_ids)
        ):
            raise ValueError(
                "topological step IDs must be unique"
            )

        unknown = (
            set(self.approved_step_ids)
            - set(self.topological_step_ids)
        )

        if unknown:
            raise ValueError(
                "approved steps must be inside "
                "the topological recipe scope"
            )

        return self

class SnakemakeRecipeExportResult(BaseModel):
    """Result of generating one Snakemake replay package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    export_path: str

    workflow_path: str
    workflow_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    configuration_path: str
    configuration_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    manifest_path: str

    generated_files: list[str] = Field(
        min_length=3
    )

    export_performed: Literal[True] = True
    workflow_executed: Literal[False] = False
    recipe_execution_performed: Literal[False] = False
    approval_modified: Literal[False] = False
    recipe_modified: Literal[False] = False

class SnakemakeExportContractResult(BaseModel):
    """Static validation result for one replay package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    export_path: str

    passed: bool
    checked_files: list[str] = Field(
        default_factory=list
    )
    violations: list[str] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(
        default_factory=list
    )

    workflow_executed: Literal[False] = False
    recipe_execution_performed: Literal[False] = False
    approval_modified: Literal[False] = False
    recipe_modified: Literal[False] = False

class SnakemakeReplayConfiguration(BaseModel):
    """Exact non-executed configuration for approved replay."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    recipe_filename: str = Field(
        pattern=r"^[^/\\]+\.json$"
    )
    approval_filename: str = Field(
        pattern=r"^[^/\\]+\.json$"
    )

    approved_step_ids: list[str] = Field(
        min_length=1
    )
    topological_step_ids: list[str] = Field(
        min_length=1
    )

    replay_entrypoint: Literal[
        "geoagent_harness.snakemake_export."
        "replay:run_approved_recipe_replay"
    ]

    workflow_executed: Literal[False] = False
    recipe_execution_performed: Literal[False] = False
    approval_modified: Literal[False] = False
    recipe_modified: Literal[False] = False

    @model_validator(mode="after")
    def scopes_are_consistent(
        self,
    ) -> "SnakemakeReplayConfiguration":
        if len(self.approved_step_ids) != len(
            set(self.approved_step_ids)
        ):
            raise ValueError(
                "approved step IDs must be unique"
            )

        if len(self.topological_step_ids) != len(
            set(self.topological_step_ids)
        ):
            raise ValueError(
                "topological step IDs must be unique"
            )

        if not set(
            self.approved_step_ids
        ).issubset(
            set(self.topological_step_ids)
        ):
            raise ValueError(
                "approved steps must be inside "
                "the topological scope"
            )

        return self


class SnakemakeReplayCompletion(BaseModel):
    """Durable successful completion marker for replay."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    approval_id: str

    final_status: Literal[
        "validated_success"
    ] = "validated_success"

    run_result_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    run_result_path: str = Field(
        min_length=1
    )

    evidence_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    evidence_path: str = Field(
        min_length=1
    )
    report_path: str = Field(
        min_length=1
    )

    executor_result: dict[str, Any]

    workflow_executed: Literal[True] = True
    recipe_execution_performed: Literal[True] = True
    evidence_recorded: Literal[True] = True
    replay_completed: Literal[True] = True
    approval_modified: Literal[False] = False
    recipe_modified: Literal[False] = False
