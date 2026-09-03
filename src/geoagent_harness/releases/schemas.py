"""Strict schemas for authoritative release lifecycles."""

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


class ReleaseLifecycleState(str, Enum):
    """Deterministic lifecycle states for release artifacts."""

    CANDIDATE = "candidate"
    VALIDATED = "validated"
    RELEASED = "released"
    REJECTED = "rejected"


class ReleaseSubjectType(str, Enum):
    """Supported authoritative run families."""

    WORKFLOW = "workflow"
    RECIPE = "recipe"


class ReleaseComponentKind(str, Enum):
    """Allowlisted evidence roles inside a release package."""

    RECIPE = "recipe"
    PLAN = "plan"
    APPROVAL = "approval"
    RUN_RESULT = "run_result"
    RECIPE_EVIDENCE = "recipe_evidence"
    VALIDATION = "validation"
    CRITIC_RESULT = "critic_result"
    ARTIFACT_MANIFEST = "artifact_manifest"
    LINEAGE = "lineage"
    REPORT = "report"
    TRACE = "trace"
    OPERATIONAL_HISTORY = "operational_history"


class ReleaseComponentReference(BaseModel):
    """One exact digest-bound release input."""

    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_-]{0,99}$",
    )
    kind: ReleaseComponentKind
    path: str = Field(min_length=1, max_length=2000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=1)
    required: Literal[True] = True

    @field_validator("path")
    @classmethod
    def path_must_be_bounded(
        cls,
        value: str,
    ) -> str:
        if (
            "\x00" in value
            or "\n" in value
            or "\r" in value
            or "\\" in value
        ):
            raise ValueError(
                "release component paths must be bounded POSIX paths"
            )
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or str(path) != value
            or any(
                part in {"", ".", ".."} or part.startswith(".")
                for part in path.parts
            )
        ):
            raise ValueError(
                "release component paths must be normalized and relative"
            )
        return value


def _required_component_kinds(
    subject_type: ReleaseSubjectType,
) -> set[ReleaseComponentKind]:
    common = {
        ReleaseComponentKind.APPROVAL,
        ReleaseComponentKind.CRITIC_RESULT,
        ReleaseComponentKind.REPORT,
        ReleaseComponentKind.OPERATIONAL_HISTORY,
    }
    if subject_type == ReleaseSubjectType.RECIPE:
        return common | {
            ReleaseComponentKind.RECIPE,
            ReleaseComponentKind.RUN_RESULT,
            ReleaseComponentKind.RECIPE_EVIDENCE,
        }
    return common | {
        ReleaseComponentKind.PLAN,
        ReleaseComponentKind.TRACE,
    }


class AuthoritativeReleaseCandidate(BaseModel):
    """Non-writing deterministic assessment of release readiness."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    release_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    subject_type: ReleaseSubjectType
    subject_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    deterministic_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ]
    lifecycle_state: Literal[
        ReleaseLifecycleState.CANDIDATE,
        ReleaseLifecycleState.VALIDATED,
        ReleaseLifecycleState.REJECTED,
    ]
    components: list[ReleaseComponentReference] = Field(
        min_length=1,
        max_length=100,
    )
    approval_complete: bool
    validation_complete: bool
    critic_complete: bool
    evidence_complete: bool
    ready_for_release: bool
    violations: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
    assessed_at: datetime

    assessment_performed: Literal[True] = True
    files_copied: Literal[False] = False
    release_created: Literal[False] = False
    registry_modified: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("assessed_at")
    @classmethod
    def assessed_at_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "release assessment timestamp must include a timezone"
            )
        return value

    @model_validator(mode="after")
    def readiness_must_follow_evidence(
        self,
    ) -> "AuthoritativeReleaseCandidate":
        component_ids = [item.component_id for item in self.components]
        paths = [item.path for item in self.components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError(
                "release component IDs must be unique"
            )
        if len(paths) != len(set(paths)):
            raise ValueError(
                "release component paths must be unique"
            )
        kinds = {item.kind for item in self.components}
        missing = _required_component_kinds(
            self.subject_type
        ) - kinds

        complete = (
            self.approval_complete
            and self.validation_complete
            and self.critic_complete
            and not missing
        )
        if self.evidence_complete != complete:
            raise ValueError(
                "release evidence-complete claim is inconsistent"
            )
        ready = (
            self.deterministic_status == "validated_success"
            and complete
            and not self.violations
        )
        if self.ready_for_release != ready:
            raise ValueError(
                "release readiness conflicts with evidence"
            )
        if not ready and not self.violations:
            raise ValueError(
                "non-ready release candidate requires violations"
            )
        expected_state = (
            ReleaseLifecycleState.VALIDATED
            if ready
            else (
                ReleaseLifecycleState.REJECTED
                if self.deterministic_status
                in {"validation_failed", "execution_failed"}
                else ReleaseLifecycleState.CANDIDATE
            )
        )
        if self.lifecycle_state != expected_state:
            raise ValueError(
                "release lifecycle state conflicts with readiness"
            )
        return self


class AuthoritativeReleaseManifest(BaseModel):
    """Canonical manifest for one completed immutable release."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    release_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    subject_type: ReleaseSubjectType
    subject_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    components: list[ReleaseComponentReference] = Field(
        min_length=1,
        max_length=100,
    )
    released_at: datetime
    lifecycle_state: Literal[
        ReleaseLifecycleState.RELEASED
    ] = ReleaseLifecycleState.RELEASED

    candidate_validated: Literal[True] = True
    exact_file_set_verified: Literal[True] = True
    component_digests_verified: Literal[True] = True
    files_copied: Literal[True] = True
    release_created: Literal[True] = True
    registry_modified: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("released_at")
    @classmethod
    def released_at_must_be_aware(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "release timestamp must include a timezone"
            )
        return value

    @model_validator(mode="after")
    def components_must_be_unique(
        self,
    ) -> "AuthoritativeReleaseManifest":
        ids = [item.component_id for item in self.components]
        paths = [item.path for item in self.components]
        if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
            raise ValueError(
                "release manifest components must be unique"
            )
        kinds = {item.kind for item in self.components}
        if _required_component_kinds(self.subject_type) - kinds:
            raise ValueError(
                "release manifest is missing required component kinds"
            )
        return self


class AuthoritativeReleaseStorageResult(BaseModel):
    """Result of one atomic immutable release creation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    release_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    subject_type: ReleaseSubjectType
    subject_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_directory: str
    release_manifest: str
    component_count: int = Field(ge=1, le=100)

    candidate_validated: Literal[True] = True
    exact_file_set_verified: Literal[True] = True
    component_digests_verified: Literal[True] = True
    files_copied: Literal[True] = True
    release_created: Literal[True] = True
    registry_modified: Literal[False] = False
    execution_performed: Literal[False] = False


class AuthoritativeReleaseInspectionResult(BaseModel):
    """Result of independently verifying one immutable release."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    release_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    subject_type: ReleaseSubjectType
    subject_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_directory: str
    release_manifest: str
    component_count: int = Field(ge=1, le=100)

    manifest_canonical: Literal[True] = True
    directory_identity_verified: Literal[True] = True
    candidate_verified: Literal[True] = True
    exact_file_set_verified: Literal[True] = True
    component_digests_verified: Literal[True] = True
    release_verified: Literal[True] = True
    files_modified: Literal[False] = False
    registry_modified: Literal[False] = False
    execution_performed: Literal[False] = False
