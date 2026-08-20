"""Tests for bounded recipe-proposal loading."""

import json
from pathlib import Path

import pytest

from geoagent_harness.recipe_proposals import (
    RecipeProposalStorageError,
    load_recipe_proposal,
)


def valid_payload() -> dict:
    return {
        "schema_version": "1.0",
        "original_request": (
            "Convert sample points."
        ),
        "summary": (
            "Inspect and convert sample points."
        ),
        "recipe_id_hint": (
            "checkpoint9d-conversion"
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
                    "checkpoint9d.gpkg"
                ),
                "target_format": "geopackage",
            },
        },
    }


def write_payload(
    path: Path,
    payload: dict,
) -> None:
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_valid_proposal_is_loaded(
    tmp_path: Path,
) -> None:
    proposal_file = (
        tmp_path / "proposal.json"
    )
    write_payload(
        proposal_file,
        valid_payload(),
    )

    proposal = load_recipe_proposal(
        proposal_file,
        proposal_root=tmp_path,
    )

    assert proposal.recipe_id_hint == (
        "checkpoint9d-conversion"
    )
    assert (
        proposal.selection.template_id
        == "inspect_and_convert_vector"
    )


def test_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    proposal_root = tmp_path / "approved"
    proposal_root.mkdir()

    outside = tmp_path / "outside.json"
    write_payload(
        outside,
        valid_payload(),
    )

    with pytest.raises(
        RecipeProposalStorageError,
        match="escaped",
    ):
        load_recipe_proposal(
            outside,
            proposal_root=proposal_root,
        )


def test_future_schema_is_rejected(
    tmp_path: Path,
) -> None:
    proposal_file = (
        tmp_path / "proposal.json"
    )

    payload = valid_payload()
    payload["schema_version"] = "2.0"

    write_payload(
        proposal_file,
        payload,
    )

    with pytest.raises(
        RecipeProposalStorageError,
        match="schema validation",
    ):
        load_recipe_proposal(
            proposal_file,
            proposal_root=tmp_path,
        )


def test_unknown_fields_are_rejected(
    tmp_path: Path,
) -> None:
    proposal_file = (
        tmp_path / "proposal.json"
    )

    payload = valid_payload()
    payload["shell_command"] = "rm -rf /"

    write_payload(
        proposal_file,
        payload,
    )

    with pytest.raises(
        RecipeProposalStorageError,
        match="schema validation",
    ):
        load_recipe_proposal(
            proposal_file,
            proposal_root=tmp_path,
        )

