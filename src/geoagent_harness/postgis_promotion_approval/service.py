"""Safe loading and creation of PostGIS promotion approvals."""

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.postgis_promotion_approval.schemas import (
    APPROVAL_STEP_IDS,
    PostGISPromotionApproval,
)
from geoagent_harness.postgis_promotion_plan import (
    PostGISPromotionPlanResult,
    postgis_promotion_plan_sha256,
)
from geoagent_harness.redaction import redact_text


MAX_PLAN_BYTES = 2_000_000


class PostGISPromotionApprovalError(RuntimeError):
    """Raised when approval evidence is unsafe or inconsistent."""


def _canonical_sha256(value: object) -> str:
    payload = (
        value.model_dump(mode="json")  # type: ignore[attr-defined]
        if hasattr(value, "model_dump")
        else value
    )
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safe_file(path: Path, *, root: Path) -> Path:
    if root.is_symlink():
        raise PostGISPromotionApprovalError("approved root cannot be a symlink")
    try:
        safe_root = root.resolve(strict=True)
        if path.is_absolute():
            candidate = path
        else:
            direct = path.resolve()
            try:
                direct.relative_to(safe_root)
                candidate = direct
            except ValueError:
                candidate = safe_root / path
        if candidate.is_symlink() or candidate.parent.is_symlink():
            raise PostGISPromotionApprovalError("plan path cannot be a symlink")
        safe = candidate.resolve(strict=True)
        safe.relative_to(safe_root)
    except (OSError, ValueError) as exc:
        raise PostGISPromotionApprovalError(
            "promotion plan is unavailable beneath the approved root"
        ) from exc
    if safe.parent != safe_root or not safe.is_file():
        raise PostGISPromotionApprovalError(
            "promotion plan must be a direct file beneath the approved root"
        )
    return safe


def load_postgis_promotion_plan_result(
    plan_file: Path,
    *,
    plan_root: Path,
) -> PostGISPromotionPlanResult:
    """Load a plan result and verify its canonical plan digest."""
    safe = _safe_file(plan_file, root=plan_root)
    try:
        size = safe.stat().st_size
        if size < 1 or size > MAX_PLAN_BYTES:
            raise PostGISPromotionApprovalError(
                "promotion plan file has an invalid size"
            )
        payload: Any = json.loads(safe.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PostGISPromotionApprovalError(
                "promotion plan file must contain one JSON object"
            )
        result = PostGISPromotionPlanResult.model_validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise PostGISPromotionApprovalError(
            "promotion plan file failed validation"
        ) from exc
    digest = postgis_promotion_plan_sha256(result.plan)
    if result.plan_sha256 != digest:
        raise PostGISPromotionApprovalError(
            "promotion plan digest does not match canonical content"
        )
    plan = result.plan
    embedded_digests = {
        "assessment": (
            plan.assessment_sha256,
            _canonical_sha256(plan.assessment),
        ),
        "reference snapshot": (
            plan.reference_snapshot_sha256,
            _canonical_sha256(plan.assessment.comparison.reference),
        ),
        "candidate snapshot": (
            plan.candidate_snapshot_sha256,
            _canonical_sha256(plan.assessment.comparison.candidate),
        ),
    }
    for label, (claimed, observed) in embedded_digests.items():
        if claimed != observed:
            raise PostGISPromotionApprovalError(
                f"promotion plan {label} digest is invalid"
            )
    return result


def _approval_id(now: datetime) -> str:
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        f"postgis-promotion-approval-{stamp}-{uuid.uuid4().hex[:8]}"
    ).lower()


def create_postgis_promotion_approval(
    *,
    plan_result: PostGISPromotionPlanResult,
    decision: str,
    approver: str,
    reason: str,
    human_corrections: list[str] | None = None,
    expires_at: datetime | None = None,
    now: datetime | None = None,
    approval_id: str | None = None,
) -> PostGISPromotionApproval:
    """Create one typed decision without executing the approved plan."""
    digest = postgis_promotion_plan_sha256(plan_result.plan)
    if plan_result.plan_sha256 != digest:
        raise PostGISPromotionApprovalError("promotion plan digest changed")
    if decision not in {"approved", "denied"}:
        raise PostGISPromotionApprovalError("decision must be approved or denied")
    corrections = [redact_text(item) for item in (human_corrections or [])]
    active_now = now or datetime.now(timezone.utc)
    try:
        return PostGISPromotionApproval(
            approval_id=approval_id or _approval_id(active_now),
            plan_id=plan_result.plan.plan_id,
            plan_sha256=digest,
            assessment_sha256=plan_result.plan.assessment_sha256,
            decision=decision,
            approved_step_ids=(APPROVAL_STEP_IDS if decision == "approved" else []),
            approver=redact_text(approver),
            reason=redact_text(reason),
            human_corrections=corrections,
            created_at=active_now,
            expires_at=expires_at,
        )
    except ValidationError as exc:
        raise PostGISPromotionApprovalError(
            "promotion approval failed policy validation"
        ) from exc
