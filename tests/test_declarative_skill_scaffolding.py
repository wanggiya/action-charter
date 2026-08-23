"""Tests for declarative-to-scaffold compilation."""

from pathlib import Path

import pytest

from geoagent_harness.skill_definitions import (
    DeclarativeSkillScaffoldError,
    SkillProfile,
    compile_declarative_skill_scaffold,
    generate_declarative_skill_scaffold,
    load_skill_definition,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillKind,
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


def trusted_inputs():
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

    return definition, registry


def test_compiles_into_existing_scaffold_plan(
) -> None:
    definition, registry = trusted_inputs()

    result = compile_declarative_skill_scaffold(
        definition,
        registry=registry,
    )

    plan = result.scaffold_plan

    assert plan.skill_id == "inspect_raster"
    assert plan.kind == SkillKind.INSPECTION
    assert plan.access == SkillAccess.READ_ONLY
    assert plan.approval_required is False
    assert plan.validation_required is False

    assert (
        result.definition_sha256
        == result.contract.definition_sha256
    )
    assert result.compilation_performed is True
    assert result.generation_performed is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.execution_performed is False


def test_generates_through_existing_scaffold_system(
    tmp_path: Path,
) -> None:
    definition, registry = trusted_inputs()

    result = generate_declarative_skill_scaffold(
        definition,
        registry=registry,
        scaffold_root=tmp_path / "scaffolds",
    )

    bundle = Path(
        result.scaffold.scaffold_path
    )

    assert bundle.is_dir()

    contract = validate_skill_scaffold_contract(
        bundle
    )

    assert contract.passed is True
    assert result.generation_performed is True
    assert result.scaffold.registry_modified is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_incompatible_profile_cannot_compile(
) -> None:
    definition, registry = trusted_inputs()

    incompatible = definition.model_copy(
        update={
            "profile": SkillProfile.DATABASE_WRITE
        }
    )

    with pytest.raises(
        DeclarativeSkillScaffoldError,
        match="could not be compiled",
    ):
        compile_declarative_skill_scaffold(
            incompatible,
            registry=registry,
        )

