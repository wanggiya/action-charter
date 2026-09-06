"""Approval-gated transactional restoration of a PostGIS promotion."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier
from geoagent_harness.postgis_inspection import PostGISInspectionRequest, PostGISInspectionResult
from geoagent_harness.postgis_promotion_execution import PsycopgPromotionTransaction
from geoagent_harness.postgis_rollback_plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.postgis_rollback_approval import ROLLBACK_APPROVAL_STEP_IDS, load_postgis_rollback_approval, postgis_rollback_approval_sha256
from .schemas import PostGISRollbackExecutionResult


class PostGISRollbackExecutionError(RuntimeError): pass
class RollbackTransaction(Protocol):
    def lock(self,relations:list[tuple[str,str]])->None: ...
    def inspect(self,request:PostGISInspectionRequest)->PostGISInspectionResult: ...
    def rename(self,source:tuple[str,str],target:tuple[str,str])->None: ...
    def commit(self)->None: ...
    def rollback(self)->None: ...
    def close(self)->None: ...

def _profile(value):
    return {"columns":[x.model_dump(mode="json") for x in value.columns],"primary_key":value.primary_key.columns if value.primary_key else None,"unique_keys":sorted(x.columns for x in value.unique_keys),"row_count":value.row_count,"geometry_columns":[x.model_dump(mode="json") for x in value.geometry_columns]}

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
    if confirm_rollback_plan_sha256!=plan_digest or confirm_approval_sha256!=approval_digest: raise PostGISRollbackExecutionError("explicit digest confirmation does not match")
    active_now=now or datetime.now(timezone.utc)
    if active_now.tzinfo is None or active_now.utcoffset() is None: raise PostGISRollbackExecutionError("execution time must be timezone-aware")
    if approval.expires_at is not None:
        if approval.expires_at.tzinfo is None or approval.expires_at.utcoffset() is None:
            raise PostGISRollbackExecutionError("approval expiry must be timezone-aware")
        if active_now>=approval.expires_at: raise PostGISRollbackExecutionError("rollback approval has expired")
    if approval.decision!="approved" or approval.approved_step_ids!=ROLLBACK_APPROVAL_STEP_IDS: raise PostGISRollbackExecutionError("rollback is not approved for the exact scope")
    if approval.rollback_plan_id!=plan.rollback_plan_id or approval.rollback_plan_sha256!=plan_digest or approval.verification_sha256!=plan.verification_sha256: raise PostGISRollbackExecutionError("approval does not bind the rollback plan")
    reference,candidate,archive=plan.original_reference,plan.promoted_candidate,plan.archive_relation
    requests=[PostGISInspectionRequest(target_schema=x.target_schema,target_table=x.target_table) for x in (reference,candidate,archive)]
    for request in requests:
        validate_identifier(request.target_schema,label="target_schema"); validate_identifier(request.target_table,label="target_table")
        if request.target_schema not in settings.allowed_schemas: raise PostGISRollbackExecutionError("rollback schema is not allowlisted")
    try:
        active=transaction or PsycopgPromotionTransaction(settings)
    except Exception as exc:
        raise PostGISRollbackExecutionError("PostGIS rollback connection failed; details were redacted") from exc
    committed=False
    try:
        active.lock([(reference.target_schema,reference.target_table),(archive.target_schema,archive.target_table)])
        observed_reference=active.inspect(requests[0]); observed_candidate=active.inspect(requests[1]); observed_archive=active.inspect(requests[2])
        if not observed_reference.table_exists or _profile(observed_reference)!=_profile(candidate): raise PostGISRollbackExecutionError("promoted reference changed")
        if observed_candidate.table_exists: raise PostGISRollbackExecutionError("original candidate identity now exists")
        if not observed_archive.table_exists or _profile(observed_archive)!=_profile(reference): raise PostGISRollbackExecutionError("archived reference changed")
        active.rename((reference.target_schema,reference.target_table),(candidate.target_schema,candidate.target_table))
        active.rename((archive.target_schema,archive.target_table),(reference.target_schema,reference.target_table))
        restored_reference=active.inspect(requests[0]); restored_candidate=active.inspect(requests[1])
        if _profile(restored_reference)!=_profile(reference) or _profile(restored_candidate)!=_profile(candidate): raise PostGISRollbackExecutionError("restored relations failed validation")
        active.commit(); committed=True
    except Exception as exc:
        if not committed: active.rollback()
        if isinstance(exc,PostGISRollbackExecutionError): raise
        raise PostGISRollbackExecutionError("PostGIS rollback failed and was rolled back; details were redacted") from None
    finally:
        try: active.close()
        except Exception:
            if not committed: raise PostGISRollbackExecutionError("PostGIS rollback connection could not be closed safely") from None
    stamp=active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISRollbackExecutionResult(execution_id=f"postgis-rollback-execution-{stamp}-{uuid.uuid4().hex[:8]}",rollback_plan_id=plan.rollback_plan_id,rollback_plan_sha256=plan_digest,approval_id=approval.approval_id,approval_sha256=approval_digest,restored_reference=restored_reference,restored_candidate=restored_candidate,approved_step_ids=approval.approved_step_ids)
