"""Creation of decisions bound to exact immutable rollback plans."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import ValidationError
from geoagent_harness.redaction import redact_text
from geoagent_harness.postgis_rollback_plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from .schemas import PostGISRollbackApproval, ROLLBACK_APPROVAL_STEP_IDS


class PostGISRollbackApprovalError(RuntimeError): pass


def create_postgis_rollback_approval(*, rollback_plan_file: Path,
    rollback_plan_root: Path, decision: str, approver: str, reason: str,
    human_corrections: list[str] | None = None, expires_at: datetime | None = None,
    now: datetime | None = None, approval_id: str | None = None) -> PostGISRollbackApproval:
    try:
        plan = load_postgis_rollback_plan(rollback_plan_file, rollback_plan_root=rollback_plan_root)
    except Exception as exc:
        raise PostGISRollbackApprovalError("rollback plan could not be verified") from exc
    if decision not in {"approved", "denied"}:
        raise PostGISRollbackApprovalError("decision must be approved or denied")
    active_now = now or datetime.now(timezone.utc)
    if active_now.tzinfo is None or active_now.utcoffset() is None:
        raise PostGISRollbackApprovalError("approval time must be timezone-aware")
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    try:
        return PostGISRollbackApproval(
            approval_id=approval_id or f"postgis-rollback-approval-{stamp}-{uuid.uuid4().hex[:8]}",
            rollback_plan_id=plan.rollback_plan_id,
            rollback_plan_sha256=postgis_rollback_plan_sha256(plan),
            verification_sha256=plan.verification_sha256,
            decision=decision,
            approved_step_ids=ROLLBACK_APPROVAL_STEP_IDS if decision == "approved" else [],
            approver=redact_text(approver), reason=redact_text(reason),
            human_corrections=[redact_text(x) for x in (human_corrections or [])],
            created_at=active_now, expires_at=expires_at)
    except ValidationError as exc:
        raise PostGISRollbackApprovalError("rollback approval failed policy validation") from exc
