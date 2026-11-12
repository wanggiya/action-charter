"""Approval-gated transactional PostGIS relation promotion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path


from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.databases.postgis.promotion.approval import APPROVAL_STEP_IDS
from geoagent_harness.data.databases.postgis.promotion.approval import load_postgis_promotion_approval, postgis_promotion_approval_sha256
from geoagent_harness.data.databases.postgis.promotion.plan import postgis_promotion_plan_sha256
from geoagent_harness.data.databases.postgis.promotion.approval.service import load_postgis_promotion_plan_result
from geoagent_harness.data.databases.postgis.promotion.execution.schemas import PostGISPromotionExecutionResult


class PostGISPromotionExecutionError(RuntimeError):
    """Raised when promotion cannot be committed safely."""


from geoagent_harness.data.databases.postgis.lifecycle import RelationTransaction as PromotionTransaction, PsycopgRelationTransaction, check_authority, relation_requests, execute_change
from geoagent_harness.data.databases.postgis.attempts import RelationAttempt


class PsycopgPromotionTransaction(PsycopgRelationTransaction):
    """Compatibility name for the shared fixed relation driver."""
    def __init__(self, settings):
        try: super().__init__(settings)
        except Exception:
            raise PostGISPromotionExecutionError(
                'PostGIS promotion connection failed; connection details were redacted') from None


from geoagent_harness.core.policy.write_policy import guarded

@guarded
def execute_postgis_promotion(
    *, plan_file: Path, plan_root: Path, approval_file: Path,
    approval_root: Path, settings: MCPSettings,
    confirm_plan_sha256: str, confirm_approval_sha256: str,
    transaction: PromotionTransaction | None = None,
    now: datetime | None = None,
) -> PostGISPromotionExecutionResult:
    """Execute exactly two approved renames and commit only after validation."""
    if not settings.enable_write_tools:
        raise PostGISPromotionExecutionError("PostGIS write tools are disabled")
    try:
        plan_result = load_postgis_promotion_plan_result(plan_file, plan_root=plan_root)
        approval = load_postgis_promotion_approval(approval_file, approval_root=approval_root)
    except Exception as exc:
        raise PostGISPromotionExecutionError("promotion evidence could not be verified") from exc
    plan_digest = postgis_promotion_plan_sha256(plan_result.plan)
    approval_digest = postgis_promotion_approval_sha256(approval)
    active_now = now or datetime.now(timezone.utc)
    plan = plan_result.plan
    check_authority(kind='promotion', approval=approval, plan_digest=plan_digest,
        approval_digest=approval_digest, confirmed_plan=confirm_plan_sha256,
        confirmed_approval=confirm_approval_sha256, step_ids=APPROVAL_STEP_IDS,
        bindings=[(approval.plan_id, plan.plan_id, 'approval does not bind the promotion plan'),
                  (approval.plan_sha256, plan_digest, 'approval does not bind the promotion plan'),
                  (approval.assessment_sha256, plan.assessment_sha256, 'approval assessment digest does not match')],
        now=active_now, error=PostGISPromotionExecutionError)
    reference = plan.assessment.comparison.reference
    candidate = plan.assessment.comparison.candidate
    relation_requests((reference, candidate, plan.archive), settings, label='promotion', error=PostGISPromotionExecutionError)
    attempt = RelationAttempt(settings, 'promotion', plan_digest, approval_digest, PostGISPromotionExecutionError)
    promoted, _ = execute_change(kind='promotion', reference=reference, candidate=candidate,
        archive=plan.archive, settings=settings, transaction=transaction,
        factory=PsycopgPromotionTransaction, error=PostGISPromotionExecutionError, attempt=attempt)
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISPromotionExecutionResult(
        execution_id=f"postgis-promotion-execution-{stamp}-{uuid.uuid4().hex[:8]}",
        plan_id=plan.plan_id, plan_sha256=plan_digest,
        approval_id=approval.approval_id, approval_sha256=approval_digest,
        reference_before_sha256=plan.reference_snapshot_sha256,
        candidate_before_sha256=plan.candidate_snapshot_sha256,
        promoted_relation=promoted, approved_step_ids=approval.approved_step_ids,
    )
