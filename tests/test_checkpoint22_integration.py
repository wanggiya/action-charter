"""Checked Intent joins the real plan/decision/recipe services, without execution."""
import json
from pathlib import Path
import shutil
from unittest.mock import patch
import pytest
from geoagent_harness.context_retrieval import retrieve_task_context, save_reviewed_context
from geoagent_harness.task_history import append_task_event
from geoagent_harness.intent.review import inspect_intent_for_review, save_reviewed_intent
from geoagent_harness.intent.handoff import plan_reviewed_intent, save_reviewed_intent_plan
from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan, PlanStep
from geoagent_harness.interface_api.server import (
    InterfaceApiError, InterfacePlanApprovalPreparationRequest, InterfacePlanApprovalDecisionRequest,
    InterfacePlanApprovalVerificationRequest, InterfacePlanRecipeCompilationRequest, InterfacePlanRecipeSaveRequest,
    prepare_interface_plan_approval, record_interface_plan_approval, verify_interface_plan_approval,
    compile_interface_plan_recipe, save_interface_plan_recipe,
)

PROJECT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('skill',['inspect_vector','inspect_raster'])
@pytest.mark.parametrize('history',[False,True])
@pytest.mark.parametrize('decision',['approved','denied','not_required'])
def test_intent_plan_decision_recipe_join(tmp_path: Path, skill: str, history: bool, decision: str):
    (tmp_path/'context').mkdir()
    shutil.copyfile(PROJECT/'context/SKILLS_INDEX.yaml',tmp_path/'context/SKILLS_INDEX.yaml')
    context_filename = context_digest = None
    if history:
        append_task_event(root=tmp_path/'task-history',task_id='task-integration',event_type='decision',summary='An old plan was denied; history only')
        context = retrieve_task_context(root=tmp_path/'task-history',query='denied',task_ids=['task-integration'])
        stored_context = save_reviewed_context(history_root=tmp_path/'task-history',review_root=tmp_path/'reviewed-contexts',query='denied',task_ids=['task-integration'],confirmed_context_sha256=context['context_sha256'],reviewer='operator',reason='History is not work authority')
        context_filename = stored_context['review_filename']; context_digest = context['context_sha256']
    path = 'data/input/sample_points.geojson' if skill == 'inspect_vector' else 'data/input/sample_dem.tif'
    outputs = ['feature count','fields','CRS'] if skill == 'inspect_vector' else ['width','height','band count','CRS']
    payload = dict(schema_version='1.0',agent_id='intent',model='fixture',original_request='Inspect metadata only',clarification_answers=[],review_filename=context_filename,context_sha256=context_digest,proposal=dict(status='intent_proposed',objective='Inspect metadata only',known_inputs=[path],requested_outputs=outputs,constraints=['No writes'],clarification_questions=[],cited_sequences=[1] if history else []),status='proposed_not_saved',human_review_required=True,correction_attempted=False,model_called=True,plan_created=False,approval_inferred=False,execution_performed=False,tools_called=False)
    inspected = inspect_intent_for_review(payload=payload,project_root=tmp_path)
    reviewed = save_reviewed_intent(payload=payload,project_root=tmp_path,confirmed_intent_sha256=inspected['intent_sha256'],reviewer='operator',reason='Exact inspection intent')
    def planner(**kwargs):
        return PlannerResult(model='fixture',original_request=kwargs['original_request'],context_references=[],plan=WorkflowPlan(summary='Inspect metadata',steps=[PlanStep(step_id='step_1',skill=skill,purpose='Read exact metadata',arguments={'path':path},requires_approval=decision!='not_required')]))
    with patch('geoagent_harness.intent.handoff.plan_task',side_effect=planner) as model:
        handoff = plan_reviewed_intent(project_root=tmp_path,filename=reviewed['review_filename'],allowed_skill_ids=[skill])
    stored = save_reviewed_intent_plan(project_root=tmp_path,filename=reviewed['review_filename'],planner_result=PlannerResult.model_validate(handoff['planner_result']),confirmed_plan_sha256=handoff['plan_sha256'])
    basis = dict(plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256'])
    prepared = prepare_interface_plan_approval(InterfacePlanApprovalPreparationRequest(action='prepare_plan_approval',**basis),project_root=tmp_path)
    assert prepared['steps'][0]['skill'] == skill and prepared['steps'][0]['arguments'] == {'path':path}
    assert model.call_count == 1 and stored['approval_performed'] is stored['execution_performed'] is False
    if decision == 'not_required':
        assert prepared['status'] == 'approval_not_required' and prepared['approval_required_step_ids'] == []
        with pytest.raises(InterfaceApiError,match='does not require'):
            record_interface_plan_approval(InterfacePlanApprovalDecisionRequest(action='record_plan_approval',**basis,confirmed_approval_request_sha256=prepared['approval_request_sha256'],decision='approved',approver='operator',reason='Must not invent authority'),project_root=tmp_path)
        assert not (tmp_path/'approvals').exists()
        return
    scope = {**basis,'confirmed_approval_request_sha256':prepared['approval_request_sha256']}
    recorded = record_interface_plan_approval(InterfacePlanApprovalDecisionRequest(action='record_plan_approval',**scope,decision=decision,approver='operator',reason='Exact test decision',valid_for_minutes=60),project_root=tmp_path)
    linked = {**scope,'approval_filename':recorded['approval_filename']}
    verified = verify_interface_plan_approval(InterfacePlanApprovalVerificationRequest(action='verify_plan_approval',**linked),project_root=tmp_path)
    assert verified['approved'] is (decision == 'approved')
    assert recorded['execution_performed'] is verified['execution_performed'] is False
    compile_request = InterfacePlanRecipeCompilationRequest(action='compile_plan_recipe',**linked)
    if decision == 'denied':
        with pytest.raises(InterfaceApiError,match='does not permit'):
            compile_interface_plan_recipe(compile_request,project_root=tmp_path)
        assert not (tmp_path/'workflow-recipes').exists()
        return
    compiled = compile_interface_plan_recipe(compile_request,project_root=tmp_path)
    assert compiled['recipe']['steps'][0]['skill_id'] == skill
    assert compiled['recipe']['steps'][0]['arguments'] == {'path':path}
    recipe = save_interface_plan_recipe(InterfacePlanRecipeSaveRequest(action='save_reviewed_plan_recipe',**linked,confirmed_recipe_sha256=compiled['recipe_sha256']),project_root=tmp_path)
    assert recipe['recipe_saved'] is True
    assert recipe['approval_performed'] is recipe['execution_performed'] is False
    assert (tmp_path/'workflow-recipes'/recipe['recipe_filename']).is_file()
    assert json.loads((tmp_path/'plans'/stored['plan_filename']).read_text())['plan']['steps'][0]['skill'] == skill
