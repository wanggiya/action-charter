"""R12 context/admission/claim acceptance; temporary fixtures, no model or DB service."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import inspect
import json
from pathlib import Path
from shutil import copyfile
import sqlite3
import subprocess
import sys

import pytest

from geoagent_harness.contracts.task_context import (
    Actor, RunContext, RunBudget, PolicyDecision, ActionContextError, ActionStorageError, DuplicateAction,
)
from geoagent_harness.core.execution.actions import task_entrypoint
from geoagent_harness.platform.action_context import current_action, request_context
from geoagent_harness.platform.execution_services import execution_services, using_execution_services
from geoagent_harness.platform.storage.action_ledger import LocalActionLedger
from geoagent_harness.platform.workspace import runtime_store_path

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    (tmp_path/'context').mkdir()
    copyfile(ROOT/'context/SKILLS_INDEX.yaml',tmp_path/'context/SKILLS_INDEX.yaml')
    return tmp_path


def events(project, run): return LocalActionLedger(project).events(run.run_id)


def test_context_is_immutable_and_never_an_authorization_record(project):
    actor=Actor();run=RunContext(str(project))
    with pytest.raises(FrozenInstanceError):actor.actor_id='other'
    with pytest.raises(FrozenInstanceError):run.trigger='automation'
    assert not hasattr(run,'approved') and not hasattr(actor,'permissions')
    assert execution_services().credentials.issue(actor,run,'any-resource') is None


@pytest.mark.parametrize('budget', [{'max_actions':True},{'max_actions':0},{'wall_seconds':float('nan')},{'wall_seconds':-1}])
def test_invalid_budgets_fail_before_dispatch(budget):
    with pytest.raises(ActionContextError):RunBudget(**budget)


def test_nested_calls_share_identity_budget_and_lineage_without_changing_results(project):
    seen=[]
    @task_entrypoint
    def child(*,project_root):
        seen.append(current_action())
        return {'run_id':'a'*32,'value':'unchanged'}
    @task_entrypoint
    def parent(*,project_root):
        seen.append(current_action())
        return child(project_root=project_root)
    run=RunContext(str(project),budget=RunBudget(max_actions=2))
    assert parent(project_root=project,actor=Actor(),run_context=run)=={'run_id':'a'*32,'value':'unchanged'}
    assert len({frame.run.run_id for frame in seen})==1
    assert all(frame.actor==Actor() for frame in seen)
    recorded=events(project,run)
    starts=[e for e in recorded if e['phase']=='started']
    assert len(starts)==2 and starts[1]['parent_action_id']==starts[0]['identity']
    assert all(e['execution_authority_granted'] is False for e in recorded)
    assert any(e.get('reference')=='a'*32 for e in recorded)
    assert current_action() is None
    # Internal identity/context kwargs do not become public tool input fields.
    assert list(inspect.signature(parent).parameters)==['project_root']


def test_cross_project_and_nested_actor_substitution_fail_before_inner_body(project,tmp_path_factory):
    other=tmp_path_factory.mktemp('other-project')
    @task_entrypoint
    def child(*,project_root):pytest.fail('Invalid scope dispatched')
    @task_entrypoint
    def parent(*,project_root):
        with pytest.raises(ActionContextError,match='different project'):child(project_root=other)
        with pytest.raises(ActionContextError,match='cannot replace'):child(project_root=project,actor=Actor('other'))
    parent(project_root=project)
    with pytest.raises(ActionContextError,match='trusted application'):child(project_root=project,actor={'actor_id':'owner'})


@pytest.mark.parametrize('outcome',['deny','escalate'])
def test_policy_blocks_and_records_without_entering_body(project,outcome):
    class Restricted:
        def decide(self,*args):return PolicyDecision(outcome,'fixture_restriction')
    @task_entrypoint
    def action(*,project_root):pytest.fail('Restricted action dispatched')
    run=RunContext(str(project))
    with using_execution_services(replace(execution_services(),policy=Restricted())):
        with pytest.raises(ActionContextError,match=outcome):action(project_root=project,run_context=run)
    assert [e['phase'] for e in events(project,run)]==['started','blocked']


def test_local_policy_rejects_nonowner_identity(project):
    @task_entrypoint
    def action(*,project_root):pytest.fail('Nonowner admitted locally')
    with pytest.raises(ActionContextError,match='local_owner_required'):
        action(project_root=project,actor=Actor('service','service'))


def test_same_event_after_failure_is_consumed_and_private_text_is_not_in_audit(project):
    calls=[]
    @task_entrypoint
    def action(value,*,project_root):
        calls.append(value)
        raise ValueError('private-exception-content')
    run=RunContext(str(project),idempotency_key='event-1')
    with pytest.raises(ValueError):action('private-input-content',project_root=project,run_context=run)
    with pytest.raises(DuplicateAction,match='failed'):
        action('private-input-content',project_root=project,run_context=replace(run,run_id='b'*32))
    with pytest.raises(ActionContextError,match='conflicts'):
        action('different-input',project_root=project,run_context=run)
    assert calls==['private-input-content']
    with sqlite3.connect(runtime_store_path(project,'workflow-state')/'action-ledger.sqlite3') as db:
        text='\n'.join(db.iterdump())
    assert 'private-input-content' not in text and 'private-exception-content' not in text


def test_concurrent_duplicates_dispatch_once(project):
    calls=[]
    @task_entrypoint
    def action(*,project_root):calls.append(1);return 'done'
    run=RunContext(str(project),idempotency_key='same-event')
    def invoke(_):
        try:return action(project_root=project,run_context=run)
        except DuplicateAction:return 'duplicate'
    with ThreadPoolExecutor(max_workers=4) as worker:results=list(worker.map(invoke,range(8)))
    assert results.count('done')==1 and results.count('duplicate')==7 and calls==[1]


def test_process_restart_cannot_repeat_claimed_event(project):
    script='''
from pathlib import Path
import sys
from geoagent_harness.core.execution.actions import task_entrypoint
from geoagent_harness.contracts.task_context import RunContext, DuplicateAction
project=Path(sys.argv[1])
@task_entrypoint
def action(*,project_root):
    with (project/'dispatches').open('a') as stream:stream.write('once\\n')
try:action(project_root=project,run_context=RunContext(str(project),idempotency_key='persistent-event'))
except DuplicateAction:print('duplicate')
else:print('dispatched')
'''
    for expected in ['dispatched','duplicate']:
        result=subprocess.run([sys.executable,'-c',script,str(project)],capture_output=True,text=True,timeout=15)
        assert result.returncode==0,result.stderr
        assert result.stdout.strip()==expected
    assert (project/'dispatches').read_text()=='once\n'


def test_uncertain_completion_does_not_release_dispatch_claim(project):
    original=execution_services();calls=[]
    class Uncertain(LocalActionLedger):
        def finish(self,*args,**kwargs):raise ActionStorageError('fixture acknowledgement lost')
    @task_entrypoint
    def action(*,project_root):calls.append(1)
    run=RunContext(str(project),idempotency_key='uncertain')
    with using_execution_services(replace(original,ledger=Uncertain)):
        with pytest.raises(ActionStorageError):action(project_root=project,run_context=run)
    with pytest.raises(DuplicateAction,match='started'):action(project_root=project,run_context=run)
    assert calls==[1]


def test_storage_unavailable_before_claim_prevents_dispatch(project):
    class Unavailable(LocalActionLedger):
        def claim(self,**kwargs):raise ActionStorageError('fixture unavailable')
    @task_entrypoint
    def action(*,project_root):pytest.fail('Dispatch without audit claim')
    with using_execution_services(replace(execution_services(),ledger=Unavailable)):
        with pytest.raises(ActionStorageError):action(project_root=project)


def test_queue_preserves_services_actor_run_and_restores_context(project):
    seen=[];run=RunContext(str(project),trigger='cli')
    @task_entrypoint
    def worker(*,project_root):seen.append((current_action(),execution_services()))
    services=replace(execution_services())
    with using_execution_services(services),request_context(project,trigger='cli',run_context=run):
        job=services.queue.submit(worker,project_root=project)
        job.join(timeout=5)
        assert not job.is_alive()
    assert seen[0][0].run==run and seen[0][0].actor==Actor()
    assert seen[0][1] is services and current_action() is None


def test_action_budget_stops_nested_dispatch(project):
    @task_entrypoint
    def child(*,project_root):pytest.fail('Budget exhausted')
    @task_entrypoint
    def parent(*,project_root):child(project_root=project)
    with pytest.raises(ActionContextError,match='action budget'):
        parent(project_root=project,run_context=RunContext(str(project),budget=RunBudget(max_actions=1)))


def test_clock_controls_wall_budget_and_real_approval_expiry(project):
    from tests.test_approval_service import planner_result,NOW
    from geoagent_harness.core.policy.approvals.service import create_approval,verify_approval
    class Clock:
        stamp=NOW
        seconds=0
        def now(self):return self.stamp
        def monotonic(self):return self.seconds
    clock=Clock()
    @task_entrypoint
    def child(*,project_root):pytest.fail('Wall budget exhausted')
    @task_entrypoint
    def parent(*,project_root):clock.seconds=2;child(project_root=project)
    result=planner_result()
    with using_execution_services(replace(execution_services(),clock=clock)):
        approval,_=create_approval(planner_result=result,decision='approved',step_ids=['step_2'],approver='fixture',reason='temporary',
            approval_root=project/'approvals',project_root=project,expires_at=NOW+timedelta(minutes=1))
        assert verify_approval(approval=approval,plan=result.plan,required_step_ids=['step_2']).approved
        clock.stamp=NOW+timedelta(minutes=2)
        assert not verify_approval(approval=approval,plan=result.plan,required_step_ids=['step_2']).approved
        with pytest.raises(ActionContextError,match='wall-clock budget'):
            parent(project_root=project,run_context=RunContext(str(project),budget=RunBudget(wall_seconds=1)))


def test_audit_chain_detects_tampering(project):
    @task_entrypoint
    def action(*,project_root):return None
    run=RunContext(str(project));action(project_root=project,run_context=run)
    path=runtime_store_path(project,'workflow-state')/'action-ledger.sqlite3'
    with sqlite3.connect(path) as db:db.execute("UPDATE action_events SET payload=replace(payload,'local_owner_admission_only','tampered') WHERE phase='started'")
    with pytest.raises(ActionStorageError,match='verification'):events(project,run)


def test_partial_relocation_cannot_forget_duplicate_claims(project,tmp_path_factory):
    from tests.test_workspace_layout import configure
    @task_entrypoint
    def action(*,project_root):return None
    run=RunContext(str(project),idempotency_key='before-relocation')
    action(project_root=project,run_context=run)
    configure(project,tmp_path_factory.mktemp('incomplete-action-copy'))
    with pytest.raises(ActionStorageError):action(project_root=project,run_context=run)


def test_missing_audit_read_is_pure_and_shared_workspace_cannot_mix_projects(project,tmp_path_factory):
    from tests.test_workspace_layout import configure
    before=list(project.rglob('*'))
    assert LocalActionLedger(project).events('a'*32)==[]
    assert list(project.rglob('*'))==before
    shared=tmp_path_factory.mktemp('shared-action-state')
    other=tmp_path_factory.mktemp('other-action-project')
    configure(project,shared);configure(other,shared)
    @task_entrypoint
    def action(*,project_root):return None
    action(project_root=project)
    with pytest.raises(ActionStorageError,match='different source project'):action(project_root=other)


def test_registered_task_entrypoints_have_context_boundary_without_extra_public_fields():
    from importlib import import_module
    manifest=json.loads((ROOT/'tests/architecture/r12_entrypoints.json').read_text())
    for module,names in manifest.items():
        owner=import_module('geoagent_harness.task_actions.'+module)
        for name in names:
            function=getattr(owner,name)
            assert function.__task_entrypoint__ is True,(module,name)
            assert 'actor' not in inspect.signature(function).parameters
            assert 'run_context' not in inspect.signature(function).parameters


def test_http_event_key_blocks_repetition_without_accepting_actor_from_body(project,monkeypatch):
    from email.message import Message
    from io import BytesIO
    from geoagent_harness.apps.http import server
    calls=[]
    monkeypatch.setattr(server,'plan_interface_task',lambda *a,**k:calls.append(1) or {'fixture':True})
    def post(body,key):
        handler=server._handler(project).__new__(server._handler(project))
        handler.path='/api/v1/plans/create'
        handler.headers=Message();handler.headers['Content-Type']='application/json';handler.headers['Idempotency-Key']=key
        encoded=json.dumps(body).encode();handler.headers['Content-Length']=str(len(encoded));handler.rfile=BytesIO(encoded)
        sent=[];handler._send=lambda status,payload:sent.append((int(status),payload))
        handler.do_POST();assert len(sent)==1
        return sent[0]
    body={'action':'plan_task','request':'Inspect only','allowed_skill_ids':['inspect_vector']}
    assert post(body,'http-event')[0]==200
    status,response=post(body,'http-event')
    assert status==409 and response['code']=='action_already_claimed' and calls==[1]
    assert post({**body,'actor':{'actor_id':'owner'}},'another-event')[0]==400
    assert calls==[1]


def test_http_early_response_waits_for_audit_acknowledgement(project):
    from email.message import Message
    from geoagent_harness.apps.http import server
    class Uncertain(LocalActionLedger):
        def finish(self,*args,**kwargs):raise ActionStorageError('fixture acknowledgement lost')
    sent=[]
    with using_execution_services(replace(execution_services(),queries=Uncertain)):
        handler=server._handler(project).__new__(server._handler(project))
        handler.path='/missing';handler.headers=Message()
        handler._send=lambda status,payload:sent.append((int(status),payload))
        handler.do_GET()
    assert len(sent)==1 and sent[0][0]==503
    assert sent[0][1]['execution_status']=='unconfirmed'


def test_admission_allow_does_not_replace_fresh_write_authority(project):
    from geoagent_harness.core.policy import write_policy as policy
    from geoagent_harness.core.policy.approvals.service import create_approval
    from geoagent_harness.platform.settings import MCPSettings
    from tests.test_approval_service import planner_result,NOW
    calls=[];leases=[]
    class Broker:
        def issue(self,*args):leases.append(args);return None
    @task_entrypoint
    def action(*,project_root):
        with policy.operation(MCPSettings(project_root=project_root,input_root=project_root/'data/input',
                                         output_root=project_root/'data/output',enable_write_tools=True)):
            calls.append(1)
    with using_execution_services(replace(execution_services(),credentials=Broker())),policy.session(project,enabled=True):
        with pytest.raises(policy.WritePolicyError,match='fresh session-bound authorization'):
            action(project_root=project)
        assert calls==[] and leases==[]
        approval,_=create_approval(planner_result=planner_result(),decision='approved',step_ids=['step_2'],
            approver='fixture',reason='temporary',approval_root=project/'approvals',project_root=project,now=NOW)
        with policy.authority(project,approval):action(project_root=project)
        assert calls==[1] and len(leases)==1
        state=policy.snapshot(project)
        policy.update(project,policy.PolicyUpdate(enabled=False,session_id=state['session_id'],revision=state['revision']))
        with pytest.raises(policy.WritePolicyError):
            with policy.authority(project,approval):action(project_root=project)
        assert calls==[1] and len(leases)==1


def test_cli_records_owner_and_run_without_changing_json_output(project):
    from typer.testing import CliRunner
    from geoagent_harness.apps.cli.main import app
    run=RunContext(str(project),trigger='cli')
    with request_context(project,trigger='cli',run_context=run):
        response=CliRunner().invoke(app,['planning-tasks','--project-root',str(project)])
    assert response.exit_code==0,response.output
    assert 'tasks' in json.loads(response.output)
    starts=[event for event in execution_services().queries(project).events(run.run_id) if event['phase']=='started']
    assert len(starts)>=2 and all(e['actor']=={'actor_id':'owner','kind':'owner'} for e in starts)
    assert {e['trigger'] for e in starts}=={'cli'}
    assert len({e['run_id'] for e in starts})==1
    assert not (project/'workflow-state').exists()


def test_http_threads_keep_server_composition_after_configuration_scope_exits(project):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.apps.http import server
    calls=[]
    class ComposedLedger(LocalActionLedger):
        def claim(self,**kwargs):calls.append(kwargs['run'].project_root);return super().claim(**kwargs)
    with using_execution_services(replace(execution_services(),ledger=ComposedLedger,queries=ComposedLedger)):
        handler=server._handler(project)
    http=ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=Thread(target=http.serve_forever,daemon=True);thread.start()
    connection=HTTPConnection(*http.server_address,timeout=5)
    try:
        connection.request('GET','/missing');response=connection.getresponse()
        assert response.status==404 and json.loads(response.read())=={'error':'endpoint is not available'}
    finally:
        connection.close();http.shutdown();http.server_close();thread.join(timeout=5)
    assert calls==[str(project)]


@pytest.mark.parametrize('command',[
    ['agent-info','planner','--agents-root',str(ROOT/'agents')],
    ['recipe-template-catalog','--project-root',str(ROOT)],
])
def test_static_cli_metadata_does_not_require_a_writable_workspace(command):
    from typer.testing import CliRunner
    from geoagent_harness.apps.cli.main import app
    def forbidden(root):pytest.fail('Static metadata must not open an action ledger')
    with using_execution_services(replace(execution_services(),ledger=forbidden)):
        response=CliRunner().invoke(app,command)
    assert response.exit_code==0,response.output
    assert isinstance(json.loads(response.output),dict)


def test_unkeyed_query_keeps_bounded_context_telemetry_without_creating_state(project):
    @task_entrypoint(audit=False)
    def query(*,project_root):return {'records':[]}
    run=RunContext(str(project))
    assert query(project_root=project,run_context=run)=={'records':[]}
    assert not (project/'workflow-state').exists()
    recorded=execution_services().queries(project).events(run.run_id)
    assert [event['phase'] for event in recorded]==['started','completed']
    assert all(event['actor']=={'actor_id':'owner','kind':'owner'} and event['durable'] is False for event in recorded)


def test_explicit_query_event_uses_durable_claim_and_cannot_repeat(project):
    @task_entrypoint(audit=False)
    def query(*,project_root):return {'records':[]}
    run=RunContext(str(project),idempotency_key='keyed-query')
    query(project_root=project,run_context=run)
    with pytest.raises(DuplicateAction):query(project_root=project,run_context=run)
    assert [event['phase'] for event in events(project,run)]==['started','completed']


def test_all_mcp_ingress_callbacks_keep_the_twenty_seven_tool_schemas():
    import asyncio
    from geoagent_harness.apps.mcp.server import create_mcp_server
    server=create_mcp_server()
    actual=[tool.model_dump(mode='json') for tool in asyncio.run(server.list_tools())]
    expected=json.loads((ROOT/'tests/architecture/r12_mcp_tools.json').read_text())
    assert actual==expected and len(actual)==27
    for tool in actual:
        assert server._tool_manager.get_tool(tool['name']).fn.__task_entrypoint__ is True


def test_legacy_mcp_alias_records_owner_run_and_keeps_composed_profile(project,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from geoagent_harness.apps.mcp import server as application
    frames=[];claims=[]
    monkeypatch.chdir(project)
    def fixture(path):
        frames.append(current_action())
        return SimpleNamespace(model_dump=lambda **_: {'fixture':True})
    monkeypatch.setattr(application.tools,'inspect_vector_dataset',fixture)
    class ComposedLedger(LocalActionLedger):
        def claim(self,**kwargs):claims.append(kwargs);return super().claim(**kwargs)
    with using_execution_services(replace(execution_services(),ledger=ComposedLedger)):
        server=application.create_mcp_server()
    asyncio.run(server.call_tool('inspect_vector_dataset',{'path':'fixture.geojson'}))
    assert len(frames)==len(claims)==1
    assert frames[0].actor==Actor() and frames[0].run.trigger=='mcp'
    assert frames[0].run.project_root==str(project)
    assert [event['phase'] for event in LocalActionLedger(project,namespace='mcp').events(frames[0].run.run_id)]==['started','completed']


def test_mcp_audit_uses_existing_trace_mount_with_readonly_source(project,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from geoagent_harness.apps.mcp import server as application
    trace=project/'traces';trace.mkdir(mode=0o700)
    monkeypatch.chdir(project)
    monkeypatch.setattr(application.tools,'inspect_vector_dataset',lambda path:SimpleNamespace(model_dump=lambda **_: {'fixture':True}))
    project.chmod(0o555)
    try:
        server=application.create_mcp_server()
        asyncio.run(server.call_tool('inspect_vector_dataset',{'path':'fixture.geojson'}))
        assert (trace/'.action-audit/action-ledger.sqlite3').is_file()
        assert not (project/'workflow-state').exists()
    finally:project.chmod(0o700)


def test_proposal_only_cli_keeps_readonly_agent_root_usable(project,monkeypatch):
    from typer.testing import CliRunner
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.agents.roles import planner
    from tests.test_approval_service import planner_result
    monkeypatch.setattr(planner,'plan_task',lambda *a,**k:planner_result())
    project.chmod(0o555)
    try:
        result=CliRunner().invoke(app,['plan-task','--request','Inspect only',
            '--project-root',str(project),'--agents-root',str(ROOT/'agents')])
        assert result.exit_code==0,result.output
        assert json.loads(result.output)['plan']['status']=='planned'
        assert not (project/'workflow-state').exists()
    finally:project.chmod(0o700)
