"""Automatic private helper: independent contract, truthful evidence, bounded effects."""
from dataclasses import replace
import json
from pathlib import Path
from shutil import copytree, copyfile
from threading import Event, Thread

import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.interface_api import method_helper as helper
from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.model import ModelClientError
from geoagent_harness.model.schemas import ModelResult
from geoagent_harness.model.settings import ModelSettings

REPO = Path(__file__).parents[1]
CHAT = 'a'*32
OTHER = 'b'*32
DOCUMENT = {'title':'Inspect a dataset','purpose':'Inspect structure before choosing transformations.',
            'inputs':['An operator-selected dataset'],'prerequisites':['A supported data format'],
            'operations':[{'skill':'inspect_csv','guidance':'Inspect schema and counts.'}],
            'checks':['Check expected metadata.'],'limitations':['Proposed procedure only; not execution evidence.']}


@pytest.fixture
def project(tmp_path):
    for name in ('agents','context'):
        copytree(REPO/name,tmp_path/name)
    (tmp_path/'data/input').mkdir(parents=True)
    for name in ('sample_orders.csv','sample_regions.csv','sample_points.geojson'):
        copyfile(REPO/'data/input'/name,tmp_path/'data/input'/name)
    return tmp_path


class Planner:
    def __init__(self,skill='inspect_csv',path=None):
        self.skill=skill;self.path=path;self.requests=[]
    def complete(self,request):
        self.requests.append(request)
        plan=None if self.skill is None else {'summary':'Inspect selected data','steps':[{'step_id':'step_1','skill':self.skill,
            'purpose':'Inspect selected structure','arguments':{'path':self.path or ('data/input/sample_points.geojson' if self.skill=='inspect_vector' else 'data/input/sample_orders.csv')},
            'requires_approval':False,'validation_required':False}]}
        return ModelResult(model='fixture',content=json.dumps({'message':'Proposal only. Nothing executed.','plan':plan}))


class Helper:
    def __init__(self,document=None,error=None):self.requests=[];self.document=document;self.error=error
    def complete(self,request):
        self.requests.append(request)
        if self.error:raise self.error
        skill=json.loads(request.messages[1].content)['workflow_structure'][0]['skill']
        document=self.document or {**DOCUMENT,'operations':[{'skill':skill,'guidance':'Inspect schema and counts.'}]}
        return ModelResult(model='helper-fixture',content=json.dumps(document))


def read(root,chat=CHAT):return conversation_turn(TurnRequest(action='read',conversation_id=chat),project_root=root)
def enable(root,value=True):return helper.configure(root,enabled=value,expected_revision=helper.setting(root)['revision'])
def turn(root,planner=None,agent=None,chat=CHAT):
    state=read(root,chat)
    return conversation_turn(TurnRequest(action='turn',conversation_id=chat,expected_revision=state['revision'],message='Inspect or explain the selected workflow'),
                             project_root=root,model_client=planner or Planner(),helper_client=agent)


def test_default_off_read_enable_and_chat_open_make_no_model_call(project):
    assert helper.setting(project)=={'enabled':False,'revision':0}
    model=Helper()
    result=turn(project,agent=model)
    assert not model.requests and result['method_helper']['status']=='disabled'
    enable(project)
    assert read(project)['method_helper']['status']=='not_prepared'
    assert not model.requests
    assert helper.after_turn(project,CHAT,result['revision'],changed=False,model_client=model)['status']=='unchanged'
    assert not model.requests


def test_changed_plan_prepares_once_and_later_turn_uses_typed_unvalidated_note(project):
    enable(project);model=Helper();first=turn(project,agent=model)
    assert len(model.requests)==1
    assert first['method_helper_update']['model_calls']==1
    assert first['context_usage']['method_helper']['status']=='no_workflow'
    note=helper.NoteBundle.model_validate(first['method_helper']['note'])
    assert note.status=='machine_generated_unvalidated' and note.evidence_kind=='validated_plan_only'
    assert note.source_plan_sha256==first['planner_result']['plan_sha256']
    source=json.loads(model.requests[0].messages[1].content)
    assert source['execution_evidence'] is None
    assert 'sample_orders.csv' not in json.dumps(source) and 'arguments' not in json.dumps(source)
    planner=Planner(None);second=turn(project,planner,model)
    payload=json.loads(planner.requests[0].messages[1].content)
    assert payload['method_helper_note']['note_id']==note.note_id
    assert second['context_usage']['method_helper']['status']=='included'
    assert len(model.requests)==1
    # Duplicate changed-event delivery is idempotent, including after reload.
    assert helper.after_turn(project,CHAT,second['revision'],changed=True,model_client=model)['status']=='cached'
    assert read(project)['method_helper']['status']=='ready' and len(model.requests)==1
    assert not second['approval_performed'] and not second['execution_performed']
    assert not (project/'data/output').exists()


def test_current_scope_and_conversation_isolation(project):
    enable(project);model=Helper();first=turn(project,agent=model)
    assert read(project,OTHER)['method_helper']['status']=='no_workflow'
    changed=Planner('inspect_vector');second=turn(project,changed,model)
    assert json.loads(changed.requests[0].messages[1].content)['method_helper_note']['source_plan_sha256']==first['planner_result']['plan_sha256']
    assert second['method_helper']['note']['document']['operations'][0]['skill']=='inspect_vector'
    assert second['method_helper']['note']['note_id']!=first['method_helper']['note']['note_id']
    assert len(model.requests)==2
    foreign=turn(project,Planner(),model,chat=OTHER)
    assert foreign['context_usage']['method_helper']['status']=='no_workflow'
    assert foreign['method_helper']['note']['conversation_id']==OTHER
    assert foreign['method_helper']['note']['note_id']!=first['method_helper']['note']['note_id']


@pytest.mark.parametrize('agent',[
    Helper(error=ModelClientError.timeout()),
    Helper(document={'title':'incomplete'}),
    Helper(document={**DOCUMENT,'operations':[{'skill':'eval','guidance':'Execute arbitrary code'}]}),
    Helper(document={**DOCUMENT,'inputs':['data/input/private.csv']}),
    Helper(document={**DOCUMENT,'operations':[{'skill':'inspect_vector','guidance':'Inspect a different data contract'}]}),
])
def test_failure_does_not_fail_saved_plan_or_retry_same_source(project,agent):
    enable(project);result=turn(project,agent=agent)
    assert result['planner_result'] is not None and result['revision']==1
    assert result['method_helper_update']['status']=='failed'
    assert result['method_helper']['status']=='failed'
    assert helper.after_turn(project,CHAT,1,changed=True,model_client=agent)['status']=='failed_cached'
    assert len(agent.requests)==1
    planner=Planner(None);turn(project,planner,agent)
    assert json.loads(planner.requests[0].messages[1].content)['method_helper_note'] is None
    assert len(agent.requests)==1


def test_off_hides_notes_and_prevents_new_calls(project):
    enable(project);model=Helper();turn(project,agent=model);enable(project,False)
    assert read(project)['method_helper']['status']=='disabled'
    planner=Planner('inspect_vector');result=turn(project,planner,model)
    assert json.loads(planner.requests[0].messages[1].content)['method_helper_note'] is None
    assert result['method_helper_update']['status']=='disabled' and len(model.requests)==1
    assert helper.setting(project)['enabled'] is False


def test_off_on_during_helper_generation_discards_result_but_keeps_plan(project):
    enable(project)
    class Changing(Helper):
        def complete(self,request):
            enable(project,False);enable(project,True)
            return super().complete(request)
    model=Changing();result=turn(project,agent=model)
    assert result['method_helper_update']['status']=='setting_changed'
    assert result['planner_result'] is not None and read(project)['revision']==1
    assert result['method_helper']['status']=='not_prepared'


def test_off_during_note_assisted_planning_discards_stale_reply(project):
    enable(project);turn(project,agent=Helper())
    class Changing(Planner):
        def complete(self,request):enable(project,False);return super().complete(request)
    with pytest.raises(InterfaceApiError,match='setting changed'):
        turn(project,Changing(None),Helper())
    assert read(project)['revision']==1


def test_corrupt_or_incompatible_note_is_not_injected(project):
    enable(project);turn(project,agent=Helper())
    with helper.database(project,write=True) as connection:
        row=connection.execute('SELECT source_key,value FROM method_helper_notes').fetchone()
        value=json.loads(row[1]);value['note']['contract_version']='999'
        connection.execute('UPDATE method_helper_notes SET value=? WHERE source_key=?',(json.dumps(value),row[0]))
    assert read(project)['method_helper']['status']=='unavailable'
    planner=Planner(None);result=turn(project,planner,Helper())
    assert result['revision']==2
    assert json.loads(planner.requests[0].messages[1].content)['method_helper_note'] is None


def test_helper_uses_separate_bounded_model_settings(project,monkeypatch):
    enable(project)
    settings=ModelSettings(base_url='http://127.0.0.1:1/v1',model='fixture',timeout_seconds=120,max_tokens=8192)
    model=Helper();captured=[]
    monkeypatch.setattr(helper,'load_model_settings',lambda:settings)
    monkeypatch.setattr(helper,'SharedModelClient',lambda value:(captured.append(value) or model))
    turn(project)
    assert captured==[replace(settings,timeout_seconds=15,max_tokens=768)]
    assert len(model.requests)==1


def test_cli_setting_and_note_inspection_share_service(project,tmp_path):
    runner=CliRunner();request=tmp_path/'helper.json'
    def run(payload):
        request.write_text(json.dumps(payload))
        result=runner.invoke(app,['method-memory','--request-file',str(request),'--project-root',str(project)])
        assert result.exit_code==0,result.output
        return json.loads(result.stdout)
    assert run({'action':'helper_state'})['enabled'] is False
    run({'action':'enable_helper','enabled':True})
    turn(project,agent=Helper())
    inspected=run({'action':'inspect_helper','conversation_id':CHAT})
    assert inspected['helper']['note']['status']=='machine_generated_unvalidated'
    assert not inspected['approval_performed'] and not inspected['execution_performed']


def test_concurrent_helper_delivery_is_serial_and_idempotent(project):
    first=turn(project);enable(project);started=Event();finish=Event();results=[]
    class Slow(Helper):
        def complete(self,request):
            started.set();assert finish.wait(5);return super().complete(request)
    agent=Slow()
    worker=Thread(target=lambda:results.append(helper.after_turn(project,CHAT,first['revision'],changed=True,model_client=agent)))
    worker.start();assert started.wait(5)
    try:
        assert helper.after_turn(project,CHAT,first['revision'],changed=True,model_client=agent)['status']=='busy'
    finally:finish.set();worker.join(5)
    assert results[0]['status']=='prepared' and len(agent.requests)==1
    assert helper.after_turn(project,CHAT,first['revision'],changed=True,model_client=agent)['status']=='cached'
    assert len(agent.requests)==1


def test_graph_binding_triggers_helper_outside_conversation_lock(project):
    first=turn(project);enable(project);agent=Helper()
    state=helper._current(project,CHAT)
    proposed=state.planner_result.model_copy(deep=True)
    proposed.plan.summary='Updated validated inspection'
    result=conversation_turn(TurnRequest(action='bind_task_plan',conversation_id=CHAT,task_id=CHAT,
        expected_revision=first['revision'],expected_task_revision=first['revision'],current_plan=proposed),
        project_root=project,helper_client=agent)
    assert result['method_helper_update']['status']=='prepared' and len(agent.requests)==1
    assert result['context_usage']==first['context_usage']
    assert not result['approval_performed'] and not result['execution_performed']


def test_source_revision_change_discards_note_after_model(project):
    enable(project)
    class Changing(Helper):
        def complete(self,request):
            from geoagent_harness.interface_api.planning_tasks import write_turn
            current=helper._current(project,CHAT);value=current.model_dump(mode='json');value['revision']+=1
            write_turn(project,value,expected_revision=current.revision,expected_task_revision=current.revision)
            return super().complete(request)
    result=turn(project,agent=Changing())
    assert result['method_helper_update']['status']=='source_changed'
    assert read(project)['method_helper']['status']=='not_prepared'


def test_off_before_model_send_omits_note_and_records_actual_prompt_bytes(project,monkeypatch):
    enable(project);turn(project,agent=Helper())
    current=read(project)
    original=helper.context_for_turn
    def switch_off(*args,**kwargs):
        bundle,receipt=original(*args,**kwargs)
        if bundle:enable(project,False)
        return bundle,receipt
    monkeypatch.setattr(helper,'context_for_turn',switch_off)
    planner=Planner(None)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=current['revision'],message='Explain this workflow'),project_root=project,model_client=planner,helper_client=Helper())
    request=planner.requests[0]
    assert json.loads(request.messages[1].content)['method_helper_note'] is None
    assert result['context_usage']['method_helper']['status']=='setting_changed'
    assert result['context_usage']['prompt_bytes']==sum(len(message.content.encode()) for message in request.messages)
