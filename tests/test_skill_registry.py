"""Tests for the reusable typed skill registry."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from geoagent_harness.skill_registry import (
    SkillRegistry,
    SkillRegistryError,
    load_skill_registry,
    parse_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]

def implemented_skill(
    *,
    skill_id: str = "example_skill",
    entrypoint: str = "example.skill:run",
    verifier: str | None = None,
    access: str = "read_only",
    kind: str = "inspection",
    approval_required: bool = False,
    validation_required: bool = False,
) -> dict[str, object]:
    """Return one complete implemented-skill payload."""
    payload: dict[str, object] = {
        "id": skill_id,
        "version": "0.1.0",
        "status": "implemented",
        "kind": kind,
        "access": access,
        "approval_required": approval_required,
        "validation_required": validation_required,
        "entrypoint": entrypoint,
    }

    if verifier is not None:
        payload["verifier"] = verifier

    return payload


def test_loads_project_skill_registry() -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    implemented = {
        skill.id
        for skill in registry.implemented_skills()
    }

    assert "inspect_vector" in implemented
    assert "convert_vector" in implemented
    assert "load_vector_to_postgis" in implemented
    assert "validate_postgis_layer" in implemented
    assert "generate_report" in implemented


def test_conversion_skill_declares_verifier() -> None:
    registry = load_skill_registry(
        PROJECT_ROOT
    )

    skill = registry.get_skill(
        "convert_vector"
    )

    assert skill.verifier == (
        "geoagent_harness.skills.convert_vector."
        "validation:validate_vector_conversion"
    )


def test_duplicate_skill_ids_are_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="duplicate IDs",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [
                    implemented_skill(
                        skill_id="inspect_vector"
                    ),
                    implemented_skill(
                        skill_id="inspect_vector"
                    ),
                ],
            }
        )

def test_implemented_skill_requires_entrypoint() -> None:
    skill = implemented_skill()
    skill.pop("entrypoint")

    with pytest.raises(
        ValidationError,
        match="missing metadata: entrypoint",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [skill],
            }
        )


def test_invalid_entrypoint_is_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="package.module:function",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [
                    implemented_skill(
                        entrypoint="invalid entrypoint"
                    )
                ],
            }
        )


def test_missing_registry_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        SkillRegistryError,
        match="does not exist",
    ):
        load_skill_registry(tmp_path)


def test_malformed_registry_is_rejected(
    tmp_path: Path,
) -> None:
    context_root = tmp_path / "context"
    context_root.mkdir()

    path = context_root / "SKILLS_INDEX.yaml"

    path.write_text(
        "skills: [invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillRegistryError,
        match="not valid YAML",
    ):
        load_skill_registry(tmp_path)


def test_extra_registry_fields_are_rejected(
    tmp_path: Path,
) -> None:
    context_root = tmp_path / "context"
    context_root.mkdir()

    path = context_root / "SKILLS_INDEX.yaml"

    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "unexpected": True,
                "skills": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        SkillRegistryError,
        match="schema validation",
    ):
        load_skill_registry(tmp_path)

def test_parse_registry_from_trusted_text() -> None:
    registry = parse_skill_registry(
        """
schema_version: "1.0"
skills:
  - id: example_skill
    version: "0.1.0"
    status: implemented
    kind: transformation
    access: artifact_write
    approval_required: true
    validation_required: true
    entrypoint: example.skill:run
    verifier: example.skill:validate
"""
    )

    skill = registry.get_skill(
        "example_skill"
    )

    assert skill.approval_required is True
    assert skill.validation_required is True

def test_parse_registry_rejects_non_object() -> None:
    with pytest.raises(
        SkillRegistryError,
        match="must be an object",
    ):
        parse_skill_registry(
            "- one\n- two\n"
        )


def test_parse_registry_rejects_unknown_field() -> None:
    with pytest.raises(
        SkillRegistryError,
        match="schema validation",
    ):
        parse_skill_registry(
            """
schema_version: "1.0"
unexpected: true
skills: []
"""
        )


def test_database_write_requires_approval() -> None:
    skill = implemented_skill(
        kind="database_load",
        access="database_write",
        approval_required=False,
        validation_required=True,
        verifier="example.skill:validate",
    )

    with pytest.raises(
        ValidationError,
        match="require approval",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [skill],
            }
        )


def test_database_write_requires_validation() -> None:
    skill = implemented_skill(
        kind="database_load",
        access="database_write",
        approval_required=True,
        validation_required=False,
        verifier="example.skill:validate",
    )

    with pytest.raises(
        ValidationError,
        match="require deterministic validation",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [skill],
            }
        )


def test_validated_write_requires_verifier() -> None:
    skill = implemented_skill(
        kind="transformation",
        access="artifact_write",
        approval_required=True,
        validation_required=True,
    )

    with pytest.raises(
        ValidationError,
        match="require a verifier",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [skill],
            }
        )


def test_read_only_skill_rejects_write_approval() -> None:
    skill = implemented_skill(
        access="read_only",
        approval_required=True,
    )

    with pytest.raises(
        ValidationError,
        match="cannot require write approval",
    ):
        SkillRegistry.model_validate(
            {
                "schema_version": "1.0",
                "skills": [skill],
            }
        )


def test_reporting_skill_may_write_evidence() -> None:
    registry = SkillRegistry.model_validate(
        {
            "schema_version": "1.0",
            "skills": [
                implemented_skill(
                    kind="reporting",
                    access="evidence_write",
                    approval_required=False,
                    validation_required=False,
                    entrypoint="example.report:write",
                )
            ],
        }
    )

    skill = registry.get_skill(
        "example_skill"
    )

    assert skill.access.value == "evidence_write"

