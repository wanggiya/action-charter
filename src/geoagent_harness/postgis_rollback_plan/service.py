"""Evidence-bound planning for a future PostGIS promotion rollback."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from geoagent_harness.postgis_promotion_approval.service import (
    load_postgis_promotion_plan_result,
)
from geoagent_harness.postgis_promotion_execution import (
    load_postgis_promotion_execution,
    postgis_promotion_execution_sha256,
)
from geoagent_harness.postgis_promotion_plan import postgis_promotion_plan_sha256
from geoagent_harness.postgis_promotion_verification import (
    load_postgis_promotion_verification,
    postgis_promotion_verification_sha256,
)

from .schemas import PostGISRollbackOperation, PostGISRollbackPlan


class PostGISRollbackPlanError(RuntimeError):
    """Raised when rollback planning cannot bind trusted evidence."""


def _profile(value: object) -> dict[str, object]:
    """Return the identity-independent facts used by promotion verification."""
    return {
        "columns": [item.model_dump(mode="json") for item in value.columns],
        "primary_key": value.primary_key.columns if value.primary_key else None,
        "unique_keys": sorted(item.columns for item in value.unique_keys),
        "row_count": value.row_count,
        "geometry_columns": [
            item.model_dump(mode="json") for item in value.geometry_columns
        ],
    }


def plan_postgis_rollback(
    *,
    plan_file: Path,
    plan_root: Path,
    execution_file: Path,
    execution_root: Path,
    verification_file: Path,
    verification_root: Path,
    now: datetime | None = None,
) -> PostGISRollbackPlan:
    """Create a non-mutating plan from one exact verified promotion chain."""
    try:
        plan_result = load_postgis_promotion_plan_result(plan_file, plan_root=plan_root)
        execution = load_postgis_promotion_execution(
            execution_file, execution_root=execution_root
        )
        verification = load_postgis_promotion_verification(
            verification_file, verification_root=verification_root
        )
    except Exception as exc:
        raise PostGISRollbackPlanError(
            "rollback source evidence could not be verified"
        ) from exc

    promotion_plan = plan_result.plan
    plan_digest = postgis_promotion_plan_sha256(promotion_plan)
    execution_digest = postgis_promotion_execution_sha256(execution)
    verification_digest = postgis_promotion_verification_sha256(verification)
    if plan_result.plan_sha256 != plan_digest:
        raise PostGISRollbackPlanError("promotion plan digest does not match")
    if (
        execution.plan_id != promotion_plan.plan_id
        or execution.plan_sha256 != plan_digest
    ):
        raise PostGISRollbackPlanError("execution does not bind the promotion plan")
    if (
        verification.status != "verified"
        or verification.findings
        or verification.plan_id != promotion_plan.plan_id
        or verification.plan_sha256 != plan_digest
        or verification.execution_id != execution.execution_id
        or verification.execution_sha256 != execution_digest
    ):
        raise PostGISRollbackPlanError(
            "verification does not prove the exact promotion execution"
        )

    reference = promotion_plan.assessment.comparison.reference
    candidate = promotion_plan.assessment.comparison.candidate
    archive = verification.archived_relation
    if (
        (verification.promoted_relation.target_schema, verification.promoted_relation.target_table)
        != (reference.target_schema, reference.target_table)
        or (archive.target_schema, archive.target_table)
        != (promotion_plan.archive.target_schema, promotion_plan.archive.target_table)
    ):
        raise PostGISRollbackPlanError("verified relation identities do not match the plan")
    if (
        _profile(verification.promoted_relation) != _profile(candidate)
        or _profile(archive) != _profile(reference)
    ):
        raise PostGISRollbackPlanError(
            "verified relation profiles do not match the promotion snapshots"
        )

    active_now = now or datetime.now(timezone.utc)
    if active_now.tzinfo is None or active_now.utcoffset() is None:
        raise PostGISRollbackPlanError("planning time must be timezone-aware")
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    operations = [
        PostGISRollbackOperation(step_id="step_1_reverify_evidence", operation="reverify_evidence", requires_approval=False, database_mutation=False),
        PostGISRollbackOperation(step_id="step_2_lock_relations", operation="lock_relations", requires_approval=False, database_mutation=False),
        PostGISRollbackOperation(step_id="step_3_verify_candidate_absent", operation="verify_candidate_absent", requires_approval=False, database_mutation=False),
        PostGISRollbackOperation(step_id="step_4_restore_candidate", operation="restore_candidate", requires_approval=True, database_mutation=True),
        PostGISRollbackOperation(step_id="step_5_restore_reference", operation="restore_reference", requires_approval=True, database_mutation=True),
        PostGISRollbackOperation(step_id="step_6_validate_restored_relations", operation="validate_restored_relations", requires_approval=False, database_mutation=False),
    ]
    return PostGISRollbackPlan(
        rollback_plan_id=f"postgis-rollback-plan-{stamp}-{uuid.uuid4().hex[:8]}",
        promotion_plan_id=promotion_plan.plan_id,
        promotion_plan_sha256=plan_digest,
        execution_id=execution.execution_id,
        execution_sha256=execution_digest,
        verification_id=verification.verification_id,
        verification_sha256=verification_digest,
        original_reference=reference,
        promoted_candidate=candidate,
        archive_relation=archive,
        operations=operations,
        approval_required_step_ids=[
            "step_4_restore_candidate",
            "step_5_restore_reference",
        ],
    )
