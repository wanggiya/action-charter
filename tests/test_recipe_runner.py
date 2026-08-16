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
    RecipeRunError,
    RecipeStepExecutionResult,
    WorkflowRecipe,
    create_recipe_approval,
    run_approved_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
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

