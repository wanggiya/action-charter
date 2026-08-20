"""Tests for proposal runtime dependency injection."""

from pathlib import Path

from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    propose_recipe_with_shared_model,
)


PROJECT_ROOT = Path(__file__).parents[1]

REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint9f.gpkg."
)


class FakeModelClient:
    def __init__(self) -> None:
        self.request: ModelRequest | None = None

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        self.request = request

        return ModelResult(
            model="fake-qwen",
            finish_reason="stop",
            content=f"""
{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "{REQUEST}",
  "summary": "Inspect and convert the vector dataset.",
  "recipe_id_hint": "checkpoint9f",
  "selection": {{
    "template_id": "inspect_and_convert_vector",
    "parameters": {{
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint9f.gpkg",
      "target_layer": null,
      "target_format": "geopackage"
    }}
  }},
  "assumptions": [],
  "missing_information": [],
  "warnings": [],
  "compilation_performed": false,
  "execution_requested": false,
  "approval_performed": false,
  "execution_performed": false
}}
""".strip(),
        )


def test_runtime_uses_injected_model_client() -> None:
    client = FakeModelClient()

    result = propose_recipe_with_shared_model(
        original_request=REQUEST,
        agents_root=PROJECT_ROOT / "agents",
        model_client=client,
    )

    assert result.model == "fake-qwen"
    assert result.proposal.recipe_id_hint == (
        "checkpoint9f"
    )
    assert result.execution_performed is False

    assert client.request is not None
    assert client.request.json_mode is True

