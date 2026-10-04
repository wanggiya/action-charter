import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from geoagent_harness.intent.review import inspect_intent_for_review, save_reviewed_intent
from geoagent_harness.intent.handoff import plan_reviewed_intent, save_reviewed_intent_plan
from geoagent_harness.intent.service import IntentError
from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan, PlanStep


def reviewed_raster(root):
    intent = dict(schema_version='1.0',agent_id='intent',model='fake',original_request='Inspect raster metadata',clarification_answers=[],review_filename=None,context_sha256=None,proposal=dict(status='intent_proposed',objective='Inspect raster metadata',known_inputs=['data/input/sample_dem.tif'],requested_outputs=['width','height','band count','CRS'],constraints=['No writes'],clarification_questions=[],cited_sequences=[]),status='proposed_not_saved',human_review_required=True,correction_attempted=False,model_called=True,plan_created=False,approval_inferred=False,execution_performed=False,tools_called=False)
    checked = inspect_intent_for_review(payload=intent,project_root=root)
    return save_reviewed_intent(payload=intent,project_root=root,confirmed_intent_sha256=checked['intent_sha256'],reviewer='operator',reason='Read-only raster metadata')['review_filename']


def planner(**kwargs):
    assert kwargs['allowed_skill_ids'] == ['inspect_raster']
    assert json.loads(kwargs['original_request'])['inspection_skill'] == 'inspect_raster'
    return PlannerResult(model='fake',original_request=kwargs['original_request'],context_references=[],plan=WorkflowPlan(summary='Inspect raster',steps=[PlanStep(step_id='step_1',skill='inspect_raster',purpose='Inspect exact raster',arguments={'path':'data/input/sample_dem.tif'},requires_approval=True)]))


def test_raster_handoff_and_storage_preserve_exact_scope(tmp_path: Path):
    filename = reviewed_raster(tmp_path)
    with patch('geoagent_harness.intent.handoff.plan_task',side_effect=planner) as model:
        result = plan_reviewed_intent(project_root=tmp_path,filename=filename,allowed_skill_ids=['inspect_raster'])
    assert model.call_count == 1 and result['execution_performed'] is False
    with patch('geoagent_harness.interface_api.server.load_skill_registry',return_value=SimpleNamespace(implemented_skills=lambda:[SimpleNamespace(id='inspect_raster')])):
        stored = save_reviewed_intent_plan(project_root=tmp_path,filename=filename,planner_result=PlannerResult.model_validate(result['planner_result']),confirmed_plan_sha256=result['plan_sha256'])
    assert stored['plan_saved'] is True
    assert stored['execution_performed'] is stored['approval_performed'] is stored['model_called'] is False
    raw = json.loads((tmp_path/'plans'/stored['plan_filename']).read_text())
    assert raw['plan']['steps'][0]['requires_approval'] is True
    assert json.loads(raw['original_request'])['inspection_skill'] == 'inspect_raster'


def test_wrong_capability_rejected_before_model_and_wrong_path_after_model(tmp_path: Path):
    filename = reviewed_raster(tmp_path)
    with patch('geoagent_harness.intent.handoff.plan_task') as model:
        for skills in (['inspect_vector'],['inspect_vector','inspect_raster'],['convert_raster']):
            with pytest.raises(IntentError):
                plan_reviewed_intent(project_root=tmp_path,filename=filename,allowed_skill_ids=skills)
        model.assert_not_called()
    def wrong(**kwargs):
        result = planner(**kwargs); result.plan.steps[0].arguments['path']='data/input/other.tif'; return result
    with patch('geoagent_harness.intent.handoff.plan_task',side_effect=wrong):
        with pytest.raises(IntentError,match='arguments must equal'):
            plan_reviewed_intent(project_root=tmp_path,filename=filename,allowed_skill_ids=['inspect_raster'])
    assert not (tmp_path/'plans').exists()
