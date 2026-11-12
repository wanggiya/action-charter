"""Approval-gated transactional restoration of a PostGIS promotion."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.databases.postgis.promotion.execution import PsycopgPromotionTransaction
from geoagent_harness.data.databases.postgis.rollback.plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.data.databases.postgis.rollback.approval import ROLLBACK_APPROVAL_STEP_IDS
from geoagent_harness.data.databases.postgis.rollback.approval import load_postgis_rollback_approval, postgis_rollback_approval_sha256
from geoagent_harness.data.databases.postgis.rollback.execution.schemas import PostGISRollbackExecutionResult


class PostGISRollbackExecutionError(RuntimeError): pass
from geoagent_harness.data.databases.postgis.lifecycle import RelationTransaction as RollbackTransaction, check_authority, relation_requests, execute_change
from geoagent_harness.data.databases.postgis.attempts import RelationAttempt

from geoagent_harness.core.policy.write_policy import guarded

@guarded
def execute_postgis_rollback(*,rollback_plan_file:Path,rollback_plan_root:Path,
    approval_file:Path,approval_root:Path,settings:MCPSettings,
    confirm_rollback_plan_sha256:str,confirm_approval_sha256:str,
    transaction:RollbackTransaction|None=None,now:datetime|None=None)->PostGISRollbackExecutionResult:
    if not settings.enable_write_tools: raise PostGISRollbackExecutionError("PostGIS write tools are disabled")
    try:
        plan=load_postgis_rollback_plan(rollback_plan_file,rollback_plan_root=rollback_plan_root)
        approval=load_postgis_rollback_approval(approval_file,approval_root=approval_root)
    except Exception as exc: raise PostGISRollbackExecutionError("rollback evidence could not be verified") from exc
    plan_digest=postgis_rollback_plan_sha256(plan); approval_digest=postgis_rollback_approval_sha256(approval)
    active_now=now or datetime.now(timezone.utc)
    check_authority(kind='rollback', approval=approval, plan_digest=plan_digest,
        approval_digest=approval_digest, confirmed_plan=confirm_rollback_plan_sha256,
        confirmed_approval=confirm_approval_sha256, step_ids=ROLLBACK_APPROVAL_STEP_IDS,
        bindings=[(approval.rollback_plan_id, plan.rollback_plan_id, 'approval does not bind the rollback plan'),
                  (approval.rollback_plan_sha256, plan_digest, 'approval does not bind the rollback plan'),
                  (approval.verification_sha256, plan.verification_sha256, 'approval does not bind the rollback plan')],
        now=active_now, error=PostGISRollbackExecutionError)
    reference,candidate,archive=plan.original_reference,plan.promoted_candidate,plan.archive_relation
    relation_requests((reference, candidate, archive), settings, label='rollback', error=PostGISRollbackExecutionError)
    attempt = RelationAttempt(settings, 'rollback', plan_digest, approval_digest, PostGISRollbackExecutionError)
    restored_reference, restored_candidate = execute_change(kind='rollback', reference=reference,
        candidate=candidate, archive=archive, settings=settings, transaction=transaction,
        factory=PsycopgPromotionTransaction, error=PostGISRollbackExecutionError, attempt=attempt)
    stamp=active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISRollbackExecutionResult(execution_id=f"postgis-rollback-execution-{stamp}-{uuid.uuid4().hex[:8]}",rollback_plan_id=plan.rollback_plan_id,rollback_plan_sha256=plan_digest,approval_id=approval.approval_id,approval_sha256=approval_digest,restored_reference=restored_reference,restored_candidate=restored_candidate,approved_step_ids=approval.approved_step_ids)
