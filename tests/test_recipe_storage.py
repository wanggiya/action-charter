"""Tests for immutable reusable-recipe storage."""

from pathlib import Path
import json

import pytest

from geoagent_harness.recipes import (
    RecipeStorageError,
    WorkflowRecipe,
    load_recipe,
    load_recipe_draft,
    recipe_sha256,
    save_recipe,
)


def make_recipe(
    *,
    request: str = "Convert sample points.",
) -> WorkflowRecipe:
    return WorkflowRecipe.model_validate(
        {
            "recipe_id": "convert-sample-points",
            "summary": "Convert sample points.",
            "original_request": request,
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
                            "sample_points.gpkg"
                        ),
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )


def test_recipe_round_trip(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()

    stored, path = save_recipe(
        recipe,
        recipe_root=tmp_path,
    )

    loaded = load_recipe(
        path,
        recipe_root=tmp_path,
    )

    assert loaded == stored
    assert recipe_sha256(loaded) in path.name


def test_recipe_overwrite_is_blocked(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()

    save_recipe(
        recipe,
        recipe_root=tmp_path,
    )

    with pytest.raises(
        RecipeStorageError,
        match="overwriting is blocked",
    ):
        save_recipe(
            recipe,
            recipe_root=tmp_path,
        )


def test_recipe_is_secret_redacted(
    tmp_path: Path,
) -> None:
    recipe = make_recipe(
        request=(
            "Convert data with "
            "POSTGRES_PASSWORD=do-not-expose"
        )
    )

    stored, path = save_recipe(
        recipe,
        recipe_root=tmp_path,
    )

    content = path.read_text(
        encoding="utf-8"
    )

    assert "do-not-expose" not in content
    assert "[REDACTED]" in content
    assert "do-not-expose" not in (
        stored.original_request
    )


def test_tampered_recipe_is_rejected(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()

    _, path = save_recipe(
        recipe,
        recipe_root=tmp_path,
    )

    content = path.read_text(
        encoding="utf-8"
    )
    path.write_text(
        content.replace(
            "Convert sample points.",
            "Changed after persistence.",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeStorageError,
        match="canonical identity",
    ):
        load_recipe(
            path,
            recipe_root=tmp_path,
        )


def test_recipe_outside_root_is_rejected(
    tmp_path: Path,
) -> None:
    recipe_root = tmp_path / "recipes"
    outside = tmp_path / "outside.json"

    recipe_root.mkdir()
    outside.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeStorageError,
        match="escaped",
    ):
        load_recipe(
            outside,
            recipe_root=recipe_root,
        )


def test_missing_recipe_is_rejected(
    tmp_path: Path,
) -> None:
    recipe_root = tmp_path / "recipes"
    recipe_root.mkdir()

    with pytest.raises(
        RecipeStorageError,
        match="does not exist",
    ):
        load_recipe(
            recipe_root / "missing.json",
            recipe_root=recipe_root,
        )
        
def test_load_recipe_draft(
    tmp_path: Path,
) -> None:
    recipe = make_recipe()
    path = tmp_path / "draft.json"

    path.write_text(
        json.dumps(
            recipe.model_dump(mode="json")
        ),
        encoding="utf-8",
    )

    loaded = load_recipe_draft(path)

    assert loaded == recipe
