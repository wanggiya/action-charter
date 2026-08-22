"""Tests for shared skill scaffold contracts."""

from pathlib import Path

from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillKind,
    SkillRegistry,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldRequest,
    generate_skill_scaffold,
    plan_skill_scaffold,
    validate_skill_scaffold_contract,
)


def generated_bundle(
    tmp_path: Path,
) -> Path:
    request = SkillScaffoldRequest(
        skill_id="reproject_vector",
        summary="Reproject a vector dataset.",
        kind=SkillKind.TRANSFORMATION,
        access=SkillAccess.ARTIFACT_WRITE,
    )

    plan = plan_skill_scaffold(
        request,
        registry=SkillRegistry(skills=[]),
    )

    result = generate_skill_scaffold(
        plan,
        scaffold_root=tmp_path / "scaffolds",
    )

    return Path(result.scaffold_path)


def test_generated_bundle_passes_contracts(
    tmp_path: Path,
) -> None:
    bundle = generated_bundle(tmp_path)

    result = validate_skill_scaffold_contract(
        bundle
    )

    assert result.passed is True
    assert result.violations == []
    assert result.implementation_trusted is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_missing_generated_file_fails_contract(
    tmp_path: Path,
) -> None:
    bundle = generated_bundle(tmp_path)

    service = (
        bundle
        / "src"
        / "geoagent_harness"
        / "skills"
        / "reproject_vector"
        / "service.py"
    )
    service.unlink()

    result = validate_skill_scaffold_contract(
        bundle
    )

    assert result.passed is False
    assert any(
        "generated file is missing" in violation
        for violation in result.violations
    )


def test_invalid_python_fails_contract(
    tmp_path: Path,
) -> None:
    bundle = generated_bundle(tmp_path)

    service = (
        bundle
        / "src"
        / "geoagent_harness"
        / "skills"
        / "reproject_vector"
        / "service.py"
    )
    service.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    result = validate_skill_scaffold_contract(
        bundle
    )

    assert result.passed is False
    assert any(
        "invalid Python syntax" in violation
        for violation in result.violations
    )


def test_prohibited_subprocess_fails_contract(
    tmp_path: Path,
) -> None:
    bundle = generated_bundle(tmp_path)

    service = (
        bundle
        / "src"
        / "geoagent_harness"
        / "skills"
        / "reproject_vector"
        / "service.py"
    )
    service.write_text(
        "import subprocess\n",
        encoding="utf-8",
    )

    result = validate_skill_scaffold_contract(
        bundle
    )

    assert result.passed is False
    assert any(
        "prohibited import subprocess"
        in violation
        for violation in result.violations
    )


def test_implemented_registry_fragment_fails(
    tmp_path: Path,
) -> None:
    bundle = generated_bundle(tmp_path)

    registry = (
        bundle
        / "registry-fragment.yaml"
    )

    content = registry.read_text(
        encoding="utf-8"
    )
    registry.write_text(
        content.replace(
            "status: planned",
            "status: implemented",
        ),
        encoding="utf-8",
    )

    result = validate_skill_scaffold_contract(
        bundle
    )

    assert result.passed is False
    assert any(
        (
            "registry fragment failed schema validation"
            in violation
            or "must remain planned" in violation
        )
        for violation in result.violations
    )

