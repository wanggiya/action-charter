"""Actual acceptance wording must receive calculation contracts and bounded repair."""
import json

import pytest

from tests.test_planner_conversation import project, Client, turn, read, ID, SCHEMA_DEFERRAL
from tests.test_bounded_calculations import proposal
from geoagent_harness.interface_api.conversation import Reply, TurnRequest, conversation_turn
from geoagent_harness.planner.agent import PlannerAgentError
from geoagent_harness.planner.bindings import allocate_csv_outputs
from geoagent_harness.planner.calculation_prompt import calculation_reply_example
from geoagent_harness.operations.registry import argument_models
from geoagent_harness.planner.prompt_scope import schema_scope

PROMPT = 'Inspect sample_orders.csv. Create a new numeric column doubled equal to amount multiplied by 2. Preserve all original columns and propagate missing values. Save to a fresh CSV. Do not execute yet.'
FOLLOWUP = 'Keep the CSV inspection. Add a calculation creating doubled = amount * 2 for every row. Save the result to a fresh CSV under data/output. Do not use PostgreSQL or PostGIS.'


def ready(multiplier=2,inspect=True):
    plan=proposal().plan.model_dump(mode='json')
    plan['steps'][0]['arguments']['calculations'][0]['expression']['right']['value']=multiplier
    if inspect:
        calculation=plan['steps'][0]
        calculation.update(step_id='step_2',depends_on=['step_1'])
        plan['steps'].insert(0,{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect original source','arguments':{'path':calculation['arguments']['path']},'requires_approval':False,'validation_required':False,'expected_artifacts':[]})
    return {'message':'Calculation ready for review. Nothing executed.', 'plan':plan}


@pytest.mark.parametrize('message', [FOLLOWUP, FOLLOWUP.replace('CSV inspection', 'inspection')])
@pytest.mark.parametrize('broad_selection', [False, True])
def test_keep_inspection_calculation_followup_has_focused_typed_decoder(project, message, broad_selection):
    initial = ready()
    initial['plan']['steps'] = initial['plan']['steps'][:1]
    saved = turn(project, Client(initial), 'Inspect sample_orders.csv. No writes.')
    client = Client(ready())
    result = conversation_turn(TurnRequest(action='turn', conversation_id=ID, expected_revision=1, message=message,
        allowed_skill_ids=list(argument_models(project)) if broad_selection else []), project_root=project, model_client=client)
    system = json.loads(client.requests[0].messages[0].content)
    assert set(system['operation_argument_schemas']) == {'inspect_csv', 'calculate_csv_columns'}
    assert set(system['available_skills']) == set(argument_models(project))
    assert system['requested_step_sequence'] == ['inspect_csv', 'calculate_csv_columns']
    assert system['requested_operation_coverage']['operation'] == 'calculate_csv_columns'
    steps = result['planner_result']['plan']['steps']
    assert steps[0]['arguments'] == saved['planner_result']['plan']['steps'][0]['arguments']
    assert steps[1]['depends_on'] == ['step_1']
    assert steps[1]['arguments']['path'] == steps[0]['arguments']['path']
    assert steps[1]['arguments']['calculations'][0]['expression']['right']['value'] == 2
    assert steps[1]['requires_approval'] and steps[1]['validation_required']
    assert result['context_usage']['model_request']['prompt_bytes'] < 28000
    assert result['context_usage']['model_request']['planner_contract'] == 'inspection-source-v2'
    assert not result['execution_performed'] and not result['approval_performed']
    assert not (project/'data/output').exists()


def test_failed_keep_inspection_followup_preserves_saved_inspection(project):
    initial = ready()
    initial['plan']['steps'] = initial['plan']['steps'][:1]
    saved = turn(project, Client(initial), 'Inspect sample_orders.csv. No writes.')
    invalid = {'message': 'Ready', 'plan': None, 'undeclared_fixture_field': True}
    client = Client(invalid, invalid)
    with pytest.raises(PlannerAgentError):
        turn(project, client, FOLLOWUP, revision=1)
    assert len(client.requests) == 2
    assert read(project)['planner_result'] == saved['planner_result']
    assert read(project)['revision'] == 1
    assert not (project/'data/output').exists()


@pytest.mark.parametrize('change', ['source', 'preview', 'dependency'])
def test_keep_inspection_followup_repairs_source_or_settings_drift(project, change):
    initial = ready()
    initial['plan']['steps'] = initial['plan']['steps'][:1]
    turn(project, Client(initial), 'Inspect sample_orders.csv. No writes.')
    wrong = ready()
    if change == 'source':
        wrong['plan']['steps'][0]['arguments']['path'] = 'data/input/example.csv'
    elif change == 'preview':
        wrong['plan']['steps'][0]['arguments']['preview_rows'] = 20
    else:
        wrong['plan']['steps'][1].pop('depends_on')
    client = Client(wrong, ready())
    result = turn(project, client, FOLLOWUP, revision=1)
    assert len(client.requests) == 2
    decoder = client.requests[0].response_schema
    args = decoder['$defs']['WorkflowPlan']['properties']['steps']['prefixItems'][0]['properties']['arguments']
    assert args['additionalProperties'] is False
    assert args['properties']['path']['const'] == 'data/input/sample_orders.csv'
    assert result['planner_result']['plan']['steps'][0]['arguments'] == {'path': 'data/input/sample_orders.csv'}
    assert not result['execution_performed']


def test_exact_acceptance_wording_gets_positive_complete_calculation_example(project):
    client=Client(ready())
    result=turn(project,client,PROMPT)
    system=json.loads(client.requests[0].messages[0].content)
    assert 'calculate_csv_columns' in system['operation_argument_schemas']
    assert set(system['operation_argument_schemas'])=={'inspect_csv','calculate_csv_columns'}
    assert set(system['available_skills'])==set(argument_models(project))
    example=Reply.model_validate(system['reply_shape_example'])
    assert example.plan and example.plan.steps[-1].skill=='calculate_csv_columns'
    assert 'requires_approval' not in system['reply_shape_example']['plan']['steps'][-1]
    assert result['planner_result']['plan']['steps'][-1]['requires_approval']
    assert result['planner_result']['plan']['steps'][-1]['validation_required']
    assert system['calculation_contract']
    assert 'conversion_clarification_example' not in system
    assert result['context_usage']['model_request']['prompt_bytes']<17000
    assert len(system['mandatory_rules'])==10
    assert set(system['required_skill_arguments']).issubset({'inspect_csv','calculate_csv_columns'})
    assert not any('implemented and approved' in text for text in system['instructions'])
    assert any('propose operations that require later approval' in text for text in system['instructions'])
    assert not result['execution_performed'] and not result['approval_performed']
    assert not (project/'data/output').exists()


@pytest.mark.parametrize('message',[
    'Inspect x.csv and multiply amount by 2',
    'Inspect x.csv; amount multiplied by 2 into a new column',
    'Inspect x.csv; amount divided by 2',
    'Inspect x.csv; create a computed column',
    'Inspect x.csv; create a numeric column',
    'Inspect x.csv; create a new column',
])
def test_calculation_inflections_preserve_full_allowlist(message):
    available=['inspect_csv','calculate_csv_columns','aggregate_csv','inspect_vector']
    original=available.copy()
    detailed=schema_scope(message,available)
    assert 'calculate_csv_columns' in detailed
    assert 'inspect_vector' not in detailed
    assert available==original
    assert 'aggregate_csv' in schema_scope(message+' then group and sum by region',available)


@pytest.mark.parametrize('include_inspection',[True,False])
def test_complete_example_matches_typed_argument_models(project,include_inspection):
    reply=Reply.model_validate(calculation_reply_example(include_inspection=include_inspection))
    allocate_csv_outputs(reply.plan)
    models=argument_models(project)
    for step in reply.plan.steps:
        models[step.skill].model_validate(step.arguments)
    assert not reply.execution_performed and not reply.approval_performed


def test_schema_promise_receives_one_grounded_correction_not_a_canned_workflow(project):
    client=Client(SCHEMA_DEFERRAL,ready(multiplier=7))
    result=turn(project,client,PROMPT)
    correction=json.loads(client.requests[1].messages[-1].content)
    assert correction['failure_kind']=='repair_deferral'
    assert correction['valid_reply_structure_example']['plan']
    assert correction['example_scope']
    assert 'Please confirm' not in client.requests[1].messages[-2].content
    assert result['planner_result']['plan']['steps'][-1]['arguments']['calculations'][0]['expression']['right']['value']==7
    assert result['context_usage']['effort_budget']['model_calls']==2
    assert not result['execution_performed']


def test_repeated_deferral_has_specific_failure_and_preserves_last_workflow(project):
    first=turn(project,Client(ready()),PROMPT)
    client=Client(SCHEMA_DEFERRAL,SCHEMA_DEFERRAL)
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client,PROMPT,revision=1)
    assert caught.value.reason=='schema_repair_deferred'
    assert caught.value.correction_attempted
    assert caught.value.planner_diagnostics['effort_budget']['model_calls']==2
    assert len(client.requests)==2
    assert read(project)['planner_result']==first['planner_result']
    assert read(project)['revision']==first['revision']
    assert not (project/'data/output').exists()


def test_original_schema_finding_survives_following_deferral(project):
    bad=ready();bad['plan']['steps'][-1]['arguments'].pop('missing_policy')
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,Client(bad,SCHEMA_DEFERRAL),PROMPT)
    assert caught.value.reason=='schema_repair_deferred'
    assert any('missing_policy' in finding for finding in caught.value.findings)
    assert read(project)['revision']==0


def test_genuine_missing_column_question_remains_valid(project):
    client=Client({'message':'Which numeric column should I scale, and by what factor?', 'plan':None})
    result=turn(project,client,'Inspect sample_orders.csv and add a calculated column.')
    assert result['planner_result'] is None and len(client.requests)==1


def test_selected_calculation_example_does_not_invent_inspection_permission(project):
    client=Client(ready(inspect=False))
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,message='Create a numeric column doubled equal to amount multiplied by 2 in sample_orders.csv, preserving missing values.',
        allowed_skill_ids=['calculate_csv_columns']),project_root=project,model_client=client)
    system=json.loads(client.requests[0].messages[0].content)
    assert [s['skill'] for s in system['reply_shape_example']['plan']['steps']]==['calculate_csv_columns']
    assert result['planner_result']


def test_repeated_deferral_http_response_does_not_request_technical_scope(project,monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    import geoagent_harness.interface_api.conversation as service
    original=service.conversation_turn
    client=Client(SCHEMA_DEFERRAL,SCHEMA_DEFERRAL)
    monkeypatch.setattr(service,'conversation_turn',lambda request,*,project_root:original(request,project_root=project_root,model_client=client))
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection(*server.server_address)
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'turn','conversation_id':ID,'message':PROMPT}),
            {'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response=connection.getresponse();body=json.loads(response.read());connection.close()
        assert response.status==422 and body['code']=='planner_repair_deferred'
        assert 'model-output failure' in body['retry_guidance']
        assert 'Clarify the exact skills' not in body['retry_guidance']
        assert body['planner_diagnostics']['effort_budget']['model_calls']==2
        assert not body['approval_performed'] and not body['execution_performed'] and not body['plan_saved']
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)


def inspection_claiming_calculation():
    # Reproduces the persisted local failure without using/modifying user records.
    return {
        'message': "The workflow to create doubled equal to amount multiplied by 2 is planned.",
        'plan': {'summary': PROMPT, 'steps': [{
            'step_id':'step_1', 'skill':'inspect_csv',
            'purpose':'Inspect metadata and preview',
            'arguments':{'path':'data/input/sample_orders.csv'},
        }]},
    }


def test_inspection_only_success_claim_is_corrected_before_storage(project):
    client=Client(inspection_claiming_calculation(),ready())
    result=turn(project,client,PROMPT)
    assert len(client.requests)==2
    system=json.loads(client.requests[0].messages[0].content)
    assert system['requested_operation_coverage']['operation']=='calculate_csv_columns'
    correction=json.loads(client.requests[1].messages[-1].content)
    assert correction['failure_kind']=='request_coverage'
    assert 'missing from plan.steps' in correction['deterministic_findings'][0]
    assert any(step['skill']=='calculate_csv_columns' for step in result['planner_result']['plan']['steps'])
    assert result['context_usage']['effort_budget']['model_calls']==2
    assert read(project)['planner_result']==result['planner_result']
    assert not result['approval_performed'] and not result['execution_performed']
    assert not (project/'data/output').exists()


def test_repeated_operation_omission_preserves_workflow_and_transcript(project):
    first=turn(project,Client(inspection_claiming_calculation()),'Inspect sample_orders.csv. No writes.')
    client=Client(inspection_claiming_calculation(),inspection_claiming_calculation())
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client,PROMPT,revision=1)
    assert caught.value.reason=='request_coverage_incomplete'
    assert caught.value.correction_attempted and len(client.requests)==2
    assert read(project)['planner_result']==first['planner_result']
    assert read(project)['messages']==first['messages']
    assert read(project)['revision']==1
    assert not (project/'data/output').exists()


@pytest.mark.parametrize('message',[
    PROMPT,
    'Add calculate_csv_columns: doubled = amount multiplied by 2.',
    'Inspect x.csv then multiply amount by 2. Do not execute.',
    'Create a derived column total. Do not execute yet.',
    'Inspect orders.csv, then calculate doubled = amount * 2.',
])
def test_explicit_calculation_coverage_requests(message):
    from geoagent_harness.planner.request_coverage import requests_calculated_columns
    assert requests_calculated_columns(message)


@pytest.mark.parametrize('message',[
    'Inspect sample_orders.csv. Return row count and column names. No writes.',
    'Select columns region and amount.',
    'Join the city column from the lookup table.',
    'Remove calculate_csv_columns and inspect the source instead.',
    'Do not create any new numeric columns. Inspect only.',
    'Inspect the original file without calculating columns.',
    'Skip the calculation step and inspect only.',
    'Create a column city using a join.',
])
def test_metadata_projection_join_and_negative_requests_do_not_require_calculation(message):
    from geoagent_harness.planner.request_coverage import requests_calculated_columns
    assert not requests_calculated_columns(message)


def test_unavailable_calculation_can_explain_without_partial_success(project):
    client=Client({'message':'The selected skills only allow inspection; enable calculated columns or automatic selection.', 'plan':None})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,message=PROMPT,
        allowed_skill_ids=['inspect_csv']),project_root=project,model_client=client)
    assert not result['proposal_changed'] and result['planner_result'] is None
    assert len(client.requests)==1
    assert json.loads(client.requests[0].messages[0].content)['requested_operation_coverage']['available'] is False


def test_http_repeated_omission_is_specific_and_does_not_save_or_execute(project,monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    import geoagent_harness.interface_api.conversation as service
    original=service.conversation_turn
    client=Client(inspection_claiming_calculation(),inspection_claiming_calculation())
    monkeypatch.setattr(service,'conversation_turn',lambda request,*,project_root:original(request,project_root=project_root,model_client=client))
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection(*server.server_address)
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'turn','conversation_id':ID,'message':PROMPT}),
            {'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response=connection.getresponse();body=json.loads(response.read());connection.close()
        assert response.status==422 and body['code']=='planner_scope_incomplete'
        assert 'missing from plan.steps' in body['finding']
        assert body['correction_attempted']
        assert not body['plan_saved'] and not body['approval_performed'] and not body['execution_performed']
        assert 'authorization instructions' in body['retry_guidance']
    finally:
        server.shutdown();server.server_close();thread.join()


@pytest.mark.parametrize('message',[
    'Create a numeric column doubled, then create a numeric column quadrupled from doubled.',
    'Create two numeric columns from the source.',
    'Create a numeric column doubled. Do not inspect the source.',
])
def test_complex_or_negative_requests_keep_general_step_decoding(message):
    from geoagent_harness.planner.request_coverage import simple_calculation_sequence
    assert not simple_calculation_sequence(message)


def test_repeat_existing_inspection_calculation_gets_typed_two_step_guide(project):
    turn(project,Client(ready()),PROMPT)
    client=Client(ready(multiplier=3))
    response=turn(project,client,'Replace the current workflow: inspect sample_orders.csv and calculate doubled = amount * 3, propagating missing values. Save to a fresh CSV.',revision=1)
    system=json.loads(client.requests[0].messages[0].content)
    assert system['requested_step_sequence']==['inspect_csv','calculate_csv_columns']
    assert len(client.requests[0].response_schema['$defs']['WorkflowPlan']['properties']['steps']['prefixItems'])==2
    assert response['planner_result']['plan']['steps'][1]['arguments']['calculations'][0]['expression']['right']['value']==3
    assert not response['execution_performed']


def test_existing_calculation_without_inspection_keeps_general_structure(project):
    turn(project,Client(ready(inspect=False)),PROMPT.replace('Inspect sample_orders.csv. ',''))
    client=Client(ready(multiplier=3,inspect=False))
    response=turn(project,client,'Change the numeric column doubled to amount multiplied by 3 in sample_orders.csv, preserving missing values.',revision=1)
    assert 'requested_step_sequence' not in json.loads(client.requests[0].messages[0].content)
    assert [step['skill'] for step in response['planner_result']['plan']['steps']]==['calculate_csv_columns']
