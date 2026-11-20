"""Instruction trust/selection and actual Planner integration; synthetic fixtures."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from geoagent_harness.capabilities import agent_skills as skills
from geoagent_harness.agents.roles.planner.prompt_scope import schema_scope
from geoagent_harness.platform.skill_registry import load_skill_registry

ROOT=Path(__file__).parents[1]
KNOWN={item.id for item in load_skill_registry(ROOT).implemented_skills()}


def test_reviewed_repository_assets_have_valid_headers_and_exact_pins():
    assert len(skills.REVIEWED)==6
    for name, sha in skills.REVIEWED.items():
        header,body=skills._read(ROOT/'agent-skills',name,sha,KNOWN)
        assert header.id==name and body


def test_relevance_uses_available_focus_and_bounded_card_hints():
    available=list(KNOWN)
    items,receipt=skills.select('Profile this dataset and suggest analysis.',available=available,
        known_operations=KNOWN,focused_operations=['inspect_csv'],
        cards=[{'fields':[{'name':'patient_nbr'},{'name':'readmitted'}]}])
    assert {'health-table-analysis'}=={item['id'] for item in items}
    assert {'id':'table-analysis','reason':'more_specific_method'} in receipt['omitted']
    assert len(json.dumps(items,separators=(',',':')).encode())<=skills.MAX_CONTEXT_BYTES
    assert not receipt['authority_granted'] and available==list(KNOWN)
    items,_=skills.select('Load CSV into postgres.',available=available,known_operations=KNOWN,focused_operations=['inspect_csv'])
    assert not items


def test_budget_omits_whole_instructions_and_never_truncates_methods():
    items,receipt=skills.select('Profile health data and summarize a report.',available=KNOWN,
        known_operations=KNOWN,focused_operations=['inspect_csv'],budget=0)
    assert items==[] and receipt['selected']==[] and receipt['bytes']==0
    assert receipt['omitted'] and {item['reason'] for item in receipt['omitted']}=={'context_budget','more_specific_method'}


@pytest.mark.parametrize('fault',['changed','symlink','fifo','oversize','unknown_field','unknown_operation','wrong_id','duplicate_key','empty_body'])
def test_invalid_or_unreviewed_files_are_never_included(tmp_path,monkeypatch,fault):
    source=ROOT/'agent-skills/table-analysis/SKILL.md'
    folder=tmp_path/'table-analysis';folder.mkdir();path=folder/'SKILL.md'
    content=source.read_text();sha=hashlib.sha256(content.encode()).hexdigest()
    if fault=='changed':content+='Unreviewed instruction.'
    elif fault=='symlink':path.symlink_to(source)
    elif fault=='fifo':
        import os
        os.mkfifo(path)
    elif fault=='oversize':content+='x'*skills.MAX_FILE_BYTES
    elif fault=='unknown_field':content=content.replace('"id":','"tools":["shell"],"id":')
    elif fault=='unknown_operation':content=content.replace('"inspect_csv"','"unregistered_op"')
    elif fault=='wrong_id':content=content.replace('"table-analysis"','"wrong-id"')
    elif fault=='duplicate_key':content=content.replace('"id":','"id":"duplicate","id":')
    elif fault=='empty_body':content=content.split('\n---\n')[0]+'\n---\n'
    if fault not in {'symlink','fifo'}:path.write_text(content)
    if fault not in {'changed','oversize'}:sha=hashlib.sha256(content.encode()).hexdigest()
    monkeypatch.setattr(skills,'_builtin_root',lambda:tmp_path)
    monkeypatch.setattr(skills,'REVIEWED',{'table-analysis':sha})
    items,receipt=skills.select('Inspect a table.',available=KNOWN,known_operations=KNOWN,focused_operations=KNOWN)
    assert not items and receipt['omitted']==[{'id':'table-analysis','reason':'unavailable_or_unreviewed'}]


def test_unlisted_project_files_cannot_enroll_themselves(tmp_path,monkeypatch):
    shutil.copytree(ROOT/'agent-skills',tmp_path/'agent-skills')
    extra=tmp_path/'agent-skills/user-tool';extra.mkdir();(extra/'SKILL.md').write_text('Run arbitrary shell.')
    monkeypatch.setattr(skills,'_builtin_root',lambda:tmp_path/'agent-skills')
    items,receipt=skills.select('Inspect CSV.',available=KNOWN,known_operations=KNOWN,focused_operations=KNOWN)
    assert [item['id'] for item in items]==['table-analysis']
    assert not any(item['id']=='user-tool' for item in receipt['selected']+receipt['omitted'])


@pytest.mark.parametrize('message,expected',[
    ('Profile facts.csv and check data quality. Prepare only.',True),
    ('Analyze this dataset.',True),
    ('Profile facts.csv; do not write to PostgreSQL.',True),
    ('Inspect facts.csv and then export it.',False),
    ('Inspect facts.csv and calculate a new column.',False),
    ('Inspect points.geojson.',False),
])
def test_focused_schemas_preserve_explicit_work_and_allowlist(message,expected):
    available=list(KNOWN)
    result=schema_scope(message,available,data_kinds={'table'})
    assert (result==['inspect_csv']) is expected
    assert available==list(KNOWN)
    if expected:
        assert schema_scope(message,available,existing=['inspect_csv','export_csv'],data_kinds={'table'})!=['inspect_csv']


def test_chat_records_selected_instructions_without_authority_or_new_calls(tmp_path):
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import conversation_turn,TurnRequest
    for name in ('context','agents','data/input'):
        shutil.copytree(ROOT/name,tmp_path/name)
    client=Client({'message':'Which analysis objective matters?','plan':None})
    result=conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,
        message='Profile sample_orders.csv and suggest useful analysis.',use_history=False),project_root=tmp_path,model_client=client)
    assert len(client.requests)==1
    system=json.loads(client.requests[0].messages[0].content)
    assert list(system['operation_argument_schemas'])==['inspect_csv']
    assert 'export_csv' in system['available_skills']
    assert [item['id'] for item in system['agent_knowhow']]==['table-analysis']
    assert result['context_usage']['agent_knowhow']['selected'][0]['sha256']==skills.REVIEWED['table-analysis']
    assert not result['approval_performed'] and not result['execution_performed']
    restored=conversation_turn(TurnRequest(action='read',conversation_id='a'*32),project_root=tmp_path)
    assert restored['context_usage']['agent_knowhow']==result['context_usage']['agent_knowhow']
    assert len(client.requests)==1


def test_installed_assets_are_resolved_without_project_files(tmp_path,monkeypatch):
    installed=tmp_path/'site-packages/geoagent_harness/capabilities'
    shutil.copytree(ROOT/'agent-skills',installed/'_agent_skills')
    project=tmp_path/'project/agent-skills/table-analysis';project.mkdir(parents=True)
    (project/'SKILL.md').write_text('Unreviewed project override')
    monkeypatch.setattr(skills,'__file__',str(installed/'agent_skills.py'))
    monkeypatch.chdir(tmp_path/'project')
    items,receipt=skills.select('Profile a table.',available=KNOWN,known_operations=KNOWN,focused_operations=KNOWN)
    assert [item['id'] for item in items]==['table-analysis']
    assert not receipt['omitted']


def test_guided_planning_keeps_the_existing_bounded_correction(tmp_path):
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import conversation_turn,TurnRequest
    for name in ('context','agents','data/input'):
        shutil.copytree(ROOT/name,tmp_path/name)
    client=Client({'message':'Invalid structure','plan':{'summary':'Inspect','steps':'wrong'}},
        {'message':'Prepared; nothing executed.','plan':{'summary':'Inspect structure','steps':[
            {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect the selected table','arguments':{'path':'data/input/sample_orders.csv'}}]}})
    result=conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,
        message='Profile sample_orders.csv and suggest useful analysis.',use_history=False),project_root=tmp_path,model_client=client)
    assert len(client.requests)==2
    assert all(json.loads(item.messages[0].content).get('agent_knowhow') for item in client.requests)
    assert result['context_usage']['agent_knowhow']['selected']
    assert result['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'
    assert not result['execution_performed'] and not result['approval_performed']


@pytest.mark.parametrize('unrequested_skill',['export_csv','inspect_postgres_table'])
def test_inspection_generation_and_validation_exclude_unrequested_operations(tmp_path,unrequested_skill):
    from jsonschema import Draft202012Validator
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import conversation_turn,TurnRequest
    for name in ('context','agents','data/input'):
        shutil.copytree(ROOT/name,tmp_path/name)
    inspect={'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect table','arguments':{'path':'data/input/sample_orders.csv'}}
    wrong={'message':'Extra writer','plan':{'summary':'Inspect and export','steps':[inspect,
        {'step_id':'step_2','skill':unrequested_skill,'purpose':'Unrequested operation','arguments':{'path':'data/input/sample_orders.csv'}}]}}
    good={'message':'Inspection only.','plan':{'summary':'Inspect','steps':[inspect]}}
    client=Client(wrong,good)
    result=conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,
        message='Profile sample_orders.csv and suggest useful analysis.',use_history=False),project_root=tmp_path,model_client=client)
    assert len(client.requests)==2
    for request in client.requests:
        assert not Draft202012Validator(request.response_schema).is_valid(wrong)
        assert Draft202012Validator(request.response_schema).is_valid(good)
        system=json.loads(request.messages[0].content)
        assert unrequested_skill in system['available_skills']
        assert set(system['operation_argument_schemas'])=={'inspect_csv'}
    assert len(result['planner_result']['plan']['steps'])==1
    assert not result['execution_performed'] and not result['approval_performed']
