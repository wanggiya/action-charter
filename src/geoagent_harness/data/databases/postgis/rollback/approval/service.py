"""Creation of decisions bound to exact immutable rollback plans."""
from datetime import datetime, timezone
from pathlib import Path
from pydantic import ValidationError
from geoagent_harness.data.databases.postgis.rollback.plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.data.databases.postgis.rollback.approval.schemas import PostGISRollbackApproval, ROLLBACK_APPROVAL_STEP_IDS


class PostGISRollbackApprovalError(RuntimeError): pass


def create_postgis_rollback_approval(*, rollback_plan_file: Path,
    rollback_plan_root: Path, decision: str, approver: str, reason: str,
    human_corrections: list[str] | None = None, expires_at: datetime | None = None,
    now: datetime | None = None, approval_id: str | None = None) -> PostGISRollbackApproval:
    try:
        plan = load_postgis_rollback_plan(rollback_plan_file, rollback_plan_root=rollback_plan_root)
    except Exception as exc:
        raise PostGISRollbackApprovalError("rollback plan could not be verified") from exc
    active_now = now or datetime.now(timezone.utc)
    from geoagent_harness.data.databases.postgis.lifecycle import approval_fields
    try:
        return PostGISRollbackApproval(
            rollback_plan_id=plan.rollback_plan_id,
            rollback_plan_sha256=postgis_rollback_plan_sha256(plan),
            verification_sha256=plan.verification_sha256,
            **approval_fields(kind='rollback', decision=decision, approver=approver, reason=reason,
                corrections=human_corrections, expires_at=expires_at, now=active_now,
                approval_id=approval_id, step_ids=ROLLBACK_APPROVAL_STEP_IDS, error=PostGISRollbackApprovalError))
    except ValidationError as exc:
        raise PostGISRollbackApprovalError("rollback approval failed policy validation") from exc
