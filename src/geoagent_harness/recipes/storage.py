"""Immutable storage for validated workflow recipes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.recipes.digest import (
    recipe_sha256,
)
from geoagent_harness.recipes.schemas import (
    WorkflowRecipe,
)
from geoagent_harness.redaction import (
    redact_value,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    SchemaRegistryError,
    assess_schema_compatibility,
)


MAX_RECIPE_BYTES = 1_000_000


class RecipeStorageError(RuntimeError):
    """Raised when a recipe cannot be safely stored or loaded."""


def _safe_recipe_path(
    *,
    path: Path,
    recipe_root: Path,
) -> Path:
    root = recipe_root.resolve()
    resolved = path.resolve()

    if resolved.parent != root:
        raise RecipeStorageError(
            "recipe path escaped the approved root"
        )

    return resolved


def _persisted_recipe(
    recipe: WorkflowRecipe,
) -> WorkflowRecipe:
    """Create the secret-redacted recipe that is persisted."""

    payload = redact_value(
        recipe.model_dump(mode="json")
    )

    try:
        return WorkflowRecipe.model_validate(payload)
    except ValidationError as exc:
        raise RecipeStorageError(
            "redacted recipe failed schema validation"
        ) from exc


def recipe_path(
    recipe: WorkflowRecipe,
    *,
    recipe_root: Path,
) -> Path:
    """Return the canonical immutable recipe path."""

    digest = recipe_sha256(recipe)

    return _safe_recipe_path(
        path=(
            recipe_root.resolve()
            / f"{recipe.recipe_id}.{digest}.json"
        ),
        recipe_root=recipe_root,
    )


def save_recipe(
    recipe: WorkflowRecipe,
    *,
    recipe_root: Path,
) -> tuple[WorkflowRecipe, Path]:
    """Persist one redacted recipe without overwriting."""

    safe_recipe = _persisted_recipe(recipe)

    root = recipe_root.resolve()

    try:
        root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise RecipeStorageError(
            "recipe root could not be prepared"
        ) from exc

    path = recipe_path(
        safe_recipe,
        recipe_root=root,
    )

    payload = safe_recipe.model_dump(
        mode="json"
    )

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".recipe-",
            suffix=".tmp",
            dir=root,
        )
    except OSError as exc:
        raise RecipeStorageError(
            "temporary recipe file could not be created"
        ) from exc

    temporary_path = Path(temporary_name)

    try:
        os.fchmod(descriptor, 0o644)

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(
                payload,
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        try:
            os.link(
                temporary_path,
                path,
            )
        except FileExistsError as exc:
            raise RecipeStorageError(
                "recipe already exists; "
                "overwriting is blocked"
            ) from exc

        directory_descriptor = os.open(
            root,
            os.O_RDONLY,
        )

        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)

    except RecipeStorageError:
        raise
    except OSError as exc:
        raise RecipeStorageError(
            "recipe could not be persisted"
        ) from exc
    finally:
        temporary_path.unlink(
            missing_ok=True
        )

    return safe_recipe, path


def _read_recipe_payload(
    path: Path,
) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise RecipeStorageError(
            "recipe file could not be inspected"
        ) from exc

    if size <= 0:
        raise RecipeStorageError(
            "recipe file is empty"
        )

    if size > MAX_RECIPE_BYTES:
        raise RecipeStorageError(
            "recipe file exceeds the size limit"
        )

    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RecipeStorageError(
            "recipe file is not UTF-8"
        ) from exc
    except OSError as exc:
        raise RecipeStorageError(
            "recipe file could not be read"
        ) from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RecipeStorageError(
            "recipe file is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeStorageError(
            "recipe JSON must be an object"
        )

    return payload


def load_recipe(
    path: Path,
    *,
    recipe_root: Path,
) -> WorkflowRecipe:
    """Load and verify an immutable recipe."""

    safe_path = _safe_recipe_path(
        path=path,
        recipe_root=recipe_root,
    )

    if not safe_path.is_file():
        raise RecipeStorageError(
            "recipe file does not exist"
        )

    payload = _read_recipe_payload(
        safe_path
    )

    artifact_version = payload.get(
        "schema_version"
    )

    if not isinstance(artifact_version, str):
        raise RecipeStorageError(
            "recipe has no valid schema version"
        )

    try:
        compatibility = assess_schema_compatibility(
            artifact_type=ArtifactType.RECIPE,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
        raise RecipeStorageError(
            "recipe schema type is unavailable"
        ) from exc

    if not compatibility.readable:
        raise RecipeStorageError(
            "recipe schema version is unsupported"
        )

    try:
        recipe = WorkflowRecipe.model_validate(
            payload
        )
    except ValidationError as exc:
        raise RecipeStorageError(
            "recipe failed schema validation"
        ) from exc

    expected_path = recipe_path(
        recipe,
        recipe_root=recipe_root,
    )

    if safe_path != expected_path:
        raise RecipeStorageError(
            "recipe filename does not match its "
            "canonical identity"
        )

    return recipe

def load_recipe_draft(
    path: Path,
) -> WorkflowRecipe:
    """Load a bounded recipe draft before persistence."""

    if not path.is_file():
        raise RecipeStorageError(
            "recipe draft does not exist"
        )

    payload = _read_recipe_payload(path)

    version = payload.get("schema_version")

    if not isinstance(version, str):
        raise RecipeStorageError(
            "recipe draft has no schema version"
        )

    compatibility = assess_schema_compatibility(
        artifact_type=ArtifactType.RECIPE,
        artifact_version=version,
    )

    if not compatibility.writable:
        raise RecipeStorageError(
            "recipe draft schema is not writable"
        )

    try:
        return WorkflowRecipe.model_validate(
            payload
        )
    except ValidationError as exc:
        raise RecipeStorageError(
            "recipe draft failed schema validation"
        ) from exc

