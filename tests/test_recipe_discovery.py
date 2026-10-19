"""Planner-directed read-only discovery uses shared services and never authority."""
import json
import pytest
from typer.testing import CliRunner

from tests.test_planner_conversation import project,Client,turn,read
from tests.test_successful_retrieval import completed
from geoagent_harness.recipe_catalog.discovery import DiscoveryRequest,discover,library_structure
from geoagent_harness.recipe_catalog.composition import catalog,RecipeRequest,recipe_action
from geoagent_harness.planner.agent import PlannerAgentError
from geoagent_harness.model import ModelClientError
from geoagent_harness.cli import app


def request(action,**fields):
    return {'message':'Discovering recipes','recipe_discovery':{'action':action,**fields}}


def final_plan():
    return {'message':'Prepared inspection','reused_recipe_ids':['recipe_inspect_csv'],'plan':{'summary':'Inspect CSV structure','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect metadata','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False}]}}


def reply_properties(schema):
    return [schema['properties']] if 'properties' in schema else [branch['properties'] for branch in schema['anyOf']]


def test_planner_searches_inspects_and_plans_without_manual_selection(project):
    client=Client(request('search',query='csv inspection'),request('inspect',recipe_id='recipe_inspect_csv'),final_plan())
    reply=turn(project,client,'Inspect sample_orders.csv metadata')
    assert len(client.requests)==3
    assert reply['context_usage']['recipe_discovery']['actions']==['search','inspect']
    assert reply['context_usage']['recipe_reuse'][0]['id']=='recipe_inspect_csv'
    assert 'Adapted from: Inspect CSV' in reply['messages'][-1]['content']
    assert not reply['execution_performed'] and not reply['approval_performed']
    inspected=json.loads(client.requests[2].messages[-1].content)['recipe_discovery_result']
    assert inspected['definition']['composition_available']
    # Search summaries alone cannot be cited. Only the successful inspection
    # enables this ID in the following model request, within the same turn.
    for model_request in client.requests[:2]:
        assert all('reused_recipe_ids' not in props for props in reply_properties(model_request.response_schema))
        assert json.loads(model_request.messages[0].content)['reuse_claim_policy']['eligible_source_ids']==[]
    assert all(props['reused_recipe_ids']['items']['enum']==['recipe_inspect_csv'] for props in reply_properties(client.requests[2].response_schema))
    assert not (project/'workflow-state/interface-runs').exists()


def test_no_match_can_continue_with_normal_operations(project):
    ordinary=final_plan();ordinary.pop('reused_recipe_ids')
    client=Client(request('search',query='no_matching_method_zz'),ordinary)
    reply=turn(project,client,'Inspect sample_orders.csv')
    result=json.loads(client.requests[1].messages[-1].content)['recipe_discovery_result']
    assert result['status']=='no_matches'
    assert reply['planner_result'] and not reply['context_usage']['recipe_reuse']


def test_discovery_cannot_loop_or_execute(project):
    client=Client(request('search',query='csv'),request('search',query='csv'),request('search',query='csv'))
    with pytest.raises(PlannerAgentError,match='bounded budget'):
        turn(project,client,'Inspect CSV')
    assert len(client.requests)==3 and read(project)['revision']==0
    mixed=final_plan();mixed['recipe_discovery']={'action':'search','query':'csv'}
    client=Client(mixed)
    with pytest.raises(PlannerAgentError):turn(project,client,'Inspect CSV')
    assert len(client.requests)==1


def test_timeout_after_search_has_stage_and_preserves_workflow(project):
    client=Client(request('search',query='csv'),ModelClientError.timeout())
    with pytest.raises(ModelClientError) as caught:turn(project,client,'Inspect CSV')
    assert caught.value.planner_diagnostics['stage']=='planner_after_discovery'
    assert caught.value.planner_diagnostics['discovery_rounds']==1
    assert len(client.requests)==2 and read(project)['revision']==0


def test_registered_structure_hides_fixed_private_values_and_descriptions(project):
    definition=catalog(project)['recipe_clean_csv'].model_copy(deep=True)
    definition.id='recipe_private_fixture';definition.name='secret_data_file.csv';definition.description='private target data/output/private.csv'
    definition.steps[0].arguments['columns']=['private_customer_name']
    definition.steps[0].arguments['target_path']='data/output/private.csv'
    definition.parameters['source'].description='private/internal/customer.csv'
    public=library_structure(definition,project)
    content=json.dumps(public)
    for secret in ['secret_data_file','private.csv','private_customer_name','private/internal']:
        assert secret not in content
    assert not public['composition_available']
    assert public['steps'][0]['arguments']['columns']=={'current_binding_required':True}


def test_inspection_is_scoped_and_respects_history_off(completed):
    root,record,_=completed
    fields={'root':root,'conversation_id':record['conversation_id'],'available':[s['skill_id'] for s in record['steps']]}
    query=DiscoveryRequest(action='inspect',method_id=record['retention_basis']['method_id'])
    assert discover(query,**fields)['status']=='found'
    assert discover(query,**{**fields,'conversation_id':'c'*32})['status']=='not_found'
    assert discover(query,**fields,use_history=False)['status']=='not_found'
    assert discover(query,**fields,use_history=False,selected_id=query.method_id)['status']=='found'
    assert discover(query,**{**fields,'available':['inspect_csv']})['status']=='not_found'


def test_unknown_reuse_claim_gets_one_correction(project):
    invalid=final_plan();invalid['reused_recipe_ids']=['recipe_unknown']
    valid=final_plan();valid.pop('reused_recipe_ids')
    client=Client(invalid,valid)
    reply=turn(project,client,'Inspect CSV')
    assert len(client.requests)==2
    assert reply['planner_result'] and not reply['context_usage']['recipe_reuse']
    assert json.loads(client.requests[1].messages[-1].content)['failure_kind']=='reuse_claim'
    assert all('reused_recipe_ids' not in props for r in client.requests for props in reply_properties(r.response_schema))


def test_search_results_do_not_enable_provenance_without_inspection(project):
    valid=final_plan();valid.pop('reused_recipe_ids')
    client=Client(request('search',query='csv inspection'),final_plan(),valid)
    reply=turn(project,client,'Inspect sample_orders.csv')
    assert len(client.requests)==3 and not reply['context_usage']['recipe_reuse']
    assert all('reused_recipe_ids' not in props for r in client.requests for props in reply_properties(r.response_schema))


def test_repeated_unsupported_reuse_preserves_workflow_and_transcript(project):
    valid=final_plan();valid.pop('reused_recipe_ids')
    first=turn(project,Client(valid),'Inspect sample_orders.csv')
    client=Client(final_plan(),final_plan())
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client,'Inspect sample_orders.csv',revision=1)
    assert caught.value.reason=='unverified_reuse_claim' and len(client.requests)==2
    recovered=read(project)
    assert recovered['revision']==first['revision']
    assert recovered['messages']==first['messages']
    assert recovered['planner_result']==first['planner_result']


def test_supplied_source_is_decodable_but_still_must_match_proposed_skills(completed):
    root,record,_=completed
    method_id=record['retention_basis']['method_id']
    unrelated={'message':'Adapted method','reused_recipe_ids':[method_id], 'plan':{'summary':'Inspect vector','steps':[
        {'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect vector','arguments':{'path':'data/input/sample_points.geojson'}}]}}
    client=Client(unrelated,unrelated)
    with pytest.raises(PlannerAgentError) as caught:
        turn(root,client,'Inspect sample_points.geojson using the earlier CSV cleaning method',revision=1)
    assert caught.value.reason=='unverified_reuse_claim'
    for model_request in client.requests:
        assert all(method_id in props['reused_recipe_ids']['items']['enum'] for props in reply_properties(model_request.response_schema))


def test_changed_inspected_contract_is_rejected(project,monkeypatch):
    import geoagent_harness.recipe_catalog.discovery as service
    original=service.discover;calls=0
    def changing(*args,**kwargs):
        nonlocal calls
        result=original(*args,**kwargs);calls+=1
        if calls>1 and 'definition' in result:result['definition']['recipe_sha256']='f'*64
        return result
    monkeypatch.setattr(service,'discover',changing)
    from geoagent_harness.interface_api.server import InterfaceApiError
    client=Client(request('inspect',recipe_id='recipe_inspect_csv'),final_plan())
    with pytest.raises(InterfaceApiError,match='changed during planning'):turn(project,client,'Inspect CSV')
    assert read(project)['revision']==0


def test_api_cli_discovery_parity_uses_read_only_service(project):
    payload={'action':'search','query':'csv inspection'}
    expected=recipe_action(RecipeRequest.model_validate(payload),project_root=project)
    path=project/'search.json';path.write_text(json.dumps(payload))
    result=CliRunner().invoke(app,['reusable-recipes','--request-file',str(path),'--project-root',str(project)])
    assert result.exit_code==0,result.output
    assert json.loads(result.output)==expected
    assert not expected['execution_performed'] and not expected['approval_performed']


def test_correction_timeout_after_discovery_is_identified(project):
    invalid=final_plan();invalid['reused_recipe_ids']=['recipe_unknown']
    client=Client(request('search',query='csv'),invalid,ModelClientError.timeout())
    with pytest.raises(ModelClientError) as caught:turn(project,client,'Inspect CSV')
    assert caught.value.planner_diagnostics['stage']=='planner_correction_after_discovery'
    assert len(client.requests)==3 and read(project)['revision']==0


def test_http_unverified_reuse_returns_specific_model_guidance(project,monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    import geoagent_harness.interface_api.conversation as service
    from geoagent_harness.interface_api.server import _handler
    original=service.conversation_turn
    client=Client(final_plan(),final_plan())
    monkeypatch.setattr(service,'conversation_turn',lambda req,*,project_root:original(req,project_root=project_root,model_client=client))
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection(*server.server_address)
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'turn','conversation_id':'b'*32,'message':'Inspect sample_orders.csv'}),
            {'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response=connection.getresponse();body=json.loads(response.read());connection.close()
        assert response.status==422 and body['code']=='planner_reuse_unverified'
        assert 'ordinary planning needs no recipe selection' in body['retry_guidance']
        assert body['correction_attempted'] and not body['plan_saved'] and not body['execution_performed'] and not body['approval_performed']
    finally:
        server.shutdown();server.server_close();thread.join()
