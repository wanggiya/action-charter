"""Digest-bound planning for a future PostGIS relation promotion."""

from __future__ import annotations

import hashlib
import json

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_change_assessment import (
    PostGISChangeDisposition,
    assess_postgis_change,
)
from geoagent_harness.postgis_comparison import (
    PostGISComparisonRequest,
    compare_postgis_tables,
)
from geoagent_harness.postgis_inspection import inspect_postgis_table
from geoagent_harness.postgis_inspection.service import (
    PostGISInspectionReader,
    PsycopgPostGISInspectionReader,
)
from geoagent_harness.postgis_promotion_plan.schemas import (
    PostGISPromotionOperation,
    PostGISPromotionPlan,
    PostGISPromotionPlanRequest,
    PostGISPromotionPlanResult,
)


class PostGISPromotionPlanError(RuntimeError):
    """Raised when promotion planning cannot complete safely."""


def _canonical_json(value: object) -> str:
    payload = (
        value.model_dump(mode="json")  # type: ignore[attr-defined]
        if hasattr(value, "model_dump")
        else value
    )
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def postgis_promotion_plan_sha256(plan: PostGISPromotionPlan) -> str:
    """Return the canonical identity of one promotion plan."""
    return _sha256(plan)


def plan_postgis_promotion(
    *,
    request: PostGISPromotionPlanRequest,
    settings: MCPSettings,
    reader: PostGISInspectionReader | None = None,
) -> PostGISPromotionPlanResult:
    """Reinspect and plan one exact promotion without modifying PostGIS."""
    active_reader = reader
    owns_reader = reader is None
    try:
        if active_reader is None:
            active_reader = PsycopgPostGISInspectionReader(settings)
        comparison = compare_postgis_tables(
            request=PostGISComparisonRequest(
                reference=request.reference,
                candidate=request.candidate,
            ),
            settings=settings,
            reader=active_reader,
        )
        assessment = assess_postgis_change(comparison)
        if assessment.disposition != PostGISChangeDisposition.COMPATIBLE:
            raise PostGISPromotionPlanError(
                "promotion planning requires a compatible change assessment"
            )
        archive = inspect_postgis_table(
            request=request.archive,
            settings=settings,
            reader=active_reader,
        )
        if archive.table_exists:
            raise PostGISPromotionPlanError(
                "archive relation already exists"
            )

        operations = [
            PostGISPromotionOperation(
                step_id="step_1_reverify_assessment",
                operation="reverify_assessment",
                requires_approval=False,
                database_mutation=False,
            ),
            PostGISPromotionOperation(
                step_id="step_2_lock_relations",
                operation="lock_relations",
                requires_approval=False,
                database_mutation=False,
            ),
            PostGISPromotionOperation(
                step_id="step_3_verify_archive_absent",
                operation="verify_archive_absent",
                requires_approval=False,
                database_mutation=False,
            ),
            PostGISPromotionOperation(
                step_id="step_4_archive_reference",
                operation="archive_reference",
                requires_approval=True,
                database_mutation=True,
            ),
            PostGISPromotionOperation(
                step_id="step_5_promote_candidate",
                operation="promote_candidate",
                requires_approval=True,
                database_mutation=True,
            ),
            PostGISPromotionOperation(
                step_id="step_6_validate_promoted_relation",
                operation="validate_promoted_relation",
                requires_approval=False,
                database_mutation=False,
            ),
        ]
        plan = PostGISPromotionPlan(
            plan_id=request.plan_id,
            assessment_sha256=_sha256(assessment),
            reference_snapshot_sha256=_sha256(comparison.reference),
            candidate_snapshot_sha256=_sha256(comparison.candidate),
            assessment=assessment,
            archive=archive,
            operations=operations,
            approval_required_step_ids=[
                "step_4_archive_reference",
                "step_5_promote_candidate",
            ],
        )
        return PostGISPromotionPlanResult(
            plan_sha256=postgis_promotion_plan_sha256(plan),
            plan=plan,
        )
    finally:
        if owns_reader and active_reader is not None:
            active_reader.close()
