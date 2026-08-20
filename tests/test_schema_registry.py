"""Tests for the central artifact schema registry."""

import pytest

from geoagent_harness.schema_registry import (
    ArtifactType,
    CompatibilityDisposition,
    SchemaRegistryError,
    assess_schema_compatibility,
    get_schema_policy,
    list_schema_policies,
)


def test_every_artifact_has_one_policy() -> None:
    policies = list_schema_policies()

    assert len(policies) == len(ArtifactType)
    assert {
        policy.artifact_type
        for policy in policies
    } == set(ArtifactType)


@pytest.mark.parametrize(
    "artifact_type",
    [
        ArtifactType.RECIPE,
        ArtifactType.RECIPE_VALIDATION,
        ArtifactType.RECIPE_APPROVAL,
        ArtifactType.RECIPE_EXECUTION_ENVELOPE,
        ArtifactType.RECIPE_STEP_EXECUTION_RESULT,
        ArtifactType.RECIPE_RUN_RESULT,
        ArtifactType.RECIPE_RUN_EVIDENCE,
        ArtifactType.RECIPE_EXECUTION_RECORD,
        ArtifactType.PERSISTED_RECIPE_EXECUTION_RESULT,
    ],
)
def test_recipe_artifacts_use_current_schema(
    artifact_type: ArtifactType,
) -> None:
    policy = get_schema_policy(
        artifact_type
    )

    assert policy.current_version == "1.0"
    assert policy.writable_version == "1.0"
    assert policy.supported_read_versions == (
        "1.0",
    )

    assessment = assess_schema_compatibility(
        artifact_type=artifact_type,
        artifact_version="1.0",
    )

    assert assessment.disposition == (
        CompatibilityDisposition.CURRENT
    )
    assert assessment.readable is True
    assert assessment.writable is True


@pytest.mark.parametrize(
    "version",
    [
        "2.0",
        "1.1",
        "10.0",
    ],
)
def test_future_versions_fail_closed(
    version: str,
) -> None:
    assessment = assess_schema_compatibility(
        artifact_type=ArtifactType.WORKFLOW_TRACE,
        artifact_version=version,
    )

    assert assessment.disposition == (
        CompatibilityDisposition.UNSUPPORTED_FUTURE
    )
    assert assessment.readable is False
    assert assessment.writable is False
    assert assessment.migration_required is False


@pytest.mark.parametrize(
    "version",
    [
        "0.9",
        "0.1",
    ],
)
def test_older_versions_without_migration_fail_closed(
    version: str,
) -> None:
    assessment = assess_schema_compatibility(
        artifact_type=ArtifactType.APPROVAL_RECORD,
        artifact_version=version,
    )

    assert assessment.disposition == (
        CompatibilityDisposition.UNSUPPORTED_OLDER
    )
    assert assessment.readable is False
    assert assessment.writable is False


@pytest.mark.parametrize(
    "version",
    [
        "",
        "1",
        "v1.0",
        "1.0.0",
        "latest",
        "01.0",
    ],
)
def test_invalid_versions_are_rejected(
    version: str,
) -> None:
    assessment = assess_schema_compatibility(
        artifact_type=ArtifactType.WORKFLOW_PLAN,
        artifact_version=version,
    )

    assert assessment.disposition == (
        CompatibilityDisposition.INVALID_VERSION
    )
    assert assessment.readable is False
    assert assessment.writable is False


def test_unknown_artifact_type_is_rejected() -> None:
    with pytest.raises(
        SchemaRegistryError,
        match="unknown artifact type",
    ):
        get_schema_policy("unknown_artifact")