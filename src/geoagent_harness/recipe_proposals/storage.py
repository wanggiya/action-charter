"""Bounded loading of non-executable recipe proposals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.recipe_proposals.schemas import (
    RecipeProposal,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)


MAX_RECIPE_PROPOSAL_BYTES = 250_000


class RecipeProposalStorageError(RuntimeError):
    """Raised when a proposal cannot be loaded safely."""


def _safe_proposal_path(
    path: Path,
    *,
    proposal_root: Path,
) -> Path:
    try:
        root = proposal_root.resolve(
            strict=True
        )
    except OSError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal root is unavailable"
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
        raise RecipeProposalStorageError(
            "recipe proposal does not exist"
        ) from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal path escaped its "
            "approved root"
        ) from exc

    if not resolved.is_file():
        raise RecipeProposalStorageError(
            "recipe proposal is not a file"
        )

    if resolved.suffix.lower() != ".json":
        raise RecipeProposalStorageError(
            "recipe proposal must be a JSON file"
        )

    return resolved


def load_recipe_proposal(
    path: Path,
    *,
    proposal_root: Path,
) -> RecipeProposal:
    """Load one bounded schema-compatible proposal."""

    safe_path = _safe_proposal_path(
        path,
        proposal_root=proposal_root,
    )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal could not be inspected"
        ) from exc

    if size > MAX_RECIPE_PROPOSAL_BYTES:
        raise RecipeProposalStorageError(
            "recipe proposal exceeds the size limit"
        )

    try:
        text = safe_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal is not UTF-8"
        ) from exc
    except OSError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal could not be read"
        ) from exc

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RecipeProposalStorageError(
            "recipe proposal is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeProposalStorageError(
            "recipe proposal must be an object"
        )

    try:
        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.RECIPE_PROPOSAL
            ),
        )

        return RecipeProposal.model_validate(
            payload
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise RecipeProposalStorageError(
            "recipe proposal failed schema "
            "validation"
        ) from exc

