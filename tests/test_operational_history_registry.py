"""Tests for operational-history schema registration."""

from geoagent_harness.schema_registry import (
    ArtifactType,
    CompatibilityDisposition,
    assess_schema_compatibility,
    get_schema_policy,
)


def test_operational_artifacts_use_current_schema() -> None:
    for artifact_type in (
        ArtifactType.OPERATIONAL_EVENT,
        ArtifactType.OPERATIONAL_TIMELINE,
    ):
        policy = get_schema_policy(artifact_type)

        assert policy.current_version == "1.0"
        assert policy.writable_version == "1.0"
        assert policy.supported_read_versions == ("1.0",)

        assessment = assess_schema_compatibility(
            artifact_type=artifact_type,
            artifact_version="1.0",
        )

        assert assessment.disposition == (
            CompatibilityDisposition.CURRENT
        )
        assert assessment.readable is True
        assert assessment.writable is True
