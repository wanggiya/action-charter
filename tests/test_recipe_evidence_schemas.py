"""Tests for typed recipe-run evidence."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from geoagent_harness.recipes import (
    ArtifactReference,
    ArtifactRole,
    LineageEdge,
    RecipeRunEvidence,
    RecipeRunResult,
)


DIGEST = "a" * 64
APPROVAL_ID = (
    "recipe-approval-20260817t200000z-1234abcd"
)
NOW = datetime.now(timezone.utc)


def recipe_result() -> RecipeRunResult:
    return RecipeRunResult.model_validate(
        {
            "schema_version": "1.0",
            "recipe_id": "evidence-test",
            "recipe_sha256": DIGEST,
            "approval_id": APPROVAL_ID,
            "final_status": "validated_success",
            "step_results": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "status": "completed",
                    "execution": {
                        "schema_version": "1.0",
                        "step_id": "step_1",
                        "skill_id": "inspect_vector",
                        "status": "completed",
                        "output_ids": [
                            "source_metadata"
                        ],
                        "result": {
                            "source": (
                                "data/input/sample.geojson"
                            )
                        },
                        "execution_performed": True,
                        "validation_performed": False,
                    },
                    "validation_result": None,
                    "execution_performed": True,
                    "validation_performed": False,
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_vector",
                    "status": "validated_success",
                    "execution": {
                        "schema_version": "1.0",
                        "step_id": "step_2",
                        "skill_id": "convert_vector",
                        "status": (
                            "completed_pending_validation"
                        ),
                        "output_ids": [
                            "converted_vector"
                        ],
                        "result": {
                            "target": (
                                "data/output/sample.gpkg"
                            )
                        },
                        "execution_performed": True,
                        "validation_performed": False,
                    },
                    "validation_result": {
                        "schema_version": "1.0",
                        "passed": True,
                    },
                    "execution_performed": True,
                    "validation_performed": True,
                },
            ],
            "failed_step_id": None,
            "warnings": [],
            "execution_performed": True,
            "validation_performed": True,
        }
    )


def evidence() -> RecipeRunEvidence:
    return RecipeRunEvidence(
        recipe_id="evidence-test",
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        final_status="validated_success",
        run_result=recipe_result(),
        artifacts=[
            ArtifactReference(
                artifact_id="source_vector",
                role=ArtifactRole.INPUT,
                path="data/input/sample.geojson",
                sha256="b" * 64,
                size_bytes=100,
                media_type=(
                    "application/geo+json"
                ),
            ),
            ArtifactReference(
                artifact_id="converted_vector",
                role=ArtifactRole.OUTPUT,
                path="data/output/sample.gpkg",
                sha256="c" * 64,
                size_bytes=200,
                media_type=(
                    "application/geopackage+sqlite3"
                ),
                producer_step_id="step_2",
            ),
        ],
        lineage=[
            LineageEdge(
                source_artifact_id="source_vector",
                target_artifact_id=(
                    "converted_vector"
                ),
                step_id="step_2",
                skill_id="convert_vector",
            )
        ],
        skill_versions={
            "inspect_vector": "0.1.0",
            "convert_vector": "0.1.0",
        },
        recorded_at=NOW,
    )


def test_recipe_run_evidence_is_valid() -> None:
    result = evidence()

    assert result.schema_version == "1.0"
    assert result.final_status == (
        "validated_success"
    )
    assert len(result.artifacts) == 2
    assert len(result.lineage) == 1


def test_duplicate_artifact_ids_are_rejected() -> None:
    payload = evidence().model_dump(
        mode="json"
    )

    payload["artifacts"][1][
        "artifact_id"
    ] = "source_vector"

    with pytest.raises(
        ValidationError,
        match="artifact IDs must be unique",
    ):
        RecipeRunEvidence.model_validate(payload)


def test_unknown_lineage_artifact_is_rejected() -> None:
    payload = evidence().model_dump(
        mode="json"
    )

    payload["lineage"][0][
        "source_artifact_id"
    ] = "missing_artifact"

    with pytest.raises(
        ValidationError,
        match="unknown artifact",
    ):
        RecipeRunEvidence.model_validate(payload)


def test_output_requires_producer_step() -> None:
    with pytest.raises(
        ValidationError,
        match="requires a producer step",
    ):
        ArtifactReference(
            artifact_id="output_vector",
            role=ArtifactRole.OUTPUT,
            path="data/output/sample.gpkg",
            sha256="d" * 64,
            size_bytes=10,
        )


def test_evidence_identity_must_match_result() -> None:
    payload = evidence().model_dump(
        mode="json"
    )

    payload["recipe_sha256"] = "e" * 64

    with pytest.raises(
        ValidationError,
        match="digest conflicts",
    ):
        RecipeRunEvidence.model_validate(payload)

