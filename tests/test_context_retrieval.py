"""Selected-history retrieval has deterministic citations and no authority."""
import tempfile
import unittest
from pathlib import Path
from geoagent_harness.task_history import append_task_event
from geoagent_harness.context_retrieval import retrieve_task_context, ContextRetrievalError

class ContextRetrievalTests(unittest.TestCase):
    def test_selected_scope_determinism_sources_and_untrusted_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=append_task_event(root=root,task_id="task-selected",event_type="request",summary="Convert sample_points geojson")
            append_task_event(root=root,task_id="task-selected",event_type="decision",summary="Denied conversion")
            append_task_event(root=root,task_id="task-other",event_type="request",summary="Convert sample_points geojson private")
            def retrieve(): return retrieve_task_context(root=root,query="sample_points convert",task_ids=["task-selected"])
            result=retrieve()
            self.assertEqual(result,retrieve())
            self.assertEqual(result["excerpts"][0]["source"],first["reference"])
            self.assertNotIn("task-other",str(result))
            self.assertFalse(result["review_performed"])
            self.assertFalse(result["approval_inferred"])
            self.assertFalse(result["execution_performed"])
            self.assertEqual(result["content_trust"],"untrusted_historical_text")

    def test_bounds_no_match_and_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=append_task_event(root=root,task_id="task-bounds",event_type="request",summary="vector "*100)
            for index in range(10):append_task_event(root=root,task_id="task-bounds",event_type="selection",summary=f"vector {index}")
            result=retrieve_task_context(root=root,query="vector",task_ids=["task-bounds"])
            self.assertEqual(len(result["excerpts"]),8)
            self.assertTrue(result["truncated"])
            self.assertEqual(retrieve_task_context(root=root,query="unmatchedword",task_ids=["task-bounds"])["excerpts"],[])
            for tasks in [[],["task-bounds"]*2,["../escape"],["task-missing"]]:
                with self.assertRaises(ContextRetrievalError):retrieve_task_context(root=root,query="vector",task_ids=tasks)
            path=root/first["reference"]["path"];path.write_bytes(path.read_bytes()+b" ")
            with self.assertRaises(ContextRetrievalError):retrieve_task_context(root=root,query="vector",task_ids=["task-bounds"])

    def test_redaction_and_snapshot_changes_after_new_event(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            append_task_event(root=root,task_id="task-snapshot",event_type="request",summary="Inspect vector")
            first=retrieve_task_context(root=root,query="vector password=private",task_ids=["task-snapshot"])
            self.assertNotIn("private",str(first))
            append_task_event(root=root,task_id="task-snapshot",event_type="failure",summary="Vector inspection failed")
            second=retrieve_task_context(root=root,query="vector password=private",task_ids=["task-snapshot"])
            self.assertNotEqual(first["context_sha256"],second["context_sha256"])
