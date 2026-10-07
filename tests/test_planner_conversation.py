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
    record = (project / 'planner-conversations' / (ID + '.json')).read_text()
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
