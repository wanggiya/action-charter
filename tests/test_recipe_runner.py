"""Tests for complete approved recipe execution."""

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes import (
    ArtifactRole,
    RecipeRunError,
    RecipeStepExecutionResult,
    WorkflowRecipe,
    build_recipe_run_evidence,
    create_recipe_approval,
    persist_recipe_run,
    run_approved_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    16,
    16,
    0,
    tzinfo=timezone.utc,
)


class FakeValidation(BaseModel):
    status: str
    passed: bool
    warnings: list[str] = Field(
        default_factory=list
    )


def make_recipe() -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "recipe_id": "recipe-runner-test",
            "summary": "Convert sample points.",
            "original_request": (
                "Convert sample points."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        )
                    },
                    "output_ids": [
                        "source_metadata"
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_vector",
                    "depends_on": [
                        "step_1"
                    ],
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_path": (
                            "data/output/"
                            "runner-test.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )


def approved_inputs(
    tmp_path: Path,
):
    recipe = make_recipe()
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    approval, _ = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=["step_2"],
        decision="approved",
        approver="test-operator",
        reason="Approved runner test.",
        approval_root=tmp_path / "approvals",
        now=NOW,
    )

    settings = MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        enable_write_tools=True,
    )

    settings.input_root.mkdir()
    settings.output_root.mkdir()

    return recipe, registry, approval, settings


def fake_execution(
    *,
    step_id: str,
    skill_id: str,
) -> RecipeStepExecutionResult:
    return RecipeStepExecutionResult(
        step_id=step_id,
        skill_id=skill_id,
        status=(
            "completed"
            if skill_id == "inspect_vector"
            else "completed_pending_validation"
        ),
        output_ids=["test_output"],
        result={"status": "test"},
        execution_performed=True,
        validation_performed=False,
    )


def test_success_requires_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geoagent_harness.recipes import (
        runner,
    )

    recipe, registry, approval, settings = (
        approved_inputs(tmp_path)
    )

    monkeypatch.setattr(
        runner,
        "dispatch_recipe_step",
        lambda **kwargs: fake_execution(
            step_id=kwargs["step_id"],
            skill_id=next(
                step.skill_id
                for step in kwargs[
                    "envelope"
                ].steps
                if step.step_id
                == kwargs["step_id"]
            ),
        ),
    )

    monkeypatch.setattr(
        runner,
        "validate_vector_conversion",
        lambda **kwargs: FakeValidation(
            status="validation_passed",
            passed=True,
        ),
    )

    result = run_approved_recipe(
        recipe=recipe,
        approval=approval,
        registry=registry,
        settings=settings,
    )

    assert result.final_status == (
        "validated_success"
    )
    assert result.validation_performed is True
    assert [
        step.status
        for step in result.step_results
    ] == [
        "completed",
        "validated_success",
    ]


def test_failed_validation_withholds_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geoagent_harness.recipes import (
        runner,
    )

    recipe, registry, approval, settings = (
        approved_inputs(tmp_path)
    )

    monkeypatch.setattr(
        runner,
        "dispatch_recipe_step",
        lambda **kwargs: fake_execution(
            step_id=kwargs["step_id"],
            skill_id=next(
                step.skill_id
                for step in kwargs[
                    "envelope"
                ].steps
                if step.step_id
                == kwargs["step_id"]
            ),
        ),
    )

    monkeypatch.setattr(
        runner,
        "validate_vector_conversion",
        lambda **kwargs: FakeValidation(
            status="validation_failed",
            passed=False,
            warnings=["Feature count changed."],
        ),
    )

    result = run_approved_recipe(
        recipe=recipe,
        approval=approval,
        registry=registry,
        settings=settings,
    )

    assert result.final_status == (
        "validation_failed"
    )
    assert result.failed_step_id == "step_2"
    assert result.warnings == [
        "Feature count changed."
    ]
    assert (
        result.step_results[-1].status
        == "validation_failed"
    )


def test_writes_disabled_blocks_recipe(
    tmp_path: Path,
) -> None:
    recipe, registry, approval, settings = (
        approved_inputs(tmp_path)
    )

    blocked = settings.model_copy(
        update={
            "enable_write_tools": False
        }
    )

    with pytest.raises(
        RecipeRunError,
        match="write tools are disabled",
    ):
        run_approved_recipe(
            recipe=recipe,
            approval=approval,
            registry=registry,
            settings=blocked,
        )

def test_real_raster_conversion_recipe_is_validated(
    tmp_path: Path,
) -> None:
    """Execute the promoted raster skill and verifier."""

    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    approval_root = tmp_path / "approvals"

    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample_dem.tif"
    )
    target = (
        output_root / "converted_dem.tif"
    )

    recipe = WorkflowRecipe.model_validate(
        {
            "recipe_id": (
                "raster-conversion-runner-test"
            ),
            "summary": (
                "Inspect and reproject a raster."
            ),
            "original_request": (
                "Convert the sample raster "
                "to EPSG:3857."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_raster",
                    "arguments": {
                        "path": str(source),
                    },
                    "output_ids": [
                        "source_raster_metadata",
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_raster",
                    "depends_on": [
                        "step_1",
                    ],
                    "arguments": {
                        "path": str(source),
                        "target_path": str(
                            target
                        ),
                        "target_crs": "EPSG:3857",
                        "resampling": "bilinear",
                    },
                    "output_ids": [
                        "converted_raster",
                    ],
                },
            ],
        }
    )

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    approval, _ = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=[
            "step_2",
        ],
        decision="approved",
        approver="test-operator",
        reason=(
            "Approved exact raster conversion."
        ),
        approval_root=approval_root,
        now=NOW,
    )

    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=True,
        allow_overwrite=False,
    )

    assert not target.exists()
    assert approval.step_ids == [
        "step_2"
    ]

    result = run_approved_recipe(
        recipe=recipe,
        approval=approval,
        registry=registry,
        settings=settings,
    )

    assert target.is_file()
    assert target.stat().st_size > 0

    assert result.final_status == (
        "validated_success"
    )
    assert result.failed_step_id is None
    assert result.execution_performed is True
    assert result.validation_performed is True

    assert [
        step.skill_id
        for step in result.step_results
    ] == [
        "inspect_raster",
        "convert_raster",
    ]

    inspection = result.step_results[0]
    conversion = result.step_results[1]

    assert inspection.status == "completed"
    assert (
        inspection.validation_performed
        is False
    )

    assert conversion.status == (
        "validated_success"
    )
    assert (
        conversion.execution.status
        == "completed_pending_validation"
    )
    assert (
        conversion.execution
        .validation_performed
        is False
    )
    assert (
        conversion.validation_performed
        is True
    )
    assert (
        conversion.validation_result
        is not None
    )
    assert (
        conversion.validation_result[
            "passed"
        ]
        is True
    )
    assert (
        conversion.validation_result[
            "final_success_claimed"
        ]
        is True
    )

    evidence = build_recipe_run_evidence(
        run_result=result,
        registry=registry,
        input_root=input_root,
        output_root=output_root,
        recorded_at=NOW,
    )

    assert evidence.final_status == (
        "validated_success"
    )
    assert evidence.skill_versions == {
        "inspect_raster": "0.1.0",
        "convert_raster": "0.1.0",
    }

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

    assert len(inputs) == 1
    assert len(outputs) == 1
    assert inputs[0].media_type == "image/tiff"
    assert outputs[0].media_type == "image/tiff"

    assert inputs[0].path.endswith(
        "sample_dem.tif"
    )
    assert outputs[0].path.endswith(
        "converted_dem.tif"
    )
    assert (
        outputs[0].producer_step_id
        == "step_2"
    )

    assert len(evidence.lineage) == 1

    edge = evidence.lineage[0]

    assert edge.source_artifact_id == (
        inputs[0].artifact_id
    )
    assert edge.target_artifact_id == (
        outputs[0].artifact_id
    )
    assert edge.step_id == "step_2"
    assert edge.skill_id == "convert_raster"

    persistence_settings = (
        settings.model_copy(
            update={
                "project_root": tmp_path,
                "recipe_run_root": (
                    tmp_path / "recipe-runs"
                ),
                "recipe_evidence_root": (
                    tmp_path
                    / "recipe-evidence"
                ),
                "report_root": (
                    tmp_path / "reports"
                ),
            }
        )
    )

    execution_record = persist_recipe_run(
        run_result=result,
        registry=registry,
        settings=persistence_settings,
        recorded_at=NOW,
    )

    assert (
        execution_record.final_status
        == "validated_success"
    )
    assert (
        execution_record.execution_performed
        is True
    )
    assert (
        execution_record.evidence_recorded
        is True
    )
    assert (
        execution_record.report_written
        is True
    )

    run_path = (
        tmp_path
        / execution_record.run_result_path
    )
    evidence_path = (
        tmp_path
        / execution_record.evidence_path
    )
    report_path = (
        tmp_path
        / execution_record.report_path
    )

    assert run_path.is_file()
    assert evidence_path.is_file()
    assert report_path.is_file()

    assert run_path.stat().st_size > 0
    assert evidence_path.stat().st_size > 0
    assert report_path.stat().st_size > 0

    report_text = report_path.read_text(
        encoding="utf-8"
    )

    assert "convert_raster" in report_text
    assert "converted_dem.tif" in report_text


def test_denied_raster_recipe_does_not_write(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    approval_root = tmp_path / "approvals"

    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample_dem.tif"
    )
    target = (
        output_root / "denied_output.tif"
    )

    recipe = WorkflowRecipe.model_validate(
        {
            "recipe_id": (
                "denied-raster-conversion-test"
            ),
            "summary": (
                "A denied raster conversion."
            ),
            "original_request": (
                "Convert the sample raster."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_raster",
                    "arguments": {
                        "path": str(source),
                    },
                    "output_ids": [
                        "source_raster_metadata",
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_raster",
                    "depends_on": [
                        "step_1",
                    ],
                    "arguments": {
                        "path": str(source),
                        "target_path": str(
                            target
                        ),
                        "target_crs": "EPSG:3857",
                    },
                    "output_ids": [
                        "converted_raster",
                    ],
                },
            ],
        }
    )

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    approval, _ = create_recipe_approval(
        recipe=recipe,
        registry=registry,
        step_ids=[
            "step_2",
        ],
        decision="denied",
        approver="test-operator",
        reason="Raster conversion denied.",
        approval_root=approval_root,
        now=NOW,
    )

    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=True,
    )

    with pytest.raises(RecipeRunError):
        run_approved_recipe(
            recipe=recipe,
            approval=approval,
            registry=registry,
            settings=settings,
        )

    assert not target.exists()

