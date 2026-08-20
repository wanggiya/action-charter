"""Offline tests for model-produced recipe proposals."""

from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals import (
    RecipeProposalAgentError,
    generate_recipe_proposal,
)


PROJECT_ROOT = Path(__file__).parents[1]
PLANNER_MANIFEST = load_agent_manifest(
    "planner",
    PROJECT_ROOT / "agents",
)

REQUEST = (
    "Convert data/input/sample_points.geojson "
    "to data/output/checkpoint9e.gpkg."
)


class FakeModelClient:
    def __init__(
        self,
        content: str,
    ) -> None:
        self.content = content
        self.request: ModelRequest | None = None

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        self.request = request

        return ModelResult(
            model="fake-qwen",
            content=self.content,
            finish_reason="stop",
        )


def valid_content() -> str:
    return """
{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "Convert data/input/sample_points.geojson to data/output/checkpoint9e.gpkg.",
  "summary": "Inspect and convert the vector dataset.",
  "recipe_id_hint": "checkpoint9e",
  "selection": {
    "template_id": "inspect_and_convert_vector",
    "parameters": {
      "path": "data/input/sample_points.geojson",
      "source_layer": null,
      "target_path": "data/output/checkpoint9e.gpkg",
      "target_layer": null,
      "target_format": "geopackage"
    }
  },
  "assumptions": [],
  "missing_information": [],
  "warnings": [],
  "compilation_performed": false,
  "execution_requested": false,
  "approval_performed": false,
  "execution_performed": false
}
""".strip()


def test_valid_model_proposal_is_accepted() -> None:
    client = FakeModelClient(
        valid_content()
    )

    result = generate_recipe_proposal(
        original_request=REQUEST,
        manifest=PLANNER_MANIFEST,
        model_client=client,
    )

    assert result.model == "fake-qwen"
    assert (
        result.proposal.selection.template_id
        == "inspect_and_convert_vector"
    )
    assert result.proposal_schema_validated is True

    assert result.assessment_performed is False
    assert result.compilation_performed is False
    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False

    assert client.request is not None
    assert client.request.json_mode is True


def test_invalid_json_is_rejected() -> None:
    client = FakeModelClient(
        "This is not JSON."
    )

    with pytest.raises(
        RecipeProposalAgentError,
        match="invalid JSON",
    ):
        generate_recipe_proposal(
            original_request=REQUEST,
            manifest=PLANNER_MANIFEST,
            model_client=client,
        )


def test_unknown_template_is_rejected() -> None:
    content = valid_content().replace(
        "inspect_and_convert_vector",
        "arbitrary_shell",
    )

    with pytest.raises(
        RecipeProposalAgentError,
        match="invalid proposal schema",
    ):
        generate_recipe_proposal(
            original_request=REQUEST,
            manifest=PLANNER_MANIFEST,
            model_client=FakeModelClient(
                content
            ),
        )


def test_execution_claim_is_rejected() -> None:
    content = valid_content().replace(
        '"execution_performed": false',
        '"execution_performed": true',
    )

    with pytest.raises(
        RecipeProposalAgentError,
        match="invalid proposal schema",
    ):
        generate_recipe_proposal(
            original_request=REQUEST,
            manifest=PLANNER_MANIFEST,
            model_client=FakeModelClient(
                content
            ),
        )


def test_shell_field_is_rejected() -> None:
    content = valid_content().replace(
        '"warnings": [],',
        (
            '"warnings": [], '
            '"shell_command": "rm -rf /",'
        ),
    )

    with pytest.raises(
        RecipeProposalAgentError,
        match="invalid proposal schema",
    ):
        generate_recipe_proposal(
            original_request=REQUEST,
            manifest=PLANNER_MANIFEST,
            model_client=FakeModelClient(
                content
            ),
        )


def test_changed_original_request_is_rejected() -> None:
    content = valid_content().replace(
        REQUEST,
        "Perform a different operation.",
    )

    with pytest.raises(
        RecipeProposalAgentError,
        match="changed the original",
    ):
        generate_recipe_proposal(
            original_request=REQUEST,
            manifest=PLANNER_MANIFEST,
            model_client=FakeModelClient(
                content
            ),
        )

