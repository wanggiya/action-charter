"""Tests for deterministic proposal assessment."""

from pathlib import Path

from geoagent_harness.recipe_proposals import (
    RecipeProposal,
    assess_recipe_proposal,
    list_recipe_templates,
)
from geoagent_harness.skill_registry import (
    SkillStatus,
    load_skill_registry,
)
from tests.test_recipe_proposal_schemas import (
    conversion_payload,
)


PROJECT_ROOT = Path(__file__).parents[1]


def trusted_registry():
    return load_skill_registry(
        PROJECT_ROOT
    )


def test_template_registry_has_stable_order() -> None:
    assert [
        template.template_id
        for template in list_recipe_templates()
    ] == [
        "inspect_vector",
        "inspect_and_convert_vector",
        "vector_to_postgis",
    ]


def test_complete_conversion_is_ready() -> None:
    proposal = RecipeProposal.model_validate(
        conversion_payload()
    )

    assessment = assess_recipe_proposal(
        proposal,
        registry=trusted_registry(),
    )

    assert assessment.ready_for_compilation is True
    assert assessment.missing_fields == []
    assert assessment.unavailable_skills == []
    assert assessment.policy_conflicts == []
    assert assessment.compilation_performed is False


def test_missing_target_requests_clarification() -> None:
    payload = conversion_payload()
    payload["selection"]["parameters"][
        "target_path"
    ] = None

    proposal = RecipeProposal.model_validate(
        payload
    )

    assessment = assess_recipe_proposal(
        proposal,
        registry=trusted_registry(),
    )

    assert assessment.ready_for_compilation is False
    assert assessment.missing_fields == [
        "target_path"
    ]
    assert assessment.clarification_questions


def test_declared_missing_information_blocks_compilation() -> None:
    payload = conversion_payload()
    payload["missing_information"] = [
        "The requested output name is ambiguous."
    ]

    proposal = RecipeProposal.model_validate(
        payload
    )

    assessment = assess_recipe_proposal(
        proposal,
        registry=trusted_registry(),
    )

    assert assessment.ready_for_compilation is False
    assert (
        "The requested output name is ambiguous."
        in assessment.clarification_questions
    )


def test_target_format_conflict_is_detected() -> None:
    payload = conversion_payload()
    payload["selection"]["parameters"][
        "target_format"
    ] = "geojson"

    proposal = RecipeProposal.model_validate(
        payload
    )

    assessment = assess_recipe_proposal(
        proposal,
        registry=trusted_registry(),
    )

    assert assessment.ready_for_compilation is False
    assert assessment.policy_conflicts == [
        (
            "target_format conflicts with "
            "the target_path extension"
        )
    ]


def test_unimplemented_skill_blocks_template() -> None:
    registry = trusted_registry()

    changed_skills = [
        skill.model_copy(
            update={
                "status": SkillStatus.PLANNED,
                "entrypoint": None,
                "verifier": None,
            }
        )
        if skill.id == "convert_vector"
        else skill
        for skill in registry.skills
    ]

    changed_registry = registry.model_copy(
        update={
            "skills": changed_skills,
        }
    )

    proposal = RecipeProposal.model_validate(
        conversion_payload()
    )

    assessment = assess_recipe_proposal(
        proposal,
        registry=changed_registry,
    )

    assert assessment.ready_for_compilation is False
    assert assessment.unavailable_skills == [
        "convert_vector"
    ]

