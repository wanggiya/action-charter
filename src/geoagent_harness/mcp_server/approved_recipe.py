"""Server-side verification for approved recipe execution."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
    load_settings,
)
from geoagent_harness.recipes.approval import (
    RecipeApprovalError,
    load_recipe_approval,
)
from geoagent_harness.recipes.execution import (
    RecipeExecutionPolicyError,
    build_recipe_execution_envelope,
)
from geoagent_harness.recipes.runner import (
    RecipeRunError,
    run_approved_recipe as execute_approved_recipe,
)
from geoagent_harness.recipes.schemas import (
    RecipeExecutionEnvelope,
    # RecipeRunResult,
)
from geoagent_harness.recipes.storage import (
    RecipeStorageError,
    load_recipe,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)
from geoagent_harness.skill_registry import (
    SkillRegistryError,
    load_skill_registry,
)
from geoagent_harness.recipes.evidence_persistence import (
    RecipeEvidencePersistenceError,
    persist_recipe_run,
)
from geoagent_harness.recipes.evidence_schemas import (
    PersistedRecipeExecutionResult,
)


class ApprovedRecipeError(RuntimeError):
    """Raised when an approved recipe request is unsafe."""


def _record_filename(
    value: str,
    *,
    label: str,
) -> str:
    """Accept only one plain JSON filename."""

    path = Path(value)

    if (
        path.name != value
        or path.suffix != ".json"
        or value in {".json", ".."}
    ):
        raise ApprovedRecipeError(
            f"{label} must be a plain JSON filename"
        )

    return value


def validate_approved_recipe_request(
    *,
    execution_envelope: dict[str, Any],
    recipe_filename: str,
    approval_filename: str,
    settings: MCPSettings,
) -> RecipeExecutionEnvelope:
    """Reload artifacts and rebuild the expected envelope."""

    safe_recipe_filename = _record_filename(
        recipe_filename,
        label="recipe_filename",
    )
    safe_approval_filename = _record_filename(
        approval_filename,
        label="approval_filename",
    )

    try:
        recipe = load_recipe(
            settings.recipe_root
            / safe_recipe_filename,
            recipe_root=settings.recipe_root,
        )

        approval = load_recipe_approval(
            settings.approval_root
            / safe_approval_filename,
            approval_root=settings.approval_root,
        )

        registry = load_skill_registry(
            settings.project_root
        )

        expected = (
            build_recipe_execution_envelope(
                recipe=recipe,
                approval=approval,
                registry=registry,
            )
        )

        require_supported_schema(
            execution_envelope,
            artifact_type=(
                ArtifactType
                .RECIPE_EXECUTION_ENVELOPE
            ),
        )

        supplied = (
            RecipeExecutionEnvelope.model_validate(
                execution_envelope
            )
        )

    except (
        RecipeApprovalError,
        RecipeExecutionPolicyError,
        RecipeStorageError,
        SkillRegistryError,
        ValidationError,
        ValueError,
    ) as exc:
        raise ApprovedRecipeError(
            "approved recipe request failed "
            "server-side verification"
        ) from exc

    if supplied != expected:
        raise ApprovedRecipeError(
            "execution envelope does not match "
            "the server-verified recipe and approval"
        )

    return expected


def run_approved_recipe(
    *,
    execution_envelope: dict[str, Any],
    recipe_filename: str,
    approval_filename: str,
    settings: MCPSettings | None = None,
) -> PersistedRecipeExecutionResult:
    """Verify exact artifacts, then execute the recipe."""

    active = settings or load_settings()

    if not active.enable_write_tools:
        raise ApprovedRecipeError(
            "write tools are disabled"
        )

    verified = validate_approved_recipe_request(
        execution_envelope=execution_envelope,
        recipe_filename=recipe_filename,
        approval_filename=approval_filename,
        settings=active,
    )

    try:
        recipe = load_recipe(
            active.recipe_root
            / recipe_filename,
            recipe_root=active.recipe_root,
        )
        approval = load_recipe_approval(
            active.approval_root
            / approval_filename,
            approval_root=active.approval_root,
        )
        registry = load_skill_registry(
            active.project_root
        )

        result = execute_approved_recipe(
            recipe=recipe,
            approval=approval,
            registry=registry,
            settings=active,
        )
    except (
        RecipeApprovalError,
        RecipeRunError,
        RecipeStorageError,
        SkillRegistryError,
    ) as exc:
        raise ApprovedRecipeError(
            "approved recipe execution failed"
        ) from exc

    if result.recipe_sha256 != (
        verified.recipe_sha256
    ):
        raise ApprovedRecipeError(
            "recipe result digest conflicts with "
            "the verified execution envelope"
        )

    if result.approval_id != (
        verified.approval_id
    ):
        raise ApprovedRecipeError(
            "recipe result approval conflicts with "
            "the verified execution envelope"
        )

    try:
        execution_record = persist_recipe_run(
            run_result=result,
            registry=registry,
            settings=active,
            recorded_at=datetime.now(
                timezone.utc
            ),
        )
    except RecipeEvidencePersistenceError as exc:
        raise ApprovedRecipeError(
            "recipe execution completed but durable "
            "evidence persistence failed; manual "
            "review is required"
        ) from exc

    return PersistedRecipeExecutionResult(
        run_result=result,
        execution_record=execution_record,
    )

