"""Independent read-only verification of a committed PostGIS rollback."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier
from geoagent_harness.postgis_inspection import PostGISInspectionRequest, inspect_postgis_table
from geoagent_harness.postgis_inspection.service import PostGISInspectionReader, PsycopgPostGISInspectionReader
from geoagent_harness.postgis_rollback_plan import load_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.postgis_rollback_approval import ROLLBACK_APPROVAL_STEP_IDS, load_postgis_rollback_approval, postgis_rollback_approval_sha256
from geoagent_harness.postgis_rollback_execution import load_postgis_rollback_execution, postgis_rollback_execution_sha256
from .schemas import PostGISRollbackVerificationResult

class PostGISRollbackVerificationError(RuntimeError): pass

def _profile(value) -> dict[str, Any]:
    return {"columns":[x.model_dump(mode="json") for x in value.columns],
            "primary_key":value.primary_key.columns if value.primary_key else None,
            "unique_keys":sorted(x.columns for x in value.unique_keys),
            "row_count":value.row_count,
            "geometry_columns":[x.model_dump(mode="json") for x in value.geometry_columns]}

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

    active = reader if reader is not None else PsycopgPostGISInspectionReader(settings)
    owns = reader is None
    try:
        # Keep the verifier independently readable while allowing deterministic
        # test doubles to provide one complete inspection per requested relation.
        # The production reader follows the bounded postgis_inspection API.
        if hasattr(active, "inspect") and not hasattr(active, "table_exists"):
            restored_reference = active.inspect(requests[0])
            restored_candidate = active.inspect(requests[1])
            archived = active.inspect(requests[2])
        else:
            restored_reference = inspect_postgis_table(request=requests[0], settings=settings, reader=active)
            restored_candidate = inspect_postgis_table(request=requests[1], settings=settings, reader=active)
            archived = inspect_postgis_table(request=requests[2], settings=settings, reader=active)
    except Exception as exc:
        raise PostGISRollbackVerificationError("independent rollback inspection failed") from exc
    finally:
        if owns:
            active.close()

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
