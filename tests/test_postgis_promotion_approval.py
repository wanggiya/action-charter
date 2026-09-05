import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geoagent_harness.postgis_change_assessment import assess_postgis_change
from geoagent_harness.postgis_comparison import PostGISComparisonResult
from geoagent_harness.postgis_inspection import PostGISInspectionResult
from geoagent_harness.postgis_promotion_approval import (
    PostGISPromotionApprovalError,
    PostGISPromotionApprovalStorageError,
    create_postgis_promotion_approval,
    load_postgis_promotion_approval,
    load_postgis_promotion_plan_result,
    persist_postgis_promotion_approval,
)
from geoagent_harness.postgis_promotion_plan import (
    PostGISPromotionOperation,
    PostGISPromotionPlan,
    PostGISPromotionPlanResult,
    postgis_promotion_plan_sha256,
)


NOW = datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc)


def inspection(table: str, *, exists: bool = True) -> PostGISInspectionResult:
    return PostGISInspectionResult(
        status="inspected" if exists else "not_found",
        target_schema="agent_sandbox",
        target_table=table,
        table_exists=exists,
        row_count=2 if exists else None,
        columns=[], primary_key=None, unique_keys=[], geometry_columns=[],
        warnings=[] if exists else ["Target table does not exist."],
    )


def plan_result() -> PostGISPromotionPlanResult:
    comparison = PostGISComparisonResult(
        status="matched", matches=True,
        reference=inspection("reference_layer"),
        candidate=inspection("candidate_layer"),
        differences=[], warnings=[],
    )
    assessment = assess_postgis_change(comparison)
    operations = [
        PostGISPromotionOperation(step_id="step_1_reverify_assessment", operation="reverify_assessment", requires_approval=False, database_mutation=False),
        PostGISPromotionOperation(step_id="step_2_lock_relations", operation="lock_relations", requires_approval=False, database_mutation=False),
        PostGISPromotionOperation(step_id="step_3_verify_archive_absent", operation="verify_archive_absent", requires_approval=False, database_mutation=False),
        PostGISPromotionOperation(step_id="step_4_archive_reference", operation="archive_reference", requires_approval=True, database_mutation=True),
        PostGISPromotionOperation(step_id="step_5_promote_candidate", operation="promote_candidate", requires_approval=True, database_mutation=True),
        PostGISPromotionOperation(step_id="step_6_validate_promoted_relation", operation="validate_promoted_relation", requires_approval=False, database_mutation=False),
    ]
    canonical_digest = lambda value: hashlib.sha256(json.dumps(
        value.model_dump(mode="json"), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    plan = PostGISPromotionPlan(
        plan_id="checkpoint15e-promotion-v1",
        assessment_sha256=canonical_digest(assessment),
        reference_snapshot_sha256=canonical_digest(comparison.reference),
        candidate_snapshot_sha256=canonical_digest(comparison.candidate),
        assessment=assessment,
        archive=inspection("reference_archive", exists=False),
        operations=operations,
        approval_required_step_ids=[
            "step_4_archive_reference", "step_5_promote_candidate"
        ],
    )
    return PostGISPromotionPlanResult(
        plan_sha256=postgis_promotion_plan_sha256(plan), plan=plan
    )


def test_approved_decision_binds_exact_digest_and_scope():
    result = plan_result()
    approval = create_postgis_promotion_approval(
        plan_result=result,
        decision="approved",
        approver="Jay Qi",
        reason="Approve the exact promotion.",
        now=NOW,
        approval_id="postgis-promotion-approval-20260904t180000z-1234abcd",
    )
    assert approval.plan_sha256 == result.plan_sha256
    assert approval.approved_step_ids == [
        "step_4_archive_reference", "step_5_promote_candidate"
    ]
    assert approval.execution_performed is False
    assert approval.database_modified is False


def test_approved_corrections_require_regenerated_plan():
    with pytest.raises(PostGISPromotionApprovalError, match="policy"):
        create_postgis_promotion_approval(
            plan_result=plan_result(), decision="approved",
            approver="Jay Qi", reason="Change it first.",
            human_corrections=["Use another archive."], now=NOW,
        )


def test_denied_decision_approves_no_steps():
    approval = create_postgis_promotion_approval(
        plan_result=plan_result(), decision="denied", approver="Jay Qi",
        reason="Do not promote.", human_corrections=["Reassess candidate."],
        now=NOW,
    )
    assert approval.approved_step_ids == []
    assert approval.approval_id.startswith(
        "postgis-promotion-approval-20260904t180000z-"
    )


def test_invalid_expiry_fails_closed():
    with pytest.raises(PostGISPromotionApprovalError, match="policy"):
        create_postgis_promotion_approval(
            plan_result=plan_result(), decision="approved", approver="Jay Qi",
            reason="Expired.", now=NOW, expires_at=NOW - timedelta(minutes=1),
        )


def test_plan_loader_rejects_changed_digest(tmp_path: Path):
    root = tmp_path / "plans"
    root.mkdir()
    payload = plan_result().model_dump(mode="json")
    payload["plan_sha256"] = "f" * 64
    path = root / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PostGISPromotionApprovalError, match="digest"):
        load_postgis_promotion_plan_result(path, plan_root=root)


def test_plan_loader_rejects_forged_embedded_digest(tmp_path: Path):
    root = tmp_path / "plans"
    root.mkdir()
    result = plan_result()
    payload = result.model_dump(mode="json")
    payload["plan"]["assessment_sha256"] = "f" * 64
    forged_plan = PostGISPromotionPlan.model_validate(payload["plan"])
    payload["plan_sha256"] = postgis_promotion_plan_sha256(forged_plan)
    path = root / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PostGISPromotionApprovalError, match="assessment digest"):
        load_postgis_promotion_plan_result(path, plan_root=root)


def test_plan_loader_rejects_path_escape(tmp_path: Path):
    root = tmp_path / "plans"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(PostGISPromotionApprovalError, match="approved root"):
        load_postgis_promotion_plan_result(outside, plan_root=root)


def test_storage_is_canonical_immutable_and_loadable(tmp_path: Path):
    approval = create_postgis_promotion_approval(
        plan_result=plan_result(), decision="approved", approver="Jay Qi",
        reason="Approve exact scope.", now=NOW,
        approval_id="postgis-promotion-approval-20260904t180000z-1234abcd",
    )
    root = tmp_path / "approvals"
    stored = persist_postgis_promotion_approval(approval, approval_root=root)
    loaded = load_postgis_promotion_approval(
        Path(stored.approval_file), approval_root=root
    )
    assert loaded == approval
    assert stored.approval_sha256 in stored.approval_directory
    with pytest.raises(PostGISPromotionApprovalStorageError, match="already exists"):
        persist_postgis_promotion_approval(approval, approval_root=root)


def test_storage_revalidates_mutated_approval_before_writing(tmp_path: Path):
    approval = create_postgis_promotion_approval(
        plan_result=plan_result(), decision="approved", approver="Jay Qi",
        reason="Approve exact scope.", now=NOW,
        approval_id="postgis-promotion-approval-20260904t180000z-1234abcd",
    )
    approval.approved_step_ids.clear()
    root = tmp_path / "approvals"

    with pytest.raises(
        PostGISPromotionApprovalStorageError,
        match="schema validation",
    ):
        persist_postgis_promotion_approval(approval, approval_root=root)

    assert not root.exists()
