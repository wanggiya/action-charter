"""Regression coverage for the versioned CLI/interface parity proposal."""

import json
from pathlib import Path

from geoagent_harness.recipe_proposals import (
    RecipeProposal,
    compile_recipe_proposal,
)
from geoagent_harness.skill_registry import load_skill_registry


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURE = (
    PROJECT_ROOT
    / "examples"
    / "interface-parity"
    / "checkpoint17l-vector-conversion-proposal.json"
)


def test_checkpoint17l_parity_fixture_compiles_without_authority() -> None:
    proposal = RecipeProposal.model_validate(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )

    result = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(PROJECT_ROOT),
    )

    assert [step.skill_id for step in result.recipe.steps] == [
        "inspect_vector",
        "convert_vector",
    ]
    assert result.recipe_validation.valid is True
    assert result.recipe_validation.approval_required_step_ids == [
        "step_2"
    ]
    assert result.recipe_validation.validation_required_step_ids == [
        "step_2"
    ]
    assert result.compilation_performed is True
    assert result.recipe_saved is False
    assert result.approval_performed is False
    assert result.execution_performed is False
