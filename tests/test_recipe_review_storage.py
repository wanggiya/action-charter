"""Tests for bounded operator-review loading."""

import json
from pathlib import Path

import pytest

from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    RecipeReviewStorageError,
    load_recipe_operator_review,
    review_recipe_request,
)


PROJECT_ROOT = Path(__file__).parents[1]

REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10d2.gpkg."
)


class FakeModelClient:
    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        assert request.json_mode is True

        return ModelResult(
            model="fake-qwen",
            content=json.dumps(
                {
                    "schema_version": "1.0",
                    "original_request": REQUEST,
                    "summary": (
                        "Inspect and convert a vector."
                    ),
                    "recipe_id_hint": (
                        "checkpoint10d2"
                    ),
                    "selection": {
                        "template_id": (
                            "inspect_and_convert_vector"
                        ),
                        "parameters": {
                            "path": (
                                "data/input/"
                                "sample_points.geojson"
                            ),
                            "target_path": (
                                "data/output/"
                                "checkpoint10d2.gpkg"
                            ),
                            "target_format": (
                                "geopackage"
                            ),
                        },
                    },
                }
            ),
        )


def ready_review():
    return review_recipe_request(
        original_request=REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(),
    )


def test_review_round_trip(
    tmp_path: Path,
) -> None:
    review_file = (
        tmp_path / "review.json"
    )
    review_file.write_text(
        ready_review().model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    loaded = load_recipe_operator_review(
        review_file,
        review_root=tmp_path,
    )

    assert loaded == ready_review()


def test_review_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    review_root = tmp_path / "reviews"
    review_root.mkdir()

    outside = tmp_path / "outside.json"
    outside.write_text(
        ready_review().model_dump_json(),
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeReviewStorageError,
        match="escaped",
    ):
        load_recipe_operator_review(
            outside,
            review_root=review_root,
        )


def test_future_review_schema_is_rejected(
    tmp_path: Path,
) -> None:
    review_file = (
        tmp_path / "review.json"
    )

    payload = ready_review().model_dump(
        mode="json"
    )
    payload["schema_version"] = "2.0"

    review_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeReviewStorageError,
        match="schema validation",
    ):
        load_recipe_operator_review(
            review_file,
            review_root=tmp_path,
        )

