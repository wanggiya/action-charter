"""Checkpoint 21 task history contract tests (stdlib unittest compatible)."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from geoagent_harness.task_history import (
    TaskHistoryError, append_task_event, build_task_context, load_task_events, inspect_task_inventory, inspect_task_artifacts, attach_task_artifact, record_task_attempt_state,
)


class TaskHistoryTests(unittest.TestCase):
    def test_attempt_recovery_notes_are_idempotent_and_never_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory) / "task-history"
            append_task_event(root=root,task_id="task-attempt",event_type="request",summary="Fixture")
            for state in ["running", "interrupted", "interrupted"]:
                self.assertTrue(record_task_attempt_state(root=root,task_id="task-attempt",attempt_sha256="a"*64,state=state))
            events=load_task_events(root=root,task_id="task-attempt")
            self.assertEqual(len(events),3)
            self.assertEqual(events[-1]["event_type"],"failure")
            self.assertEqual(events[-1]["payload"]["status"],"interrupted")
            self.assertFalse(record_task_attempt_state(root=root,task_id="task-attempt",attempt_sha256="a"*64,state="validated_success"))
            self.assertFalse(record_task_attempt_state(root=root,task_id="task-missing",attempt_sha256="a"*64,state="failed"))

    def test_recipe_reference_does_not_record_approval_or_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            root = project / "task-history"
            (project / "workflow-recipes").mkdir()
            (project / "workflow-recipes" / "fixture.json").write_bytes(b'{"recipe_id":"fixture"}')
            append_task_event(root=root, task_id="task-recipe", event_type="request", summary="Recipe fixture")
            result = attach_task_artifact(root=root, task_id="task-recipe", project_root=project, artifact_path="workflow-recipes/fixture.json")
            self.assertEqual(result["status"], "recorded")
            inspected = inspect_task_artifacts(root=root, task_id="task-recipe", project_root=project)
            self.assertEqual(inspected["links"][0]["status"], "matched")
            self.assertFalse(inspected["approval_recorded"])
            self.assertFalse(inspected["execution_performed"])

    def test_completed_save_reference_and_visible_partial_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            root = project / "task-history"
            (project / "plans").mkdir()
            artifact = project / "plans" / "stored.json"
            raw = b'{"stored":true}'
            artifact.write_bytes(raw)
            append_task_event(root=root, task_id="task-save", event_type="request", summary="Save fixture")
            result = attach_task_artifact(root=root, task_id="task-save", project_root=project, artifact_path="plans/stored.json")
            self.assertEqual(result["status"], "recorded")
            self.assertEqual(inspect_task_artifacts(root=root, task_id="task-save", project_root=project)["links"][0]["status"], "matched")
            failed = attach_task_artifact(root=root, task_id="task-missing", project_root=project, artifact_path="plans/stored.json")
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(artifact.read_bytes(), raw)
            self.assertFalse((root / "task-missing").exists())
            self.assertEqual(attach_task_artifact(root=root, task_id=None, project_root=project, artifact_path="plans/stored.json")["status"], "not_requested")

    def test_artifact_inspection_matches_tampering_missing_and_symlink(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = project / "task-history"
            (project / "plans").mkdir()
            artifact = project / "plans" / "example.json"
            raw = b'{"scope":"inspect"}\n'
            artifact.write_bytes(raw)
            append_task_event(root=root, task_id="task-links", event_type="request", summary="Inspect")
            append_task_event(root=root, task_id="task-links", event_type="artifact_reference", summary="Plan reference",
                              artifact_path="plans/example.json", artifact_sha256=hashlib.sha256(raw).hexdigest())
            def inspect():
                return inspect_task_artifacts(root=root, task_id="task-links", project_root=project)
            self.assertEqual(inspect()["links"][0]["status"], "matched")
            self.assertFalse(inspect()["semantic_relationship_verified"])
            self.assertFalse(inspect()["execution_performed"])
            artifact.write_bytes(b"changed")
            self.assertEqual(inspect()["links"][0]["status"], "mismatch")
            artifact.unlink()
            self.assertEqual(inspect()["links"][0]["status"], "unavailable")
            outside = project / "private.json"
            outside.write_bytes(raw)
            artifact.symlink_to(outside)
            self.assertEqual(inspect()["links"][0]["status"], "unavailable")
            artifact.unlink()
            (project / "plans").rmdir()
            (project / "plans").symlink_to(project, target_is_directory=True)
            self.assertEqual(inspect()["links"][0]["status"], "unavailable")

    def test_inventory_checks_history_without_modifying_or_resuming_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "task-history"
            valid = append_task_event(root=root, task_id="task-valid", event_type="request", summary="Inspect data")
            invalid = append_task_event(root=root, task_id="task-invalid", event_type="request", summary="Inspect other data")
            invalid_path = root / invalid["reference"]["path"]
            invalid_path.write_bytes(invalid_path.read_bytes() + b" ")
            original = (root / valid["reference"]["path"]).read_bytes()
            inventory = inspect_task_inventory(root=root)
            self.assertEqual([task["task_id"] for task in inventory["tasks"]], ["task-valid"])
            self.assertEqual(inventory["findings"][0]["task_id"], "task-invalid")
            self.assertFalse(inventory["execution_performed"])
            self.assertFalse(inventory["approval_recorded"])
            self.assertEqual((root / valid["reference"]["path"]).read_bytes(), original)

    def test_append_redaction_chain_and_reproducible_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "task-history"
            args = {"root": root, "task_id": "task-example", "occurred_at": datetime(2026, 9, 29, tzinfo=timezone.utc)}
            first = append_task_event(**args, event_type="request", summary="Inspect password=private points")
            second = append_task_event(**args, event_type="decision", summary="Denied for now")
            events = load_task_events(root=root, task_id="task-example")
            self.assertEqual(len(events), 2)
            self.assertEqual(events[1]["previous_sha256"], first["reference"]["sha256"])
            self.assertNotIn("private", json.dumps(events))
            context = build_task_context(root=root, task_id="task-example")
            self.assertEqual(context, build_task_context(root=root, task_id="task-example"))
            self.assertEqual(context["selected_count"], 2)
            self.assertEqual(context["excerpts"][1]["source"], second["reference"])
            self.assertFalse(context["model_called"])
            self.assertFalse(context["execution_performed"])

    def test_tampering_and_missing_event_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "task-history"
            first = append_task_event(root=root, task_id="task-tamper", event_type="request", summary="Inspect")
            append_task_event(root=root, task_id="task-tamper", event_type="outcome", summary="Inspected")
            path = root / first["reference"]["path"]
            path.write_bytes(path.read_bytes().replace(b"Inspect", b"Altered"))
            with self.assertRaisesRegex(TaskHistoryError, "digest mismatch"):
                load_task_events(root=root, task_id="task-tamper")
            with self.assertRaises(TaskHistoryError):
                append_task_event(root=root, task_id="task-tamper", event_type="failure", summary="Do not append")

    def test_unsafe_input_and_bounded_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "task-history"
            with self.assertRaises(TaskHistoryError):
                append_task_event(root=root, task_id="../escape", event_type="request", summary="x")
            with self.assertRaises(TaskHistoryError):
                append_task_event(root=root, task_id="task-safe", event_type="artifact_reference", summary="x", artifact_path="../secret", artifact_sha256="a" * 64)
            for number in range(25):
                append_task_event(root=root, task_id="task-bounded", event_type="clarification", summary=f"Entry {number}")
            context = build_task_context(root=root, task_id="task-bounded")
            self.assertEqual(context["selected_count"], 20)
            self.assertEqual(context["excerpts"][0]["sequence"], 1)
            self.assertEqual(context["excerpts"][1]["sequence"], 7)
            self.assertTrue(context["truncated"])


if __name__ == "__main__":
    unittest.main()
