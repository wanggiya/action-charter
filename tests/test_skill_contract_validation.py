"""Tests for static skill-contract validation."""

import json
from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    SkillContractValidationError,
    generate_skill_contract_bundle,
    load_skill_definition,
    validate_skill_contract_bundle,
)


PROJECT_ROOT = Path(__file__).parents[1]


def generated_bundle(
    tmp_path: Path,
) -> tuple[Path, Path]:
    definition_root = (
        PROJECT_ROOT / "skill-definitions"
    )

    definition = load_skill_definition(
        (
            definition_root
            / "inspect_raster.skill.yaml"
        ),
        definition_root=definition_root,
    )

    contract_root = tmp_path / "contracts"

    generated = generate_skill_contract_bundle(
        definition,
        contract_root=contract_root,
    )

    return (
        Path(generated.bundle_path),
        contract_root,
    )


def test_validates_generated_contract_without_execution(
    tmp_path: Path,
) -> None:
    bundle, root = generated_bundle(tmp_path)

    result = validate_skill_contract_bundle(
        bundle,
        contract_root=root,
    )

    assert result.passed is True
    assert result.implementation_imported is False
    assert result.implementation_executed is False
    assert result.registry_modified is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_changed_contract_is_rejected(
    tmp_path: Path,
) -> None:
    bundle, root = generated_bundle(tmp_path)

    contract_path = bundle / "contract.json"

    payload = json.loads(
        contract_path.read_text(
            encoding="utf-8"
        )
    )
    payload["access"] = "database_write"

    contract_path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillContractValidationError,
        match="does not match",
    ):
        validate_skill_contract_bundle(
            bundle,
            contract_root=root,
        )


def test_unexpected_file_is_rejected(
    tmp_path: Path,
) -> None:
    bundle, root = generated_bundle(tmp_path)

    (bundle / "service.py").write_text(
        "raise RuntimeError('must not execute')\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillContractValidationError,
        match="unexpected file set",
    ):
        validate_skill_contract_bundle(
            bundle,
            contract_root=root,
        )


def test_bundle_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    approved_root = tmp_path / "approved"
    approved_root.mkdir()

    outside = tmp_path / "outside.contract"
    outside.mkdir()

    with pytest.raises(
        SkillContractValidationError,
        match="escaped",
    ):
        validate_skill_contract_bundle(
            outside,
            contract_root=approved_root,
        )

