"""Tests for isolated skill scaffold generation."""

import json
from pathlib import Path

import pytest
import yaml

from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillKind,
    SkillRegistry,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldGenerationError,
    SkillScaffoldRequest,
    generate_skill_scaffold,
    plan_skill_scaffold,
)


def artifact_write_plan():
    request = SkillScaffoldRequest(
        skill_id="reproject_vector",
        summary="Reproject a vector dataset.",
        kind=SkillKind.TRANSFORMATION,
        access=SkillAccess.ARTIFACT_WRITE,
    )

    return plan_skill_scaffold(
        request,
        registry=SkillRegistry(skills=[]),
    )


def test_generator_creates_isolated_bundle(
    tmp_path: Path,
) -> None:
    result = generate_skill_scaffold(
        artifact_write_plan(),
        scaffold_root=tmp_path / "scaffolds",
    )

    bundle = Path(result.scaffold_path)

    assert bundle.is_dir()

    service = (
        bundle
        / "src"
        / "geoagent_harness"
        / "skills"
        / "reproject_vector"
        / "service.py"
    )
    validation = service.with_name(
        "validation.py"
    )

    assert service.is_file()
    assert validation.is_file()

    assert "not implemented" in (
        service.read_text(
            encoding="utf-8"
        ).lower()
    )

    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False
    assert result.generation_performed is True


def test_registry_fragment_remains_planned(
    tmp_path: Path,
) -> None:
    result = generate_skill_scaffold(
        artifact_write_plan(),
        scaffold_root=tmp_path / "scaffolds",
    )

    fragment_path = (
        Path(result.scaffold_path)
        / result.registry_fragment_path
    )

    payload = yaml.safe_load(
        fragment_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["skill"]["status"] == "planned"
    assert "entrypoint" not in payload["skill"]
    assert "verifier" not in payload["skill"]


def test_manifest_records_no_promotion(
    tmp_path: Path,
) -> None:
    result = generate_skill_scaffold(
        artifact_write_plan(),
        scaffold_root=tmp_path / "scaffolds",
    )

    manifest_path = (
        Path(result.scaffold_path)
        / result.manifest_path
    )

    payload = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_existing_bundle_is_not_overwritten(
    tmp_path: Path,
) -> None:
    root = tmp_path / "scaffolds"

    generate_skill_scaffold(
        artifact_write_plan(),
        scaffold_root=root,
    )

    with pytest.raises(
        SkillScaffoldGenerationError,
        match="already exists",
    ):
        generate_skill_scaffold(
            artifact_write_plan(),
            scaffold_root=root,
        )

