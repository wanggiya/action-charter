import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.postgis_promotion_execution import (
    PostGISPromotionExecutionResult,
    persist_postgis_promotion_execution,
    postgis_promotion_execution_sha256,
)
from geoagent_harness.postgis_promotion_verification import (
    PostGISPromotionVerificationResult,
    persist_postgis_promotion_verification,
)
from geoagent_harness.postgis_rollback_plan import (
    PostGISRollbackPlan,
    PostGISRollbackPlanError,
    PostGISRollbackPlanStorageError,
    load_postgis_rollback_plan,
    persist_postgis_rollback_plan,
    plan_postgis_rollback,
)
from tests.test_postgis_promotion_approval import plan_result


NOW = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


def evidence(tmp_path: Path, *, status: str = "verified", mismatch: bool = False):
    result = plan_result()
    plan_root = tmp_path / "plans"
    plan_root.mkdir()
    plan_file = plan_root / "PLAN.json"
    plan_file.write_text(json.dumps(result.model_dump(mode="json")), encoding="utf-8")
    reference = result.plan.assessment.comparison.reference
    candidate = result.plan.assessment.comparison.candidate
    promoted = candidate.model_copy(update={
        "target_schema": reference.target_schema,
        "target_table": reference.target_table,
    })
    archive = reference.model_copy(update={
        "target_schema": result.plan.archive.target_schema,
        "target_table": result.plan.archive.target_table,
        "row_count": 99 if mismatch else reference.row_count,
    })
    execution = PostGISPromotionExecutionResult(
        execution_id="postgis-promotion-execution-20260906t100000z-1234abcd",
        plan_id=result.plan.plan_id,
        plan_sha256=result.plan_sha256,
        approval_id="postgis-promotion-approval-20260906t090000z-1234abcd",
        approval_sha256="a" * 64,
        reference_before_sha256=result.plan.reference_snapshot_sha256,
        candidate_before_sha256=result.plan.candidate_snapshot_sha256,
        promoted_relation=promoted,
        approved_step_ids=["step_4_archive_reference", "step_5_promote_candidate"],
    )
    execution_root = tmp_path / "executions"
    stored_execution = persist_postgis_promotion_execution(
        execution, execution_root=execution_root
    )
    findings = [] if status == "verified" else ["promoted_relation_mismatch"]
    verification = PostGISPromotionVerificationResult(
        verification_id="postgis-promotion-verification-20260906t110000z-1234abcd",
        execution_id=execution.execution_id,
        execution_sha256=postgis_promotion_execution_sha256(execution),
        plan_id=result.plan.plan_id,
        plan_sha256=result.plan_sha256,
        status=status,
        findings=findings,
        promoted_relation=promoted,
        archived_relation=archive,
    )
    verification_root = tmp_path / "verifications"
    verification_file = persist_postgis_promotion_verification(
        verification, verification_root=verification_root
    )
    return {
        "plan_file": plan_file, "plan_root": plan_root,
        "execution_file": Path(stored_execution.execution_file),
        "execution_root": execution_root,
        "verification_file": verification_file,
        "verification_root": verification_root,
    }


def create_plan(tmp_path: Path):
    values = evidence(tmp_path)
    return plan_postgis_rollback(**values, now=NOW)


def test_verified_chain_creates_exact_non_mutating_plan(tmp_path: Path):
    plan = create_plan(tmp_path)
    assert [item.operation for item in plan.operations] == [
        "reverify_evidence", "lock_relations", "verify_candidate_absent",
        "restore_candidate", "restore_reference", "validate_restored_relations",
    ]
    assert plan.approval_required_step_ids == [
        "step_4_restore_candidate", "step_5_restore_reference"
    ]
    assert plan.database_modified is False
    assert plan.execution_performed is False
    assert plan.model_called is False


def test_failed_verification_cannot_produce_plan(tmp_path: Path):
    values = evidence(tmp_path, status="failed")
    with pytest.raises(PostGISRollbackPlanError, match="does not prove"):
        plan_postgis_rollback(**values, now=NOW)


def test_verified_claim_with_mismatched_profile_fails_closed(tmp_path: Path):
    with pytest.raises(PostGISRollbackPlanError, match="profiles"):
        plan_postgis_rollback(**evidence(tmp_path, mismatch=True), now=NOW)


def test_naive_planning_time_fails_closed(tmp_path: Path):
    with pytest.raises(PostGISRollbackPlanError, match="timezone-aware"):
        plan_postgis_rollback(**evidence(tmp_path), now=NOW.replace(tzinfo=None))


def test_choreography_cannot_be_reordered(tmp_path: Path):
    payload = create_plan(tmp_path).model_dump(mode="json")
    payload["operations"][3], payload["operations"][4] = (
        payload["operations"][4], payload["operations"][3]
    )
    with pytest.raises(ValidationError, match="choreography"):
        PostGISRollbackPlan.model_validate(payload)


def test_storage_is_immutable_and_loadable(tmp_path: Path):
    value = create_plan(tmp_path)
    root = tmp_path / "rollback-plans"
    stored = persist_postgis_rollback_plan(value, rollback_plan_root=root)
    assert load_postgis_rollback_plan(
        Path(stored.rollback_plan_file), rollback_plan_root=root
    ) == value
    with pytest.raises(PostGISRollbackPlanStorageError, match="already exists"):
        persist_postgis_rollback_plan(value, rollback_plan_root=root)


def test_storage_rejects_path_escape(tmp_path: Path):
    root = tmp_path / "rollback-plans"
    root.mkdir()
    outside = tmp_path / "ROLLBACK_PLAN.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(PostGISRollbackPlanStorageError, match="invalid"):
        load_postgis_rollback_plan(outside, rollback_plan_root=root)
