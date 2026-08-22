"""Tests for deterministic skill scaffold planning."""

import pytest

from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillDefinition,
    SkillKind,
    SkillRegistry,
    SkillStatus,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldPolicyError,
    SkillScaffoldRequest,
    plan_skill_scaffold,
)


def empty_registry() -> SkillRegistry:
    return SkillRegistry(skills=[])


def test_artifact_write_scaffold_requires_controls() -> None:
    request = SkillScaffoldRequest(
        skill_id="reproject_vector",
        summary="Reproject a vector dataset.",
        kind=SkillKind.TRANSFORMATION,
        access=SkillAccess.ARTIFACT_WRITE,
    )

    plan = plan_skill_scaffold(
        request,
        registry=empty_registry(),
    )

    assert plan.approval_required is True
    assert plan.validation_required is True
    assert plan.registry_entry.status == (
        SkillStatus.PLANNED
    )
    assert plan.registry_entry.entrypoint is None
    assert plan.registry_entry.verifier is None

    assert (
        "src/geoagent_harness/skills/"
        "reproject_vector/validation.py"
        in plan.files
    )

    assert plan.generation_performed is False
    assert plan.registry_modified is False
    assert plan.implementation_trusted is False
    assert plan.execution_performed is False


def test_read_only_scaffold_has_no_write_controls() -> None:
    request = SkillScaffoldRequest(
        skill_id="inspect_raster",
        summary="Inspect an approved raster dataset.",
        kind=SkillKind.INSPECTION,
        access=SkillAccess.READ_ONLY,
    )

    plan = plan_skill_scaffold(
        request,
        registry=empty_registry(),
    )

    assert plan.approval_required is False
    assert plan.validation_required is False

    assert not any(
        path.endswith("/validation.py")
        for path in plan.files
    )


def test_existing_skill_is_rejected() -> None:
    registry = SkillRegistry(
        skills=[
            SkillDefinition(
                id="inspect_vector",
                status=SkillStatus.PLANNED,
            )
        ]
    )

    request = SkillScaffoldRequest(
        skill_id="inspect_vector",
        summary="Duplicate skill.",
        kind=SkillKind.INSPECTION,
        access=SkillAccess.READ_ONLY,
    )

    with pytest.raises(
        SkillScaffoldPolicyError,
        match="already registered",
    ):
        plan_skill_scaffold(
            request,
            registry=registry,
        )


def test_validation_write_skill_is_rejected() -> None:
    request = SkillScaffoldRequest(
        skill_id="validate_raster",
        summary="Validate a raster.",
        kind=SkillKind.VALIDATION,
        access=SkillAccess.ARTIFACT_WRITE,
    )

    with pytest.raises(
        SkillScaffoldPolicyError,
        match="validation skills must be read-only",
    ):
        plan_skill_scaffold(
            request,
            registry=empty_registry(),
        )


def test_non_reporting_evidence_write_is_rejected() -> None:
    request = SkillScaffoldRequest(
        skill_id="inspect_to_file",
        summary="Invalid evidence writer.",
        kind=SkillKind.INSPECTION,
        access=SkillAccess.EVIDENCE_WRITE,
    )

    with pytest.raises(
        SkillScaffoldPolicyError,
        match="must be reporting",
    ):
        plan_skill_scaffold(
            request,
            registry=empty_registry(),
        )

