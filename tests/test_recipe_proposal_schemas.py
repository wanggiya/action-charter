"""Tests for non-executable recipe proposals."""

import pytest
from pydantic import ValidationError

from geoagent_harness.recipe_proposals import (
    RecipeProposal,
)


def conversion_payload() -> dict:
    return {
        "schema_version": "1.0",
        "status": "proposed_not_compiled",
        "original_request": (
            "Convert sample points to GeoPackage."
        ),
        "summary": (
            "Inspect and convert one vector dataset."
        ),
        "recipe_id_hint": "sample_conversion",
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
                    "sample_points.gpkg"
                ),
                "target_layer": "sample_points",
                "target_format": "geopackage",
            },
        },
        "assumptions": [],
        "missing_information": [],
        "warnings": [],
        "compilation_performed": False,
        "execution_requested": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def test_conversion_proposal_is_typed() -> None:
    proposal = RecipeProposal.model_validate(
        conversion_payload()
    )

    assert (
        proposal.selection.template_id
        == "inspect_and_convert_vector"
    )
    assert (
        proposal.selection.parameters.target_format
        == "geopackage"
    )

    assert proposal.compilation_performed is False
    assert proposal.execution_requested is False
    assert proposal.approval_performed is False
    assert proposal.execution_performed is False


def test_incomplete_proposal_can_request_clarification() -> None:
    payload = conversion_payload()

    payload["selection"]["parameters"][
        "target_path"
    ] = None
    payload["missing_information"] = [
        "A target output path is required."
    ]

    proposal = RecipeProposal.model_validate(
        payload
    )

    assert (
        proposal.selection.parameters.target_path
        is None
    )
    assert proposal.missing_information


def test_unknown_template_is_rejected() -> None:
    payload = conversion_payload()

    payload["selection"]["template_id"] = (
        "run_arbitrary_shell"
    )

    with pytest.raises(
        ValidationError,
        match="union_tag_invalid",
    ):
        RecipeProposal.model_validate(payload)


def test_arbitrary_parameters_are_rejected() -> None:
    payload = conversion_payload()

    payload["selection"]["parameters"][
        "shell_command"
    ] = "rm -rf /"

    with pytest.raises(
        ValidationError,
        match="extra_forbidden",
    ):
        RecipeProposal.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    [
        "compilation_performed",
        "execution_requested",
        "approval_performed",
        "execution_performed",
    ],
)
def test_model_cannot_claim_actions(
    field: str,
) -> None:
    payload = conversion_payload()
    payload[field] = True

    with pytest.raises(ValidationError):
        RecipeProposal.model_validate(payload)


def test_postgis_identifiers_are_conservative() -> None:
    payload = conversion_payload()

    payload["selection"] = {
        "template_id": "vector_to_postgis",
        "parameters": {
            "path": (
                "data/input/"
                "sample_points.geojson"
            ),
            "target_schema": "agent_sandbox",
            "target_table": "sample_points",
        },
    }

    proposal = RecipeProposal.model_validate(
        payload
    )

    assert (
        proposal.selection.parameters.target_schema
        == "agent_sandbox"
    )


def test_unsafe_postgis_identifier_is_rejected() -> None:
    payload = conversion_payload()

    payload["selection"] = {
        "template_id": "vector_to_postgis",
        "parameters": {
            "path": (
                "data/input/"
                "sample_points.geojson"
            ),
            "target_schema": "public; DROP SCHEMA",
            "target_table": "sample_points",
        },
    }

    with pytest.raises(ValidationError):
        RecipeProposal.model_validate(payload)

