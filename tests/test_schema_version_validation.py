"""Tests for pre-validation artifact version checks."""

import pytest

from geoagent_harness.schema_registry import (
    ArtifactType,
    CompatibilityDisposition,
    SchemaVersionError,
    require_supported_schema,
)


def test_accepts_current_top_level_version() -> None:
    assessment = require_supported_schema(
        {
            "schema_version": "1.0",
        },
        artifact_type=ArtifactType.APPROVAL_RECORD,
    )

    assert assessment.readable is True
    assert assessment.disposition == (
        CompatibilityDisposition.CURRENT
    )


def test_accepts_nested_plan_version() -> None:
    assessment = require_supported_schema(
        {
            "plan": {
                "schema_version": "1.0",
            }
        },
        artifact_type=ArtifactType.WORKFLOW_PLAN,
        version_path=(
            "plan",
            "schema_version",
        ),
    )

    assert assessment.readable is True


def test_rejects_missing_version() -> None:
    with pytest.raises(
        SchemaVersionError,
        match="missing required",
    ):
        require_supported_schema(
            {},
            artifact_type=ArtifactType.WORKFLOW_TRACE,
        )


def test_rejects_missing_nested_version() -> None:
    with pytest.raises(
        SchemaVersionError,
        match="missing required",
    ):
        require_supported_schema(
            {
                "plan": {},
            },
            artifact_type=ArtifactType.WORKFLOW_PLAN,
            version_path=(
                "plan",
                "schema_version",
            ),
        )


def test_rejects_non_string_version() -> None:
    with pytest.raises(
        SchemaVersionError,
        match="must be a string",
    ):
        require_supported_schema(
            {
                "schema_version": 1,
            },
            artifact_type=ArtifactType.APPROVAL_RECORD,
        )


@pytest.mark.parametrize(
    "version",
    [
        "0.9",
        "1.1",
        "2.0",
        "latest",
    ],
)
def test_rejects_unreadable_versions(
    version: str,
) -> None:
    with pytest.raises(
        SchemaVersionError,
        match="not readable",
    ):
        require_supported_schema(
            {
                "schema_version": version,
            },
            artifact_type=ArtifactType.WORKFLOW_STATE,
        )
