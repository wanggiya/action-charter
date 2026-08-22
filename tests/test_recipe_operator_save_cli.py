"""CLI tests for explicitly saving reviewed recipes."""

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    review_recipe_request,
)


runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[1]

REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint10d2-cli.gpkg."
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
                        "checkpoint10d2-cli"
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
                                "checkpoint10d2-cli.gpkg"
                            ),
                            "target_format": (
                                "geopackage"
                            ),
                        },
                    },
                }
            ),
        )


def test_ready_review_is_saved_by_cli(
    tmp_path: Path,
) -> None:
    review_root = tmp_path / "reviews"
    recipe_root = tmp_path / "recipes"

    review_root.mkdir()
    recipe_root.mkdir()

    review = review_recipe_request(
        original_request=REQUEST,
        project_root=PROJECT_ROOT,
        agents_root=PROJECT_ROOT / "agents",
        model_client=FakeModelClient(),
    )

    review_file = (
        review_root / "review.json"
    )
    review_file.write_text(
        review.model_dump_json(indent=2),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "save-reviewed-recipe",
            str(review_file),
            "--review-root",
            str(review_root),
            "--recipe-root",
            str(recipe_root),
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    assert result.exit_code == 0, (
        result.output
    )

    payload = json.loads(result.stdout)

    assert payload["recipe_saved"] is True
    assert (
        payload["approval_performed"]
        is False
    )
    assert (
        payload["execution_performed"]
        is False
    )

    saved_path = (
        recipe_root
        / payload["recipe_filename"]
    )

    assert saved_path.is_file()
    assert (
        payload["recipe_sha256"]
        in saved_path.name
    )

