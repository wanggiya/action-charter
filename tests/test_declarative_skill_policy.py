"""Tests for declarative skill security profiles."""

import pytest

from geoagent_harness.skill_definitions import (
    DeclarativeSkillDefinition,
    SkillProfile,
    assess_declarative_skill,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillKind,
)


def definition(
    profile: SkillProfile,
) -> DeclarativeSkillDefinition:
    return DeclarativeSkillDefinition(
        skill_id="inspect_raster",
        version="0.1.0",
        summary="Inspect one raster dataset.",
        profile=profile,
        adapter_id="raster_inspection",
        arguments_schema_id=(
            "inspect_raster_arguments"
        ),
        result_schema_id="inspect_raster_result",
        fixture_path="data/input/sample_dem.tif",
    )


@pytest.mark.parametrize(
    (
        "profile",
        "expected_kind",
        "expected_access",
        "approval_required",
        "validation_required",
        "verifier_required",
        "expected_ready",
    ),
    [
        (
            SkillProfile.READ_ONLY_INSPECTION,
            SkillKind.INSPECTION,
            SkillAccess.READ_ONLY,
            False,
            False,
            False,
            True,
        ),
        (
            SkillProfile.ARTIFACT_TRANSFORMATION,
            SkillKind.TRANSFORMATION,
            SkillAccess.ARTIFACT_WRITE,
            True,
            True,
            True,
            False,
        ),
        (
            SkillProfile.DATABASE_WRITE,
            SkillKind.DATABASE_LOAD,
            SkillAccess.DATABASE_WRITE,
            True,
            True,
            True,
            False,
        ),
        (
            SkillProfile.READ_ONLY_VALIDATION,
            SkillKind.VALIDATION,
            SkillAccess.READ_ONLY,
            False,
            False,
            False,
            False,
        ),
        (
            SkillProfile.EVIDENCE_REPORTING,
            SkillKind.REPORTING,
            SkillAccess.EVIDENCE_WRITE,
            False,
            False,
            False,
            False,
        ),
    ],
)
def test_profiles_derive_fixed_policy(
    profile: SkillProfile,
    expected_kind: SkillKind,
    expected_access: SkillAccess,
    approval_required: bool,
    validation_required: bool,
    verifier_required: bool,
    expected_ready: bool,
) -> None:
    result = assess_declarative_skill(
        definition(profile),
    )

    assert result.kind == expected_kind
    assert result.access == expected_access
    assert (
        result.approval_required
        is approval_required
    )
    assert (
        result.validation_required
        is validation_required
    )
    assert (
        result.verifier_required
        is verifier_required
    )
    assert (
        result.ready_for_generation
        is expected_ready
    )

    if expected_ready:
        assert result.policy_conflicts == []
    else:
        assert result.policy_conflicts == [
            (
                "adapter is incompatible with the "
                "selected security profile"
            )
        ]
    assert result.execution_performed is False


def test_unknown_adapter_blocks_generation() -> None:
    # result = assess_declarative_skill(
    #     definition(
    #         SkillProfile.READ_ONLY_INSPECTION
    #     ),
    #     # available_adapters=frozenset(),
    # )
    unknown = definition(
        SkillProfile.READ_ONLY_INSPECTION
    ).model_copy(
        update={
            "adapter_id": "unknown_adapter"
        }
    )

    result = assess_declarative_skill(unknown)

    assert result.adapter_available is False
    assert result.ready_for_generation is False
    assert result.policy_conflicts == [
        (
            "adapter is not present in the trusted "
            "adapter catalog"
        )
    ]
    assert result.generation_performed is False
    assert result.promotion_performed is False
    assert result.execution_performed is False

