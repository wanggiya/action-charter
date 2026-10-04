"""Malformed proposals get one fresh attempt, never a validation bypass."""
import json
from pathlib import Path
import pytest
from geoagent_harness.agent_manifest import load_agent_manifest
from geoagent_harness.context_pack import build_context_pack
from geoagent_harness.model.schemas import ModelResult
from geoagent_harness.planner.agent import PlannerAgentError, run_planner_agent
from geoagent_harness.planner.prompt import build_planner_request

ROOT = Path(__file__).resolve().parents[1]

class Responses:
    def __init__(self, contents):
        self.contents = contents
        self.requests = []
    def complete(self, request):
        self.requests.append(request)
        return ModelResult(model='fixture', content=self.contents[len(self.requests)-1])

def plan(**updates):
    value = dict(summary='Inspect only', steps=[dict(step_id='step_1', skill='inspect_vector',
        purpose='Read metadata', arguments={'path':'data/input/sample_points.geojson'},
        requires_approval=False, validation_required=False, expected_artifacts=[])])
    value.update(updates)
    return json.dumps(value)

def scope():
    source = json.dumps({'intent_review_filename':'intent-review.' + 'a'*64 + '.json',
                         'exact_arguments':{'path':'data/input/sample_points.geojson'}})
    return build_context_pack(source, ROOT, allowed_skill_ids=['inspect_vector']), load_agent_manifest('planner', ROOT/'agents')

def run(client):
    context, manifest = scope()
    return run_planner_agent(context_pack=context, manifest=manifest, model_client=client)

@pytest.mark.parametrize('malformed', ['not JSON', plan(assumptions='text instead of array'), json.dumps({'plan':json.loads(plan())})])
def test_fresh_response_is_revalidated(malformed):
    client = Responses([malformed, plan()])
    result = run(client)
    assert len(client.requests) == 2
    assert result.plan.steps[0].skill == 'inspect_vector'
    assert result.plan.execution_performed is False
    assert any('correction' in warning for warning in result.warnings)

def test_second_failure_exposes_fields_without_model_values():
    bad = plan(assumptions={'password':'never-display-this'})
    client = Responses([bad, bad])
    with pytest.raises(PlannerAgentError) as caught:
        run(client)
    assert len(client.requests) == 2
    assert caught.value.correction_attempted is True
    assert any('assumptions' in finding for finding in caught.value.findings)
    assert 'never-display-this' not in str(caught.value.findings)
    assert 'never-display-this' not in client.requests[1].messages[-1].content

@pytest.mark.parametrize('second', [plan(execution_performed=True), plan(steps=[dict(step_id='step_1',skill='run_shell',purpose='Unsafe',arguments={},requires_approval=True,validation_required=True)])])
def test_shared_retry_budget_cannot_admit_unsafe_second_response(second):
    client = Responses(['invalid JSON', second])
    with pytest.raises(PlannerAgentError):
        run(client)
    assert len(client.requests) == 2

def test_policy_then_schema_reports_the_actual_final_failure():
    client = Responses([plan(steps=[dict(step_id='step_1',skill='run_shell',purpose='Unsafe',arguments={},requires_approval=True,validation_required=True)]), plan(risks='invalid')])
    with pytest.raises(PlannerAgentError, match='invalid plan schema') as caught:
        run(client)
    assert any('risks' in finding for finding in caught.value.findings)
    assert len(client.requests) == 2

def test_exact_inspection_example_matches_reviewed_path():
    context, manifest = scope()
    payload = json.loads(build_planner_request(context, manifest).messages[0].content)
    example = payload['response_shape_example']
    assert example['steps'][0]['arguments'] == {'path':'data/input/sample_points.geojson'}
    assert example['steps'][0]['skill'] == 'inspect_vector'
    assert example['execution_performed'] is False
    ordinary = build_context_pack('Inspect metadata.', ROOT, allowed_skill_ids=['inspect_vector'])
    assert 'response_shape_example' not in json.loads(build_planner_request(ordinary, manifest).messages[0].content)

def test_transport_failure_is_not_retried():
    class Unavailable:
        calls = 0
        def complete(self, request):
            self.calls += 1
            raise TimeoutError('fixture transport timeout')
    client = Unavailable()
    with pytest.raises(TimeoutError):
        run(client)
    assert client.calls == 1

def test_intent_http_exposes_schema_fields_and_no_authority(tmp_path, monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    import geoagent_harness.intent.handoff as handoff
    from geoagent_harness.interface_api.server import _handler
    def fail(**kwargs):
        raise PlannerAgentError('Planner model returned an invalid plan schema',
            findings=['steps.0.expected_artifacts: must be a list'], correction_attempted=True)
    monkeypatch.setattr(handoff, 'plan_reviewed_intent', fail)
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(tmp_path))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
        connection.request('GET', '/api/v1/health')
        health_response = connection.getresponse()
        health = json.loads(health_response.read())
        assert health['planner_contract_revision'] == 'schema-correction-v52'
        assert health['planner_correction_limit'] == 1
        connection.request('POST', '/api/v1/intent/plan', body=json.dumps({
            'action':'plan_reviewed_intent', 'review_filename':'intent-review.'+'a'*64+'.json',
            'allowed_skill_ids':['inspect_vector']}), headers={
                'Content-Type':'application/json', 'Origin':'http://localhost:5173'})
        response = connection.getresponse()
        result = json.loads(response.read())
        assert response.status == 422
        assert result['code'] == 'planner_invalid_schema'
        assert result['schema_findings'] == ['steps.0.expected_artifacts: must be a list']
        assert result['correction_attempted'] is True
        assert result['plan_saved'] is result['approval_performed'] is result['execution_performed'] is False
        connection.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    assert not (tmp_path/'plans').exists()


def test_readonly_prompt_distinguishes_planning_from_approval():
    context, manifest = scope()
    payload = json.loads(build_planner_request(context, manifest).messages[0].content)
    assert any('Planning-only does not itself require approval' in rule for rule in payload['mandatory_rules'])
    conservative = json.loads(plan())
    conservative['steps'][0]['requires_approval'] = True
    result = run(Responses([json.dumps(conservative)]))
    assert result.plan.steps[0].requires_approval is True
    assert result.plan.execution_performed is False
