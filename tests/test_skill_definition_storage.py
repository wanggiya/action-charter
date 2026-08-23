"""Tests for declarative skill-definition storage."""

from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    SkillDefinitionStorageError,
    assess_declarative_skill,
    load_skill_definition,
)


PROJECT_ROOT = Path(__file__).parents[1]


def test_loads_canonical_raster_definition() -> None:
    root = PROJECT_ROOT / "skill-definitions"

    definition = load_skill_definition(
        root / "inspect_raster.skill.yaml",
        definition_root=root,
    )

    assert definition.skill_id == "inspect_raster"
    assert definition.adapter_id == (
        "raster_inspection"
    )
    assert definition.execution_requested is False

    assessment = assess_declarative_skill(
        definition
    )

    assert assessment.adapter_available is True
    assert assessment.ready_for_generation is True
    assert assessment.execution_performed is False


def test_definition_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "definitions"
    root.mkdir()

    outside = tmp_path / "outside.skill.yaml"
    outside.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillDefinitionStorageError,
        match="escaped",
    ):
        load_skill_definition(
            outside,
            definition_root=root,
        )


def test_noncanonical_filename_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "definitions"
    root.mkdir()

    path = root / "wrong.skill.yaml"
    path.write_text(
        (
            'schema_version: "1.0"\n'
            "skill_id: inspect_raster\n"
            'version: "0.1.0"\n'
            "summary: Inspect a raster.\n"
            "profile: read_only_inspection\n"
            "adapter_id: raster_inspection\n"
            "arguments_schema_id: "
            "inspect_raster_arguments\n"
            "result_schema_id: "
            "inspect_raster_result\n"
            "fixture_path: sample.tif\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        SkillDefinitionStorageError,
        match="filename does not match",
    ):
        load_skill_definition(
            path,
            definition_root=root,
        )

