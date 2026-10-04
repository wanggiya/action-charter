import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from geoagent_harness.model import ModelResult
from geoagent_harness.intent.service import reason_task_intent, IntentError
from geoagent_harness.intent.review import inspect_intent_for_review, save_reviewed_intent, load_reviewed_intent
from geoagent_harness.intent.handoff import plan_reviewed_intent, save_reviewed_intent_plan
from geoagent_harness.intent.inventory import reviewed_context_inventory
from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan, PlanStep

class FakeIntent:
    def __init__(self, citations=None): self.citations = citations or []; self.calls = 0
    def complete(self, request):
        self.calls += 1
        content = json.loads(request.messages[1].content)
        assert content['untrusted_reviewed_history']['excerpts'] == []
        return ModelResult(model='fake', finish_reason='stop', content=json.dumps(dict(status='intent_proposed', objective='Inspect metadata', known_inputs=['data/input/sample.geojson'], requested_outputs=['feature count','fields','CRS'], constraints=['No writes'], clarification_questions=[], cited_sequences=self.citations)))


def test_no_history_lifecycle_is_explicit_and_has_no_work_authority(tmp_path: Path):
    model = FakeIntent()
    with patch('geoagent_harness.intent.service.load_reviewed_context', side_effect=AssertionError('must not load history')):
        result = reason_task_intent(project_root=tmp_path, review_filename=None, request='Inspect metadata', model_client=model)
    assert result['review_filename'] is result['context_sha256'] is None
    assert not (tmp_path/'task-history').exists() and model.calls == 1
    inspected = inspect_intent_for_review(payload=result, project_root=tmp_path)
    saved = save_reviewed_intent(payload=result, project_root=tmp_path, confirmed_intent_sha256=inspected['intent_sha256'], reviewer='operator', reason='Read-only inspection')
    assert load_reviewed_intent(project_root=tmp_path, filename=saved['review_filename'])['intent']['context_sha256'] is None
    assert reviewed_context_inventory(project_root=tmp_path)['reviews'][0]['status'] == 'available'
    def planner(**kwargs):
        source = json.loads(kwargs['original_request'])
        assert source['context_sha256'] is None
        return PlannerResult(model='fake', original_request=kwargs['original_request'], context_references=[], plan=WorkflowPlan(summary='Inspect metadata', steps=[PlanStep(step_id='step_1',skill='inspect_vector',purpose='Inspect',arguments={'path':'data/input/sample.geojson'},requires_approval=True)]))
    with patch('geoagent_harness.intent.handoff.plan_task', side_effect=planner):
        handoff = plan_reviewed_intent(project_root=tmp_path, filename=saved['review_filename'], allowed_skill_ids=['inspect_vector'])
    with patch('geoagent_harness.interface_api.server.load_skill_registry', return_value=SimpleNamespace(implemented_skills=lambda:[SimpleNamespace(id='inspect_vector')])):
        stored = save_reviewed_intent_plan(project_root=tmp_path, filename=saved['review_filename'], planner_result=PlannerResult.model_validate(handoff['planner_result']), confirmed_plan_sha256=handoff['plan_sha256'])
    assert stored['context_sha256'] is None and stored['plan_saved'] is True
    assert stored['approval_performed'] is stored['execution_performed'] is stored['model_called'] is False
    assert json.loads((tmp_path/'plans'/stored['plan_filename']).read_text())['plan']['steps'][0]['requires_approval'] is True


def test_no_history_citations_and_mixed_context_identity_are_rejected(tmp_path: Path):
    with pytest.raises(IntentError, match='unavailable history'):
        reason_task_intent(project_root=tmp_path,review_filename=None,request='Inspect',model_client=FakeIntent([1]))
    result = reason_task_intent(project_root=tmp_path,review_filename=None,request='Inspect',model_client=FakeIntent())
    for key,value in [('context_sha256','a'*64), ('review_filename','context-review.'+'a'*64+'.json')]:
        with pytest.raises(IntentError, match='envelope'):
            inspect_intent_for_review(payload={**result,key:value},project_root=tmp_path)


def test_api_requires_explicit_null_context_and_keeps_authority_fields_out():
    from geoagent_harness.interface_api.server import InterfaceIntentRequest
    from pydantic import ValidationError
    payload = dict(action='reason_task_intent', review_filename=None, request='Inspect metadata')
    assert InterfaceIntentRequest.model_validate(payload).review_filename is None
    for changed in ({key:value for key,value in payload.items() if key != 'review_filename'}, {**payload,'execute':True}):
        with pytest.raises(ValidationError):
            InterfaceIntentRequest.model_validate(changed)


def test_http_reasoning_accepts_explicit_history_free_request(tmp_path: Path, monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    import geoagent_harness.intent.service as service
    fake = FakeIntent()
    monkeypatch.setattr(service, 'load_model_settings', lambda: None)
    monkeypatch.setattr(service, 'SharedModelClient', lambda settings: fake)
    server = ThreadingHTTPServer(('127.0.0.1',0), _handler(tmp_path))
    thread = Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        connection = HTTPConnection('127.0.0.1',server.server_port,timeout=3)
        connection.request('POST','/api/v1/intent/reason',body=json.dumps(dict(action='reason_task_intent',review_filename=None,request='Inspect data/input/sample.geojson read-only')),headers={'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response = connection.getresponse(); result = json.loads(response.read())
        assert response.status == 200
        assert result['context_sha256'] is result['review_filename'] is None
        assert result['approval_inferred'] is result['execution_performed'] is False
        assert fake.calls == 1 and not (tmp_path/'reviewed-contexts').exists()
        connection.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
