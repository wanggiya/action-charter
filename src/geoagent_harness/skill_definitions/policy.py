"""Deterministic policy for declarative skill definitions."""

from __future__ import annotations

from dataclasses import dataclass

from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillAssessment,
    DeclarativeSkillDefinition,
    SkillProfile,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillKind,
)
from geoagent_harness.skill_definitions.catalog import (
    TrustedAdapterError,
    get_trusted_adapter,
)



@dataclass(frozen=True)
class ProfilePolicy:
    """Security properties fixed by one profile."""

    kind: SkillKind
    access: SkillAccess
    approval_required: bool
    validation_required: bool
    verifier_required: bool


_PROFILE_POLICIES = {
    SkillProfile.READ_ONLY_INSPECTION: (
        ProfilePolicy(
            kind=SkillKind.INSPECTION,
            access=SkillAccess.READ_ONLY,
            approval_required=False,
            validation_required=False,
            verifier_required=False,
        )
    ),
    SkillProfile.ARTIFACT_TRANSFORMATION: (
        ProfilePolicy(
            kind=SkillKind.TRANSFORMATION,
            access=SkillAccess.ARTIFACT_WRITE,
            approval_required=True,
            validation_required=True,
            verifier_required=True,
        )
    ),
    SkillProfile.DATABASE_WRITE: (
        ProfilePolicy(
            kind=SkillKind.DATABASE_LOAD,
            access=SkillAccess.DATABASE_WRITE,
            approval_required=True,
            validation_required=True,
            verifier_required=True,
        )
    ),
    SkillProfile.READ_ONLY_VALIDATION: (
        ProfilePolicy(
            kind=SkillKind.VALIDATION,
            access=SkillAccess.READ_ONLY,
            approval_required=False,
            validation_required=False,
            verifier_required=False,
        )
    ),
    SkillProfile.EVIDENCE_REPORTING: (
        ProfilePolicy(
            kind=SkillKind.REPORTING,
            access=SkillAccess.EVIDENCE_WRITE,
            approval_required=False,
            validation_required=False,
            verifier_required=False,
        )
    ),
}


def get_profile_policy(
    profile: SkillProfile,
) -> ProfilePolicy:
    """Return the immutable policy for one profile."""

    return _PROFILE_POLICIES[profile]


def assess_declarative_skill(
    definition: DeclarativeSkillDefinition,
) -> DeclarativeSkillAssessment:
    """Assess a definition without generating or executing."""

    profile_policy = get_profile_policy(
        definition.profile
    )

    conflicts: list[str] = []
    adapter_available = True

    try:
        adapter = get_trusted_adapter(
            definition.adapter_id
        )
    except TrustedAdapterError:
        adapter_available = False
        conflicts.append(
            "adapter is not present in the trusted "
            "adapter catalog"
        )
    else:
        if (
            definition.profile
            not in adapter.allowed_profiles
        ):
            conflicts.append(
                "adapter is incompatible with the "
                "selected security profile"
            )

        if (
            adapter.fixture_required
            and definition.fixture_path is None
        ):
            conflicts.append(
                "adapter requires a deterministic "
                "test fixture"
            )

    return DeclarativeSkillAssessment(
        skill_id=definition.skill_id,
        profile=definition.profile,
        kind=profile_policy.kind,
        access=profile_policy.access,
        approval_required=(
            profile_policy.approval_required
        ),
        validation_required=(
            profile_policy.validation_required
        ),
        verifier_required=(
            profile_policy.verifier_required
        ),
        adapter_available=adapter_available,
        ready_for_generation=not conflicts,
        policy_conflicts=conflicts,
        definition_modified=False,
        generation_performed=False,
        promotion_performed=False,
        execution_performed=False,
    )
    
