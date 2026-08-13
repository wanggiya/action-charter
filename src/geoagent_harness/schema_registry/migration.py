"""Read-only schema migration assessment."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from geoagent_harness.schema_registry.registry import (
    assess_schema_compatibility,
)
from geoagent_harness.schema_registry.schemas import (
    ArtifactType,
    CompatibilityDisposition,
)


class MigrationAssessment(BaseModel):
    """Non-executing migration recommendation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    artifact_type: ArtifactType
    source_version: str
    target_version: str

    compatibility: CompatibilityDisposition

    migration_available: bool
    migration_required: bool
    manual_review_required: bool

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )
    next_action: str = Field(
        min_length=1,
        max_length=2000,
    )

    artifact_modified: Literal[False] = False
    migration_performed: Literal[False] = False


def assess_migration(
    *,
    artifact_type: ArtifactType | str,
    artifact_version: str,
) -> MigrationAssessment:
    """Assess migration without modifying an artifact."""
    compatibility = assess_schema_compatibility(
        artifact_type=artifact_type,
        artifact_version=artifact_version,
    )

    if (
        compatibility.disposition
        == CompatibilityDisposition.CURRENT
    ):
        reason = (
            "The artifact already uses the current "
            "schema version."
        )
        next_action = (
            "No migration is required."
        )
        manual_review_required = False

    elif (
        compatibility.disposition
        == CompatibilityDisposition.SUPPORTED_READ
    ):
        reason = (
            "The artifact is readable, but new writes "
            "must use the current writable version."
        )
        next_action = (
            "Continue reading the artifact without "
            "modification, or create a separately "
            "approved migrated copy when a migration "
            "is registered."
        )
        manual_review_required = False

    elif (
        compatibility.disposition
        == CompatibilityDisposition.MIGRATION_REQUIRED
    ):
        reason = (
            "The registry identifies the source "
            "version as requiring migration."
        )
        next_action = (
            "Use an explicitly implemented and tested "
            "migration after operator approval."
        )
        manual_review_required = True

    elif (
        compatibility.disposition
        == CompatibilityDisposition.UNSUPPORTED_FUTURE
    ):
        reason = (
            "The artifact was produced by a newer "
            "schema that this harness does not "
            "understand."
        )
        next_action = (
            "Upgrade the harness or use a compatible "
            "reader. Do not downgrade or rewrite the "
            "artifact automatically."
        )
        manual_review_required = True

    elif (
        compatibility.disposition
        == CompatibilityDisposition.UNSUPPORTED_OLDER
    ):
        reason = (
            "The artifact uses an older version for "
            "which no migration is registered."
        )
        next_action = (
            "Preserve the original artifact and add a "
            "tested migration before attempting to "
            "use it."
        )
        manual_review_required = True

    else:
        reason = (
            "The artifact version is not valid."
        )
        next_action = (
            "Correct the version metadata or recover "
            "the artifact from a trusted source."
        )
        manual_review_required = True

    return MigrationAssessment(
        artifact_type=compatibility.artifact_type,
        source_version=artifact_version,
        target_version=(
            compatibility.writable_version
        ),
        compatibility=(
            compatibility.disposition
        ),
        migration_available=False,
        migration_required=(
            compatibility.migration_required
        ),
        manual_review_required=(
            manual_review_required
        ),
        reason=reason,
        next_action=next_action,
        artifact_modified=False,
        migration_performed=False,
    )
