import json
from pathlib import Path

import pytest

from geoagent_harness.context_pack import (
    ContextPackError,
    build_context_pack,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_builds_context_pack_from_trusted_files() -> None:
    pack = build_context_pack(
        (
            "Inspect sample_points and load it into PostGIS, "
            "then validate and report."
        ),
        PROJECT_ROOT,
    )

    assert pack.schema_version == "1.0"
    assert pack.datasets[0].id == "sample_points"

    skill_ids = {
        skill.id
        for skill in pack.available_skills
    }

    assert "inspect_vector" in skill_ids
    assert "load_vector_to_postgis" in skill_ids
    assert "validate_postgis_layer" in skill_ids
    assert "generate_report" in skill_ids
    assert "convert_vector" not in skill_ids

    assert len(pack.context_references) == 6
    assert all(
        len(reference.sha256) == 64
        for reference in pack.context_references
    )


def test_context_pack_redacts_request_secrets() -> None:
    pack = build_context_pack(
        (
            "Load the data with "
            "password=do-not-send-this"
        ),
        PROJECT_ROOT,
    )

    serialized = json.dumps(
        pack.model_dump(mode="json")
    )

    assert "do-not-send-this" not in serialized
    assert "[REDACTED]" in serialized


def test_empty_request_is_rejected() -> None:
    with pytest.raises(
        ContextPackError,
        match="cannot be empty",
    ):
        build_context_pack(
            "   ",
            PROJECT_ROOT,
        )


def test_request_size_is_bounded() -> None:
    with pytest.raises(
        ContextPackError,
        match="8000",
    ):
        build_context_pack(
            "x" * 8001,
            PROJECT_ROOT,
        )


def test_context_references_do_not_contain_file_contents() -> None:
    pack = build_context_pack(
        "Inspect the sample dataset.",
        PROJECT_ROOT,
    )

    for reference in pack.context_references:
        assert reference.path.startswith("context/")
        assert "Project Summary" not in reference.path