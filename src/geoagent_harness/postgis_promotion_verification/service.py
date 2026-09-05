"""Independent read-only verification of a committed promotion."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_inspection import PostGISInspectionRequest, inspect_postgis_table
from geoagent_harness.postgis_inspection.service import PostGISInspectionReader, PsycopgPostGISInspectionReader
from geoagent_harness.postgis_promotion_execution import load_postgis_promotion_execution, postgis_promotion_execution_sha256
from geoagent_harness.postgis_promotion_approval import APPROVAL_STEP_IDS
from geoagent_harness.postgis_promotion_approval.service import load_postgis_promotion_plan_result
from .schemas import PostGISPromotionVerificationResult


class PostGISPromotionVerificationError(RuntimeError): pass


def _profile(value) -> dict[str, Any]:
    return {"columns":[x.model_dump(mode="json") for x in value.columns],
            "primary_key":value.primary_key.columns if value.primary_key else None,
            "unique_keys":sorted(x.columns for x in value.unique_keys),
            "row_count":value.row_count,
            "geometry_columns":[x.model_dump(mode="json") for x in value.geometry_columns]}


def verify_postgis_promotion(*, execution_file: Path, execution_root: Path,
    plan_file: Path, plan_root: Path, settings: MCPSettings,
    reader: PostGISInspectionReader | None = None,
    now: datetime | None = None) -> PostGISPromotionVerificationResult:
    try:
        execution = load_postgis_promotion_execution(execution_file, execution_root=execution_root)
        plan_result = load_postgis_promotion_plan_result(plan_file, plan_root=plan_root)
    except Exception as exc:
        raise PostGISPromotionVerificationError("verification evidence could not be loaded") from exc
    digest = postgis_promotion_execution_sha256(execution)
    if execution.plan_id != plan_result.plan.plan_id or execution.plan_sha256 != plan_result.plan_sha256:
        raise PostGISPromotionVerificationError("execution does not bind the supplied plan")
    plan = plan_result.plan
    if (execution.reference_before_sha256 != plan.reference_snapshot_sha256 or
        execution.candidate_before_sha256 != plan.candidate_snapshot_sha256 or
        execution.approved_step_ids != APPROVAL_STEP_IDS):
        raise PostGISPromotionVerificationError("execution scope or snapshots do not bind the supplied plan")
    reference = plan.assessment.comparison.reference
    candidate = plan.assessment.comparison.candidate
    active = reader or PsycopgPostGISInspectionReader(settings)
    owns = reader is None
    try:
        promoted = inspect_postgis_table(request=PostGISInspectionRequest(target_schema=reference.target_schema,target_table=reference.target_table), settings=settings, reader=active)
        archived = inspect_postgis_table(request=PostGISInspectionRequest(target_schema=plan.archive.target_schema,target_table=plan.archive.target_table), settings=settings, reader=active)
    finally:
        if owns: active.close()
    findings=[]
    if not promoted.table_exists or _profile(promoted) != _profile(candidate): findings.append("promoted_relation_mismatch")
    if not archived.table_exists or _profile(archived) != _profile(reference): findings.append("archived_relation_mismatch")
    stamp=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISPromotionVerificationResult(
        verification_id=f"postgis-promotion-verification-{stamp}-{uuid.uuid4().hex[:8]}",
        execution_id=execution.execution_id, execution_sha256=digest,
        plan_id=execution.plan_id, plan_sha256=execution.plan_sha256,
        status="failed" if findings else "verified", findings=findings,
        promoted_relation=promoted, archived_relation=archived)
