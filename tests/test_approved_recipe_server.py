"""Tests for server-side approved recipe verification."""

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest

from geoagent_harness.mcp_server.approved_recipe import (
    ApprovedRecipeError,
    run_approved_recipe,
    validate_approved_recipe_request,
)
from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes import (
    WorkflowRecipe,
    build_recipe_execution_envelope,
    create_recipe_approval,
    save_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    16,
    20,
    0,
    tzinfo=timezone.utc,
)


def prepared_request(
    tmp_path: Path,
):
    recipe_root = tmp_path / "recipes"
    approval_root = tmp_path / "approvals"
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    draft = WorkflowRecipe.model_validate(
        {
            "recipe_id": "server-recipe-test",
            "summary": "Convert sample points.",
            "original_request": (
                "Convert sample points."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "arguments": {
                        "path": "input.geojson"
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
                        "path": "input.geojson",
                        "target_path": "output.gpkg",
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )

    recipe, recipe_path = save_recipe(
        draft,
        recipe_root=recipe_root,
    )

    approval, approval_path = (
        create_recipe_approval(
            recipe=recipe,
            registry=registry,
            step_ids=["step_2"],
            decision="approved",
            approver="test-operator",
            reason="Approved server test.",
            approval_root=approval_root,
            now=NOW,
        )
    )

    envelope = (
        build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
    )

    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        recipe_root=recipe_root,
        approval_root=approval_root,
        project_root=PROJECT_ROOT,
        enable_write_tools=True,
    )

    return (
        recipe_path,
        approval_path,
        envelope,
        settings,
    )


def test_server_rebuilds_exact_envelope(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    verified = validate_approved_recipe_request(
        execution_envelope=(
            envelope.model_dump(mode="json")
        ),
        recipe_filename=recipe_path.name,
        approval_filename=approval_path.name,
        settings=settings,
    )

    assert verified == envelope


def test_changed_envelope_is_rejected(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    payload = envelope.model_dump(
        mode="json"
    )
    payload["steps"][1]["arguments"][
        "target_path"
    ] = "changed.gpkg"

    with pytest.raises(
        ApprovedRecipeError,
        match="does not match",
    ):
        validate_approved_recipe_request(
            execution_envelope=payload,
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )


def test_recipe_path_traversal_is_rejected(
    tmp_path: Path,
) -> None:
    (
        _recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    with pytest.raises(
        ApprovedRecipeError,
        match="plain JSON filename",
    ):
        validate_approved_recipe_request(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename="../recipe.json",
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )


def test_writes_disabled_blocks_server(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    blocked = settings.model_copy(
        update={
            "enable_write_tools": False
        }
    )

    with pytest.raises(
        ApprovedRecipeError,
        match="write tools are disabled",
    ):
        run_approved_recipe(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=blocked,
        )

