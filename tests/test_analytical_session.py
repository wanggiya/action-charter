"""Adaptive read-only tools, role-neutral orchestration, no authority from text."""
import json
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace
import pytest
from geoagent_harness.model.schemas import ModelResult
from geoagent_harness.model import ModelClientError
from geoagent_harness.tabular.strategy import discover_inputs,assess_table
from geoagent_harness.tabular.analyst import run_session,exploration_directory

@pytest.fixture
def data(tmp_path,monkeypatch):
    monkeypatch.setenv("ACTIONCHARTER_ANALYTICAL_RUNTIME","local")
    folder=tmp_path/'data/input/test';folder.mkdir(parents=True)
    (folder/'visits.csv').write_text('patient_nbr,age,stay\np001,older,2\np002,younger,4\np001,older,6\n')
    (folder/'visits_sample_2.csv').write_text('patient_nbr,age,stay\np001,older,2\np002,younger,4\n')
    (folder/'codes.csv').write_text('age,description\nolder,Older band\nyounger,Younger band\n')
    return tmp_path

class Client:
    def __init__(self,*actions):self.actions=list(actions);self.requests=[]
    def complete(self,request):
        self.requests.append(request)
        action=self.actions.pop(0)
        if isinstance(action,Exception):raise action
        return ModelResult(model='fixture',content=json.dumps(action))

def assessment(path='data/input/test/visits.csv',operation='profile'):
    return {'action':'assess_table','path':path,'operation':operation}

def profile(**options):return {'action':'profile_table','path':'data/input/test/visits.csv','options':options}

def test_model_uses_assessment_and_computed_evidence_then_summarizes(data):
    client=Client(assessment(),profile(numeric_columns=['stay'],distinct_columns=['patient_nbr']),{'action':'answer','message':'All 3 encounters were scanned; mean stay is 4 and there are 2 distinct patients.'})
    result=run_session(data,'Explore data/input/test and summarize hospital stays','test',model_client=client)
    assert result['status']=='completed' and result['model_calls']==3 and result['tool_calls']==3
    observed=result['observations'][-1]['result']
    assert observed['source_rows']==3 and observed['distinct_counts']['patient_nbr']==2
    assert next(p for p in observed['profiles'] if p['name']=='stay')['numeric']['mean']==4
    assert all('p001' not in m.content and 'p002' not in m.content for r in client.requests for m in r.messages)
    assert not result['data_written'] and not result['workflow_changed']
    assert not (data/'data/output').exists()


def test_operation_specific_limits_and_oversized_header_probe(data):
    path=data/'data/input/test/big.csv'
    with path.open('wb') as stream:
        stream.write(b'id,value\n'+b'a,1\n'*25);stream.truncate(1024**3+1)
    assert assess_table(data,'test/visits.csv','profile')['strategy']=='full_stream'
    assert assess_table(data,'test/big.csv','profile')['strategy']=='needs_alternative'
    assert not assess_table(data,'test/big.csv','profile')['sample_creation_available']
    assert next(f for f in discover_inputs(data,'test')['files'] if f['path'].endswith('big.csv'))['columns']==['id','value']
    with path.open('r+b') as stream:stream.truncate(9*1024**2)
    assert assess_table(data,'test/big.csv','profile')['strategy']=='full_stream'
    assert assess_table(data,'test/big.csv','join_csv')['strategy']=='needs_alternative'
    assert assess_table(data,'test/visits.csv','statistical_model')['strategy']=='unavailable'
    inventory=discover_inputs(data,'test')
    assert next(f for f in inventory['files'] if f['path'].endswith('big.csv'))['columns']==['id','value']
    sample=next(f for f in inventory['files'] if f['possible_sample'])
    assert sample['sample_provenance']=='unverified'


def test_unassessed_unknown_and_identifier_reads_rejected(data):
    client=Client(profile(),assessment(),profile(group_by=['patient_nbr']),{'action':'answer','message':'Identifier groups were blocked; use aggregate distinct counts.'})
    result=run_session(data,'Explore data/input/test','test',model_client=client)
    assert [j['status'] for j in result['journal']]==['completed','failed','completed','failed']
    assert not any(o['tool']=='profile_table' and 'source_sha256' in o['result'] for o in result['observations'])
    client=Client({'action':'profile_table','path':'data/input/outside.csv'},{'action':'answer','message':'outside'})
    result=run_session(data,'Explore data/input/test','test',model_client=client)
    assert result['status']=='partial' and result['tool_calls']==1


def test_tool_failure_and_timeout_keep_evidence_no_retry(data):
    client=Client(assessment(),profile(numeric_columns=['absent']),{'action':'answer','message':'The requested field does not exist; completed discovery is available.'})
    result=run_session(data,'Explore data/input/test','test',model_client=client)
    assert result['journal'][-1]['status']=='failed' and result['tool_calls']==3
    timed=Client(assessment(),ModelClientError.timeout())
    result=run_session(data,'Explore data/input/test','test',model_client=timed)
    assert result['status']=='partial' and result['failure_code']=='model_timeout'
    assert len(timed.requests)==2 and len(result['observations'])==2


def test_sample_is_not_certified_and_no_write_tools_exist(data):
    client=Client(assessment('data/input/test/visits_sample_2.csv'),{'action':'profile_table','path':'data/input/test/visits_sample_2.csv'},
        {'action':'answer','message':'This provisional sample has 2 rows; its provenance is unverified.'})
    result=run_session(data,'Explore data/input/test','test',model_client=client)
    assert result['observations'][-1]['result']['possible_sample']
    assert result['observations'][-1]['result']['sample_provenance']=='unverified'
    assert result['observations'][-1]['result']['source_rows']==2
    assert not list(data.rglob('*.gpkg')) and not (data/'data/output').exists()


def test_directory_boundaries_and_empty_folder(data,tmp_path):
    (data/'data/input/test/link.csv').symlink_to(data/'data/input/test/visits.csv')
    (data/'data/input/escape').symlink_to(data/'data/input/test',target_is_directory=True)
    assert not any(f['path'].endswith('link.csv') for f in discover_inputs(data,'test')['files'])
    for directory in ['../test','data/input/escape','/etc','test/../test','test//bad']:
        with pytest.raises(ValueError):discover_inputs(data,directory)
    (data/'data/input/empty').mkdir()
    result=run_session(data,'Explore data/input/empty','empty',model_client=Client())
    assert result['status']=='needs_input' and result['model_calls']==0


def test_loop_bounds_and_intent_scope(data):
    result=run_session(data,'Explore data/input/test','test',model_client=Client(*[{'invalid':'schema'}]*5))
    assert result['model_calls']==5 and result['status']=='partial'
    assert exploration_directory('Explore the data in data/input/test. No writes.')=='data/input/test'
    assert exploration_directory('Inspect sample_orders.csv.') is None
    assert exploration_directory('Continue exploring the missing fields',{'directory':'data/input/test'})=='data/input/test'


def test_conversation_records_loop_and_refresh_does_not_call_tools_again(data,monkeypatch):
    from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
    from geoagent_harness.interface_api.planner_submission import submission_action,SubmissionRequest
    repo=Path(__file__).parents[1]
    for directory in ['context','agents']:copytree(repo/directory,data/directory)
    (data/'README.md').write_text((repo/'README.md').read_text())
    client=Client(assessment(),profile(numeric_columns=['stay']),{'action':'answer','message':'The complete file has 3 encounters; mean stay is 4.'})
    request=TurnRequest(action='turn',conversation_id='a'*32,message='Explore data/input/test. Compute mean stay. No writes.')
    envelope=submission_action(SubmissionRequest(action='submit',submission_id='b'*32,conversation_id='a'*32,turn=request),project_root=data,model_client=client,background=False)
    response=envelope['conversation']
    assert response['analytical_session']['status']=='completed' and response['planner_result'] is None
    assert envelope['submission']['status']=='explored' and envelope['run'] is None
    assert not response['execution_performed'] and not response['proposal_changed']
    def no_discovery(*a,**kw):raise AssertionError('Refresh must use stored evidence')
    monkeypatch.setattr('geoagent_harness.tabular.analyst.discover_inputs',no_discovery)
    restored=conversation_turn(TurnRequest(action='read',conversation_id='a'*32),project_root=data)
    assert restored['analytical_session']==response['analytical_session']
    assert len(client.requests)==3


def test_explicit_statistics_cannot_be_omitted_silently(data):
    client=Client(assessment(),profile(),profile(numeric_columns=['stay'],distinct_columns=['patient_nbr']),{'action':'answer','message':'Mean stay is 4 and distinct patients 2.'})
    result=run_session(data,'Compute mean stay and distinct patient_nbr','test',model_client=client)
    assert result['journal'][2]['status']=='failed'
    assert 'Requested statistics' in result['observations'][2]['result']['error']
    assert result['observations'][3]['result']['distinct_counts']['patient_nbr']==2


def test_unsupported_final_claims_get_bounded_correction(data):
    client=Client(assessment(),profile(numeric_columns=['stay']),
        {'action':'answer','message':'Mean stay is 4 days; the sample is not representative.'},
        {'action':'answer','message':'Mean stay is 4 in unspecified source units; sample representativeness is unknown.'})
    result=run_session(data,'Compute mean stay','test',model_client=client)
    assert result['status']=='completed' and result['model_calls']==4 and result['tool_calls']==3
    assert 'unspecified source units' in result['message']


def test_continuation_verifies_previous_source_binding(data):
    client=Client(assessment(),profile(),{'action':'answer','message':'Three source rows were inspected.'})
    old=run_session(data,'Explore data/input/test','test',model_client=client)
    with (data/'data/input/test/visits.csv').open('a') as stream:stream.write('p003,older,8\n')
    client=Client(assessment(),profile(),{'action':'answer','message':'The source changed; start a fresh explicit exploration before drawing new conclusions.'})
    result=run_session(data,'Continue exploring','test',previous=old,model_client=client)
    assert result['journal'][-1]['status']=='failed'
    assert not any(o['tool']=='profile_table' and o['result'].get('source_sha256') for o in result['observations'])


def test_analytical_followup_and_narrow_legacy_provenance_projection(data):
    import sqlite3
    from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
    from geoagent_harness.interface_api.planner_submission import submission_action,SubmissionRequest
    from geoagent_harness.interface_api.planning_tasks import task_record
    repo=Path(__file__).parents[1]
    for directory in ['context','agents']:copytree(repo/directory,data/directory)
    (data/'README.md').write_text((repo/'README.md').read_text())
    identity='c'*32
    result=conversation_turn(TurnRequest(action='turn',conversation_id=identity,message='Explore data/input/test. Compute mean stay.'),
        project_root=data,model_client=Client(assessment(),profile(numeric_columns=['stay']),{'action':'answer','message':'Mean stay is 4.'}))
    assert result['analytical_session']['conversation_revision']==1
    assert all(m['task_id']==identity and m['conversation_id']==identity for m in result['messages'])
    # Reproduce only the old writer's missing IDs in our temporary fixture.
    db=data/'planner-workspace/tasks.sqlite3'
    with sqlite3.connect(db) as connection:
        for table in ['conversations','memories']:
            raw=connection.execute(f'SELECT value FROM {table} WHERE id=?',(identity,)).fetchone()[0]
            value=json.loads(raw)
            for m in value['messages'][-2:]:m['task_id']=None;m['conversation_id']=None
            connection.execute(f'UPDATE {table} SET value=? WHERE id=?',(json.dumps(value),identity))
        before=connection.execute('SELECT value FROM memories WHERE id=?',(identity,)).fetchone()[0]
    projected=task_record(data,identity)
    assert all(m['task_id']==identity for m in projected['messages'])
    with sqlite3.connect(db) as connection:assert connection.execute('SELECT value FROM memories WHERE id=?',(identity,)).fetchone()[0]==before
    followup=submission_action(SubmissionRequest(action='submit',submission_id='d'*32,conversation_id=identity,
        turn=TurnRequest(action='turn',conversation_id=identity,expected_revision=1,
                         message='Inspect test/visits.csv. Return row count and column names. No writes.')),
        project_root=data,model_client=Client(),background=False)['conversation']
    assert followup['revision']==2 and followup['planner_result']
    assert followup['analytical_session']['conversation_revision']==1
    assert all(m['task_id']==identity and m['conversation_id']==identity for m in task_record(data,identity)['messages'])
    # Nonempty foreign provenance is never normalized or imported.
    with sqlite3.connect(db) as connection:
        value=json.loads(connection.execute('SELECT value FROM memories WHERE id=?',(identity,)).fetchone()[0])
        value['messages'][0]['conversation_id']='e'*32
        connection.execute('UPDATE memories SET value=? WHERE id=?',(json.dumps(value),identity))
    with pytest.raises(Exception,match='provenance'):task_record(data,identity)


def test_explicit_grouped_nonmissing_counts_keep_legacy_contract(data):
    client=Client(assessment(operation='group'),profile(group_by=['age'],count_columns=['stay']),{'action':'answer','message':'All three encounters were grouped by the supplied age categories.'})
    result=run_session(data,'Explore data/input/test and count nonmissing stay by age','test',model_client=client)
    assert result['status']=='completed'
    observed=result['observations'][-1]['result']
    assert sum(g['stay_count'] for g in observed['groups'])==3
    assert 'dataset_profile' not in observed  # specialized request is not silently broadened/dropped
