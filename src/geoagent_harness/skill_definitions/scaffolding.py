"""Compile declarative definitions into existing scaffolds."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.skill_definitions.generation import (
    SkillContractGenerationError,
    build_skill_contract,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    DeclarativeSkillScaffoldGenerationResult,
    DeclarativeSkillScaffoldPlan,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldGenerationError,
    SkillScaffoldPolicyError,
    SkillScaffoldRequest,
    generate_skill_scaffold,
    plan_skill_scaffold,
)


class DeclarativeSkillScaffoldError(RuntimeError):
    """Raised when declarative scaffold compilation fails."""


def compile_declarative_skill_scaffold(
    definition: DeclarativeSkillDefinition,
    *,
    registry: SkillRegistry,
) -> DeclarativeSkillScaffoldPlan:
    """Compile one definition into the existing scaffold plan."""

    try:
        contract = build_skill_contract(
            definition
        )

        request = SkillScaffoldRequest(
            skill_id=definition.skill_id,
            summary=definition.summary,
            kind=contract.kind,
            access=contract.access,
            generation_requested=False,
            registry_modification_requested=False,
            execution_requested=False,
        )

        scaffold_plan = plan_skill_scaffold(
            request,
            registry=registry,
        )
    except (
        SkillContractGenerationError,
        SkillScaffoldPolicyError,
        ValueError,
    ) as exc:
        raise DeclarativeSkillScaffoldError(
            "declarative skill could not be "
            "compiled into a scaffold"
        ) from exc

    if (
        scaffold_plan.kind != contract.kind
        or scaffold_plan.access != contract.access
        or scaffold_plan.approval_required
        != contract.approval_required
        or scaffold_plan.validation_required
        != contract.validation_required
    ):
        raise DeclarativeSkillScaffoldError(
            "scaffold plan conflicts with the "
            "declarative skill contract"
        )

    return DeclarativeSkillScaffoldPlan(
        definition_sha256=(
            contract.definition_sha256
        ),
        contract=contract,
        scaffold_plan=scaffold_plan,
        compilation_performed=True,
        generation_performed=False,
        registry_modified=False,
        implementation_trusted=False,
        promotion_performed=False,
        execution_performed=False,
    )


def generate_declarative_skill_scaffold(
    definition: DeclarativeSkillDefinition,
    *,
    registry: SkillRegistry,
    scaffold_root: Path,
) -> DeclarativeSkillScaffoldGenerationResult:
    """Generate one untrusted scaffold through the existing system."""

    compiled = compile_declarative_skill_scaffold(
        definition,
        registry=registry,
    )

    try:
        generated = generate_skill_scaffold(
            compiled.scaffold_plan,
            scaffold_root=scaffold_root,
        )
    except (
        SkillScaffoldGenerationError,
        OSError,
        ValueError,
    ) as exc:
        raise DeclarativeSkillScaffoldError(
            "compiled declarative scaffold could "
            "not be generated"
        ) from exc

    return DeclarativeSkillScaffoldGenerationResult(
        definition_sha256=(
            compiled.definition_sha256
        ),
        contract=compiled.contract,
        scaffold=generated,
        compilation_performed=True,
        generation_performed=True,
        registry_modified=False,
        implementation_trusted=False,
        promotion_performed=False,
        execution_performed=False,
    )

