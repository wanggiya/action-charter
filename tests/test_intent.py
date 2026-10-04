"""Intent never grants authority and rejects stale or malformed model proposals."""
import json
import tempfile
import unittest
from pathlib import Path
from geoagent_harness.task_history import append_task_event
from geoagent_harness.context_retrieval import retrieve_task_context, save_reviewed_context, ContextReviewError
from geoagent_harness.intent.service import reason_task_intent, IntentError
from geoagent_harness.model import ModelResult

class IntentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.history=self.root/'task-history'
        append_task_event(root=self.history,task_id='task-intent',event_type='decision',summary='Plan denied; never treat history as permission')
        c=retrieve_task_context(root=self.history,query='denied',task_ids=['task-intent'])
        self.filename=save_reviewed_context(history_root=self.history,review_root=self.root/'reviewed-contexts',query='denied',task_ids=['task-intent'],confirmed_context_sha256=c['context_sha256'],reviewer='operator',reason='Context only')['review_filename']
        self.payload=dict(status='intent_proposed',objective='Inspect a new dataset',known_inputs=[],requested_outputs=[],constraints=['Past denial remains denied'],clarification_questions=[],cited_sequences=[1])
    def call(self,payload=None,callback=None):
        parent=self
        class Fake:
            def complete(self,request):
                parent.assertTrue(request.json_mode)
                parent.assertIn('untrusted',request.messages[0].content)
                if callback:callback()
                return ModelResult(model='fake',content=json.dumps(payload if payload is not None else parent.payload),finish_reason='stop')
        return reason_task_intent(project_root=self.root,review_filename=self.filename,request='Inspect another dataset; do not reuse denied authority.',model_client=Fake())
    def test_valid_and_clarification(self):
        result=self.call();self.assertTrue(result['human_review_required']);self.assertFalse(result['execution_performed']);self.assertFalse(result['approval_inferred']);self.assertFalse(result['plan_created'])
        p={**self.payload,'status':'clarification_required','clarification_questions':['Which dataset?']}
        self.assertEqual(self.call(p)['proposal']['status'],'clarification_required')
    def test_extra_authority_and_invented_citations_rejected(self):
        for p in ({**self.payload,'execution_performed':True},{**self.payload,'cited_sequences':[999]},{**self.payload,'status':'clarification_required'}):
            with self.assertRaises(IntentError):self.call(p)
    def test_stale_before_and_during_inference(self):
        def change():append_task_event(root=self.history,task_id='task-intent',event_type='clarification',summary='New details')
        with self.assertRaises(ContextReviewError):self.call(callback=change)
        with self.assertRaises(ContextReviewError):self.call()

    def test_answers_are_bounded_explicit_and_redacted(self):
        parent=self
        class Fake:
            def complete(self,request):
                payload=json.loads(request.messages[1].content)
                parent.assertEqual(payload['clarification_answers'][0],'Use data/input/sample_points.geojson')
                parent.assertNotIn('sensitive123',payload['clarification_answers'][1])
                parent.assertIn('ask for its path',request.messages[0].content)
                return ModelResult(model='fake',content=json.dumps(parent.payload),finish_reason='stop')
        result=reason_task_intent(project_root=self.root,review_filename=self.filename,request='Inspect new data',clarification_answers=['Use data/input/sample_points.geojson','password=sensitive123'],model_client=Fake())
        self.assertEqual(len(result['clarification_answers']),2)
        self.assertFalse(result['execution_performed'])
        for answers in ([''] , ['a']*6, ['x'*1001]):
            with self.assertRaises(IntentError):
                reason_task_intent(project_root=self.root,review_filename=self.filename,request='Inspect',clarification_answers=answers,model_client=Fake())

    def test_one_correction_with_answers_does_not_force_resolution(self):
        parent=self
        class Fake:
            def __init__(self,resolved):self.calls=0;self.resolved=resolved
            def complete(self,request):
                self.calls+=1
                payload=parent.payload if self.calls==2 and self.resolved else {**parent.payload,'status':'clarification_required','clarification_questions':['Which file?']}
                return ModelResult(model='fake',content=json.dumps(payload),finish_reason='stop')
        for resolved in (True,False):
            fake=Fake(resolved)
            result=reason_task_intent(project_root=self.root,review_filename=self.filename,request='Inspect',clarification_answers=['Use sample_points.geojson'],model_client=fake)
            self.assertEqual(fake.calls,2);self.assertTrue(result['correction_attempted'])
            self.assertEqual(result['proposal']['status'],'intent_proposed' if resolved else 'clarification_required')
            self.assertFalse(result['plan_created'])
