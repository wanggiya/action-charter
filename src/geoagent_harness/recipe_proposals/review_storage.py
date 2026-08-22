"""Bounded loading of recipe operator reviews."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.recipe_proposals.schemas import (
    RecipeOperatorReview,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)


MAX_RECIPE_REVIEW_BYTES = 1_000_000


class RecipeReviewStorageError(RuntimeError):
    """Raised when an operator review is unavailable."""


def _safe_review_path(
    path: Path,
    *,
    review_root: Path,
) -> Path:
    try:
        root = review_root.resolve(
            strict=True
        )
    except OSError as exc:
        raise RecipeReviewStorageError(
            "recipe review root is unavailable"
        ) from exc

    candidate = (
        path
        if path.is_absolute()
        else Path.cwd() / path
    )

    try:
        resolved = candidate.resolve(
            strict=True
        )
    except OSError as exc:
        raise RecipeReviewStorageError(
            "recipe review does not exist"
        ) from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RecipeReviewStorageError(
            "recipe review path escaped its "
            "approved root"
        ) from exc

    if not resolved.is_file():
        raise RecipeReviewStorageError(
            "recipe review is not a file"
        )

    if resolved.suffix.lower() != ".json":
        raise RecipeReviewStorageError(
            "recipe review must be a JSON file"
        )

    return resolved


def load_recipe_operator_review(
    path: Path,
    *,
    review_root: Path,
) -> RecipeOperatorReview:
    """Load one schema-compatible operator review."""

    safe_path = _safe_review_path(
        path,
        review_root=review_root,
    )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise RecipeReviewStorageError(
            "recipe review could not be inspected"
        ) from exc

    if size > MAX_RECIPE_REVIEW_BYTES:
        raise RecipeReviewStorageError(
            "recipe review exceeds the size limit"
        )

    try:
        text = safe_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RecipeReviewStorageError(
            "recipe review is not UTF-8"
        ) from exc
    except OSError as exc:
        raise RecipeReviewStorageError(
            "recipe review could not be read"
        ) from exc

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RecipeReviewStorageError(
            "recipe review is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeReviewStorageError(
            "recipe review must be an object"
        )

    try:
        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.RECIPE_OPERATOR_REVIEW
            ),
        )

        return RecipeOperatorReview.model_validate(
            payload
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise RecipeReviewStorageError(
            "recipe review failed schema validation"
        ) from exc

