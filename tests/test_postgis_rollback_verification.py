from pathlib import Path
from datetime import timedelta
import pytest
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_inspection import PostGISInspectionResult
from geoagent_harness.postgis_rollback_plan import persist_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.postgis_rollback_approval import create_postgis_rollback_approval, persist_postgis_rollback_approval, postgis_rollback_approval_sha256
from geoagent_harness.postgis_rollback_execution import execute_postgis_rollback, persist_postgis_rollback_execution, postgis_rollback_execution_sha256
from geoagent_harness.postgis_rollback_verification import *
from tests.test_postgis_rollback_plan import NOW, create_plan
from tests.test_postgis_rollback_approval_execution import FakeTransaction, missing_like

def evidence(tmp_path):
    plan=create_plan(tmp_path); pr=tmp_path/'plans'; ps=persist_postgis_rollback_plan(plan,rollback_plan_root=pr); pf=Path(ps.rollback_plan_file)
    ar=tmp_path/'approvals'; approval=create_postgis_rollback_approval(rollback_plan_file=pf,rollback_plan_root=pr,decision='approved',approver='Jay',reason='Restore exact relations.',now=NOW,expires_at=NOW+timedelta(hours=1),approval_id='postgis-rollback-approval-20260906t120000z-1234abcd'); aps=persist_postgis_rollback_approval(approval,approval_root=ar); af=Path(aps.approval_file)
    ref,cand,archive=plan.original_reference,plan.promoted_candidate,plan.archive_relation
    promoted=cand.model_copy(update={'target_schema':ref.target_schema,'target_table':ref.target_table})
    tx=FakeTransaction([promoted,missing_like(cand),archive,ref,cand])
    settings=MCPSettings(input_root=tmp_path/'input',output_root=tmp_path/'output',enable_write_tools=True)
    ex=execute_postgis_rollback(rollback_plan_file=pf,rollback_plan_root=pr,approval_file=af,approval_root=ar,settings=settings,confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(plan),confirm_approval_sha256=postgis_rollback_approval_sha256(approval),transaction=tx,now=NOW+timedelta(minutes=1))
    er=tmp_path/'executions'; es=persist_postgis_rollback_execution(ex,execution_root=er)
    return plan,pf,pr,approval,af,ar,ex,Path(es.execution_file),er,settings

def test_verified_only_when_exact_post_rollback_state(tmp_path):
    plan,pf,pr,approval,af,ar,ex,ef,er,settings=evidence(tmp_path)
    class Reader:
        def __init__(self, values): self.values=iter(values)
        def inspect(self, request): return next(self.values)
        def close(self): pass
    reader=Reader([plan.original_reference,plan.promoted_candidate,missing_like(plan.archive_relation)])
    result=verify_postgis_rollback(execution_file=ef,execution_root=er,rollback_plan_file=pf,rollback_plan_root=pr,approval_file=af,approval_root=ar,settings=settings,reader=reader,now=NOW+timedelta(minutes=2))
    assert result.status=='verified' and result.findings==[] and result.execution_sha256==postgis_rollback_execution_sha256(ex)

def test_archive_remaining_fails_closed(tmp_path):
    plan,pf,pr,approval,af,ar,ex,ef,er,settings=evidence(tmp_path)
    class Reader:
        def __init__(self, values): self.values=iter(values)
        def inspect(self, request): return next(self.values)
        def close(self): pass
    result=verify_postgis_rollback(execution_file=ef,execution_root=er,rollback_plan_file=pf,rollback_plan_root=pr,approval_file=af,approval_root=ar,settings=settings,reader=Reader([plan.original_reference,plan.promoted_candidate,plan.archive_relation]),now=NOW)
    assert result.status=='failed' and result.findings==['archive_relation_still_exists']

def test_execution_scope_mismatch_is_rejected(tmp_path):
    plan,pf,pr,approval,af,ar,ex,ef,er,settings=evidence(tmp_path)
    from geoagent_harness.postgis_rollback_execution import persist_postgis_rollback_execution
    tampered = ex.model_copy(update={
        'approved_step_ids':['step_4_restore_candidate','unexpected'],
    })
    tampered_root = tmp_path/'tampered-executions'
    tampered_file = Path(persist_postgis_rollback_execution(
        tampered, execution_root=tampered_root
    ).execution_file)
    with pytest.raises(PostGISRollbackVerificationError, match='scope is not exact'):
        verify_postgis_rollback(
            execution_file=tampered_file, execution_root=tampered_root,
            rollback_plan_file=pf, rollback_plan_root=pr,
            approval_file=af, approval_root=ar, settings=settings,
        )

def test_tampered_execution_is_rejected(tmp_path):
    plan,pf,pr,approval,af,ar,ex,ef,er,settings=evidence(tmp_path)
    raw=ef.read_text(); ef.write_text(raw.replace(ex.execution_id, ex.execution_id+'x', 1))
    with pytest.raises(PostGISRollbackVerificationError,match='could not be loaded'):
        verify_postgis_rollback(execution_file=ef,execution_root=er,rollback_plan_file=pf,rollback_plan_root=pr,approval_file=af,approval_root=ar,settings=settings)

def test_storage_round_trip(tmp_path):
    plan,pf,pr,approval,af,ar,ex,ef,er,settings=evidence(tmp_path)
    class Reader:
        def __init__(self, values): self.values=iter(values)
        def inspect(self, request): return next(self.values)
        def close(self): pass
    result=verify_postgis_rollback(execution_file=ef,execution_root=er,rollback_plan_file=pf,rollback_plan_root=pr,approval_file=af,approval_root=ar,settings=settings,reader=Reader([plan.original_reference,plan.promoted_candidate,missing_like(plan.archive_relation)]),now=NOW)
    root=tmp_path/'verifications'; path=persist_postgis_rollback_verification(result,verification_root=root)
    assert load_postgis_rollback_verification(path,verification_root=root)==result
