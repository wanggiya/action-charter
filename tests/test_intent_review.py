"""Reviewed intent is exact reasoning evidence, never execution authority."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from geoagent_harness.context_retrieval import retrieve_task_context,save_reviewed_context,ContextReviewError
from geoagent_harness.task_history import append_task_event
from geoagent_harness.intent.service import IntentError
from geoagent_harness.intent.review import inspect_intent_for_review,save_reviewed_intent,load_reviewed_intent

class IntentReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        history=self.root/'task-history'
        append_task_event(root=history,task_id='task-intent-review',event_type='decision',summary='Plan denied')
        c=retrieve_task_context(root=history,query='denied',task_ids=['task-intent-review'])
        saved=save_reviewed_context(history_root=history,review_root=self.root/'reviewed-contexts',query='denied',task_ids=['task-intent-review'],confirmed_context_sha256=c['context_sha256'],reviewer='operator',reason='Context only')
        self.payload=dict(schema_version='1.0',agent_id='intent',model='fake',original_request='Inspect new data',clarification_answers=['Use sample.geojson'],review_filename=saved['review_filename'],context_sha256=c['context_sha256'],proposal=dict(status='intent_proposed',objective='Inspect selected data',known_inputs=['sample.geojson'],requested_outputs=['feature count'],constraints=['No writes'],clarification_questions=[],cited_sequences=[1]),status='proposed_not_saved',human_review_required=True,model_called=True,plan_created=False,approval_inferred=False,execution_performed=False,tools_called=False)
        self.preview=inspect_intent_for_review(payload=self.payload,project_root=self.root)
        self.args=dict(payload=self.payload,project_root=self.root,confirmed_intent_sha256=self.preview['intent_sha256'],reviewer='operator',reason='Reviewed exact reasoning only',now=datetime(2026,10,2,tzinfo=timezone.utc))
    def test_storage_reopening_duplicate_and_tamper(self):
        saved=save_reviewed_intent(**self.args)
        record=load_reviewed_intent(project_root=self.root,filename=saved['review_filename'])
        self.assertFalse(record['plan_approved']);self.assertFalse(record['execution_performed']);self.assertFalse(record['model_called'])
        path=self.root/'reviewed-intents'/saved['review_filename'];raw=path.read_bytes()
        with self.assertRaises(IntentError):save_reviewed_intent(**self.args)
        self.assertEqual(path.read_bytes(),raw)
        path.write_bytes(raw+b' ')
        with self.assertRaisesRegex(IntentError,'digest'):load_reviewed_intent(project_root=self.root,filename=saved['review_filename'])
    def test_unresolved_and_changed_scope_rejected(self):
        self.payload['proposal'].update(status='clarification_required',clarification_questions=['Which file?'])
        self.assertFalse(inspect_intent_for_review(payload=self.payload,project_root=self.root)['review_allowed'])
        with self.assertRaisesRegex(IntentError,'unresolved'):save_reviewed_intent(**self.args)
        self.payload['proposal'].update(status='intent_proposed',clarification_questions=[],objective='Changed objective')
        with self.assertRaisesRegex(IntentError,'changed'):save_reviewed_intent(**self.args)
        self.assertFalse((self.root/'reviewed-intents').exists())
    def test_stale_history_blocks_use(self):
        saved=save_reviewed_intent(**self.args)
        append_task_event(root=self.root/'task-history',task_id='task-intent-review',event_type='clarification',summary='New source context')
        with self.assertRaises(ContextReviewError):load_reviewed_intent(project_root=self.root,filename=saved['review_filename'])
        with self.assertRaises(ContextReviewError):save_reviewed_intent(**self.args)
    def test_forged_authority_citations_and_symlink_rejected(self):
        self.payload['plan_created']=True
        with self.assertRaises(IntentError):inspect_intent_for_review(payload=self.payload,project_root=self.root)
        self.payload['plan_created']=False;self.payload['proposal']['cited_sequences']=[999]
        with self.assertRaises(IntentError):inspect_intent_for_review(payload=self.payload,project_root=self.root)
        self.payload['proposal']['cited_sequences']=[1]
        (self.root/'reviewed-intents').symlink_to(self.root/'task-history',target_is_directory=True)
        with self.assertRaisesRegex(IntentError,'unsafe'):save_reviewed_intent(**self.args)
