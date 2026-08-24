"""Tests for declarative skill security profiles."""

import pytest

from geoagent_harness.skill_definitions.catalog import (
    TrustedAdapter,
    get_trusted_adapter,
)
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

def test_write_adapter_requires_trusted_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = DeclarativeSkillDefinition(
        skill_id="convert_raster",
        version="0.1.0",
        summary="Convert one raster.",
        profile=SkillProfile.ARTIFACT_TRANSFORMATION,
        adapter_id="raster_conversion",
        arguments_schema_id="convert_raster_arguments",
        result_schema_id="convert_raster_result",
        fixture_path="data/input/sample_dem.tif",
    )

    monkeypatch.setattr(
        (
            "geoagent_harness.skill_definitions."
            "policy.get_trusted_adapter"
        ),
        lambda adapter_id: TrustedAdapter(
            adapter_id=adapter_id,
            allowed_profiles=(
                SkillProfile.ARTIFACT_TRANSFORMATION,
            ),
            fixture_required=True,
            entrypoint=(
                "geoagent_harness.skills.convert_raster."
                "service:convert_raster"
            ),
            verifier=None,
        ),
    )

    result = assess_declarative_skill(
        definition
    )

    assert result.ready_for_generation is False
    assert (
        "selected security profile requires "
        "a trusted verifier"
        in result.policy_conflicts
    )

def test_inspection_adapter_has_no_verifier() -> None:
    adapter = get_trusted_adapter(
        "raster_inspection"
    )

    assert adapter.verifier is None

def test_raster_conversion_is_ready_for_generation(
) -> None:
    definition = DeclarativeSkillDefinition(
        skill_id="convert_raster",
        version="0.1.0",
        summary=(
            "Convert and reproject one raster "
            "into a new GeoTIFF."
        ),
        profile=(
            SkillProfile.ARTIFACT_TRANSFORMATION
        ),
        adapter_id="raster_conversion",
        arguments_schema_id=(
            "convert_raster_arguments"
        ),
        result_schema_id=(
            "convert_raster_result"
        ),
        fixture_path=(
            "data/input/sample_dem.tif"
        ),
    )

    result = assess_declarative_skill(
        definition
    )

    assert result.ready_for_generation is True
    assert result.adapter_available is True
    assert result.kind == SkillKind.TRANSFORMATION
    assert result.access == SkillAccess.ARTIFACT_WRITE
    assert result.approval_required is True
    assert result.validation_required is True
    assert result.verifier_required is True
    assert result.policy_conflicts == []


def test_raster_conversion_adapter_has_verifier(
) -> None:
    adapter = get_trusted_adapter(
        "raster_conversion"
    )

    assert adapter.entrypoint == (
        "geoagent_harness.skills.convert_raster."
        "service:convert_raster"
    )
    assert adapter.verifier == (
        "geoagent_harness.skills.convert_raster."
        "validation:validate_raster_conversion"
    )
