"""Authoritative artifact schema-version registry."""

from __future__ import annotations

import re

from geoagent_harness.schema_registry.schemas import (
    ArtifactType,
    CompatibilityAssessment,
    CompatibilityDisposition,
    SchemaPolicy,
)


_VERSION = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>[0-9]+)$"
)


def _policy(
    artifact_type: ArtifactType,
) -> SchemaPolicy:
    return SchemaPolicy(
        artifact_type=artifact_type,
        current_version="1.0",
        writable_version="1.0",
        supported_read_versions=("1.0",),
        migration_sources=(),
    )


_SCHEMA_POLICIES: dict[
    ArtifactType,
    SchemaPolicy,
] = {
    artifact_type: _policy(artifact_type)
    for artifact_type in ArtifactType
}


class SchemaRegistryError(ValueError):
    """Raised for an unknown artifact schema request."""


def list_schema_policies() -> tuple[SchemaPolicy, ...]:
    """Return registry policies in stable artifact order."""
    return tuple(
        _SCHEMA_POLICIES[artifact_type]
        for artifact_type in ArtifactType
    )


def get_schema_policy(
    artifact_type: ArtifactType | str,
) -> SchemaPolicy:
    """Return the policy for one known artifact type."""
    try:
        normalized = ArtifactType(artifact_type)
    except ValueError as exc:
        raise SchemaRegistryError(
            f"unknown artifact type: {artifact_type!r}"
        ) from exc

    return _SCHEMA_POLICIES[normalized]


def _version_tuple(
    value: str,
) -> tuple[int, int] | None:
    match = _VERSION.fullmatch(value)

    if match is None:
        return None

    return (
        int(match.group("major")),
        int(match.group("minor")),
    )


def assess_schema_compatibility(
    *,
    artifact_type: ArtifactType | str,
    artifact_version: str,
) -> CompatibilityAssessment:
    """Assess compatibility without changing an artifact."""
    policy = get_schema_policy(artifact_type)

    parsed = _version_tuple(artifact_version)
    current = _version_tuple(policy.current_version)

    if parsed is None:
        disposition = (
            CompatibilityDisposition.INVALID_VERSION
        )
        readable = False
        writable = False
        migration_required = False
        reason = (
            "The artifact schema version does not use "
            "the required major.minor format."
        )

    elif artifact_version == policy.current_version:
        disposition = CompatibilityDisposition.CURRENT
        readable = True
        writable = (
            artifact_version
            == policy.writable_version
        )
        migration_required = False
        reason = (
            "The artifact uses the current supported "
            "schema version."
        )

    elif artifact_version in policy.supported_read_versions:
        disposition = (
            CompatibilityDisposition.SUPPORTED_READ
        )
        readable = True
        writable = False
        migration_required = False
        reason = (
            "The artifact is readable but new writes "
            "must use the writable schema version."
        )

    elif artifact_version in policy.migration_sources:
        disposition = (
            CompatibilityDisposition.MIGRATION_REQUIRED
        )
        readable = False
        writable = False
        migration_required = True
        reason = (
            "The artifact requires an explicit "
            "validated migration before use."
        )

    elif parsed > current:
        disposition = (
            CompatibilityDisposition.UNSUPPORTED_FUTURE
        )
        readable = False
        writable = False
        migration_required = False
        reason = (
            "The artifact uses a future schema version "
            "that this harness does not understand."
        )

    else:
        disposition = (
            CompatibilityDisposition.UNSUPPORTED_OLDER
        )
        readable = False
        writable = False
        migration_required = False
        reason = (
            "The artifact uses an older unsupported "
            "schema version and no migration is "
            "registered."
        )

    return CompatibilityAssessment(
        artifact_type=policy.artifact_type,
        artifact_version=artifact_version,
        current_version=policy.current_version,
        writable_version=policy.writable_version,
        disposition=disposition,
        readable=readable,
        writable=writable,
        migration_required=migration_required,
        reason=reason,
        artifact_modified=False,
    )