"""Tests for explicit reviewed-recipe storage."""

from pathlib import Path

import pytest

from geoagent_harness.recipe_proposals import (
    RecipeOperatorSaveError,
    review_recipe_request,
    save_reviewed_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)


PROJECT_ROOT = Path(__file__).parents[1]

READY_REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10d.gpkg."
)

INCOMPLETE_REQUEST = (
    "Convert my vector dataset."
)


class FakeModelClient:
    def __init__(
        self,
        content: str,
    ) -> None:
        self.content = content

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        assert request.json_mode is True

        return ModelResult(
            model="fake-qwen",
            content=self.content,
        )


def proposal_content(
    *,
    request: str,
    path: str | None,
    target_path: str | None,
    missing_information: list[str],
) -> str:
    import json

    return json.dumps(
        {
            "schema_version": "1.0",
            "original_request": request,
            "summary": "Convert a vector dataset.",
            "recipe_id_hint": "checkpoint10d",
            "selection": {
                "template_id": (
                    "inspect_and_convert_vector"
                ),
                "parameters": {
                    "path": path,
                    "source_layer": None,
                    "target_path": target_path,
                    "target_layer": None,
                    "target_format": (
                        "geopackage"
                        if target_path is not None
                        else None
                    ),
                },
            },
            "missing_information": (
                missing_information
            ),
        }
    )


def ready_review():
    return review_recipe_request(
        original_request=READY_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            proposal_content(
                request=READY_REQUEST,
                path=(
                    "data/input/"
                    "sample_points.geojson"
                ),
                target_path=(
                    "data/output/"
                    "checkpoint10d.gpkg"
                ),
                missing_information=[],
            )
        ),
    )


def incomplete_review():
    return review_recipe_request(
        original_request=INCOMPLETE_REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(
            proposal_content(
                request=INCOMPLETE_REQUEST,
                path=None,
                target_path=None,
                missing_information=[
                    "Input and output paths are required."
                ],
            )
        ),
    )


def test_ready_review_is_saved_immutably(
    tmp_path: Path,
) -> None:
    result = save_reviewed_recipe(
        review=ready_review(),
        registry=load_skill_registry(
            PROJECT_ROOT
        ),
        recipe_root=tmp_path,
    )

    assert result.recipe_saved is True
    assert result.approval_performed is False
    assert result.execution_performed is False

    saved = tmp_path / result.recipe_filename

    assert saved.is_file()
    assert result.recipe_sha256 in saved.name


def test_clarification_review_cannot_be_saved(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RecipeOperatorSaveError,
        match="only a ready",
    ):
        save_reviewed_recipe(
            review=incomplete_review(),
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            recipe_root=tmp_path,
        )


def test_changed_compilation_is_rejected(
    tmp_path: Path,
) -> None:
    review = ready_review()

    assert review.compilation is not None

    changed_recipe = (
        review.compilation.recipe.model_copy(
            update={
                "summary": "Changed after review."
            }
        )
    )

    review.compilation = (
        review.compilation.model_copy(
            update={
                "recipe": changed_recipe
            }
        )
    )

    with pytest.raises(
        RecipeOperatorSaveError,
        match="does not match",
    ):
        save_reviewed_recipe(
            review=review,
            registry=load_skill_registry(
                PROJECT_ROOT
            ),
            recipe_root=tmp_path,
        )

