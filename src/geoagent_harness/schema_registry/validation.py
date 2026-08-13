"""Version checks applied before artifact schema validation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from geoagent_harness.schema_registry.registry import (
    assess_schema_compatibility,
)
from geoagent_harness.schema_registry.schemas import (
    ArtifactType,
    CompatibilityAssessment,
)


class SchemaVersionError(ValueError):
    """Raised when an artifact version cannot be read."""


def require_supported_schema(
    payload: Any,
    *,
    artifact_type: ArtifactType | str,
    version_path: Sequence[str] = (
        "schema_version",
    ),
) -> CompatibilityAssessment:
    """Require an explicit readable schema version."""
    current = payload

    for key in version_path:
        if not isinstance(current, dict):
            raise SchemaVersionError(
                "artifact does not contain a valid "
                "schema-version location"
            )

        if key not in current:
            joined = ".".join(version_path)

            raise SchemaVersionError(
                f"artifact is missing required "
                f"{joined!r}"
            )

        current = current[key]

    if not isinstance(current, str):
        raise SchemaVersionError(
            "artifact schema version must be a string"
        )

    assessment = assess_schema_compatibility(
        artifact_type=artifact_type,
        artifact_version=current,
    )

    if not assessment.readable:
        raise SchemaVersionError(
            "artifact schema version is not readable: "
            f"{assessment.disposition.value}"
        )

    return assessment
