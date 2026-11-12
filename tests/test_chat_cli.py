"""Shared API continuity, recorded-result parity and uncertainty/authority boundaries."""
import json
from pathlib import Path
from shutil import copytree
import httpx,pytest
from typer.testing import CliRunner
from geoagent_harness.apps.cli.main import app
from geoagent_harness.apps.chat.client import ChatClient, ChatError
from geoagent_harness.apps.chat.views import saved_view, render_view, clean
from geoagent_harness.task_actions.conversation import conversation_turn, TurnRequest
from geoagent_harness.task_actions.planner_submission import submission_action, SubmissionRequest
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.data.tabular.dataset_service import profile_dataset

ID='e'*32
@pytest.fixture
def project(tmp_path,monkeypatch):
    repo=Path(__file__).parents[1]
    for name in ['context','agents']:copytree(repo/name,tmp_path/name)
    (tmp_path/'data/input').mkdir(parents=True)
    for name in ['sample_orders.csv','sample_points.geojson','sample_regions.csv']:(tmp_path/'data/input'/name).write_bytes((repo/'data/input'/name).read_bytes())
    (tmp_path/'README.md').write_text((repo/'README.md').read_text())
    monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
    return tmp_path

@pytest.fixture
def api(project,monkeypatch):
    real=httpx.Client;calls=[]
    def handle(request):
        payload=json.loads(request.content);calls.append((request.url.path,payload))
        try:
            if request.url.path.endswith('/conversation'):value=conversation_turn(TurnRequest.model_validate(payload),project_root=project)
            else:value=submission_action(SubmissionRequest.model_validate(payload),project_root=project,background=False)
            return httpx.Response(200,json=value)
        except (ValueError,InterfaceApiError) as e:return httpx.Response(400,json={'error':str(e)})
    monkeypatch.setattr(httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(handle),**kw))
    return calls

def test_cli_continues_frontend_plan_and_frontend_reads_cli_revision(project,api):
    first=submission_action(SubmissionRequest(action='submit',conversation_id=ID,submission_id='a'*32,turn=TurnRequest(action='turn',conversation_id=ID,message='Inspect sample_regions.csv.')),project_root=project,background=False)['conversation']
    runner=CliRunner()
    listed=runner.invoke(app,['chat','list','--json']);assert listed.exit_code==0,listed.output
    assert ID in listed.stdout
    response=runner.invoke(app,['chat','send','Inspect sample_orders.csv.','--chat',ID,'--expected-revision','1','--json'])
    assert response.exit_code==0,response.output
    value=json.loads(response.stdout)
    assert value['conversation']['revision']==2
    assert value['conversation']['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'
    assert not value['execution_performed'] and value['run'] is None
    restored=conversation_turn(TurnRequest(action='read',conversation_id=ID),project_root=project)
    assert restored['planner_result']==value['conversation']['planner_result']
    assert len(restored['messages'])==4
    assert first['messages'][0]==restored['messages'][0]
    stale=runner.invoke(app,['chat','send','Inspect sample_points.geojson.','--chat',ID,'--expected-revision','1'])
    assert stale.exit_code==2 and 'changed' in stale.output
    assert len([p for url,p in api if url.endswith('/submit') and p['action']=='submit'])==1
    receipt=runner.invoke(app,['chat','receipt',ID,value['submission']['submission_id'],'--json'])
    assert receipt.exit_code==0 and json.loads(receipt.stdout)['submission']==value['submission']
    assert not (project/'approvals').exists() and not (project/'inspection-runs').exists()


def test_cli_creates_a_chat_discoverable_by_frontend(project,api):
    result=CliRunner().invoke(app,['chat','send','Inspect sample_orders.csv.','--json'])
    assert result.exit_code==0,result.output
    value=json.loads(result.stdout);identity=value['conversation']['conversation_id']
    listed=conversation_turn(TurnRequest(action='list',conversation_id='0'*32),project_root=project)
    assert identity in [c['conversation_id'] for c in listed['conversations']]
    followup=submission_action(SubmissionRequest(action='submit',conversation_id=identity,submission_id='b'*32,turn=TurnRequest(action='turn',conversation_id=identity,expected_revision=1,message='Inspect sample_regions.csv.')),project_root=project,background=False)['conversation']
    shown=CliRunner().invoke(app,['chat','show',identity,'--json'])
    assert shown.exit_code==0 and json.loads(shown.stdout)['messages']==followup['messages']
    assert all(p.get('inspect_on_send') is False for url,p in api if url.endswith('/submit') and p['action']=='submit')


def saved_state(project):
    r=profile_dataset(project,'sample_orders.csv',{'group_by':['region'],'numeric_columns':['amount']},owner=ID)
    return {'conversation_id':ID,'revision':3,'analytical_session':{'conversation_revision':2,'message':'Recorded source findings','observations':[{'tool':'profile_table','result':{'dataset_profile':r}}]}},r


def test_result_views_match_recorded_frontend_facts_without_reads(project,monkeypatch):
    state,r=saved_state(project)
    def forbidden(*args,**kw):raise AssertionError('Viewing cannot scan, dispatch or invoke a model')
    monkeypatch.setattr('geoagent_harness.data.tabular.dataset_service.profile_dataset',forbidden)
    for view in ['overview','columns','table','chart','groups','checks']:
        value=saved_view(state,view)
        assert value['source_sha256']==r['source_sha256'] and value['recorded_only'] and not value['execution_performed']
        assert render_view(value)
    v=saved_view(state,'columns',field='amount')
    assert v['profiles'][0]==next(p for p in r['profiles'] if p['name']=='amount')
    assert all(all(saved[k]==v for k,v in original.items()) for saved,original in zip(saved_view(state,'groups')['rows'],r['groups']))
    assert saved_view(state,'table',offset=1,limit=1)['rows']==r['table']['preview'][1:2]
    assert saved_view(state,'checks')['runtime']==r['runtime']
    assert saved_view(state,'chart',field='amount')['buckets']==next(p for p in r['profiles'] if p['name']=='amount')['numeric']['histogram']
    assert saved_view(state,'columns',offset=999)['profiles']==[]
    with pytest.raises(ChatError):saved_view(state,'columns',field='absent')
    with pytest.raises(ChatError):saved_view(state,'table',limit=101)
    with pytest.raises(ChatError):saved_view({'conversation_id':ID},'overview')
    state['analytical_session']['observations']*=2
    with pytest.raises(ChatError,match='source'):saved_view(state)


def test_transport_no_remote_proxy_redirect_or_automatic_retry(monkeypatch):
    for url in ['https://127.0.0.1:8765','http://example.com:8765','http://user:pass@localhost:8765','http://localhost:8765/path','http://localhost:99999']:
        with pytest.raises(ChatError):ChatClient(url)
    real=httpx.Client;seen=[]
    def factory(**kw):
        assert kw['trust_env'] is False and kw['follow_redirects'] is False
        def handle(request):seen.append(request);raise httpx.ReadTimeout('uncertain')
        return real(transport=httpx.MockTransport(handle),**kw)
    monkeypatch.setattr(httpx,'Client',factory)
    with pytest.raises(ChatError,match='automatically retried'):ChatClient().conversation('read',ID)
    assert len(seen)==1
    assert '\x1b' not in clean('\x1b[31mheader\ntext')


def test_terminal_field_and_group_charts_use_recorded_denominators(project):
    from geoagent_harness.apps.chat.views import grouped_chart
    state,r=saved_state(project)
    field=saved_view(state,'chart',field='region')
    output=render_view(field)
    assert '#' in output and '% matching' in output and 'region' in output
    detail=render_view(saved_view(state,'columns',field='region'))
    assert 'Recorded value frequencies' in detail and '%' in detail
    groups=saved_view(state,'groups',limit=100)
    total=grouped_chart(groups,'total')
    assert sum(b['count'] for b in total['buckets'])==pytest.approx(100)
    assert '#' in render_view(total) and '%' in render_view(total)
    within=grouped_chart(groups,'within')
    assert all(b['count']==100 for b in within['buckets'])
    with pytest.raises(ChatError):grouped_chart({**groups,'total_rows':101})
