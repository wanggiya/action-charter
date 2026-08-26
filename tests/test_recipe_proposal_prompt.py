"""Tests for the proposal-only model prompt."""

from geoagent_harness.recipe_proposals import (
    build_recipe_proposal_request,
)


def test_prompt_requires_json_and_no_execution() -> None:
    request = build_recipe_proposal_request(
        "Convert sample.geojson to output.gpkg."
    )

    assert request.temperature == 0.0
    assert request.json_mode is True
    assert len(request.messages) == 2

    system = request.messages[0].content

    assert "Return exactly one JSON object" in system
    assert "inspect_vector" in system
    assert "inspect_and_convert_vector" in system
    assert "vector_to_postgis" in system

    assert (
        '"execution_performed": false'
        in system
    )
    assert "must not invent" in system.lower()


def test_empty_request_is_rejected() -> None:
    try:
        build_recipe_proposal_request("   ")
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError(
            "empty request was accepted"
        )

def test_prompt_is_generated_from_catalog() -> None:
    request = build_recipe_proposal_request(
        "Inspect and convert a raster."
    )

    system = request.messages[0].content

    assert (
        "inspect_and_convert_raster"
        in system
    )
    assert '"target_crs"' in system
    assert '"resampling"' in system
    assert '"nearest"' in system
    assert '"bilinear"' in system
    assert '"cubic"' in system
