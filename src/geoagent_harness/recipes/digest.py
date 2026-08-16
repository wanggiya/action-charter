"""Canonical identity for reusable recipes."""

from __future__ import annotations

import hashlib
import json

from geoagent_harness.recipes.schemas import (
    WorkflowRecipe,
)


def canonical_recipe_json(
    recipe: WorkflowRecipe,
) -> str:
    """Return canonical JSON used for recipe identity."""

    return json.dumps(
        recipe.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def recipe_sha256(
    recipe: WorkflowRecipe,
) -> str:
    """Return the SHA-256 identity of an exact recipe."""

    return hashlib.sha256(
        canonical_recipe_json(
            recipe
        ).encode("utf-8")
    ).hexdigest()
