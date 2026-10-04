"""Input selection must fail before inference and resolved Intent must agree."""
import json
import os
from pathlib import Path
import pytest
from pydantic import ValidationError
from geoagent_harness.intent.input import check_task_input
from geoagent_harness.intent.service import reason_task_intent, IntentError
from geoagent_harness.interface_api.server import InterfaceIntentRequest
from geoagent_harness.model import ModelResult

class Model:
    def __init__(self, path='data/input/sample.geojson', callback=None):
        self.path = path; self.calls = 0; self.callback = callback
    def complete(self, request):
        self.calls += 1
        data = json.loads(request.messages[1].content)
        assert data['selected_input'] == 'data/input/sample.geojson'
        assert 'Selected input: data/input/sample.geojson.' in data['clarification_answers']
        if self.callback: self.callback()
        return ModelResult(model='fixture', finish_reason='stop', content=json.dumps({
            'status': 'intent_proposed', 'objective': 'Inspect metadata',
            'known_inputs': [self.path], 'requested_outputs': ['fields'],
            'constraints': ['No writes'], 'clarification_questions': [], 'cited_sequences': [],
        }))

def setup_input(root):
    path = root/'data/input/sample.geojson'; path.parent.mkdir(parents=True); path.write_text('{}'); return path

def test_filename_and_exact_path_refer_to_the_same_existing_input(tmp_path):
    path = setup_input(tmp_path)
    for value in ('sample.geojson', 'data/input/sample.geojson'):
        assert check_task_input(project_root=tmp_path, input_path=value) == 'data/input/sample.geojson'
        model = Model()
        result = reason_task_intent(project_root=tmp_path, review_filename=None, request='Inspect fields only', selected_input_path=value, model_client=model)
        assert result['clarification_answers'] == ['Selected input: data/input/sample.geojson.']
        assert not result['execution_performed'] and not result['plan_created']
        assert model.calls == 1
    assert path.read_text() == '{}'

@pytest.mark.parametrize('value', ['', '../outside', '/tmp/data', 'data/output/result.geojson', 'data/input/../sample.geojson', 'data//input/sample.geojson', 'data\\input\\sample.geojson', 'missing.geojson'])
def test_bad_or_missing_selection_never_calls_model(tmp_path, value):
    setup_input(tmp_path); model = Model()
    with pytest.raises(IntentError):
        reason_task_intent(project_root=tmp_path, review_filename=None, request='Inspect', selected_input_path=value, model_client=model)
    assert model.calls == 0
    assert not (tmp_path/'reviewed-intents').exists()

def test_symlinked_file_or_parent_and_non_regular_input_are_blocked(tmp_path):
    path = setup_input(tmp_path)
    (path.parent/'link.geojson').symlink_to(path)
    (path.parent/'nested').symlink_to(path.parent, target_is_directory=True)
    os.mkfifo(path.parent/'pipe')
    for value in ('link.geojson', 'data/input/nested/sample.geojson', 'pipe', 'data/input'):
        with pytest.raises(IntentError): check_task_input(project_root=tmp_path, input_path=value)

def test_different_resolved_input_and_disappearance_during_inference_are_blocked(tmp_path):
    path = setup_input(tmp_path)
    for model in (Model('data/input/other.geojson'), Model(callback=path.unlink)):
        with pytest.raises(IntentError):
            reason_task_intent(project_root=tmp_path, review_filename=None, request='Inspect', selected_input_path='sample.geojson', model_client=model)
        assert model.calls == 1
    assert not (tmp_path/'reviewed-intents').exists()

def test_selected_input_uses_one_explicit_answer_slot_without_overflow(tmp_path):
    setup_input(tmp_path); model = Model()
    with pytest.raises(IntentError, match='answer slot'):
        reason_task_intent(project_root=tmp_path, review_filename=None, request='Inspect', selected_input_path='sample.geojson', clarification_answers=['answer']*5, model_client=model)
    assert model.calls == 0

def test_api_selection_is_optional_for_legacy_clients_and_authority_is_forbidden():
    payload = {'action':'reason_task_intent', 'review_filename':None, 'request':'Inspect'}
    assert InterfaceIntentRequest.model_validate(payload).selected_input_path is None
    assert InterfaceIntentRequest.model_validate({**payload, 'selected_input_path':'sample.geojson'}).selected_input_path == 'sample.geojson'
    with pytest.raises(ValidationError): InterfaceIntentRequest.model_validate({**payload, 'execution_performed':True})


def test_cli_missing_selected_input_is_rejected_without_model_configuration(tmp_path):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    result = CliRunner().invoke(app, ['reason-task-intent', '--request', 'Inspect fields', '--selected-input', 'missing.geojson', '--project-root', str(tmp_path)])
    assert result.exit_code == 2
    assert 'selected input is unavailable' in result.output
    assert 'MODEL_NAME' not in result.output
