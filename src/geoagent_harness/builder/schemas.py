"""Typed schemas for proposal-only Builder Agent output."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

MAX_BUILDER_FILES = 8
MAX_FILE_BYTES = 32_768
MAX_TOTAL_BYTES = 98_304


class BuilderArtifactKind(str, Enum):
    """Candidate artifact types the Builder may propose."""

    ADAPTER = "adapter"
    SCHEMA = "schema"
    POLICY = "policy"
    TEST = "test"
    RENDERER = "renderer"
    CATALOG_ENTRY = "catalog_entry"


_ALLOWED_PREFIXES = {
    BuilderArtifactKind.ADAPTER: (
        "src/geoagent_harness/skill_adapters/",
    ),
    BuilderArtifactKind.SCHEMA: (
        "src/geoagent_harness/skills/",
    ),
    BuilderArtifactKind.POLICY: (
        "src/geoagent_harness/skills/",
    ),
    BuilderArtifactKind.TEST: (
        "tests/",
    ),
    BuilderArtifactKind.RENDERER: (
        "src/geoagent_harness/recipe_proposals/",
    ),
    BuilderArtifactKind.CATALOG_ENTRY: (
        "catalog_entries/",
    ),
}

_ALLOWED_SUFFIXES = {
    BuilderArtifactKind.ADAPTER: (".py",),
    BuilderArtifactKind.SCHEMA: (".py",),
    BuilderArtifactKind.POLICY: (".py",),
    BuilderArtifactKind.TEST: (".py",),
    BuilderArtifactKind.RENDERER: (".py",),
    BuilderArtifactKind.CATALOG_ENTRY: (
        ".yaml",
        ".yml",
    ),
}


def _validate_relative_candidate_path(path: str) -> str:
    if "\\" in path:
        raise ValueError(
            "candidate paths must use POSIX separators"
        )

    if "//" in path:
        raise ValueError(
            "candidate paths cannot contain empty components"
        )

    candidate = PurePosixPath(path)

    if candidate.is_absolute():
        raise ValueError(
            "candidate paths must be relative"
        )

    if str(candidate) != path:
        raise ValueError(
            "candidate paths must be normalized"
        )

    if any(
        part in {"", ".", ".."} or part.startswith(".")
        for part in candidate.parts
    ):
        raise ValueError(
            "candidate paths contain a forbidden component"
        )

    return path


class BuilderArtifactRequest(BaseModel):
    """One exact candidate artifact requested from the Builder."""

    model_config = ConfigDict(extra="forbid")

    kind: BuilderArtifactKind
    path: str = Field(
        min_length=1,
        max_length=240,
    )
    purpose: str = Field(
        min_length=1,
        max_length=1000,
    )

    @field_validator("path")
    @classmethod
    def path_must_be_safe(cls, path: str) -> str:
        return _validate_relative_candidate_path(path)

    @model_validator(mode="after")
    def path_must_match_kind(
        self,
    ) -> "BuilderArtifactRequest":
        prefixes = _ALLOWED_PREFIXES[self.kind]
        suffixes = _ALLOWED_SUFFIXES[self.kind]

        if not self.path.startswith(prefixes):
            raise ValueError(
                "candidate path is outside the allowed "
                f"prefix for {self.kind.value}"
            )

        if not self.path.endswith(suffixes):
            raise ValueError(
                "candidate path has an invalid suffix "
                f"for {self.kind.value}"
            )

        filename = PurePosixPath(self.path).name

        if (
            self.kind == BuilderArtifactKind.TEST
            and not filename.startswith("test_")
        ):
            raise ValueError(
                "test candidate filenames must start with test_"
            )

        if (
            self.kind == BuilderArtifactKind.SCHEMA
            and filename != "schemas.py"
        ):
            raise ValueError(
                "schema candidate filename must be schemas.py"
            )

        if (
            self.kind == BuilderArtifactKind.POLICY
            and filename != "policy.py"
        ):
            raise ValueError(
                "policy candidate filename must be policy.py"
            )

        return self


class BuilderRequest(BaseModel):
    """Typed, non-writing request supplied to the Builder."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
    )
    artifacts: list[BuilderArtifactRequest] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )
    context_references: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    filesystem_write_requested: Literal[False] = False
    tool_access_requested: Literal[False] = False
    execution_requested: Literal[False] = False
    approval_requested: Literal[False] = False
    promotion_requested: Literal[False] = False

    @field_validator("context_references")
    @classmethod
    def context_references_must_be_safe(
        cls,
        references: list[str],
    ) -> list[str]:
        if len(references) != len(set(references)):
            raise ValueError(
                "context references must be unique"
            )

        for reference in references:
            if len(reference) > 240:
                raise ValueError(
                    "context reference exceeds size limit"
                )
            _validate_relative_candidate_path(reference)

        return references

    @field_validator("artifacts")
    @classmethod
    def artifact_paths_must_be_unique(
        cls,
        artifacts: list[BuilderArtifactRequest],
    ) -> list[BuilderArtifactRequest]:
        paths = [artifact.path for artifact in artifacts]

        if len(paths) != len(set(paths)):
            raise ValueError(
                "requested artifact paths must be unique"
            )

        return artifacts


class BuilderFileProposal(BaseModel):
    """One in-memory, untrusted file proposal."""

    model_config = ConfigDict(extra="forbid")

    kind: BuilderArtifactKind
    path: str = Field(
        min_length=1,
        max_length=240,
    )
    content: str = Field(
        min_length=1,
        max_length=MAX_FILE_BYTES,
    )

    @field_validator("path")
    @classmethod
    def path_must_be_safe(cls, path: str) -> str:
        return _validate_relative_candidate_path(path)

    @field_validator("content")
    @classmethod
    def content_must_fit_byte_limit(
        cls,
        content: str,
    ) -> str:
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError(
                "candidate file exceeds byte limit"
            )

        return content

    @model_validator(mode="after")
    def path_must_match_kind(
        self,
    ) -> "BuilderFileProposal":
        BuilderArtifactRequest(
            kind=self.kind,
            path=self.path,
            purpose="Validate proposed artifact path.",
        )
        return self


class BuilderProposal(BaseModel):
    """Schema-constrained Builder output with no authority."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    agent_id: Literal["builder"] = "builder"
    task_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
    )
    files: list[BuilderFileProposal] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )
    assumptions: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    test_intentions: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    warnings: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    proposal_generated: Literal[True] = True
    filesystem_modified: Literal[False] = False
    tools_called: Literal[False] = False
    tests_performed: Literal[False] = False
    validation_performed: Literal[False] = False
    approval_granted: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("files")
    @classmethod
    def files_must_be_unique_and_bounded(
        cls,
        files: list[BuilderFileProposal],
    ) -> list[BuilderFileProposal]:
        paths = [file.path for file in files]

        if len(paths) != len(set(paths)):
            raise ValueError(
                "proposed file paths must be unique"
            )

        total_bytes = sum(
            len(file.content.encode("utf-8"))
            for file in files
        )

        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError(
                "candidate proposal exceeds total byte limit"
            )

        return files

class BuilderGenerationResult(BaseModel):
    """Validated in-memory result from the Builder Agent."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    agent_id: Literal["builder"] = "builder"
    model: str = Field(min_length=1)
    request: BuilderRequest
    proposal: BuilderProposal

    proposal_generated: Literal[True] = True
    proposal_schema_validated: Literal[True] = True
    policy_validated: Literal[True] = True
    filesystem_modified: Literal[False] = False
    tools_called: Literal[False] = False
    tests_performed: Literal[False] = False
    validation_performed: Literal[False] = False
    approval_granted: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class BuilderMaterializationResult(BaseModel):
    """Result of trusted atomic candidate materialization."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    model: str

    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    source_file_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    source_generation_path: str
    candidate_path: str
    materialized_files: list[str] = Field(
        min_length=1
    )

    candidate_materialized: Literal[True] = True
    source_generation_modified: Literal[False] = False
    registry_modified: Literal[False] = False
    tests_performed: Literal[False] = False
    validation_performed: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class BuilderCandidateManifestFile(BaseModel):
    """One file declared by a materialized candidate."""

    model_config = ConfigDict(extra="forbid")

    kind: BuilderArtifactKind
    path: str
    content_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    @field_validator("path")
    @classmethod
    def path_must_be_safe(cls, path: str) -> str:
        return _validate_relative_candidate_path(path)

    @model_validator(mode="after")
    def path_must_match_kind(
        self,
    ) -> "BuilderCandidateManifestFile":
        BuilderArtifactRequest(
            kind=self.kind,
            path=self.path,
            purpose="Validate materialized artifact path.",
        )
        return self


class BuilderCandidateManifest(BaseModel):
    """Trusted schema for a materialized candidate manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    model: str = Field(min_length=1)
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    files: list[BuilderCandidateManifestFile] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )

    candidate_materialized: Literal[True] = True
    tests_performed: Literal[False] = False
    validation_performed: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("files")
    @classmethod
    def file_paths_must_be_unique(
        cls,
        files: list[BuilderCandidateManifestFile],
    ) -> list[BuilderCandidateManifestFile]:
        paths = [file.path for file in files]

        if len(paths) != len(set(paths)):
            raise ValueError(
                "candidate manifest paths must be unique"
            )

        return files


class BuilderCandidateInspectionResult(BaseModel):
    """Deterministic static inspection of one candidate."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    model: str

    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256_after: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    candidate_path: str
    checked_files: list[str] = Field(
        min_length=1
    )
    syntax_checked_files: list[str] = Field(
        default_factory=list
    )
    checks: list[str] = Field(min_length=1)

    passed: Literal[True] = True
    candidate_modified: Literal[False] = False
    files_imported: Literal[False] = False
    files_executed: Literal[False] = False
    tests_performed: Literal[False] = False
    validation_performed: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def candidate_digest_must_be_stable(
        self,
    ) -> "BuilderCandidateInspectionResult":
        if (
            self.candidate_tree_sha256
            != self.candidate_tree_sha256_after
        ):
            raise ValueError(
                "candidate digest changed during inspection"
            )

        return self

class BuilderCandidateTestRecord(BaseModel):
    """Evidence emitted by isolated Builder candidate tests."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    record_type: Literal[
        "builder_candidate_test"
    ] = "builder_candidate_test"

    task_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
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

    deterministic_validation_performed: Literal[
        False
    ] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def outcome_is_consistent(
        self,
    ) -> "BuilderCandidateTestRecord":
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
                "Builder candidate test success conflicts "
                "with recorded outcomes"
            )

        if (
            self.passed_count
            + self.failed_count
            + self.skipped_count
            > self.collected
        ):
            raise ValueError(
                "Builder candidate test counts exceed "
                "collected tests"
            )

        return self

class BuilderCandidateTestAssessment(BaseModel):
    """Trusted assessment of isolated Builder test evidence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    candidate_path: str
    test_record_path: str

    collected: int = Field(ge=1)
    passed_count: int = Field(ge=0)
    failed_count: Literal[0] = 0
    skipped_count: int = Field(ge=0)
    error_count: Literal[0] = 0

    static_inspection_passed: Literal[True] = True
    isolated_tests_passed: Literal[True] = True
    candidate_unchanged: Literal[True] = True
    digest_bound: Literal[True] = True

    tests_performed: Literal[True] = True
    implementation_executed: Literal[True] = True

    deterministic_validation_performed: Literal[
        False
    ] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class BuilderReviewPackage(BaseModel):
    """Exact evidence package prepared for human review."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    model: str

    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    generation: BuilderGenerationResult
    candidate_manifest: BuilderCandidateManifest
    inspection: BuilderCandidateInspectionResult
    test_assessment: BuilderCandidateTestAssessment

    candidate_path: str
    test_record_path: str
    proposed_destinations: list[str] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )
    warnings: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    review_package_assembled: Literal[True] = True
    ready_for_human_review: Literal[True] = True

    human_review_performed: Literal[False] = False
    approval_granted: Literal[False] = False
    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    deterministic_validation_performed: Literal[
        False
    ] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def identities_must_match(
        self,
    ) -> "BuilderReviewPackage":
        task_ids = {
            self.task_id,
            self.generation.request.task_id,
            self.generation.proposal.task_id,
            self.candidate_manifest.task_id,
            self.inspection.task_id,
            self.test_assessment.task_id,
        }

        if len(task_ids) != 1:
            raise ValueError(
                "Builder review task identities do not match"
            )

        generation_digests = {
            self.generation_sha256,
            self.candidate_manifest.generation_sha256,
            self.inspection.generation_sha256,
            self.test_assessment.generation_sha256,
        }

        if len(generation_digests) != 1:
            raise ValueError(
                "Builder review generation digests do not match"
            )

        candidate_digests = {
            self.candidate_tree_sha256,
            self.inspection.candidate_tree_sha256,
            (
                self.inspection
                .candidate_tree_sha256_after
            ),
            (
                self.test_assessment
                .candidate_tree_sha256
            ),
        }

        if len(candidate_digests) != 1:
            raise ValueError(
                "Builder review candidate digests do not match"
            )

        models = {
            self.model,
            self.generation.model,
            self.candidate_manifest.model,
            self.inspection.model,
        }

        if len(models) != 1:
            raise ValueError(
                "Builder review model identities do not match"
            )

        proposed_paths = sorted(
            file.path
            for file in self.generation.proposal.files
        )

        if proposed_paths != sorted(
            self.proposed_destinations
        ):
            raise ValueError(
                "Builder review destinations do not match "
                "the proposal"
            )

        if (
            self.candidate_path
            != self.inspection.candidate_path
            or self.candidate_path
            != self.test_assessment.candidate_path
        ):
            raise ValueError(
                "Builder review candidate paths do not match"
            )

        if (
            self.test_record_path
            != self.test_assessment.test_record_path
        ):
            raise ValueError(
                "Builder review test-record paths do not match"
            )

        return self

class BuilderReviewStorageResult(BaseModel):
    """Result of immutable Builder review persistence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    review_package_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    review_directory: str
    review_file: str

    review_package_persisted: Literal[True] = True
    candidate_unchanged: Literal[True] = True
    ready_for_human_review: Literal[True] = True

    human_review_performed: Literal[False] = False
    approval_granted: Literal[False] = False
    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class BuilderReviewDecision(BaseModel):
    """Human decision bound to one immutable review package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    decision_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    task_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
    )
    reviewer_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.@-]*$",
    )
    decided_at: datetime

    decision: Literal["approved", "rejected"]
    rationale: str = Field(
        min_length=1,
        max_length=4000,
    )

    review_package_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    review_file: str
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    reviewed_paths: list[str] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )
    approved_paths: list[str] = Field(
        default_factory=list,
        max_length=MAX_BUILDER_FILES,
    )

    human_review_performed: Literal[True] = True
    approval_granted: bool
    promotion_planning_authorized: bool

    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator(
        "reviewed_paths",
        "approved_paths",
    )
    @classmethod
    def paths_must_be_unique(
        cls,
        paths: list[str],
    ) -> list[str]:
        if len(paths) != len(set(paths)):
            raise ValueError(
                "Builder review decision paths "
                "must be unique"
            )

        for path in paths:
            _validate_relative_candidate_path(path)

        return paths

    @model_validator(mode="after")
    def decision_must_be_consistent(
        self,
    ) -> "BuilderReviewDecision":
        if self.decided_at.tzinfo is None:
            raise ValueError(
                "Builder review decision timestamp "
                "must include a timezone"
            )

        reviewed = set(self.reviewed_paths)
        approved = set(self.approved_paths)

        if not approved.issubset(reviewed):
            raise ValueError(
                "approved paths must be a subset "
                "of reviewed paths"
            )

        if self.decision == "approved":
            if not approved:
                raise ValueError(
                    "approved decision requires at least "
                    "one approved path"
                )

            if not self.approval_granted:
                raise ValueError(
                    "approved decision must grant approval"
                )

            if not self.promotion_planning_authorized:
                raise ValueError(
                    "approved decision must authorize "
                    "promotion planning"
                )
        else:
            if approved:
                raise ValueError(
                    "rejected decision cannot approve paths"
                )

            if self.approval_granted:
                raise ValueError(
                    "rejected decision cannot grant approval"
                )

            if self.promotion_planning_authorized:
                raise ValueError(
                    "rejected decision cannot authorize "
                    "promotion planning"
                )

        return self

class BuilderReviewDecisionStorageResult(BaseModel):
    """Result of immutable Builder decision persistence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    decision_id: str
    task_id: str
    decision: Literal["approved", "rejected"]

    review_package_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    decision_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    decision_directory: str
    decision_file: str

    decision_persisted: Literal[True] = True
    human_review_performed: Literal[True] = True
    approval_granted: bool
    promotion_planning_authorized: bool

    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class BuilderPromotionFile(BaseModel):
    """One exact approved candidate-to-project mapping."""

    model_config = ConfigDict(extra="forbid")

    kind: BuilderArtifactKind
    source_path: str
    destination_path: str
    sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    destination_exists: Literal[False] = False


class BuilderPromotionPlan(BaseModel):
    """Non-writing plan for approved Builder files."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    decision_id: str
    reviewer_id: str

    review_package_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    decision_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    generation_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    candidate_tree_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )

    candidate_path: str
    project_root: str
    review_file: str
    decision_file: str

    files: list[BuilderPromotionFile] = Field(
        min_length=1,
        max_length=MAX_BUILDER_FILES,
    )

    human_approval_verified: Literal[True] = True
    candidate_inspection_passed: Literal[True] = True
    promotion_ready: Literal[True] = True
    planning_performed: Literal[True] = True

    files_copied: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False
