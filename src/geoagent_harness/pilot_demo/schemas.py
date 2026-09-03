"""Strict schemas for the fixed pilot-ready demonstration."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PilotDemoNextAction(str, Enum):
    """Next action exposed to the operator by read-only assessment."""

    PROPOSE_WORKFLOW = "propose_workflow"
    FIX_REPOSITORY = "fix_repository"


class PilotDemoDatasetCase(BaseModel):
    """One fixed dataset and its expected contract outcome."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    dataset: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    expected_failed_checks: list[str] = Field(max_length=32)

    @model_validator(mode="after")
    def failed_checks_are_unique(self) -> "PilotDemoDatasetCase":
        if len(self.expected_failed_checks) != len(
            set(self.expected_failed_checks)
        ):
            raise ValueError("expected failed checks must be unique")
        return self


class PilotDemoDefinition(BaseModel):
    """Data-only definition of the presentation workflow."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    demo_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,127}$")
    benchmark_manifest: Literal[
        "benchmarks/spatial-contracts/vector/BENCHMARK.json"
    ]
    contract_file: Literal[
        "benchmarks/spatial-contracts/vector/contract.yaml"
    ]
    data_root: Literal[
        "benchmarks/spatial-contracts/vector/data"
    ]
    dirty_case: PilotDemoDatasetCase
    corrected_case: PilotDemoDatasetCase
    workflow_dataset: str = Field(
        pattern=r"^data/input/[A-Za-z0-9_.-]+$"
    )
    request: str = Field(min_length=1, max_length=2_000)
    task_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    release_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    target_schema: Literal["agent_sandbox"]
    target_table: str = Field(pattern=r"^[a-z][a-z0-9_]{0,62}$")

    @model_validator(mode="after")
    def cases_have_required_roles(self) -> "PilotDemoDefinition":
        if not self.dirty_case.expected_failed_checks:
            raise ValueError("dirty case must fail at least one check")
        if self.corrected_case.expected_failed_checks:
            raise ValueError("corrected case must pass every check")
        if self.dirty_case.case_id == self.corrected_case.case_id:
            raise ValueError("dirty and corrected cases must be distinct")
        return self


class PilotDemoCaseResult(BaseModel):
    """Observed deterministic outcome for one demonstration case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    dataset: str
    expected_failed_checks: list[str]
    observed_failed_checks: list[str]
    expectation_matched: bool
    dataset_unchanged: bool


class PilotDemoReadiness(BaseModel):
    """Read-only readiness result before any model or workflow action."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    demo_id: str
    definition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    benchmark_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    workflow_dataset: str
    workflow_dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cases: list[PilotDemoCaseResult] = Field(min_length=2, max_length=2)
    repository_ready: bool
    next_action: PilotDemoNextAction
    violations: list[str]
    assessment_performed: Literal[True] = True
    model_called: Literal[False] = False
    approval_created: Literal[False] = False
    workflow_executed: Literal[False] = False
    filesystem_modified: Literal[False] = False
    database_modified: Literal[False] = False
    release_created: Literal[False] = False
    snakemake_invoked: Literal[False] = False

    @model_validator(mode="after")
    def readiness_is_consistent(self) -> "PilotDemoReadiness":
        if self.repository_ready != (not self.violations):
            raise ValueError("repository readiness must derive from violations")
        expected_action = (
            PilotDemoNextAction.PROPOSE_WORKFLOW
            if self.repository_ready
            else PilotDemoNextAction.FIX_REPOSITORY
        )
        if self.next_action != expected_action:
            raise ValueError("next action is inconsistent with readiness")
        return self
