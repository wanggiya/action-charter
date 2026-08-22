"""Typed schemas for non-executing skill scaffolds."""

from __future__ import annotations

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


class SkillScaffoldRequest(BaseModel):
    """Operator request for one new GIS skill skeleton."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    kind: SkillKind
    access: SkillAccess

    generation_requested: Literal[False] = False
    registry_modification_requested: Literal[False] = False
    execution_requested: Literal[False] = False


class SkillScaffoldPlan(BaseModel):
    """Deterministic, non-writing skill scaffold plan."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    summary: str

    kind: SkillKind
    access: SkillAccess

    approval_required: bool
    validation_required: bool

    package_path: str
    files: list[str] = Field(min_length=1)
    test_files: list[str] = Field(min_length=1)

    registry_entry: SkillDefinition

    warnings: list[str] = Field(
        default_factory=list
    )

    generation_performed: Literal[False] = False
    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def plan_is_fail_closed(
        self,
    ) -> "SkillScaffoldPlan":
        if self.registry_entry.status.value != "planned":
            raise ValueError(
                "scaffold registry entry must remain planned"
            )

        if self.registry_entry.id != self.skill_id:
            raise ValueError(
                "registry entry skill ID does not match"
            )

        if self.registry_entry.verifier is not None:
            raise ValueError(
                "planned scaffold cannot declare a verifier"
            )

        return self

class SkillScaffoldGenerationResult(BaseModel):
    """Result of generating one isolated scaffold bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    scaffold_path: str

    generated_files: list[str] = Field(
        min_length=1
    )
    registry_fragment_path: str
    manifest_path: str

    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False
    generation_performed: Literal[True] = True
    
class SkillScaffoldContractResult(BaseModel):
    """Deterministic assessment of one scaffold bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    skill_id: str
    scaffold_path: str

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

    registry_modified: Literal[False] = False
    implementation_trusted: Literal[False] = False
    promotion_performed: Literal[False] = False
    execution_performed: Literal[False] = False

