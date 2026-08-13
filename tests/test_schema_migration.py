"""Tests for read-only schema migration assessment."""

import pytest

from geoagent_harness.schema_registry import (
    ArtifactType,
    CompatibilityDisposition,
    assess_migration,
)


def test_current_version_needs_no_migration() -> None:
    assessment = assess_migration(
        artifact_type=ArtifactType.WORKFLOW_TRACE,
        artifact_version="1.0",
    )

    assert assessment.compatibility == (
        CompatibilityDisposition.CURRENT
    )
    assert assessment.migration_available is False
    assert assessment.migration_required is False
    assert assessment.manual_review_required is False
    assert assessment.artifact_modified is False
    assert assessment.migration_performed is False


@pytest.mark.parametrize(
    "version",
    [
        "0.9",
        "1.1",
        "2.0",
        "latest",
    ],
)
def test_unsupported_versions_require_review(
    version: str,
) -> None:
    assessment = assess_migration(
        artifact_type=ArtifactType.WORKFLOW_STATE,
        artifact_version=version,
    )

    assert assessment.migration_available is False
    assert assessment.manual_review_required is True
    assert assessment.artifact_modified is False
    assert assessment.migration_performed is False


def test_future_version_is_not_downgraded() -> None:
    assessment = assess_migration(
        artifact_type=ArtifactType.APPROVAL_RECORD,
        artifact_version="2.0",
    )

    assert assessment.compatibility == (
        CompatibilityDisposition.UNSUPPORTED_FUTURE
    )
    assert "Do not downgrade" in assessment.next_action
