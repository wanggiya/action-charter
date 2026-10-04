"""A reviewed intent cannot broaden the Planner execution envelope."""
import json
from unittest.mock import patch
from datetime import datetime,timezone
from geoagent_harness.intent.service import IntentError
from geoagent_harness.intent.review import inspect_intent_for_review,save_reviewed_intent
from geoagent_harness.context_retrieval import ContextReviewError
from geoagent_harness.task_history import append_task_event
from geoagent_harness.planner.schemas import PlannerResult,WorkflowPlan,PlanStep
import unittest
import tempfile
from pathlib import Path
from geoagent_harness.context_retrieval import retrieve_task_context, save_reviewed_context

class IntentHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        history=self.root/'task-history'
        append_task_event(root=history,task_id='task-intent-review',event_type='decision',summary='Plan denied')
        c=retrieve_task_context(root=history,query='denied',task_ids=['task-intent-review'])
        saved=save_reviewed_context(history_root=history,review_root=self.root/'reviewed-contexts',query='denied',task_ids=['task-intent-review'],confirmed_context_sha256=c['context_sha256'],reviewer='operator',reason='Context only')
        self.payload=dict(schema_version='1.0',agent_id='intent',model='fake',original_request='Inspect new data',clarification_answers=['Use sample.geojson'],review_filename=saved['review_filename'],context_sha256=c['context_sha256'],proposal=dict(status='intent_proposed',objective='Inspect selected data',known_inputs=['sample.geojson'],requested_outputs=['feature count'],constraints=['No writes'],clarification_questions=[],cited_sequences=[1]),status='proposed_not_saved',human_review_required=True,model_called=True,plan_created=False,approval_inferred=False,execution_performed=False,tools_called=False)
        self.preview=inspect_intent_for_review(payload=self.payload,project_root=self.root)
        self.args=dict(payload=self.payload,project_root=self.root,confirmed_intent_sha256=self.preview['intent_sha256'],reviewer='operator',reason='Reviewed exact reasoning only',now=datetime(2026,10,2,tzinfo=timezone.utc))

    def ready(self):
        self.payload['proposal']['known_inputs']=['data/input/sample.geojson']
        self.payload['proposal']['requested_outputs']=['feature count','fields','CRS']
        self.args['confirmed_intent_sha256']=inspect_intent_for_review(payload=self.payload,project_root=self.root)['intent_sha256']
        return save_reviewed_intent(**self.args)['review_filename']
    def planner(self,**kwargs):
        self.assertEqual(kwargs['allowed_skill_ids'],['inspect_vector'])
        self.assertEqual(json.loads(kwargs['original_request'])['exact_arguments'],{'path':'data/input/sample.geojson'})
        return PlannerResult(model='fake',original_request=kwargs['original_request'],context_references=[],plan=WorkflowPlan(summary='Inspect reviewed data',steps=[PlanStep(step_id='step_1',skill='inspect_vector',purpose='Inspect',arguments={'path':'data/input/sample.geojson'})]))
    def test_exact_handoff_no_save_or_authority(self):
        from geoagent_harness.intent.handoff import plan_reviewed_intent
        filename=self.ready()
        with patch('geoagent_harness.intent.handoff.plan_task',side_effect=self.planner):
            result=plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['inspect_vector'])
        self.assertEqual(result['status'],'planned_not_saved');self.assertFalse(result['plan_saved']);self.assertFalse(result['execution_performed']);self.assertFalse(result['approval_inferred'])
        self.assertFalse((self.root/'plans').exists())
    def test_wrong_path_extra_steps_and_capabilities_blocked(self):
        from geoagent_harness.intent.handoff import plan_reviewed_intent
        filename=self.ready()
        with self.assertRaises(IntentError):plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['convert_vector'])
        def wrong(**kwargs):
            result=self.planner(**kwargs);result.plan.steps[0].arguments['path']='data/input/other.geojson';return result
        def extra(**kwargs):
            result=self.planner(**kwargs);result.plan.steps.append(PlanStep(step_id='step_2',skill='inspect_vector',purpose='Extra',arguments={'path':'data/input/sample.geojson'}));return result
        for callback in (wrong,extra):
            with patch('geoagent_harness.intent.handoff.plan_task',side_effect=callback):
                with self.assertRaises(IntentError):plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['inspect_vector'])
    def test_context_changes_during_planning_discard_plan(self):
        from geoagent_harness.intent.handoff import plan_reviewed_intent
        filename=self.ready()
        def changed(**kwargs):
            result=self.planner(**kwargs)
            append_task_event(root=self.root/'task-history',task_id='task-intent-review',event_type='clarification',summary='Changed')
            return result
        with patch('geoagent_harness.intent.handoff.plan_task',side_effect=changed):
            with self.assertRaises(ContextReviewError):plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['inspect_vector'])

    def test_scope_error_identifies_flags_and_redacts_argument_credentials(self):
        from geoagent_harness.intent.handoff import plan_reviewed_intent
        filename=self.ready()
        def wrong(**kwargs):
            result=self.planner(**kwargs)
            result.plan.steps[0].validation_required=True
            result.plan.steps[0].arguments['path']='data/input/password=sensitive123.geojson'
            return result
        with patch('geoagent_harness.intent.handoff.plan_task',side_effect=wrong):
            with self.assertRaises(IntentError) as caught:
                plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['inspect_vector'])
        self.assertIn('validation_required must be false; received true',str(caught.exception))
        self.assertIn('arguments must equal',str(caught.exception))
        self.assertNotIn('sensitive123',str(caught.exception))

    def test_conservative_approval_gate_is_preserved_not_bypassed(self):
        from geoagent_harness.intent.handoff import plan_reviewed_intent
        filename=self.ready()
        def cautious(**kwargs):
            result=self.planner(**kwargs)
            result.plan.steps[0].requires_approval=True
            return result
        with patch('geoagent_harness.intent.handoff.plan_task',side_effect=cautious):
            result=plan_reviewed_intent(project_root=self.root,filename=filename,allowed_skill_ids=['inspect_vector'])
        self.assertTrue(result['planner_result']['plan']['steps'][0]['requires_approval'])
        self.assertTrue(result['additional_human_approval_required'])
        self.assertTrue(result['warnings'])
        self.assertFalse(result['approval_inferred']);self.assertFalse(result['execution_performed']);self.assertFalse(result['plan_saved'])
