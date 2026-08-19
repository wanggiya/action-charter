"""Tests for safe recipe artifact evidence construction."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from geoagent_harness.recipes import (
    ArtifactRole,
    RecipeEvidenceError,
    RecipeRunResult,
    build_recipe_run_evidence,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


DIGEST = "a" * 64
APPROVAL_ID = (
    "recipe-approval-20260817t220000z-1234abcd"
)


def registry() -> SkillRegistry:
    return SkillRegistry.model_validate(
        {
            "schema_version": "1.0",
            "skills": [
                {
                    "id": "inspect_vector",
                    "version": "0.1.0",
                    "status": "implemented",
                    "kind": "inspection",
                    "access": "read_only",
                    "approval_required": False,
                    "validation_required": False,
                    "entrypoint": (
                        "example.inspect:run"
                    ),
                },
                {
                    "id": "convert_vector",
                    "version": "0.1.0",
                    "status": "implemented",
                    "kind": "transformation",
                    "access": "artifact_write",
                    "approval_required": True,
                    "validation_required": True,
                    "entrypoint": (
                        "example.convert:run"
                    ),
                    "verifier": (
                        "example.convert:validate"
                    ),
                },
            ],
        }
    )


def run_result(
    *,
    source: str,
    target: str,
    target_size: int,
) -> RecipeRunResult:
    return RecipeRunResult.model_validate(
        {
            "schema_version": "1.0",
            "recipe_id": "evidence-builder-test",
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
                            "source_metadata",
                        ],
                        "result": {
                            "source": source,
                            "driver": "GeoJSON",
                            "layers": [],
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
                            "converted_vector",
                        ],
                        "result": {
                            "schema_version": "1.0",
                            "status": (
                                "converted_pending_validation"
                            ),
                            "source": source,
                            "source_driver": "GeoJSON",
                            "source_layer": "sample",
                            "source_crs": "EPSG:4326",
                            "source_geometry_type": "Point",
                            "source_feature_count": 1,
                            "source_fields": ["id"],
                            "target": target,
                            "target_format": "geopackage",
                            "target_driver": "GPKG",
                            "target_layer": "sample",
                            "target_size_bytes": target_size,
                            "overwrite_performed": False,
                            "validation_required": True,
                            "validation_performed": False,
                            "final_success_claimed": False,
                            "warnings": [],
                        },
                        "execution_performed": True,
                        "validation_performed": False,
                    },
                    "validation_result": {
                        "schema_version": "1.0",
                        "status": "validation_passed",
                        "passed": True,
                        "source": source,
                        "source_layer": "sample",
                        "target": target,
                        "target_layer": "sample",
                        "checks": [
                            {
                                "name": (
                                    "target_file_nonempty"
                                ),
                                "passed": True,
                                "expected": (
                                    "greater_than_zero"
                                ),
                                "actual": target_size,
                            }
                        ],
                        "source_feature_count": 1,
                        "target_feature_count": 1,
                        "source_invalid_geometry_count": 0,
                        "target_invalid_geometry_count": 0,
                        "source_null_geometry_count": 0,
                        "target_null_geometry_count": 0,
                        "warnings": [],
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


def prepare_artifacts(
    tmp_path: Path,
) -> tuple[Path, Path]:
    source = (
        tmp_path
        / "data"
        / "input"
        / "sample.geojson"
    )
    target = (
        tmp_path
        / "data"
        / "output"
        / "sample.gpkg"
    )

    source.parent.mkdir(
        parents=True
    )
    target.parent.mkdir(
        parents=True
    )

    source.write_bytes(
        b'{"type":"FeatureCollection","features":[]}'
    )
    target.write_bytes(
        b"test-geopackage-content"
    )

    return source, target


def test_builds_hashed_deduplicated_lineage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, target = prepare_artifacts(
        tmp_path
    )
    monkeypatch.chdir(tmp_path)

    evidence = build_recipe_run_evidence(
        run_result=run_result(
            source="data/input/sample.geojson",
            target="data/output/sample.gpkg",
            target_size=target.stat().st_size,
        ),
        registry=registry(),
        input_root=tmp_path / "data/input",
        output_root=tmp_path / "data/output",
    )

    assert evidence.final_status == (
        "validated_success"
    )
    assert len(evidence.artifacts) == 2
    assert len(evidence.lineage) == 1

    inputs = [
        artifact
        for artifact in evidence.artifacts
        if artifact.role == ArtifactRole.INPUT
    ]
    outputs = [
        artifact
        for artifact in evidence.artifacts
        if artifact.role == ArtifactRole.OUTPUT
    ]

    # Inspection and conversion reference the same
    # source, so only one input artifact is emitted.
    assert len(inputs) == 1
    assert len(outputs) == 1

    assert inputs[0].sha256 == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()

    assert outputs[0].sha256 == hashlib.sha256(
        target.read_bytes()
    ).hexdigest()

    assert outputs[0].producer_step_id == (
        "step_2"
    )

    edge = evidence.lineage[0]

    assert edge.source_artifact_id == (
        inputs[0].artifact_id
    )
    assert edge.target_artifact_id == (
        outputs[0].artifact_id
    )
    assert edge.step_id == "step_2"
    assert edge.skill_id == "convert_vector"

    assert evidence.skill_versions == {
        "inspect_vector": "0.1.0",
        "convert_vector": "0.1.0",
    }


def test_input_path_escape_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, target = prepare_artifacts(
        tmp_path
    )

    outside = tmp_path / "outside.geojson"
    outside.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        RecipeEvidenceError,
        match="escaped its trusted root",
    ):
        build_recipe_run_evidence(
            run_result=run_result(
                source="outside.geojson",
                target="data/output/sample.gpkg",
                target_size=target.stat().st_size,
            ),
            registry=registry(),
            input_root=tmp_path / "data/input",
            output_root=tmp_path / "data/output",
        )


def test_recorded_output_size_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, target = prepare_artifacts(
        tmp_path
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        RecipeEvidenceError,
        match="recorded output size conflicts",
    ):
        build_recipe_run_evidence(
            run_result=run_result(
                source="data/input/sample.geojson",
                target="data/output/sample.gpkg",
                target_size=(
                    target.stat().st_size + 1
                ),
            ),
            registry=registry(),
            input_root=tmp_path / "data/input",
            output_root=tmp_path / "data/output",
        )


def test_missing_output_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, target = prepare_artifacts(
        tmp_path
    )
    target.unlink()

    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        RecipeEvidenceError,
        match="output artifact does not exist",
    ):
        build_recipe_run_evidence(
            run_result=run_result(
                source="data/input/sample.geojson",
                target="data/output/sample.gpkg",
                target_size=1,
            ),
            registry=registry(),
            input_root=tmp_path / "data/input",
            output_root=tmp_path / "data/output",
        )


def test_shapefile_requires_bundle_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, target = prepare_artifacts(
        tmp_path
    )

    shapefile = source.with_suffix(".shp")
    shapefile.write_bytes(b"not-a-complete-dataset")

    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        RecipeEvidenceError,
        match="sidecar-bundle manifest",
    ):
        build_recipe_run_evidence(
            run_result=run_result(
                source="data/input/sample.shp",
                target="data/output/sample.gpkg",
                target_size=target.stat().st_size,
            ),
            registry=registry(),
            input_root=tmp_path / "data/input",
            output_root=tmp_path / "data/output",
        )

