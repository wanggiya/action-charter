"""Independent read-only verification of a committed PostGIS rollback."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier
from geoagent_harness.postgis.inspection import PostGISInspectionRequest
from geoagent_harness.postgis.inspection.service import PostGISInspectionReader
from geoagent_harness.postgis.rollback.plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.postgis.rollback.approval import ROLLBACK_APPROVAL_STEP_IDS, load_postgis_rollback_approval, postgis_rollback_approval_sha256
from geoagent_harness.postgis.rollback.execution import load_postgis_rollback_execution, postgis_rollback_execution_sha256
from .schemas import PostGISRollbackVerificationResult

class PostGISRollbackVerificationError(RuntimeError): pass

from geoagent_harness.postgis.lifecycle import relation_profile as _profile, inspection_reader, read_relations


def verify_postgis_rollback(*, execution_file: Path, execution_root: Path,
    rollback_plan_file: Path, rollback_plan_root: Path,
    approval_file: Path, approval_root: Path, settings: MCPSettings,
    reader: PostGISInspectionReader | None = None,
    now: datetime | None = None) -> PostGISRollbackVerificationResult:
    try:
        execution = load_postgis_rollback_execution(execution_file, execution_root=execution_root)
        plan = load_postgis_rollback_plan(rollback_plan_file, rollback_plan_root=rollback_plan_root)
        approval = load_postgis_rollback_approval(approval_file, approval_root=approval_root)
    except Exception as exc:
        raise PostGISRollbackVerificationError("rollback verification evidence could not be loaded") from exc

    execution_digest = postgis_rollback_execution_sha256(execution)
    plan_digest = postgis_rollback_plan_sha256(plan)
    approval_digest = postgis_rollback_approval_sha256(approval)
    if execution.rollback_plan_id != plan.rollback_plan_id or execution.rollback_plan_sha256 != plan_digest:
        raise PostGISRollbackVerificationError("rollback execution does not bind the supplied plan")
    if execution.approval_id != approval.approval_id or execution.approval_sha256 != approval_digest:
        raise PostGISRollbackVerificationError("rollback execution does not bind the supplied approval")
    if (approval.rollback_plan_id != plan.rollback_plan_id or
        approval.rollback_plan_sha256 != plan_digest or
        approval.verification_sha256 != plan.verification_sha256 or
        approval.decision != "approved" or
        approval.approved_step_ids != ROLLBACK_APPROVAL_STEP_IDS):
        raise PostGISRollbackVerificationError("rollback approval or scope does not bind the supplied plan")
    if execution.approved_step_ids != ROLLBACK_APPROVAL_STEP_IDS:
        raise PostGISRollbackVerificationError("rollback execution scope is not exact")
    if not execution.transaction_committed or not execution.rollback_performed or not execution.database_modified:
        raise PostGISRollbackVerificationError("rollback execution evidence does not prove a committed mutation")

    reference = plan.original_reference
    candidate = plan.promoted_candidate
    archive = plan.archive_relation
    requests = [
        PostGISInspectionRequest(target_schema=x.target_schema, target_table=x.target_table)
        for x in (reference, candidate, archive)
    ]
    for request in requests:
        validate_identifier(request.target_schema, label="target_schema")
        validate_identifier(request.target_table, label="target_table")
        if request.target_schema not in settings.allowed_schemas:
            raise PostGISRollbackVerificationError("rollback verification schema is not allowlisted")

    try:
        with inspection_reader(settings, reader) as active:
            restored_reference, restored_candidate, archived = read_relations(requests, settings, active)
    except Exception as exc:
        raise PostGISRollbackVerificationError('independent rollback inspection failed') from exc

    findings = []
    if not restored_reference.table_exists or _profile(restored_reference) != _profile(reference):
        findings.append("restored_reference_relation_mismatch")
    if not restored_candidate.table_exists or _profile(restored_candidate) != _profile(candidate):
        findings.append("restored_candidate_relation_mismatch")
    if archived.table_exists:
        findings.append("archive_relation_still_exists")

    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISRollbackVerificationResult(
        verification_id=f"postgis-rollback-verification-{stamp}-{uuid.uuid4().hex[:8]}",
        execution_id=execution.execution_id, execution_sha256=execution_digest,
        rollback_plan_id=plan.rollback_plan_id, rollback_plan_sha256=plan_digest,
        approval_id=approval.approval_id, approval_sha256=approval_digest,
        status="failed" if findings else "verified", findings=findings,
        restored_reference_relation=restored_reference,
        restored_candidate_relation=restored_candidate,
        archive_relation=archived,
    )
