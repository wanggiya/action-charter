"""Tests for immutable skill-contract generation."""

import json
from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    SkillContractGenerationError,
    generate_skill_contract_bundle,
    load_skill_definition,
)
from geoagent_harness.skill_definitions import (
    SkillProfile,
)


PROJECT_ROOT = Path(__file__).parents[1]


def raster_definition():
    root = PROJECT_ROOT / "skill-definitions"

    return load_skill_definition(
        root / "inspect_raster.skill.yaml",
        definition_root=root,
    )


def test_generates_isolated_contract_bundle(
    tmp_path: Path,
) -> None:
    definition = raster_definition()

    result = generate_skill_contract_bundle(
        definition,
        contract_root=tmp_path / "contracts",
    )

    bundle = Path(result.bundle_path)

    assert bundle.is_dir()
    assert Path(result.definition_path).is_file()
    assert Path(result.contract_path).is_file()

    contract = json.loads(
        Path(result.contract_path).read_text(
            encoding="utf-8"
        )
    )

    assert contract["skill_id"] == (
        "inspect_raster"
    )
    assert contract["profile"] == (
        "read_only_inspection"
    )
    assert contract["access"] == "read_only"
    assert contract["approval_required"] is False
    assert contract["validation_required"] is False

    assert "reject_path_escape" in (
        contract["required_checks"]
    )
    assert "filesystem_unchanged" in (
        contract["required_checks"]
    )
    assert "database_unchanged" in (
        contract["required_checks"]
    )

    assert result.implementation_generated is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_contract_bundle_is_immutable(
    tmp_path: Path,
) -> None:
    definition = raster_definition()
    root = tmp_path / "contracts"

    generate_skill_contract_bundle(
        definition,
        contract_root=root,
    )

    with pytest.raises(
        SkillContractGenerationError,
        match="already exists",
    ):
        generate_skill_contract_bundle(
            definition,
            contract_root=root,
        )


def test_incompatible_profile_is_rejected(
    tmp_path: Path,
) -> None:
    definition = raster_definition().model_copy(
        update={
            "profile": SkillProfile.DATABASE_WRITE
        }
    )

    with pytest.raises(
        SkillContractGenerationError,
        match="not ready",
    ):
        generate_skill_contract_bundle(
            definition,
            contract_root=tmp_path,
        )

