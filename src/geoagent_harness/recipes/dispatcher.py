"""Hard-coded dispatcher for approved recipe skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes.schemas import (
    ConvertVectorRecipeArguments,
    InspectVectorRecipeArguments,
    RecipeExecutionEnvelope,
    RecipeStepExecutionResult,
)
from geoagent_harness.redaction import (
    redact_value,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillRegistry,
    SkillStatus,
)
from geoagent_harness.skills.convert_vector.service import (
    ConvertVectorError,
    convert_vector,
)
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
    inspect_vector,
)


_EXPECTED_ENTRYPOINTS = {
    "inspect_vector": (
        "geoagent_harness.skills.inspect_vector."
        "service:inspect_vector"
    ),
    "convert_vector": (
        "geoagent_harness.skills.convert_vector."
        "service:convert_vector"
    ),
}


class RecipeDispatchError(RuntimeError):
    """Raised when a recipe step cannot be safely dispatched."""


def _step_from_envelope(
    envelope: RecipeExecutionEnvelope,
    step_id: str,
):
    matches = [
        step
        for step in envelope.steps
        if step.step_id == step_id
    ]

    if len(matches) != 1:
        raise RecipeDispatchError(
            f"execution envelope does not contain "
            f"exactly one step {step_id!r}"
        )

    return matches[0]


def _validate_registered_skill(
    *,
    skill_id: str,
    registry: SkillRegistry,
):
    try:
        skill = registry.get_skill(
            skill_id
        )
    except KeyError as exc:
        raise RecipeDispatchError(
            f"skill {skill_id!r} is not registered"
        ) from exc

    if skill.status != SkillStatus.IMPLEMENTED:
        raise RecipeDispatchError(
            f"skill {skill_id!r} is not implemented"
        )

    expected_entrypoint = (
        _EXPECTED_ENTRYPOINTS.get(skill_id)
    )

    if expected_entrypoint is None:
        raise RecipeDispatchError(
            f"skill {skill_id!r} is not in the "
            "hard-coded dispatcher allowlist"
        )

    if skill.entrypoint != expected_entrypoint:
        raise RecipeDispatchError(
            f"skill {skill_id!r} registry entrypoint "
            "does not match the hard-coded dispatcher"
        )

    return skill


def _structured_result(
    value: Any,
) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        payload = value.model_dump(
            mode="json"
        )
    elif isinstance(value, dict):
        payload = value
    else:
        raise RecipeDispatchError(
            "skill returned an unsupported result type"
        )

    redacted = redact_value(payload)

    if not isinstance(redacted, dict):
        raise RecipeDispatchError(
            "skill result must be an object"
        )

    return redacted


def dispatch_recipe_step(
    *,
    envelope: RecipeExecutionEnvelope,
    step_id: str,
    registry: SkillRegistry,
    settings: MCPSettings,
) -> RecipeStepExecutionResult:
    """Dispatch one exact allowlisted envelope step."""

    if envelope.execution_performed is not False:
        raise RecipeDispatchError(
            "execution envelope already claims execution"
        )

    step = _step_from_envelope(
        envelope,
        step_id,
    )

    if step.step_id not in (
        envelope.topological_step_ids
    ):
        raise RecipeDispatchError(
            "step is outside the validated "
            "topological scope"
        )

    skill = _validate_registered_skill(
        skill_id=step.skill_id,
        registry=registry,
    )

    if (
        skill.access != SkillAccess.READ_ONLY
        and step.step_id
        not in envelope.approved_step_ids
    ):
        raise RecipeDispatchError(
            "write step is outside the approved scope"
        )

    try:
        if step.skill_id == "inspect_vector":
            arguments = (
                InspectVectorRecipeArguments.model_validate(
                    step.arguments
                )
            )

            value = inspect_vector(
                path=Path(arguments.path),
                input_root=settings.input_root,
            )

            status = "completed"
            validation_performed = False

        elif step.skill_id == "convert_vector":
            arguments = (
                ConvertVectorRecipeArguments.model_validate(
                    step.arguments
                )
            )

            value = convert_vector(
                path=Path(arguments.path),
                target_path=Path(
                    arguments.target_path
                ),
                settings=settings,
                source_layer=(
                    arguments.source_layer
                ),
                target_layer=(
                    arguments.target_layer
                ),
            )

            status = (
                "completed_pending_validation"
            )
            validation_performed = False

        else:
            # This remains unreachable unless code changes
            # without updating the hard-coded policy.
            raise RecipeDispatchError(
                "skill has no hard-coded dispatcher"
            )

    except ValidationError as exc:
        raise RecipeDispatchError(
            f"arguments for skill "
            f"{step.skill_id!r} are invalid"
        ) from exc
    except (
        ConvertVectorError,
        InspectVectorError,
    ) as exc:
        raise RecipeDispatchError(
            f"skill {step.skill_id!r} "
            "execution failed"
        ) from exc

    return RecipeStepExecutionResult(
        step_id=step.step_id,
        skill_id=step.skill_id,
        status=status,
        output_ids=step.output_ids,
        result=_structured_result(value),
        execution_performed=True,
        validation_performed=(
            validation_performed
        ),
    )
