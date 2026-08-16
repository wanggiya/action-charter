"""Append-only human approvals for exact recipes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from geoagent_harness.recipes.digest import (
    recipe_sha256,
)
from geoagent_harness.recipes.policy import (
    RecipePolicyError,
    validate_recipe_policy,
)
from geoagent_harness.recipes.schemas import (
    RecipeApprovalRecord,
    RecipeApprovalVerification,
    WorkflowRecipe,
)
from geoagent_harness.redaction import (
    redact_text,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    assess_schema_compatibility,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


MAX_RECIPE_APPROVAL_BYTES = 250_000


class RecipeApprovalError(RuntimeError):
    """Raised when recipe approval cannot be handled safely."""


def _approval_id(
    now: datetime,
) -> str:
    timestamp = now.astimezone(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    return (
        f"recipe-approval-{timestamp}-"
        f"{uuid.uuid4().hex[:8]}"
    ).lower()


def _safe_approval_path(
    *,
    path: Path,
    approval_root: Path,
) -> Path:
    root = approval_root.resolve()
    resolved = path.resolve()

    if resolved.parent != root:
        raise RecipeApprovalError(
            "recipe approval path escaped its "
            "approved root"
        )

    return resolved


def create_recipe_approval(
    *,
    recipe: WorkflowRecipe,
    registry: SkillRegistry,
    step_ids: list[str],
    decision: Literal["approved", "denied"],
    approver: str,
    reason: str,
    approval_root: Path,
    human_corrections: list[str] | None = None,
    expires_at: datetime | None = None,
    now: datetime | None = None,
    approval_id: str | None = None,
) -> tuple[RecipeApprovalRecord, Path]:
    """Create one append-only exact-recipe approval."""

    active_now = now or datetime.now(
        timezone.utc
    )

    try:
        validation = validate_recipe_policy(
            recipe,
            registry=registry,
        )
    except RecipePolicyError as exc:
        raise RecipeApprovalError(
            "recipe failed deterministic policy"
        ) from exc

    required = set(
        validation.approval_required_step_ids
    )

    if not required:
        raise RecipeApprovalError(
            "recipe has no approval-required steps"
        )

    if not step_ids:
        raise RecipeApprovalError(
            "at least one recipe step ID is required"
        )

    supplied = set(step_ids)
    invalid = sorted(supplied - required)

    if invalid:
        raise RecipeApprovalError(
            "approval references steps that do not "
            "require approval: "
            + ", ".join(invalid)
        )

    record = RecipeApprovalRecord(
        approval_id=(
            approval_id
            or _approval_id(active_now)
        ),
        recipe_sha256=recipe_sha256(recipe),
        decision=decision,
        step_ids=step_ids,
        approver=redact_text(approver),
        reason=redact_text(reason),
        human_corrections=[
            redact_text(correction)
            for correction in (
                human_corrections or []
            )
        ],
        created_at=active_now,
        expires_at=expires_at,
        secrets_redacted=True,
    )

    root = approval_root.resolve()

    try:
        root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise RecipeApprovalError(
            "recipe approval root could not "
            "be prepared"
        ) from exc

    path = _safe_approval_path(
        path=root / f"{record.approval_id}.json",
        approval_root=root,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            json.dump(
                record.model_dump(mode="json"),
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
    except FileExistsError as exc:
        raise RecipeApprovalError(
            "recipe approval already exists; "
            "overwriting is blocked"
        ) from exc
    except OSError as exc:
        raise RecipeApprovalError(
            "recipe approval could not be written"
        ) from exc

    return record, path


def load_recipe_approval(
    path: Path,
    *,
    approval_root: Path,
) -> RecipeApprovalRecord:
    """Load one recipe approval from its trusted root."""

    safe_path = _safe_approval_path(
        path=path,
        approval_root=approval_root,
    )

    if not safe_path.is_file():
        raise RecipeApprovalError(
            "recipe approval does not exist"
        )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise RecipeApprovalError(
            "recipe approval could not be inspected"
        ) from exc

    if size <= 0:
        raise RecipeApprovalError(
            "recipe approval is empty"
        )

    if size > MAX_RECIPE_APPROVAL_BYTES:
        raise RecipeApprovalError(
            "recipe approval exceeds the size limit"
        )

    try:
        text = safe_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RecipeApprovalError(
            "recipe approval is not UTF-8"
        ) from exc
    except OSError as exc:
        raise RecipeApprovalError(
            "recipe approval could not be read"
        ) from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RecipeApprovalError(
            "recipe approval is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeApprovalError(
            "recipe approval JSON must be an object"
        )

    version = payload.get("schema_version")

    if not isinstance(version, str):
        raise RecipeApprovalError(
            "recipe approval has no schema version"
        )

    compatibility = assess_schema_compatibility(
        artifact_type=ArtifactType.RECIPE_APPROVAL,
        artifact_version=version,
    )

    if not compatibility.readable:
        raise RecipeApprovalError(
            "recipe approval schema is unsupported"
        )

    try:
        approval = (
            RecipeApprovalRecord.model_validate(
                payload
            )
        )
    except ValidationError as exc:
        raise RecipeApprovalError(
            "recipe approval failed schema validation"
        ) from exc

    expected_path = _safe_approval_path(
        path=(
            approval_root.resolve()
            / f"{approval.approval_id}.json"
        ),
        approval_root=approval_root,
    )

    if safe_path != expected_path:
        raise RecipeApprovalError(
            "recipe approval filename does not "
            "match its approval ID"
        )

    return approval


def verify_recipe_approval(
    *,
    approval: RecipeApprovalRecord,
    recipe: WorkflowRecipe,
    registry: SkillRegistry,
    now: datetime | None = None,
) -> RecipeApprovalVerification:
    """Verify approval against an exact recipe and scope."""

    active_now = now or datetime.now(
        timezone.utc
    )

    try:
        validation = validate_recipe_policy(
            recipe,
            registry=registry,
        )
    except RecipePolicyError as exc:
        raise RecipeApprovalError(
            "recipe failed deterministic policy"
        ) from exc

    digest = recipe_sha256(recipe)
    required = (
        validation.approval_required_step_ids
    )

    if approval.recipe_sha256 != digest:
        return RecipeApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            recipe_sha256=digest,
            required_step_ids=required,
            approved_step_ids=approval.step_ids,
            missing_step_ids=required,
            reason=(
                "approval does not match the "
                "exact recipe"
            ),
        )

    if approval.decision != "approved":
        return RecipeApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            recipe_sha256=digest,
            required_step_ids=required,
            approved_step_ids=approval.step_ids,
            missing_step_ids=[],
            reason="approval decision is denied",
        )

    if (
        approval.expires_at is not None
        and active_now >= approval.expires_at
    ):
        return RecipeApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            recipe_sha256=digest,
            required_step_ids=required,
            approved_step_ids=approval.step_ids,
            missing_step_ids=[],
            reason="recipe approval has expired",
        )

    approved = set(approval.step_ids)
    required_set = set(required)

    invalid = sorted(
        approved - required_set
    )

    if invalid:
        return RecipeApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            recipe_sha256=digest,
            required_step_ids=required,
            approved_step_ids=approval.step_ids,
            missing_step_ids=[],
            reason=(
                "approval includes steps outside "
                "the required approval scope"
            ),
        )

    missing = [
        step_id
        for step_id in required
        if step_id not in approved
    ]

    if missing:
        return RecipeApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            recipe_sha256=digest,
            required_step_ids=required,
            approved_step_ids=approval.step_ids,
            missing_step_ids=missing,
            reason=(
                "approval is incomplete for the "
                "required recipe steps"
            ),
        )

    return RecipeApprovalVerification(
        approved=True,
        approval_id=approval.approval_id,
        recipe_sha256=digest,
        required_step_ids=required,
        approved_step_ids=approval.step_ids,
        missing_step_ids=[],
        reason=(
            "approval matches the exact recipe "
            "and complete write-step scope"
        ),
    )
