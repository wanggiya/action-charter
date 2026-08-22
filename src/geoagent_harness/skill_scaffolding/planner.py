"""Deterministic planning for GIS skill scaffolds."""

from __future__ import annotations

from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillDefinition,
    SkillKind,
    SkillRegistry,
    SkillStatus,
)
from geoagent_harness.skill_scaffolding.schemas import (
    SkillScaffoldPlan,
    SkillScaffoldRequest,
)


class SkillScaffoldPolicyError(ValueError):
    """Raised when a skill scaffold request is unsafe."""


def _validate_kind_and_access(
    *,
    kind: SkillKind,
    access: SkillAccess,
) -> None:
    if (
        kind == SkillKind.VALIDATION
        and access != SkillAccess.READ_ONLY
    ):
        raise SkillScaffoldPolicyError(
            "validation skills must be read-only"
        )

    if (
        access == SkillAccess.EVIDENCE_WRITE
        and kind != SkillKind.REPORTING
    ):
        raise SkillScaffoldPolicyError(
            "evidence-write skills must be reporting skills"
        )

    if (
        kind == SkillKind.REPORTING
        and access != SkillAccess.EVIDENCE_WRITE
    ):
        raise SkillScaffoldPolicyError(
            "reporting skills must use evidence-write access"
        )


def plan_skill_scaffold(
    request: SkillScaffoldRequest,
    *,
    registry: SkillRegistry,
) -> SkillScaffoldPlan:
    """Build a deterministic plan without writing files."""

    try:
        registry.get_skill(request.skill_id)
    except KeyError:
        pass
    else:
        raise SkillScaffoldPolicyError(
            f"skill {request.skill_id!r} is already registered"
        )

    _validate_kind_and_access(
        kind=request.kind,
        access=request.access,
    )

    is_controlled_write = request.access in {
        SkillAccess.ARTIFACT_WRITE,
        SkillAccess.DATABASE_WRITE,
    }

    package_path = (
        "src/geoagent_harness/skills/"
        f"{request.skill_id}"
    )

    files = [
        f"{package_path}/__init__.py",
        f"{package_path}/schemas.py",
        f"{package_path}/policy.py",
        f"{package_path}/service.py",
    ]

    if is_controlled_write:
        files.append(
            f"{package_path}/validation.py"
        )

    test_files = [
        f"tests/test_{request.skill_id}_schemas.py",
        f"tests/test_{request.skill_id}_policy.py",
        f"tests/test_{request.skill_id}_service.py",
        f"tests/test_{request.skill_id}_contract.py",
    ]

    registry_entry = SkillDefinition(
        id=request.skill_id,
        status=SkillStatus.PLANNED,
        kind=request.kind,
        access=request.access,
        approval_required=(
            True if is_controlled_write else False
        ),
        validation_required=(
            True if is_controlled_write else False
        ),
        entrypoint=None,
        verifier=None,
    )

    return SkillScaffoldPlan(
        skill_id=request.skill_id,
        summary=request.summary,
        kind=request.kind,
        access=request.access,
        approval_required=is_controlled_write,
        validation_required=is_controlled_write,
        package_path=package_path,
        files=files,
        test_files=test_files,
        registry_entry=registry_entry,
        warnings=[
            (
                "This plan does not create files or modify "
                "the trusted skill registry."
            ),
            (
                "Generated code must remain untrusted and "
                "the registry entry must remain planned "
                "until implementation review and contract "
                "tests pass."
            ),
        ],
    )

