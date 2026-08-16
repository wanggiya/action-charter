"""Tests for the hard-coded recipe dispatcher."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes import (
    RecipeDispatchError,
    RecipeExecutionEnvelope,
    RecipeExecutionStep,
    dispatch_recipe_step,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]


class Dumpable(BaseModel):
    status: str = "test_result"


def settings(
    tmp_path: Path,
    *,
    writes: bool = False,
) -> MCPSettings:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir(
        exist_ok=True
    )
    output_root.mkdir(
        exist_ok=True
    )

    return MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=writes,
    )


def envelope(
    *,
    skill_id: str,
    arguments: dict,
    approved: bool = True,
) -> RecipeExecutionEnvelope:
    return RecipeExecutionEnvelope(
        recipe_id="dispatcher-test",
        recipe_sha256="a" * 64,
        approval_id=(
            "recipe-approval-"
            "20260816t120000z-1234abcd"
        ),
        approved_step_ids=(
            ["step_1"]
            if approved
            else ["step_999"]
        ),
        topological_step_ids=[
            "step_1"
        ],
        steps=[
            RecipeExecutionStep(
                step_id="step_1",
                skill_id=skill_id,
                arguments=arguments,
                output_ids=[
                    "test_output"
                ],
            )
        ],
    )


def test_dispatches_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geoagent_harness.recipes import (
        dispatcher,
    )

    monkeypatch.setattr(
        dispatcher,
        "inspect_vector",
        lambda **kwargs: Dumpable(),
    )

    result = dispatch_recipe_step(
        envelope=envelope(
            skill_id="inspect_vector",
            arguments={
                "path": "input.geojson"
            },
        ),
        step_id="step_1",
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        settings=settings(tmp_path),
    )

    assert result.status == "completed"
    assert result.execution_performed is True
    assert result.validation_performed is False


def test_dispatches_approved_conversion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geoagent_harness.recipes import (
        dispatcher,
    )

    monkeypatch.setattr(
        dispatcher,
        "convert_vector",
        lambda **kwargs: Dumpable(
            status=(
                "converted_pending_validation"
            )
        ),
    )

    result = dispatch_recipe_step(
        envelope=envelope(
            skill_id="convert_vector",
            arguments={
                "path": "input.geojson",
                "target_path": "output.gpkg",
            },
        ),
        step_id="step_1",
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        settings=settings(
            tmp_path,
            writes=True,
        ),
    )

    assert result.status == (
        "completed_pending_validation"
    )
    assert result.validation_performed is False


def test_unapproved_write_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RecipeDispatchError,
        match="approved scope",
    ):
        dispatch_recipe_step(
            envelope=envelope(
                skill_id="convert_vector",
                arguments={
                    "path": "input.geojson",
                    "target_path": "output.gpkg",
                },
                approved=False,
            ),
            step_id="step_1",
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            settings=settings(
                tmp_path,
                writes=True,
            ),
        )


def test_unknown_arguments_are_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RecipeDispatchError,
        match="arguments",
    ):
        dispatch_recipe_step(
            envelope=envelope(
                skill_id="inspect_vector",
                arguments={
                    "path": "input.geojson",
                    "shell": "not-permitted",
                },
            ),
            step_id="step_1",
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            settings=settings(tmp_path),
        )


def test_unallowlisted_skill_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RecipeDispatchError,
        match=(
            "hard-coded dispatcher allowlist"
            "|not registered"
        ),
    ):
        dispatch_recipe_step(
            envelope=envelope(
                skill_id="generate_report",
                arguments={},
            ),
            step_id="step_1",
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            settings=settings(tmp_path),
        )

def test_skill_failure_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from geoagent_harness.recipes import (
        dispatcher,
    )
    from geoagent_harness.skills.convert_vector.service import (
        ConvertVectorError,
    )

    def fail_conversion(**kwargs):
        raise ConvertVectorError(
            "controlled test failure"
        )

    monkeypatch.setattr(
        dispatcher,
        "convert_vector",
        fail_conversion,
    )

    with pytest.raises(
        RecipeDispatchError,
        match="execution failed",
    ):
        dispatch_recipe_step(
            envelope=envelope(
                skill_id="convert_vector",
                arguments={
                    "path": "input.geojson",
                    "target_path": (
                        "converted-points.gpkg"
                    ),
                },
            ),
            step_id="step_1",
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            settings=settings(
                tmp_path,
                writes=True,
            ),
        )
