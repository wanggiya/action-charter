"""Deterministic recipe-proposal readiness policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from geoagent_harness.recipe_proposals.schemas import (
    RecipeProposal,
    RecipeProposalAssessment,
)
from geoagent_harness.recipe_proposals.templates import (
    get_recipe_template,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
    SkillStatus,
)


_FORMAT_BY_SUFFIX = {
    ".geojson": "geojson",
    ".gpkg": "geopackage",
}

def _no_policy_conflicts(
    _parameters: dict[str, Any],
) -> list[str]:
    """Return no additional template conflicts."""

    return []


def _vector_conversion_conflicts(
    parameters: dict[str, Any],
) -> list[str]:
    """Validate vector target format consistency."""

    conflicts: list[str] = []

    target_path = parameters.get(
        "target_path"
    )
    target_format = parameters.get(
        "target_format"
    )

    if target_path is not None:
        suffix = Path(
            target_path
        ).suffix.lower()

        expected_format = (
            _FORMAT_BY_SUFFIX.get(suffix)
        )

        if expected_format is None:
            conflicts.append(
                "target_path must end with "
                ".geojson or .gpkg"
            )
        elif (
            target_format is not None
            and target_format
            != expected_format
        ):
            conflicts.append(
                "target_format conflicts with "
                "the target_path extension"
            )

    return conflicts


def _raster_conversion_conflicts(
    parameters: dict[str, Any],
) -> list[str]:
    """Validate the controlled raster target."""

    target_path = parameters.get(
        "target_path"
    )

    if (
        target_path is not None
        and Path(target_path).suffix.lower()
        != ".tif"
    ):
        return [
            (
                "raster target_path must end "
                "with .tif"
            )
        ]

    return []


_ASSESSMENT_POLICIES: dict[
    str,
    Callable[
        [dict[str, Any]],
        list[str],
    ],
] = {
    "none": _no_policy_conflicts,
    "vector_conversion": (
        _vector_conversion_conflicts
    ),
    "raster_conversion": (
        _raster_conversion_conflicts
    ),
}


def _clarification_question(
    field: str,
) -> str:
    questions = {
        "path": (
            "Which approved input dataset should "
            "the recipe use?"
        ),
        "target_path": (
            "Which new output path beneath the "
            "approved output root should be used?"
        ),
        "target_schema": (
            "Which approved PostGIS schema should "
            "receive the new table?"
        ),
        "target_table": (
            "What new safe PostGIS table name "
            "should be used?"
        ),
        "target_crs": (
            "Which target coordinate reference "
            "system should be used?"
        ),
    }

    return questions.get(
        field,
        f"What value should be used for {field}?",
    )


def assess_recipe_proposal(
    proposal: RecipeProposal,
    *,
    registry: SkillRegistry,
) -> RecipeProposalAssessment:
    """Assess readiness without changing the proposal."""

    template = get_recipe_template(
        proposal.selection.template_id
    )

    parameters = (
        proposal.selection.parameters.model_dump()
    )

    missing_fields = [
        field
        for field in template.required_parameters
        if parameters.get(field) is None
    ]

    unavailable_skills: list[str] = []

    for skill_id in template.skill_ids:
        try:
            skill = registry.get_skill(skill_id)
        except KeyError:
            unavailable_skills.append(skill_id)
            continue

        if skill.status != SkillStatus.IMPLEMENTED:
            unavailable_skills.append(skill_id)

    try:
        assessment_policy = (
            _ASSESSMENT_POLICIES[
                template.assessment_policy
            ]
        )
    except KeyError as exc:
        raise ValueError(
            "template selected an unknown "
            "trusted assessment policy"
        ) from exc

    conflicts = assessment_policy(
        parameters
    )

    clarification_questions = [
        _clarification_question(field)
        for field in missing_fields
    ]

    clarification_questions.extend(
        proposal.missing_information
    )

    # Preserve stable order while removing duplicates.
    clarification_questions = list(
        dict.fromkeys(
            clarification_questions
        )
    )

    ready = not (
        missing_fields
        or unavailable_skills
        or conflicts
        or proposal.missing_information
    )

    if ready:
        reason = (
            "The proposal contains all parameters "
            "required by a trusted template and all "
            "template skills are implemented."
        )
    else:
        reason = (
            "The proposal is not ready for "
            "compilation; clarification or policy "
            "resolution is required."
        )

    return RecipeProposalAssessment(
        template_id=template.template_id,
        ready_for_compilation=ready,
        required_fields=list(
            template.required_parameters
        ),
        missing_fields=missing_fields,
        unavailable_skills=(
            unavailable_skills
        ),
        policy_conflicts=conflicts,
        clarification_questions=(
            clarification_questions
        ),
        reason=reason,
        proposal_modified=False,
        compilation_performed=False,
        execution_performed=False,
    )

