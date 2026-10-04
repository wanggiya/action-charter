"""Context review is immutable, snapshot-bound and never work approval."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from geoagent_harness.task_history import append_task_event
from geoagent_harness.context_retrieval import retrieve_task_context, save_reviewed_context, load_reviewed_context, ContextReviewError

class ContextReviewTests(unittest.TestCase):
    def test_store_reopen_duplicate_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            history=Path(directory)/'history'; reviews=Path(directory)/'reviews'
            append_task_event(root=history,task_id='task-review',event_type='request',summary='Inspect vector')
            context=retrieve_task_context(root=history,query='vector',task_ids=['task-review'])
            args=dict(history_root=history,review_root=reviews,query='vector',task_ids=['task-review'],
                      confirmed_context_sha256=context['context_sha256'],reviewer='operator',reason='Relevant vector history',
                      now=datetime(2026,10,2,tzinfo=timezone.utc))
            saved=save_reviewed_context(**args)
            record=load_reviewed_context(review_root=reviews,history_root=history,filename=saved['review_filename'])
            self.assertTrue(record['review_performed']);self.assertFalse(record['plan_approved']);self.assertFalse(record['model_called'])
            self.assertEqual(record['context'],context)
            path=reviews/saved['review_filename']; original=path.read_bytes()
            with self.assertRaises(ContextReviewError):save_reviewed_context(**args)
            self.assertEqual(path.read_bytes(),original)
            path.write_bytes(original+b' ')
            with self.assertRaises(ContextReviewError):load_reviewed_context(review_root=reviews,history_root=history,filename=saved['review_filename'])

    def test_changed_source_blocks_save_and_later_use(self):
        with tempfile.TemporaryDirectory() as directory:
            history=Path(directory)/'history'; reviews=Path(directory)/'reviews'
            append_task_event(root=history,task_id='task-stale',event_type='request',summary='Inspect vector')
            context=retrieve_task_context(root=history,query='vector',task_ids=['task-stale'])
            args=dict(history_root=history,review_root=reviews,query='vector',task_ids=['task-stale'],confirmed_context_sha256=context['context_sha256'],reviewer='operator',reason='Relevant')
            saved=save_reviewed_context(**args)
            append_task_event(root=history,task_id='task-stale',event_type='failure',summary='Vector failed')
            with self.assertRaisesRegex(ContextReviewError,'changed'):save_reviewed_context(**args)
            with self.assertRaisesRegex(ContextReviewError,'stale'):load_reviewed_context(review_root=reviews,history_root=history,filename=saved['review_filename'])
            self.assertEqual(len(list(reviews.glob('*.json'))),1)

    def test_empty_context_and_symlink_destination_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            history=Path(directory)/'history'; reviews=Path(directory)/'reviews'
            append_task_event(root=history,task_id='task-empty',event_type='request',summary='Inspect vector')
            context=retrieve_task_context(root=history,query='unmatchedword',task_ids=['task-empty'])
            args=dict(history_root=history,review_root=reviews,query='unmatchedword',task_ids=['task-empty'],confirmed_context_sha256=context['context_sha256'],reviewer='operator',reason='Relevant')
            with self.assertRaisesRegex(ContextReviewError,'empty'):save_reviewed_context(**args)
            context=retrieve_task_context(root=history,query='vector',task_ids=['task-empty'])
            reviews.symlink_to(history,target_is_directory=True)
            args.update(query='vector',confirmed_context_sha256=context['context_sha256'])
            with self.assertRaisesRegex(ContextReviewError,'unsafe'):save_reviewed_context(**args)
