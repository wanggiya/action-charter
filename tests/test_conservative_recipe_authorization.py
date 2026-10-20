"""Preserve stricter plan gates through recipe authorization and execution."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_tabular_workflow import project, pipeline, saved
from geoagent_harness import write_policy as policy
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow
from geoagent_harness.planner.recipe_definition import planner_recipe_definition
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.recipes.approval import create_recipe_approval, verify_recipe_approval
from geoagent_harness.recipes.digest import canonical_recipe_json, recipe_sha256
from geoagent_harness.recipes.policy import validate_recipe_policy
from geoagent_harness.recipes.schemas import WorkflowRecipe
from geoagent_harness.skill_registry import load_skill_registry


def report_plan():
    return PlannerResult(model='fixture', original_request='Inspect CSV and assess an existing fixture table; record a report.',
        context_references=[], plan={'summary':'Inspection and fixture validation report','steps':[
            {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'}},
            {'step_id':'step_2','skill':'validate_postgis_layer','purpose':'Validate fixture table','requires_approval':True,'validation_required':True,
             'arguments':{'target_schema':'public','target_table':'fixture_points'}},
            {'step_id':'step_3','skill':'generate_report','purpose':'Record evidence report','requires_approval':True,
             'arguments':{'task_id':'fixture-report'}},
        ]})


def authorize(project):
    request=saved(project,report_plan())
    review=prepare_workflow(request,project_root=project)
    decision=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow',
        'confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,
        'approver':'fixture','reason':'Only temporary fixture scope'}),project_root=project)
    return request, review, decision


def test_evidence_write_with_conservative_gates_authorizes_without_dispatch(project,monkeypatch):
    from geoagent_harness.recipes import dispatcher
    def forbidden(**kwargs):
        pytest.fail('Authorization must not contact a database or dispatch an operation')
    monkeypatch.setattr(dispatcher,'validate_postgis_layer',forbidden)
    with policy.session(project,enabled=True):
        request,review,decision=authorize(project)
        assert review['write_step_ids']==['step_3']
        assert review['approval_required_step_ids']==['step_2','step_3']
        assert decision['approval_recorded'] and not decision['execution_performed']
        assert len(list((project/'approvals').glob('approval-*.json')))==1
        assert len(list((project/'approvals').glob('recipe-approval-*.json')))==1
        assert not list((project/'data/output').iterdir())
        assert not (project/'inspection-runs').exists()


def test_report_execution_uses_fixture_validation_and_retains_session_bounds(project,monkeypatch):
    from geoagent_harness.recipes import dispatcher
    from geoagent_harness.verifier.postgis import PostGISValidationResult
    observed=[]
    def validate(**kwargs):
        observed.append(kwargs['target_table'])
        return PostGISValidationResult(status='passed',passed=True,target_schema='public',target_table='fixture_points',
            table_exists=True,geometry_column_exists=True,geometry_column='geom',row_count=2,srid=4326,
            geometry_type='POINT',invalid_geometry_count=0,null_geometry_count=0,extent=None,checks=[],warnings=[])
    monkeypatch.setattr(dispatcher,'validate_postgis_layer',validate)
    with policy.session(project,enabled=True):
        request,review,decision=authorize(project)
        executable=WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow',
            'confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,
            'plan_approval_filename':decision['plan_approval_filename'],'recipe_approval_filename':decision['recipe_approval_filename']})
        result=execute_workflow(executable,project_root=project)
        assert result['status']=='validated_success'
        assert observed==['fixture_points']
        assert result['report_path']
        state=policy.snapshot(project)
        policy.update(project,policy.PolicyUpdate(enabled=False,session_id=state['session_id'],revision=state['revision']))
        with pytest.raises((ValueError,RuntimeError),match='review|OFF|Confirm'):
            execute_workflow(executable,project_root=project)
        assert observed==['fixture_points']


def test_extra_gates_are_digest_bound_and_cannot_weaken_registry(project):
    registry=load_skill_registry(project)
    proposal=pipeline()
    recipe=planner_recipe_definition(proposal,plan_sha256(proposal.plan))
    # Ordinary write recipes retain historical serialization and identity.
    payload=recipe.model_dump(mode='json')
    assert all('additional_approval_required' not in step for step in payload['steps'])
    assert WorkflowRecipe.model_validate(payload)==recipe
    legacy=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    assert canonical_recipe_json(recipe)==legacy
    gates=validate_recipe_policy(recipe,registry=registry).approval_required_step_ids
    assert gates==[f'step_{i}' for i in range(2,8)]
    # An explicit false flag cannot remove trusted transformation approval.
    payload['steps'][1]['additional_approval_required']=False
    assert validate_recipe_policy(WorkflowRecipe.model_validate(payload),registry=registry).approval_required_step_ids==gates
    report=report_plan()
    strict=planner_recipe_definition(report,plan_sha256(report.plan))
    assert validate_recipe_policy(strict,registry=registry).approval_required_step_ids==['step_2','step_3']
    changed=strict.model_copy(deep=True);changed.steps[1].additional_approval_required=False
    assert recipe_sha256(changed)!=recipe_sha256(strict)
    now=datetime.now(timezone.utc)
    approval,_=create_recipe_approval(recipe=strict,registry=registry,step_ids=['step_2','step_3'],
        decision='approved',approver='fixture',reason='Temporary scope',approval_root=project/'approvals',
        now=now,expires_at=now+timedelta(minutes=30))
    assert not verify_recipe_approval(approval=approval,recipe=changed,registry=registry,now=now).approved
