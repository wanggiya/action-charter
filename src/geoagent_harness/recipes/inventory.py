"""Deterministic read-only recipe approval inventory."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from geoagent_harness.recipes.approval import (
    RecipeApprovalError,
    load_recipe_approval,
    verify_recipe_approval,
)
from geoagent_harness.recipes.digest import (
    recipe_sha256,
)
from geoagent_harness.recipes.schemas import (
    RecipeApprovalInventory,
    RecipeApprovalMatch,
)
from geoagent_harness.recipes.storage import (
    RecipeStorageError,
    load_recipe,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


MAX_INVENTORY_RECIPES = 1_000
MAX_INVENTORY_APPROVALS = 5_000


class RecipeInventoryError(RuntimeError):
    """Raised when a trusted inventory cannot be built."""


def _json_files(
    root: Path,
    *,
    pattern: str,
    limit: int,
    label: str,
) -> list[Path]:
    resolved_root = root.resolve()

    if not resolved_root.is_dir():
        raise RecipeInventoryError(
            f"{label} root does not exist"
        )

    paths = sorted(
        resolved_root.glob(pattern),
        key=lambda path: path.name,
    )

    if len(paths) > limit:
        raise RecipeInventoryError(
            f"{label} root exceeds its file limit"
        )

    for path in paths:
        if path.is_symlink():
            raise RecipeInventoryError(
                f"{label} artifacts cannot be symlinks"
            )

        if path.resolve().parent != resolved_root:
            raise RecipeInventoryError(
                f"{label} artifact escaped its root"
            )

    return paths


def build_recipe_approval_inventory(
    *,
    recipe_root: Path,
    approval_root: Path,
    registry: SkillRegistry,
    now: datetime | None = None,
) -> RecipeApprovalInventory:
    """Match canonical recipes to exact approvals by digest."""

    recipe_paths = _json_files(
        recipe_root,
        pattern="*.json",
        limit=MAX_INVENTORY_RECIPES,
        label="recipe",
    )
    approval_paths = _json_files(
        approval_root,
        pattern="recipe-approval-*.json",
        limit=MAX_INVENTORY_APPROVALS,
        label="approval",
    )

    try:
        recipes = [
            (
                path,
                load_recipe(
                    path,
                    recipe_root=recipe_root,
                ),
            )
            for path in recipe_paths
        ]

        approvals = [
            (
                path,
                load_recipe_approval(
                    path,
                    approval_root=approval_root,
                ),
            )
            for path in approval_paths
        ]
    except (
        RecipeApprovalError,
        RecipeStorageError,
        OSError,
        ValueError,
    ) as exc:
        raise RecipeInventoryError(
            "trusted recipe inventory contains "
            "an invalid artifact"
        ) from exc

    recipe_digests = {
        recipe_sha256(recipe)
        for _, recipe in recipes
    }

    approval_digests = {
        approval.recipe_sha256
        for _, approval in approvals
    }

    matches: list[RecipeApprovalMatch] = []
    recipes_without: list[str] = []

    for recipe_path, recipe in recipes:
        digest = recipe_sha256(recipe)

        matching_approvals = [
            (
                approval_path,
                approval,
            )
            for (
                approval_path,
                approval,
            ) in approvals
            if approval.recipe_sha256 == digest
        ]

        if not matching_approvals:
            recipes_without.append(
                recipe_path.name
            )
            continue

        for (
            approval_path,
            approval,
        ) in matching_approvals:
            try:
                verification = (
                    verify_recipe_approval(
                        approval=approval,
                        recipe=recipe,
                        registry=registry,
                        now=now,
                    )
                )
            except (
                RecipeApprovalError,
                ValueError,
            ) as exc:
                raise RecipeInventoryError(
                    "recipe approval verification failed"
                ) from exc

            matches.append(
                RecipeApprovalMatch(
                    recipe_id=recipe.recipe_id,
                    recipe_sha256=digest,
                    recipe_filename=(
                        recipe_path.name
                    ),
                    approval_id=(
                        approval.approval_id
                    ),
                    approval_filename=(
                        approval_path.name
                    ),
                    decision=approval.decision,
                    approved=(
                        verification.approved
                    ),
                    required_step_ids=(
                        verification.required_step_ids
                    ),
                    approved_step_ids=(
                        verification.approved_step_ids
                    ),
                    missing_step_ids=(
                        verification.missing_step_ids
                    ),
                    created_at=(
                        approval.created_at
                    ),
                    expires_at=(
                        approval.expires_at
                    ),
                    reason=verification.reason,
                )
            )

    approvals_without = [
        approval_path.name
        for approval_path, approval in approvals
        if approval.recipe_sha256
        not in recipe_digests
    ]

    matches.sort(
        key=lambda match: (
            match.recipe_id,
            match.recipe_filename,
            match.approval_filename,
        )
    )

    return RecipeApprovalInventory(
        matches=matches,
        recipes_without_matching_approval=(
            recipes_without
        ),
        approvals_without_matching_recipe=(
            approvals_without
        ),
        recipe_count=len(recipes),
        approval_count=len(approvals),
        valid_match_count=sum(
            1
            for match in matches
            if match.approved
        ),
    )

