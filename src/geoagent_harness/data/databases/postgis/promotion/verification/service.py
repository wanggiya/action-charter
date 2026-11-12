"""Independent read-only verification of a committed promotion."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest
from geoagent_harness.data.databases.postgis.inspection.service import PostGISInspectionReader
from geoagent_harness.data.databases.postgis.promotion.execution import load_postgis_promotion_execution, postgis_promotion_execution_sha256
from geoagent_harness.data.databases.postgis.promotion.approval import APPROVAL_STEP_IDS
from geoagent_harness.data.databases.postgis.promotion.approval.service import load_postgis_promotion_plan_result
from geoagent_harness.data.databases.postgis.promotion.verification.schemas import PostGISPromotionVerificationResult


class PostGISPromotionVerificationError(RuntimeError): pass


from geoagent_harness.data.databases.postgis.lifecycle import relation_profile as _profile, inspection_reader, read_relations


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
    requests = [PostGISInspectionRequest(target_schema=x.target_schema, target_table=x.target_table)
                for x in (reference, plan.archive)]
    with inspection_reader(settings, reader) as active:
        promoted, archived = read_relations(requests, settings, active)
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
