"""Schemas for declarative GIS skill definitions."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillDefinition,
    SkillKind,
)

from geoagent_harness.skill_scaffolding.schemas import (
    SkillScaffoldGenerationResult,
    SkillScaffoldPlan,
)



class SkillProfile(str, Enum):
    """Fixed security and validation profiles."""

    READ_ONLY_INSPECTION = (
        "read_only_inspection"
    )
    ARTIFACT_TRANSFORMATION = (
        "artifact_transformation"
    )
    DATABASE_WRITE = "database_write"
    READ_ONLY_VALIDATION = (
        "read_only_validation"
    )
    EVIDENCE_REPORTING = (
        "evidence_reporting"
    )


class DeclarativeSkillDefinition(BaseModel):
    """A non-executing request to generate one skill."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    version: str = Field(
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    profile: SkillProfile

    adapter_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    arguments_schema_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    result_schema_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    fixture_path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )

    generation_requested: Literal[False] = False
    promotion_requested: Literal[False] = False
    execution_requested: Literal[False] = False
    execution_performed: Literal[False] = False


class DeclarativeSkillAssessment(BaseModel):
    """Deterministic policy assessment of one definition."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    profile: SkillProfile

    kind: SkillKind
    access: SkillAccess

    approval_required: bool
    validation_required: bool
    verifier_required: bool

    adapter_available: bool
    ready_for_generation: bool

    policy_conflicts: list[str] = Field(
        default_factory=list
    )

    definition_modified: Literal[False] = False
    generation_performed: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class SkillContractBundle(BaseModel):
    """Generated security and testing contract."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    profile: SkillProfile
    kind: SkillKind
    access: SkillAccess

    approval_required: bool
    validation_required: bool
    verifier_required: bool

    required_checks: list[str] = Field(
        min_length=1
    )

    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False


class SkillContractGenerationResult(BaseModel):
    """Result of generating one isolated contract bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    bundle_path: str = Field(min_length=1)
    definition_path: str = Field(min_length=1)
    contract_path: str = Field(min_length=1)

    definition_validated: Literal[True] = True
    assessment_performed: Literal[True] = True
    contract_generated: Literal[True] = True

    implementation_generated: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class SkillContractValidationResult(BaseModel):
    """Static validation of one generated contract bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    bundle_path: str = Field(min_length=1)

    passed: Literal[True] = True
    checks: list[str] = Field(min_length=1)

    files_modified: Literal[False] = False
    implementation_imported: Literal[False] = False
    implementation_executed: Literal[False] = False
    registry_modified: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class DeclarativeSkillScaffoldPlan(BaseModel):
    """Compiled handoff to the existing scaffold system."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    contract: SkillContractBundle
    scaffold_plan: SkillScaffoldPlan

    compilation_performed: Literal[True] = True
    generation_performed: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False


class DeclarativeSkillScaffoldGenerationResult(
    BaseModel
):
    """Generated untrusted scaffold with definition identity."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    contract: SkillContractBundle
    scaffold: SkillScaffoldGenerationResult

    compilation_performed: Literal[True] = True
    generation_performed: Literal[True] = True
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class TrustedAdapterMaterializationResult(BaseModel):
    """Result of materializing one isolated candidate."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    adapter_id: str
    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    source_scaffold_path: str
    candidate_path: str
    materialized_files: list[str] = Field(
        min_length=1
    )

    candidate_materialized: Literal[True] = True
    static_contract_passed: Literal[True] = True

    source_scaffold_modified: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class SkillCandidateTestRecord(BaseModel):
    """Evidence emitted by the isolated test container."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$"
    )

    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256_after: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_unchanged: bool

    pytest_exit_code: int = Field(ge=0)
    collected: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    error_count: int = Field(ge=0)

    passed: bool

    network_available: Literal[False] = False
    candidate_mount_read_only: Literal[True] = True

    tests_executed: Literal[True] = True
    implementation_executed: Literal[True] = True

    registry_modified: Literal[False] = False
    promotion_performed: Literal[False] = False

    @model_validator(mode="after")
    def outcome_is_consistent(
        self,
    ) -> "SkillCandidateTestRecord":
        hashes_match = (
            self.candidate_tree_sha256
            == self.candidate_tree_sha256_after
        )

        if self.candidate_unchanged != hashes_match:
            raise ValueError(
                "candidate unchanged claim conflicts "
                "with candidate digests"
            )

        success_conditions = (
            self.pytest_exit_code == 0
            and self.collected > 0
            and self.failed_count == 0
            and self.error_count == 0
            and self.candidate_unchanged
        )

        if self.passed != success_conditions:
            raise ValueError(
                "candidate test success conflicts "
                "with recorded outcomes"
            )

        if (
            self.passed_count
            + self.failed_count
            + self.skipped_count
            > self.collected
        ):
            raise ValueError(
                "candidate test counts exceed "
                "collected tests"
            )

        return self

class SkillCandidatePromotionAssessment(BaseModel):
    """Read-only assessment before explicit promotion."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    adapter_id: str

    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    static_contract_passed: bool
    evidence_matches_candidate: bool
    isolated_tests_passed: bool
    candidate_unchanged: bool

    ready_for_promotion_review: bool
    violations: list[str] = Field(
        default_factory=list
    )

    assessment_performed: Literal[True] = True
    candidate_tests_executed: Literal[True] = True
    implementation_trusted: Literal[False] = False
    registry_modified: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class SkillPromotionFile(BaseModel):
    """One exact candidate file selected for promotion."""

    model_config = ConfigDict(extra="forbid")

    source_path: str
    destination_path: str
    sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )


class SkillCandidatePromotionPlan(BaseModel):
    """Non-writing plan for explicit skill promotion."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    adapter_id: str

    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    registry_before_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    candidate_path: str
    project_root: str
    registry_path: str

    files: list[SkillPromotionFile] = Field(
        min_length=1
    )
    registry_entry: SkillDefinition

    ready_for_promotion: Literal[True] = True

    planning_performed: Literal[True] = True
    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class SkillCandidatePromotionResult(BaseModel):
    """Completed explicit promotion into trusted source."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    adapter_id: str

    definition_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    registry_before_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    registry_after_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    copied_files: list[str] = Field(
        min_length=1
    )
    registry_entry: SkillDefinition

    files_copied: Literal[True] = True
    registry_modified: Literal[True] = True
    implementation_trusted: Literal[True] = True
    promotion_performed: Literal[True] = True

    # Promotion does not execute the promoted GIS skill.
    execution_performed: Literal[False] = False
