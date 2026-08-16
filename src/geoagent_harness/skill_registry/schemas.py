"""Typed schemas for the reusable skill registry."""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


_ENTRYPOINT = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_.]*:"
    r"[A-Za-z_][A-Za-z0-9_]*$"
)


class SkillStatus(str, Enum):
    """Supported skill implementation states."""

    PLANNED = "planned"
    IMPLEMENTED = "implemented"


class SkillKind(str, Enum):
    """Functional category of a registered skill."""

    INSPECTION = "inspection"
    TRANSFORMATION = "transformation"
    DATABASE_LOAD = "database_load"
    VALIDATION = "validation"
    REPORTING = "reporting"


class SkillAccess(str, Enum):
    """Maximum side-effect class of a skill."""

    READ_ONLY = "read_only"
    ARTIFACT_WRITE = "artifact_write"
    DATABASE_WRITE = "database_write"
    EVIDENCE_WRITE = "evidence_write"

class SkillDefinition(BaseModel):
    """One declarative geospatial skill."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    version: str | None = Field(
        default=None,
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
    )
    status: SkillStatus
    kind: SkillKind | None = None
    access: SkillAccess | None = None

    approval_required: bool | None = None
    validation_required: bool | None = None

    entrypoint: str | None = None
    verifier: str | None = None

    @field_validator(
        "entrypoint",
        "verifier",
    )
    @classmethod
    def entrypoint_is_safe(
        cls,
        value: str | None,
    ) -> str | None:
        if (
            value is not None
            and not _ENTRYPOINT.fullmatch(value)
        ):
            raise ValueError(
                "entrypoint must use "
                "'package.module:function' format"
            )

        return value

    @model_validator(mode="after")
    def implementation_is_complete(
        self,
    ) -> "SkillDefinition":
        if self.status == SkillStatus.PLANNED:
            if self.verifier is not None:
                raise ValueError(
                    "planned skills cannot declare a verifier"
                )

            return self

        required_metadata = {
            "version": self.version,
            "entrypoint": self.entrypoint,
            "kind": self.kind,
            "access": self.access,
            "approval_required": (
                self.approval_required
            ),
            "validation_required": (
                self.validation_required
            ),
        }

        missing = [
            name
            for name, value in required_metadata.items()
            if value is None
        ]

        if missing:
            raise ValueError(
                "implemented skill is missing metadata: "
                + ", ".join(missing)
            )

        if (
            self.access == SkillAccess.READ_ONLY
            and self.approval_required is not False
        ):
            raise ValueError(
                "read-only skills cannot require "
                "write approval"
            )

        if (
            self.access == SkillAccess.READ_ONLY
            and self.validation_required is not False
        ):
            raise ValueError(
                "read-only skills cannot require "
                "post-write validation"
            )

        if self.access in {
            SkillAccess.ARTIFACT_WRITE,
            SkillAccess.DATABASE_WRITE,
        }:
            if self.approval_required is not True:
                raise ValueError(
                    "artifact and database writes "
                    "require approval"
                )

            if self.validation_required is not True:
                raise ValueError(
                    "artifact and database writes "
                    "require deterministic validation"
                )

            if self.verifier is None:
                raise ValueError(
                    "validated write skills require "
                    "a verifier"
                )

        if self.access == SkillAccess.EVIDENCE_WRITE:
            if self.kind != SkillKind.REPORTING:
                raise ValueError(
                    "evidence writes must be reporting "
                    "skills"
                )

            if self.approval_required is not False:
                raise ValueError(
                    "evidence reporting does not request "
                    "separate write approval"
                )

            if self.validation_required is not False:
                raise ValueError(
                    "evidence reporting cannot require "
                    "post-write GIS validation"
                )

        if (
            self.kind == SkillKind.VALIDATION
            and self.access != SkillAccess.READ_ONLY
        ):
            raise ValueError(
                "validation skills must be read-only"
            )

        return self

class SkillRegistry(BaseModel):
    """Validated collection of available skills."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    skills: list[SkillDefinition] = Field(
        default_factory=list
    )

    @field_validator("skills")
    @classmethod
    def skill_ids_are_unique(
        cls,
        skills: list[SkillDefinition],
    ) -> list[SkillDefinition]:
        identifiers = [
            skill.id
            for skill in skills
        ]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "skill registry contains duplicate IDs"
            )

        return skills

    def implemented_skills(
        self,
    ) -> list[SkillDefinition]:
        """Return implemented skills in registry order."""

        return [
            skill
            for skill in self.skills
            if skill.status
            == SkillStatus.IMPLEMENTED
        ]

    def get_skill(
        self,
        skill_id: str,
    ) -> SkillDefinition:
        """Return one skill or fail closed."""

        for skill in self.skills:
            if skill.id == skill_id:
                return skill

        raise KeyError(
            f"skill {skill_id!r} is not registered"
        )
