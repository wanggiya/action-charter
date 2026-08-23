"""Tests for trusted adapter materialization."""

from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    TrustedAdapterMaterializationError,
    generate_declarative_skill_scaffold,
    load_skill_definition,
    materialize_trusted_adapter_candidate,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.skill_scaffolding import (
    validate_skill_scaffold_contract,
)


PROJECT_ROOT = Path(__file__).parents[1]

def registry_without_candidate():
    """Return a test-only pre-promotion registry."""

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    return registry.model_copy(
        update={
            "skills": [
                skill
                for skill in registry.skills
                if skill.id != "inspect_raster"
            ]
        }
    )

def prepared_candidate(
    tmp_path: Path,
):
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

    registry = registry_without_candidate()

    generated = (
        generate_declarative_skill_scaffold(
            definition,
            registry=registry,
            scaffold_root=(
                tmp_path / "scaffolds"
            ),
        )
    )

    return definition, generated.scaffold


def test_materializes_separate_candidate(
    tmp_path: Path,
) -> None:
    definition, scaffold = prepared_candidate(
        tmp_path
    )

    source_service = (
        Path(scaffold.scaffold_path)
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    original = source_service.read_text(
        encoding="utf-8"
    )

    result = materialize_trusted_adapter_candidate(
        definition=definition,
        scaffold=scaffold,
        candidate_root=tmp_path / "candidates",
    )

    candidate = Path(result.candidate_path)
    candidate_service = (
        candidate
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    assert candidate.is_dir()
    assert "execute_adapter" in (
        candidate_service.read_text(
            encoding="utf-8"
        )
    )

    assert source_service.read_text(
        encoding="utf-8"
    ) == original

    validation = validate_skill_scaffold_contract(
        candidate
    )

    assert validation.passed is True
    assert result.source_scaffold_modified is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_candidate_is_immutable(
    tmp_path: Path,
) -> None:
    definition, scaffold = prepared_candidate(
        tmp_path
    )
    root = tmp_path / "candidates"

    materialize_trusted_adapter_candidate(
        definition=definition,
        scaffold=scaffold,
        candidate_root=root,
    )

    with pytest.raises(
        TrustedAdapterMaterializationError,
        match="already exists",
    ):
        materialize_trusted_adapter_candidate(
            definition=definition,
            scaffold=scaffold,
            candidate_root=root,
        )


def test_changed_placeholder_is_rejected(
    tmp_path: Path,
) -> None:
    definition, scaffold = prepared_candidate(
        tmp_path
    )

    service = (
        Path(scaffold.scaffold_path)
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    service.write_text(
        "def unexpected():\n"
        "    return True\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TrustedAdapterMaterializationError,
        match="placeholder changed",
    ):
        materialize_trusted_adapter_candidate(
            definition=definition,
            scaffold=scaffold,
            candidate_root=(
                tmp_path / "candidates"
            ),
        )

