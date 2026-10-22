"""Own-chat ranking is versioned evidence, never execution authority."""
import copy
import json
from types import SimpleNamespace
import pytest
from tests.test_planner_conversation import project, ID, Client, read, turn, plan
from geoagent_harness.interface_api.conversation import conversation_turn, TurnRequest
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.planner.outcome_recommendations import record_outcome, recommendations, reset, rank_recipes
from geoagent_harness.recipe_catalog.successful import contracts, _connection


def record(root, identity='a'*32, skill='inspect_csv', result=True):
    contract=contracts(root)[skill]
    return {'run_id':identity,'conversation_id':ID,'execution_performed':True,'finished_at':'2026-10-20',
        'status':'completed' if result else 'validation_failed',
        'retention_basis':{'operations':[{'step_id':'step_1','skill_id':skill,'contract_sha256':contract['contract_sha256']}]},
        'steps':[{'step_id':'step_1','skill_id':skill,'status':'validated_success' if result else 'validation_failed',
                  'outcome':{'secret':'must-not-store'},'validation_outcome':{'passed':result}}]}


def test_verified_persistence_privacy_and_reset(project):
    item=record(project)
    assert record_outcome(project,item)=='recorded'
    assert record_outcome(project,item)=='unchanged'
    assert recommendations(project,ID,['inspect_csv'])[0]['score']==0.2
    assert recommendations(project,'c'*32,['inspect_csv'])==[]
    assert recommendations(project,ID,['inspect_vector'])==[]
    db=_connection(project)
    payload=db.execute('SELECT payload FROM outcome_rank_v1').fetchone()[0];db.close()
    assert 'must-not-store' not in payload and 'outcome' not in payload
    changed=copy.deepcopy(item);changed['steps'][0]['validation_outcome']['passed']=False
    changed['steps'][0]['status']='validation_failed'
    with pytest.raises(ValueError):record_outcome(project,changed)
    reset(project,ID)
    assert recommendations(project,ID,['inspect_csv'])==[]


@pytest.mark.parametrize('status',['failed','cancelled','interrupted','running'])
def test_environment_and_interruption_excluded(project,status):
    item=record(project);item['status']=status
    assert record_outcome(project,item)=='excluded_environment_or_interruption'
    assert recommendations(project,ID,['inspect_csv'])==[]


def test_validation_failure_and_contract_change(project,monkeypatch):
    record_outcome(project,record(project,result=False))
    assert recommendations(project,ID,['inspect_csv'])[0]['score']==-0.2
    current=contracts(project);current['inspect_csv']['contract_sha256']='0'*64
    monkeypatch.setattr('geoagent_harness.planner.outcome_recommendations.contracts',lambda _:current)
    assert recommendations(project,ID,['inspect_csv'])==[]


def test_no_execution_or_incomplete_evidence(project):
    item=record(project);item['execution_performed']=False
    assert record_outcome(project,item)=='ineligible'
    item=record(project);item['steps']=[]
    assert record_outcome(project,item)=='incomplete'
    item=record(project);item['steps'][0]['skill_id']='inspect_vector'
    assert record_outcome(project,item)=='mismatched'
    item=record(project);item['steps'][0]['validation_outcome']={}
    assert record_outcome(project,item)=='no_verified_checks'
    assert recommendations(project,ID,['inspect_csv'])==[]


def test_limit_is_bounded_and_no_eviction(project,monkeypatch):
    monkeypatch.setattr('geoagent_harness.planner.outcome_recommendations.LIMIT',1)
    assert record_outcome(project,record(project))=='recorded'
    assert record_outcome(project,record(project,identity='d'*32))=='full'
    assert recommendations(project,ID,['inspect_csv'])[0]['verified_passes']==1


def test_preference_persists_no_model_and_stale_denied(project):
    assert read(project)['recommendations_enabled'] is False
    response=conversation_turn(TurnRequest(action='configure_recommendations',conversation_id=ID,expected_revision=0,recommendations_enabled=True),project_root=project)
    assert response['recommendations_enabled'] and response['revision']==1
    assert not response['execution_performed'] and not response['approval_performed']
    assert read(project)['recommendations_enabled']
    with pytest.raises(InterfaceApiError):
        conversation_turn(TurnRequest(action='configure_recommendations',conversation_id=ID,expected_revision=0,recommendations_enabled=False),project_root=project)
    assert not conversation_turn(TurnRequest(action='read',conversation_id='c'*32),project_root=project)['recommendations_enabled']


def test_planner_on_off_and_same_reply_baseline(project):
    record_outcome(project,record(project,skill='inspect_vector'))
    reply={'message':'Inspect','plan':plan()}
    baseline=Client(reply);first=turn(project,baseline)
    assert 'outcome_recommendations' not in json.loads(baseline.requests[0].messages[0].content)
    conversation_turn(TurnRequest(action='configure_recommendations',conversation_id=ID,expected_revision=1,recommendations_enabled=True),project_root=project)
    enabled=Client(reply);second=turn(project,enabled,revision=2)
    prompt=json.loads(enabled.requests[0].messages[0].content)
    assert prompt['outcome_recommendations']['items'][0]['operation_id']=='inspect_vector'
    assert first['planner_result']['plan']==second['planner_result']['plan']
    assert len(enabled.requests)==len(baseline.requests)==1
    assert not second['execution_performed'] and not second['approval_performed']


def test_recipe_evidence_only_breaks_relevance_ties():
    def recipe(identity,name,skill):return SimpleNamespace(id=identity,name=name,description='',steps=[SimpleNamespace(skill=skill)])
    a=recipe('a','CSV inspection','inspect_csv');b=recipe('b','CSV inspection','ext_text');c=recipe('c','raster','ext_text')
    items=[{'operation_id':'ext_text','score':0.9}]
    assert [r.id for r in rank_recipes([a,b,c],{'csv'},[]) ]==['a','b','c']
    assert [r.id for r in rank_recipes([a,b,c],{'csv'},items)]==['b','a','c']


def test_receipt_reports_supplied_order_not_model_adoption(project):
    from geoagent_harness.planner.outcome_recommendations import ranking_receipt
    record_outcome(project,record(project))
    items=recommendations(project,ID,['inspect_csv'])
    assert items[0]['contract_sha256']==contracts(project)['inspect_csv']['contract_sha256']
    assert 'not proof for new data' in items[0]['basis']
    a=SimpleNamespace(id='a',name='CSV',description='',steps=[SimpleNamespace(skill='inspect_vector')])
    b=SimpleNamespace(id='b',name='CSV',description='',steps=[SimpleNamespace(skill='inspect_csv')])
    receipt=ranking_receipt([a,b],{'csv'},items)
    assert receipt['baseline_recipe_ids']==['a','b'] and receipt['supplied_recipe_ids']==['b','a']
    assert receipt['recipe_order_changed'] and receipt['model_adoption']=='not_measured'
    assert receipt['authority_granted'] is False


def test_corrupt_classification_falls_back_instead_of_becoming_a_score(project):
    record_outcome(project,record(project))
    db=_connection(project)
    with db:
        db.execute("UPDATE outcome_rank_v1 SET payload=?",(json.dumps([{'operation_id':'inspect_csv','contract_sha256':contracts(project)['inspect_csv']['contract_sha256'],'result':'critic_says_great'}]),))
    db.close()
    with pytest.raises(ValueError,match='Stored outcome evidence is invalid'):
        recommendations(project,ID,['inspect_csv'])


def test_invalid_derived_store_uses_baseline_without_losing_proposal(project):
    record_outcome(project,record(project,skill='inspect_vector'))
    db=_connection(project)
    with db:db.execute("UPDATE outcome_rank_v1 SET payload='not json'")
    db.close()
    conversation_turn(TurnRequest(action='configure_recommendations',conversation_id=ID,expected_revision=0,recommendations_enabled=True),project_root=project)
    client=Client({'message':'Inspect the original source','plan':plan()})
    response=turn(project,client,revision=1)
    assert response['proposal_changed'] and response['planner_result']
    assert response['context_usage']['outcome_recommendations']['status']=='unavailable'
    assert len(client.requests)==1 and not response['execution_performed']
    assert 'outcome_recommendations' not in json.loads(client.requests[0].messages[0].content)


@pytest.mark.parametrize('skill,arguments',[
    ('select_csv_columns',{'path':'sample_orders.csv','columns':['order_id','region']}),
    ('filter_csv_rows',{'path':'sample_orders.csv','predicates':[{'column':'amount','operator':'ge','value':5,'value_type':'number'}],'match':'all'})])
def test_ordinary_csv_decoder_is_typed_and_full_proposal_excludes_actions(project,skill,arguments):
    client=Client({'message':'Proposed only','plan':{'summary':'CSV transformation','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect source','arguments':{'path':'sample_orders.csv'}},
        {'step_id':'step_2','skill':skill,'purpose':'Transform the original CSV','arguments':arguments,'depends_on':['step_1']}]}})
    response=conversation_turn(TurnRequest(action='turn',conversation_id=ID,message='Inspect sample_orders.csv and '+('select order_id and region' if skill=='select_csv_columns' else 'filter numeric amount >= 5')+' to a fresh CSV.',allowed_skill_ids=['inspect_csv',skill]),project_root=project,model_client=client)
    decoder=client.requests[0].response_schema
    proposal=decoder['anyOf'][0]
    assert 'workflow_action' not in proposal['properties']
    branch=next(b for b in decoder['$defs']['PlanStep']['anyOf'] if b['properties']['skill'].get('const')==skill)
    variants=branch['properties']['arguments']['anyOf']
    assert all(v['additionalProperties'] is False for v in variants)
    assert all(('path' in v['properties']) != ('source_step' in v['properties']) for v in variants)
    assert response['planner_result'] and not response['execution_performed']


@pytest.mark.parametrize('message,expected',[
    ('Inspect sample_orders.csv and select only order_id and region to a fresh CSV.',{'select_csv_columns'}),
    ('Keep rows where numeric amount is at least 5 in sample_orders.csv.',{'filter_csv_rows'}),
    ('Do not select columns. Only inspect sample_orders.csv.',set()),
    ('Remove the selection and skip filtering. Inspect sample_orders.csv.',set()),
    ('Select a file to inspect.',set())])
def test_table_request_coverage_is_narrow_and_respects_negation(message,expected):
    from geoagent_harness.planner.request_coverage import requested_table_operations
    assert requested_table_operations(message)==expected


def test_inspection_only_reply_cannot_claim_requested_selection(project):
    inspection={'summary':'Inspect CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read metadata','arguments':{'path':'sample_orders.csv'}}]}
    client=Client({'message':'Ready','plan':inspection},{'message':'Ready again','plan':inspection})
    from geoagent_harness.planner.agent import PlannerAgentError
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client,'Inspect sample_orders.csv and select only order_id and region into a fresh CSV.')
    assert 'select_csv_columns' in str(getattr(caught.value,'findings',[]))
    assert read(project)['revision']==0 and not (project/'approvals').exists()


@pytest.mark.parametrize('broad_selection',[False,True])
def test_automatic_simple_selection_focuses_schema_not_authority(project,broad_selection):
    from geoagent_harness.operations.registry import argument_models
    client=Client({'message':'Proposed only','plan':{'summary':'Select CSV fields','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'sample_orders.csv'}},
        {'step_id':'step_2','skill':'select_csv_columns','purpose':'Select','arguments':{'path':'sample_orders.csv','columns':['order_id','region']},'depends_on':['step_1']}]}})
    allowed=list(argument_models(project)) if broad_selection else []
    response=conversation_turn(TurnRequest(action='turn',conversation_id=ID,message='Inspect sample_orders.csv and select only order_id and region to a fresh CSV.',allowed_skill_ids=allowed),project_root=project,model_client=client)
    system=json.loads(client.requests[0].messages[0].content)
    assert set(system['operation_argument_schemas'])=={'inspect_csv','select_csv_columns'}
    assert set(system['available_skills'])==set(argument_models(project))
    assert system['requested_step_sequence']==['inspect_csv','select_csv_columns']
    assert not response['execution_performed'] and not response['approval_performed']
