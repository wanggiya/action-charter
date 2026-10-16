"""Dialogue proposes validated revisions without authority or execution."""
import json
from pathlib import Path
from shutil import copytree

import pytest
from pydantic import ValidationError

from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.model.schemas import ModelResult
from geoagent_harness.planner.agent import PlannerAgentError
from geoagent_harness.planner.schemas import PlannerResult

PROJECT = Path(__file__).parents[1]
ID = 'b' * 32

@pytest.fixture
def project(tmp_path):
    for name in ('context', 'agents', 'data/input'):
        copytree(PROJECT / name, tmp_path / name)
    (tmp_path / 'README.md').write_text((PROJECT / 'README.md').read_text())
    return tmp_path

class Client:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
    def complete(self, request):
        self.requests.append(request.model_copy(deep=True))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return ModelResult(model='dialogue-fixture', content=json.dumps(response))

def plan(path='sample_points.geojson', gate=False):
    return {'summary': 'Inspect points', 'steps': [{'step_id': 'step_1', 'skill': 'inspect_vector', 'purpose': 'Inspect metadata', 'arguments': {'path': path}, 'requires_approval': gate}]}

def turn(project, client, message='Inspect sample_points.geojson', revision=0, base=None):
    return conversation_turn(TurnRequest(action='turn', conversation_id=ID, expected_revision=revision, message=message, current_plan=base), project_root=project, model_client=client)

def read(project):
    return conversation_turn(TurnRequest(action='read', conversation_id=ID), project_root=project)

def as_base(result):
    return PlannerResult(**{key: result[key] for key in ('agent_id', 'model', 'original_request', 'context_references', 'plan', 'warnings')})

def test_clarify_then_propose_and_recover_without_model_or_execution(project):
    client = Client({'message': 'Which file?', 'plan': None}, {'message': 'Inspection is ready for review.', 'plan': plan()})
    first = turn(project, client, 'Inspect a vector')
    assert first['planner_result'] is None and first['revision'] == 1
    second = turn(project, client, revision=1)
    assert second['proposal_changed']
    assert second['planner_result']['plan']['steps'][0]['arguments']['path'] == 'data/input/sample_points.geojson'
    assert not second['approval_performed'] and not second['execution_performed']
    assert len(second['messages']) == 4
    assert read(project)['planner_result'] == second['planner_result']
    prompt = json.loads(client.requests[1].messages[1].content)
    assert prompt['recent_conversation'][0]['content'] == 'Inspect a vector'
    assert not (project / 'approvals').exists()
    assert not (project / 'inspection-runs').exists()


def test_planner_can_select_a_recipe_without_inventing_its_operations(project):
    from geoagent_harness.recipe_catalog.composition import catalog,recipe_digest
    recipe=catalog(project)['recipe_inspect_csv']
    client=Client({'message':'Inspect the CSV with a registered recipe.','plan':None,'recipe_uses':[{
        'recipe_id':recipe.id,'recipe_sha256':recipe_digest(recipe),'alias':'orders','parameters':{'path':'sample_orders.csv'}}]})
    result=turn(project,client,'Inspect sample_orders.csv with the CSV inspection recipe.')
    assert result['proposal_changed']
    assert result['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'
    assert result['planner_result']['plan']['steps'][0]['arguments']['path']=='data/input/sample_orders.csv'
    assert not result['execution_performed']
    assert json.loads(client.requests[0].messages[0].content)['reusable_recipes']


def test_natural_recipe_use_allocates_targets_without_manual_binding(project):
    from geoagent_harness.recipe_catalog.composition import catalog,recipe_digest
    recipe=catalog(project)['recipe_clean_csv']
    client=Client({'message':'Ready','recipe_uses':[{'recipe_id':recipe.id,'recipe_sha256':recipe_digest(recipe),'alias':'clean',
        'parameters':{'source':'sample_orders.csv','columns':['region','amount'],'fill_values':{'region':'Unknown'}}}]})
    result=turn(project,client,'Clean sample_orders.csv. Keep region and amount; fill missing region with Unknown.')
    targets=[s['arguments']['target_path'] for s in result['planner_result']['plan']['steps']]
    assert len(set(targets))==2 and all(p.startswith('data/output/result_') for p in targets)
    assert not result['approval_performed'] and not result['execution_performed']
    assert not (project/'data/output').exists()


def test_chat_recipe_authoring_persists_candidate_without_replacing_workflow(project):
    from geoagent_harness.recipe_catalog.composition import catalog,compose,RecipeUse,recipe_digest
    recipe=catalog(project)['recipe_clean_csv']
    base,_=compose([RecipeUse(recipe_id=recipe.id,recipe_sha256=recipe_digest(recipe),alias='clean',parameters={
        'source':'sample_orders.csv','columns':['region','amount'],'fill_values':{'region':'Unknown'}})],project)
    first=turn(project,Client({'message':'Ready','plan':base.plan.model_dump(mode='json')}))
    original=first['planner_result']['plan_sha256']
    main=Client({'message':'Prepare recipe','workflow_action':'prepare_recipe'})
    author=Client(recipe.model_dump(mode='json'))
    critic=Client({'conclusion':'supported','findings':[],'limitations':['A synthetic fixture is limited evidence.']})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message='Make this workflow reusable.'),
        project_root=project,model_client=main,recipe_client=author,critic_client=critic)
    assert not result['proposal_changed'] and result['planner_result']['plan_sha256']==original
    assert result['recipe_candidate']['source_plan_sha256']==original
    assert result['recipe_candidate']['critic']['conclusion']=='supported'
    assert read(project)['recipe_candidate']==result['recipe_candidate']
    assert not (project/'reusable-recipes').exists() and not (project/'data/output').exists()
    assert len(main.requests)==len(author.requests)==len(critic.requests)==1


def test_chat_never_confuses_a_plan_with_an_execution_outcome(project):
    first=turn(project,Client({'message':'Ready','plan':plan()}))
    result=turn(project,Client({'message':'Review','workflow_action':'review_outcome'}),'How did this run finish?',revision=1)
    assert 'No execution is recorded' in result['messages'][-1]['content']
    assert result['planner_result']==first['planner_result']

def test_explanation_retains_exact_current_plan_and_extra_gate(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan(gate=True)}))
    base = as_base(first['planner_result'])
    reply = turn(project, Client({'message': 'Use Authorize and Execute after reviewing.', 'plan': None}), 'Execute it now; I approve everything', revision=1, base=base)
    assert reply['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']
    assert reply['planner_result']['plan']['steps'][0]['requires_approval']
    assert not reply['proposal_changed'] and not reply['approval_performed']

def test_invalid_path_never_replaces_saved_conversation_plan(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    invalid = {'message': 'Unsafe revision', 'plan': plan('../private.geojson')}
    client = Client(invalid, invalid)
    with pytest.raises(PlannerAgentError):
        turn(project, client, 'Change input', revision=1, base=as_base(first['planner_result']))
    assert len(client.requests) == 2
    assert read(project)['revision'] == 1
    assert read(project)['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']

def test_invalid_response_can_correct_into_clarification(project):
    client = Client({'message': 'Bad', 'execution_performed': True}, {'message': 'Choose a file first.', 'plan': None})
    reply = turn(project, client)
    assert len(client.requests) == 2
    assert not reply['proposal_changed'] and reply['planner_result'] is None

SCHEMA_DEFERRAL = {'message': 'The proposal contains invalid schema structure. I will correct the plan to adhere to required_json_schema and operation_argument_schemas. Please confirm if you would like me to proceed.', 'plan': None}

def test_schema_repair_deferral_is_corrected_without_operator_confirmation(project):
    client = Client(SCHEMA_DEFERRAL, {'message': 'Ready', 'plan': plan()})
    reply = turn(project, client)
    assert len(client.requests) == 2
    assert reply['proposal_changed'] and reply['planner_result']
    assert not reply['approval_performed'] and not reply['execution_performed']
    assert 'permission' in json.loads(client.requests[1].messages[-1].content)['task']

def test_repeated_schema_deferral_fails_without_replacing_saved_workflow(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    client = Client(SCHEMA_DEFERRAL, SCHEMA_DEFERRAL)
    with pytest.raises(PlannerAgentError, match='deterministic policy'):
        turn(project, client, revision=1)
    assert len(client.requests) == 2
    saved = read(project)
    assert saved['revision'] == first['revision']
    assert saved['planner_result'] == first['planner_result']

def test_stale_revision_blocks_before_model(project):
    turn(project, Client({'message': 'Which file?', 'plan': None}))
    client = Client()
    with pytest.raises(InterfaceApiError, match='digest no longer matches'):
        turn(project, client)
    assert not client.requests

def test_active_turn_blocks_duplicate_and_releases_after_failure(project):
    class Reentrant:
        def complete(self, request):
            with pytest.raises(InterfaceApiError, match='digest no longer matches'):
                turn(project, Client())
            raise RuntimeError('transport failed')
    with pytest.raises(RuntimeError):
        turn(project, Reentrant())
    assert turn(project, Client({'message': 'Retry works', 'plan': None}))['revision'] == 1

def test_storage_symlinks_and_malicious_identity_rejected(project, tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (project / 'planner-conversations').symlink_to(outside, target_is_directory=True)
    with pytest.raises(InterfaceApiError, match='unsafe'):
        read(project)
    with pytest.raises(ValidationError):
        TurnRequest(action='read', conversation_id='../outside')

def test_history_context_is_bounded_and_current_manual_plan_is_base(project):
    for index in range(8):
        turn(project, Client({'message': 'Please clarify', 'plan': None}), f'Message {index}', revision=index)
    base = PlannerResult(model='operator-edited', original_request='Manual plan', context_references=[], plan=plan())
    client = Client({'message': 'I see the manually edited plan.', 'plan': None})
    reply = turn(project, client, 'Explain it', revision=8, base=base)
    prompt = json.loads(client.requests[0].messages[1].content)
    assert len(prompt['recent_conversation']) == 12 and prompt['older_messages_omitted']
    assert prompt['current_plan'] == base.plan.model_dump(mode='json')
    assert reply['planner_result']['model'] == 'operator-edited'

def test_add_then_remove_operation_uses_current_plan_and_keeps_immutable_identity(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    addition = plan('data/input/sample_points.geojson')
    addition['steps'].append({'step_id': 'step_2', 'skill': 'convert_vector', 'purpose': 'Convert points', 'arguments': {'path': 'data/input/sample_points.geojson', 'target_path': 'data/output/points.gpkg'}, 'requires_approval': True, 'validation_required': True})
    added = turn(project, Client({'message': 'Added conversion; authorization will be required.', 'plan': addition}), 'Add a conversion to data/output/points.gpkg', revision=1, base=as_base(first['planner_result']))
    assert len(added['planner_result']['plan']['steps']) == 2
    assert added['planner_result']['plan_sha256'] != first['planner_result']['plan_sha256']
    removed = turn(project, Client({'message': 'Removed conversion.', 'plan': plan()}), 'Remove conversion', revision=2, base=as_base(added['planner_result']))
    assert len(removed['planner_result']['plan']['steps']) == 1
    assert removed['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']
    assert not removed['execution_performed']

def test_revision_cannot_silently_remove_extra_approval_gate(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan(gate=True)}))
    invalid = {'message': 'Removed the gate', 'plan': plan(gate=False)}
    with pytest.raises(PlannerAgentError):
        turn(project, Client(invalid, invalid), 'Explain this step', revision=1, base=as_base(first['planner_result']))
    assert read(project)['planner_result']['plan']['steps'][0]['requires_approval']

def test_saved_conversations_inventory_has_no_model_call(project):
    turn(project, Client({'message': 'Which file?', 'plan': None}), 'Inspect a vector')
    inventory = conversation_turn(TurnRequest(action='list', conversation_id='0'*32), project_root=project)
    assert inventory['conversations'] == [{'conversation_id': ID, 'revision': 1, 'summary': 'Inspect a vector'}]
    assert not inventory['approval_performed'] and not inventory['execution_performed']

def test_conversation_http_contract_and_origin_guard(project, monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    import geoagent_harness.interface_api.conversation as service
    original = service.conversation_turn
    client = Client({'message': 'Which file should I inspect?', 'plan': None})
    monkeypatch.setattr(service, 'conversation_turn', lambda request, *, project_root: original(request, project_root=project_root, model_client=client))
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(project))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection(*server.server_address)
        payload = {'action': 'turn', 'conversation_id': ID, 'message': 'Inspect a vector'}
        headers = {'Content-Type': 'application/json', 'Origin': 'http://localhost:5173'}
        connection.request('POST', '/api/v1/planner/conversation', json.dumps(payload), headers)
        response = connection.getresponse()
        body = json.loads(response.read())
        assert response.status == 200 and body['revision'] == 1
        assert body['planner_result'] is None and not body['execution_performed']
        connection.request('POST', '/api/v1/planner/conversation', json.dumps(payload), {**headers, 'Origin': 'https://foreign.example'})
        response = connection.getresponse()
        response.read()
        assert response.status == 403 and len(client.requests) == 1
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def test_identical_plan_reply_does_not_invalidate_authority_state(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    second = turn(project, Client({'message': 'The existing plan already does that.', 'plan': plan()}), 'Keep inspection', revision=1, base=as_base(first['planner_result']))
    assert not second['proposal_changed']
    assert second['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']

def test_clarification_after_refresh_preserves_recoverable_proposal(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    client = Client({'message': 'This reads metadata only.', 'plan': None})
    second = turn(project, client, 'Explain my previous plan', revision=1)
    assert second['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']
    assert json.loads(client.requests[0].messages[1].content)['current_plan'] == first['planner_result']['plan']

def test_conversation_redacts_common_credentials_before_model_and_storage(project):
    client = Client({'message': 'Do not share password=another-secret.', 'plan': None})
    reply = turn(project, client, 'Inspect points. password=private-value postgresql://operator:secret-value@localhost/db')
    prompt = client.requests[0].messages[1].content
    from geoagent_harness.interface_api.planning_tasks import conversation_record, task_record
    record = json.dumps({'conversation': conversation_record(project, ID), 'memory': task_record(project, ID)})
    for secret in ('private-value', 'secret-value', 'another-secret'):
        assert secret not in prompt and secret not in record
    assert '[REDACTED]' in reply['messages'][0]['content']

def test_selected_conversion_retains_existing_inspection_and_records_turn_skills(project):
    first = turn(project, Client({'message': 'Ready', 'plan': plan()}))
    revised = plan('data/input/sample_points.geojson')
    revised['steps'].append({'step_id': 'step_2', 'skill': 'convert_vector', 'purpose': 'Convert to GeoPackage', 'arguments': {'path': 'data/input/sample_points.geojson', 'target_path': 'data/output/selection_points.gpkg'}, 'requires_approval': True, 'validation_required': True})
    client = Client({'message': 'Added conversion.', 'plan': revised})
    reply = conversation_turn(TurnRequest(action='turn', conversation_id=ID, expected_revision=1, message='Add conversion to data/output/selection_points.gpkg', current_plan=as_base(first['planner_result']), allowed_skill_ids=['convert_vector']), project_root=project, model_client=client)
    assert reply['messages'][-2]['selected_skill_ids'] == ['convert_vector']
    assert reply['messages'][-1]['plan_skill_ids'] == ['inspect_vector', 'convert_vector']
    assert set(reply['planner_result']['allowed_skill_ids']) == {'inspect_vector', 'convert_vector'}
    assert reply['selected_skill_ids'] == ['convert_vector']
    assert read(project)['messages'] == reply['messages']
    system = json.loads(client.requests[0].messages[0].content)
    arguments = system['operation_argument_schemas']['convert_vector']
    assert arguments['required'] == ['path', 'target_path']
    assert 'target_schema' not in arguments['properties']
    assert system['conversion_arguments_example']['target_path'].endswith('.gpkg')

def test_empty_selection_is_automatic_and_selection_history_does_not_change(project):
    first_client = Client({'message': 'Which file?', 'plan': None})
    first = conversation_turn(TurnRequest(action='turn', conversation_id=ID, message='Inspect a vector', allowed_skill_ids=['inspect_vector']), project_root=project, model_client=first_client)
    second_client = Client({'message': 'Ready', 'plan': plan()})
    second = turn(project, second_client, revision=1)
    assert second['messages'][0]['selected_skill_ids'] == ['inspect_vector']
    assert second['messages'][2]['selected_skill_ids'] == []
    assert second['messages'][3]['plan_skill_ids'] == ['inspect_vector']
    assert second['selected_skill_ids'] == []
    prompt = json.loads(second_client.requests[0].messages[1].content)
    assert prompt['skill_selection_mode'] == 'automatic'
    assert 'convert_vector' in second['planner_result']['allowed_skill_ids']

def test_explicit_selection_rejects_unselected_new_operation(project):
    invalid = {'message': 'Convert', 'plan': {'summary': 'Convert', 'steps': [{'step_id': 'step_1', 'skill': 'convert_vector', 'purpose': 'Convert', 'arguments': {'path': 'data/input/sample_points.geojson', 'target_path': 'data/output/unselected.gpkg'}, 'requires_approval': True, 'validation_required': True}]}}
    with pytest.raises(PlannerAgentError):
        conversation_turn(TurnRequest(action='turn', conversation_id=ID, message='Inspect only', allowed_skill_ids=['inspect_vector']), project_root=project, model_client=Client(invalid, invalid))
    assert read(project)['revision'] == 0

def test_selected_load_includes_mandatory_dependencies_without_execution(project):
    client = Client({'message': 'Which target schema and fresh table should I use?', 'plan': None})
    reply = conversation_turn(TurnRequest(action='turn', conversation_id=ID, message='Load the vector into PostGIS', allowed_skill_ids=['load_vector_to_postgis']), project_root=project, model_client=client)
    prompt = json.loads(client.requests[0].messages[0].content)
    assert set(prompt['available_skills']) == {'load_vector_to_postgis', 'inspect_vector', 'validate_postgis_layer'}
    assert reply['messages'][0]['selected_skill_ids'] == ['load_vector_to_postgis']
    assert reply['messages'][1]['plan_skill_ids'] == []
    assert not reply['execution_performed']

def test_legacy_transcript_without_skill_metadata_can_be_recovered(project):
    root = project / 'planner-conversations'
    root.mkdir()
    (root / (ID + '.json')).write_text(json.dumps({'conversation_id': ID, 'revision': 1, 'messages': [{'role': 'user', 'content': 'Old task'}, {'role': 'assistant', 'content': 'Old response'}], 'planner_result': None}))
    recovered = read(project)
    assert recovered['selected_skill_ids'] == []
    assert recovered['messages'][0]['selected_skill_ids'] is None
    assert recovered['messages'][1]['plan_skill_ids'] is None

@pytest.mark.parametrize('failure', ['http404', 'settings', 'timeout'])
def test_conversation_model_failure_returns_json_without_socket_hangup(project, monkeypatch, failure):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    from geoagent_harness.model import ModelClientError, ModelSettingsError
    import geoagent_harness.interface_api.conversation as service
    error = ModelClientError.timeout() if failure == 'timeout' else ModelClientError.http_status(404) if failure == 'http404' else ModelSettingsError('MODEL_NAME is required')
    def fail(request, *, project_root):
        raise error
    monkeypatch.setattr(service, 'conversation_turn', fail)
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(project))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection(*server.server_address)
        connection.request('POST', '/api/v1/planner/conversation', json.dumps({'action':'turn','conversation_id':ID,'message':'Inspect CSV'}), {'Content-Type':'application/json'})
        response = connection.getresponse()
        assert response.status == 503
        body = json.loads(response.read())
        assert body['code'] == ('model_timeout' if failure == 'timeout' else 'model_http_error' if failure == 'http404' else 'model_configuration_failed')
        assert 'retry_guidance' in body and body['execution_performed'] is False
        if failure == 'http404': assert '404' in body['error']
        if failure == 'timeout':
            assert 'MODEL_TIMEOUT_SECONDS' in body['retry_guidance']
            assert 'HTTP 404' not in body['retry_guidance']
        connection.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def test_history_excerpt_budget_and_disable_preserve_full_transcript(project):
    directory = project / 'planner-conversations'; directory.mkdir()
    transcript = [{'role':'user' if i % 2 == 0 else 'assistant', 'content':f'Entry {i}: '+('历史'*3000)} for i in range(20)]
    (directory / (ID+'.json')).write_text(json.dumps({'conversation_id':ID,'revision':10,'messages':transcript}))
    client = Client({'message':'What output path?', 'plan':None})
    result = conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=10,message='Export the table'),project_root=project,model_client=client)
    payload = json.loads(client.requests[0].messages[1].content)
    assert len(json.dumps(payload['recent_conversation'],ensure_ascii=False).encode()) <= 6000
    assert payload['history_excerpts_truncated'] and payload['older_messages_omitted']
    assert result['messages'][0]['content'] == transcript[0]['content']
    assert result['context_usage']['prompt_bytes'] <= 64000
    second = Client({'message':'Choose source and output', 'plan':None})
    without = conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=11,message='Start fresh',use_history=False),project_root=project,model_client=second)
    payload = json.loads(second.requests[0].messages[1].content)
    assert payload['recent_conversation']==[] and payload['initial_request'] is None
    assert len(without['messages'])==24
    assert without['context_usage']['included_messages']==0
    assert without['context_usage']['omitted_messages']==22
    system = json.loads(second.requests[0].messages[0].content)
    assert 'tabular_argument_schemas' not in system and 'workflow_json_schema' not in system


def test_prompt_budget_blocks_before_model_call_and_preserves_transcript(project,monkeypatch):
    import geoagent_harness.interface_api.conversation as service
    from geoagent_harness.context_pack.builder import ContextPackError
    monkeypatch.setattr(service,'MAX_PROMPT_BYTES',100)
    client = Client({'message':'unused','plan':None})
    with pytest.raises(ContextPackError,match='context exceeds'):
        conversation_turn(TurnRequest(action='turn',conversation_id=ID,message='Inspect CSV'),project_root=project,model_client=client)
    assert client.requests==[]
    assert read(project)['revision']==0


def test_failed_conversation_explains_schema_and_supplies_candidate_to_correction(project):
    client = Client({'plan':None}, {'plan':None})
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client)
    assert caught.value.correction_attempted
    assert any('message' in finding and 'missing' in finding for finding in caught.value.findings)
    correction = json.loads(client.requests[1].messages[-1].content)
    assert correction['failure_kind']=='schema'
    assert correction['deterministic_findings']==caught.value.findings
    assert client.requests[1].messages[-2].role=='assistant'
    assert read(project)['revision']==0


def test_failed_policy_correction_explains_safe_path_failure(project):
    invalid={'message':'Proposal', 'plan':plan('../private.geojson')}
    client=Client(invalid,invalid)
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,client)
    assert caught.value.findings
    assert 'policy' in str(caught.value)
    assert json.loads(client.requests[1].messages[-1].content)['failure_kind']=='policy'


def test_legacy_plan_only_reply_passes_same_policy_without_execution(project):
    client=Client(plan())
    response=turn(project,client)
    assert response['planner_result']['plan']['steps'][0]['skill']=='inspect_vector'
    assert len(client.requests)==1
    assert not response['approval_performed'] and not response['execution_performed']
    invalid=plan('../private.geojson')
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,Client(invalid,invalid),revision=1)
    assert caught.value.findings and 'policy' in str(caught.value)
    assert read(project)['revision']==1


def test_csv_inspection_reference_correction_names_the_consumer_and_producer(project):
    workflow={'summary':'Inspect and export selected CSV columns','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
        {'step_id':'step_2','skill':'select_csv_columns','purpose':'Select','arguments':{'source_step':'step_1','columns':['order_id'],'target_path':'data/output/selected.csv'},'requires_approval':True,'validation_required':True}
    ]}
    fixed=json.loads(json.dumps(workflow))
    fixed['steps'][1]['arguments'].pop('source_step')
    fixed['steps'][1]['arguments']['path']='data/input/sample_orders.csv'
    client=Client({'message':'Proposed','plan':workflow},{'message':'Corrected source','plan':fixed})
    result=turn(project,client,'Inspect CSV and select order_id')
    findings=json.loads(client.requests[1].messages[-1].content)['deterministic_findings']
    assert 'step_2' in findings[0] and 'source_step=step_1' in findings[0]
    assert 'Inspection returns metadata only' in findings[0]
    assert result['planner_result']['plan']['steps'][1]['arguments']['path']=='data/input/sample_orders.csv'
    assert not result['execution_performed'] and not result['approval_performed']


def test_step_numbering_finding_reaches_correction_and_preserves_references(project):
    invalid=plan()
    invalid['steps'][0]['step_id']='step_2'
    client=Client({'message':'Plan','plan':invalid},{'message':'Fixed numbering','plan':plan()})
    result=turn(project,client)
    finding=json.loads(client.requests[1].messages[-1].content)['deterministic_findings'][0]
    assert finding.startswith('plan.steps: step IDs must be sequential in array order')
    assert 'source_step' in finding and 'producer identities' in finding
    assert result['planner_result']['plan']['steps'][0]['step_id']=='step_1'
    assert not result['execution_performed']
    broken=Client({'message':'Plan','plan':invalid},{'message':'Still broken','plan':invalid})
    with pytest.raises(PlannerAgentError) as caught:
        turn(project,broken,revision=1)
    assert caught.value.findings[0]==finding
    assert read(project)['revision']==1


def test_conflicting_csv_sources_receive_actionable_correction(project):
    workflow={'summary':'Select CSV columns','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
        {'step_id':'step_2','skill':'select_csv_columns','purpose':'Select','arguments':{'path':'data/input/sample_orders.csv','source_step':'step_1','columns':['region','amount'],'target_path':'data/output/selected.csv'},'requires_approval':True,'validation_required':True}
    ]}
    fixed=json.loads(json.dumps(workflow))
    fixed['steps'][1]['arguments'].pop('source_step')
    client=Client({'message':'Proposed','plan':workflow},{'message':'Corrected','plan':fixed})
    result=turn(project,client,'Inspect then select region and amount')
    finding=json.loads(client.requests[1].messages[-1].content)['deterministic_findings'][0]
    assert 'step_2' in finding and 'never both' in finding and 'Omit the unused field' in finding
    assert 'input_value' not in finding and 'pydantic.dev' not in finding
    assert result['planner_result']['plan']['steps'][1]['arguments']['path']=='data/input/sample_orders.csv'
    assert not result['execution_performed'] and not result['approval_performed']


def test_csv_source_schema_exposes_exclusive_choices():
    from geoagent_harness.tabular.schemas import SelectColumns,JoinTables
    select=SelectColumns.model_json_schema()
    assert select['allOf'][0]['oneOf'][0]['required']==['path']
    join=JoinTables.model_json_schema()
    assert join['allOf'][1]['oneOf'][1]['required']==['right_step']
