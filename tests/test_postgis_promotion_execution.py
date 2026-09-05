import json
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_postgis_promotion_approval import NOW, plan_result

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_promotion_approval import (
    create_postgis_promotion_approval,
    persist_postgis_promotion_approval,
    postgis_promotion_approval_sha256,
)
from geoagent_harness.postgis_promotion_execution import (
    PostGISPromotionExecutionError,
    execute_postgis_promotion,
    load_postgis_promotion_execution,
    persist_postgis_promotion_execution,
)


class FakeTransaction:
    def __init__(self, inspections):
        self.inspections = iter(inspections)
        self.renames = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def lock(self, relations): self.locked = relations
    def inspect(self, request): return next(self.inspections)
    def rename(self, source, target): self.renames.append((source, target))
    def commit(self): self.committed = True
    def rollback(self): self.rolled_back = True
    def close(self): self.closed = True


def evidence(tmp_path: Path):
    result = plan_result()
    plan_root = tmp_path / "plans"
    plan_root.mkdir()
    plan_file = plan_root / "PLAN.json"
    plan_file.write_text(json.dumps(result.model_dump(mode="json")), encoding="utf-8")
    approval = create_postgis_promotion_approval(
        plan_result=result, decision="approved", approver="Jay Qi",
        reason="Approve exact scope.", now=NOW,
        approval_id="postgis-promotion-approval-20260904t180000z-1234abcd",
        expires_at=NOW + timedelta(hours=1),
    )
    approval_root = tmp_path / "approvals"
    stored = persist_postgis_promotion_approval(approval, approval_root=approval_root)
    settings = MCPSettings(
        input_root=tmp_path / "input", output_root=tmp_path / "output",
        enable_write_tools=True,
    )
    return result, approval, plan_file, plan_root, Path(stored.approval_file), approval_root, settings


def test_exact_promotion_commits_only_after_validation(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    reference = result.plan.assessment.comparison.reference
    candidate = result.plan.assessment.comparison.candidate
    archive = result.plan.archive
    promoted = candidate.model_copy(update={
        "target_schema": reference.target_schema,
        "target_table": reference.target_table,
    })
    transaction = FakeTransaction([reference, candidate, archive, promoted])
    outcome = execute_postgis_promotion(
        plan_file=plan_file, plan_root=plan_root,
        approval_file=approval_file, approval_root=approval_root,
        settings=settings, confirm_plan_sha256=result.plan_sha256,
        confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
        transaction=transaction, now=NOW + timedelta(minutes=1),
    )
    assert transaction.committed is True
    assert transaction.rolled_back is False
    assert transaction.closed is True
    assert transaction.renames == [
        (("agent_sandbox", "reference_layer"), ("agent_sandbox", "reference_archive")),
        (("agent_sandbox", "candidate_layer"), ("agent_sandbox", "reference_layer")),
    ]
    assert outcome.post_promotion_validated is True
    stored = persist_postgis_promotion_execution(
        outcome, execution_root=tmp_path / "executions"
    )
    assert load_postgis_promotion_execution(
        Path(stored.execution_file), execution_root=tmp_path / "executions"
    ) == outcome


def test_failed_post_validation_rolls_back(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    reference = result.plan.assessment.comparison.reference
    candidate = result.plan.assessment.comparison.candidate
    invalid_promoted = reference.model_copy(update={"row_count": 999})
    transaction = FakeTransaction([
        reference, candidate, result.plan.archive, invalid_promoted
    ])
    with pytest.raises(PostGISPromotionExecutionError, match="failed validation"):
        execute_postgis_promotion(
            plan_file=plan_file, plan_root=plan_root,
            approval_file=approval_file, approval_root=approval_root,
            settings=settings, confirm_plan_sha256=result.plan_sha256,
            confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
            transaction=transaction, now=NOW + timedelta(minutes=1),
        )
    assert transaction.committed is False
    assert transaction.rolled_back is True
    assert transaction.closed is True


def test_write_gate_fails_before_loading_evidence(tmp_path: Path):
    settings = MCPSettings(input_root=tmp_path, output_root=tmp_path)
    with pytest.raises(PostGISPromotionExecutionError, match="disabled"):
        execute_postgis_promotion(
            plan_file=Path("missing"), plan_root=Path("missing"),
            approval_file=Path("missing"), approval_root=Path("missing"),
            settings=settings, confirm_plan_sha256="a" * 64,
            confirm_approval_sha256="b" * 64,
        )


def test_expired_approval_fails_before_transaction(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    transaction = FakeTransaction([])
    with pytest.raises(PostGISPromotionExecutionError, match="expired"):
        execute_postgis_promotion(
            plan_file=plan_file, plan_root=plan_root,
            approval_file=approval_file, approval_root=approval_root,
            settings=settings, confirm_plan_sha256=result.plan_sha256,
            confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
            transaction=transaction, now=NOW + timedelta(hours=2),
        )
    assert transaction.committed is False
    assert transaction.rolled_back is False


def test_digest_confirmation_mismatch_fails_before_transaction(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    transaction = FakeTransaction([])
    with pytest.raises(PostGISPromotionExecutionError, match="confirmation"):
        execute_postgis_promotion(
            plan_file=plan_file, plan_root=plan_root,
            approval_file=approval_file, approval_root=approval_root,
            settings=settings, confirm_plan_sha256="f" * 64,
            confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
            transaction=transaction, now=NOW,
        )
    assert transaction.committed is False


def test_archive_conflict_rolls_back_without_rename(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    reference = result.plan.assessment.comparison.reference
    candidate = result.plan.assessment.comparison.candidate
    occupied_archive = result.plan.archive.model_copy(update={"status": "inspected", "table_exists": True, "row_count": 1, "warnings": []})
    transaction = FakeTransaction([reference, candidate, occupied_archive])
    with pytest.raises(PostGISPromotionExecutionError, match="now exists"):
        execute_postgis_promotion(
            plan_file=plan_file, plan_root=plan_root,
            approval_file=approval_file, approval_root=approval_root,
            settings=settings, confirm_plan_sha256=result.plan_sha256,
            confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
            transaction=transaction, now=NOW,
        )
    assert transaction.renames == []
    assert transaction.rolled_back is True


def test_naive_execution_time_fails_before_transaction(tmp_path: Path):
    result, approval, plan_file, plan_root, approval_file, approval_root, settings = evidence(tmp_path)
    transaction = FakeTransaction([])
    with pytest.raises(PostGISPromotionExecutionError, match="timezone-aware"):
        execute_postgis_promotion(
            plan_file=plan_file, plan_root=plan_root,
            approval_file=approval_file, approval_root=approval_root,
            settings=settings, confirm_plan_sha256=result.plan_sha256,
            confirm_approval_sha256=postgis_promotion_approval_sha256(approval),
            transaction=transaction, now=NOW.replace(tzinfo=None),
        )
    assert transaction.committed is False
