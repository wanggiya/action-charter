from datetime import timedelta
from pathlib import Path
import pytest
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_inspection import PostGISInspectionResult
from geoagent_harness.postgis_rollback_plan import persist_postgis_rollback_plan,postgis_rollback_plan_sha256
from geoagent_harness.postgis_rollback_approval import (PostGISRollbackApprovalError,create_postgis_rollback_approval,load_postgis_rollback_approval,persist_postgis_rollback_approval,postgis_rollback_approval_sha256)
from geoagent_harness.postgis_rollback_execution import (PostGISRollbackExecutionError,execute_postgis_rollback,load_postgis_rollback_execution,persist_postgis_rollback_execution)
from tests.test_postgis_rollback_plan import NOW,create_plan


class FakeTransaction:
    def __init__(self,inspections): self.inspections=iter(inspections); self.renames=[]; self.committed=False; self.rolled_back=False; self.closed=False
    def lock(self,relations): self.locked=relations
    def inspect(self,request): return next(self.inspections)
    def rename(self,source,target): self.renames.append((source,target))
    def commit(self): self.committed=True
    def rollback(self): self.rolled_back=True
    def close(self): self.closed=True


def missing_like(value):
    return PostGISInspectionResult(status="not_found",target_schema=value.target_schema,target_table=value.target_table,table_exists=False,columns=[],primary_key=None,unique_keys=[],geometry_columns=[],warnings=["Target table does not exist."])


def approved_evidence(tmp_path:Path):
    plan=create_plan(tmp_path); plan_root=tmp_path/"rollback-plans"; stored_plan=persist_postgis_rollback_plan(plan,rollback_plan_root=plan_root)
    approval=create_postgis_rollback_approval(rollback_plan_file=Path(stored_plan.rollback_plan_file),rollback_plan_root=plan_root,decision="approved",approver="Jay Qi",reason="Restore exact relations.",now=NOW,expires_at=NOW+timedelta(hours=1),approval_id="postgis-rollback-approval-20260906t120000z-1234abcd")
    approval_root=tmp_path/"rollback-approvals"; stored_approval=persist_postgis_rollback_approval(approval,approval_root=approval_root)
    settings=MCPSettings(input_root=tmp_path/"input",output_root=tmp_path/"output",enable_write_tools=True)
    return plan,plan_root,Path(stored_plan.rollback_plan_file),approval,approval_root,Path(stored_approval.approval_file),settings


def test_approval_binds_exact_plan_and_round_trips(tmp_path:Path):
    plan,_,_,approval,root,path,_=approved_evidence(tmp_path)
    assert approval.rollback_plan_sha256==postgis_rollback_plan_sha256(plan)
    assert approval.approved_step_ids==["step_4_restore_candidate","step_5_restore_reference"]
    assert load_postgis_rollback_approval(path,approval_root=root)==approval


def test_approved_corrections_fail_closed(tmp_path:Path):
    plan=create_plan(tmp_path); root=tmp_path/"plans"; stored=persist_postgis_rollback_plan(plan,rollback_plan_root=root)
    with pytest.raises(PostGISRollbackApprovalError,match="policy"):
        create_postgis_rollback_approval(rollback_plan_file=Path(stored.rollback_plan_file),rollback_plan_root=root,decision="approved",approver="Jay",reason="Change",human_corrections=["Different target"],now=NOW)


def test_exact_rollback_commits_after_validation(tmp_path:Path):
    plan,plan_root,plan_file,approval,approval_root,approval_file,settings=approved_evidence(tmp_path)
    ref=plan.original_reference; candidate=plan.promoted_candidate; archive=plan.archive_relation
    promoted=candidate.model_copy(update={"target_schema":ref.target_schema,"target_table":ref.target_table})
    restored_ref=ref; restored_candidate=candidate
    transaction=FakeTransaction([promoted,missing_like(candidate),archive,restored_ref,restored_candidate])
    result=execute_postgis_rollback(rollback_plan_file=plan_file,rollback_plan_root=plan_root,approval_file=approval_file,approval_root=approval_root,settings=settings,confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(plan),confirm_approval_sha256=postgis_rollback_approval_sha256(approval),transaction=transaction,now=NOW+timedelta(minutes=1))
    assert transaction.committed and not transaction.rolled_back and transaction.closed
    assert transaction.renames==[(('agent_sandbox','reference_layer'),('agent_sandbox','candidate_layer')),(('agent_sandbox','reference_archive'),('agent_sandbox','reference_layer'))]
    root=tmp_path/"rollback-executions"; stored=persist_postgis_rollback_execution(result,execution_root=root)
    assert load_postgis_rollback_execution(Path(stored.execution_file),execution_root=root)==result


def test_candidate_conflict_rolls_back_before_rename(tmp_path:Path):
    plan,plan_root,plan_file,approval,approval_root,approval_file,settings=approved_evidence(tmp_path)
    ref=plan.original_reference; candidate=plan.promoted_candidate
    promoted=candidate.model_copy(update={"target_schema":ref.target_schema,"target_table":ref.target_table})
    transaction=FakeTransaction([promoted,candidate,plan.archive_relation])
    with pytest.raises(PostGISRollbackExecutionError,match="candidate identity"):
        execute_postgis_rollback(rollback_plan_file=plan_file,rollback_plan_root=plan_root,approval_file=approval_file,approval_root=approval_root,settings=settings,confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(plan),confirm_approval_sha256=postgis_rollback_approval_sha256(approval),transaction=transaction,now=NOW)
    assert transaction.rolled_back and transaction.renames==[]


def test_failed_final_validation_rolls_back(tmp_path:Path):
    plan,plan_root,plan_file,approval,approval_root,approval_file,settings=approved_evidence(tmp_path)
    ref=plan.original_reference; candidate=plan.promoted_candidate
    promoted=candidate.model_copy(update={"target_schema":ref.target_schema,"target_table":ref.target_table})
    bad_reference=ref.model_copy(update={"row_count":999})
    transaction=FakeTransaction([promoted,missing_like(candidate),plan.archive_relation,bad_reference,candidate])
    with pytest.raises(PostGISRollbackExecutionError,match="failed validation"):
        execute_postgis_rollback(rollback_plan_file=plan_file,rollback_plan_root=plan_root,approval_file=approval_file,approval_root=approval_root,settings=settings,confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(plan),confirm_approval_sha256=postgis_rollback_approval_sha256(approval),transaction=transaction,now=NOW)
    assert transaction.rolled_back and not transaction.committed


def test_expired_approval_fails_before_transaction(tmp_path:Path):
    plan,plan_root,plan_file,approval,approval_root,approval_file,settings=approved_evidence(tmp_path)
    transaction=FakeTransaction([])
    with pytest.raises(PostGISRollbackExecutionError,match="expired"):
        execute_postgis_rollback(rollback_plan_file=plan_file,rollback_plan_root=plan_root,approval_file=approval_file,approval_root=approval_root,settings=settings,confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(plan),confirm_approval_sha256=postgis_rollback_approval_sha256(approval),transaction=transaction,now=NOW+timedelta(hours=2))
    assert not transaction.committed and not transaction.rolled_back


def test_write_gate_fails_before_evidence_loading(tmp_path:Path):
    settings=MCPSettings(input_root=tmp_path,output_root=tmp_path)
    with pytest.raises(PostGISRollbackExecutionError,match="disabled"):
        execute_postgis_rollback(rollback_plan_file=Path("missing"),rollback_plan_root=Path("missing"),approval_file=Path("missing"),approval_root=Path("missing"),settings=settings,confirm_rollback_plan_sha256="a"*64,confirm_approval_sha256="b"*64)
