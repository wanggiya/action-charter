"""Typed schemas for proposal-only Builder Agent output."""

from __future__ import annotations

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
