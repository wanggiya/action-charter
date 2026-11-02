# Checkpoint 21E — task artifact byte verification

This backend slice adds `inspect_task_artifacts` and read-only GET `/api/v1/tasks/<task_id>/artifacts`. It rechecks the history chain, then compares explicitly recorded file digests with current bytes. Results are matched, mismatch, or unavailable. There is no model call, approval, or execution.

Only plans, approvals, workflow-recipes, recipe-runs, recipe-evidence, traces, reports and critic-results are inspected. Directory traversal, symlinks, nonregular files and files over 8 MiB are rejected. Inspection opens each path component without following symlinks. The bytes are not returned through this endpoint.

## Limitations

This checks exact byte identity only. An event reference remains a recorded claim, not proof of semantic relationships or execution authority. Existing histories without explicit artifact_path and artifact_sha256 return an empty links list. Automatic UI attachment and plan/approval/recipe relationship verification remain follow-up work. No interface redesign is included.

## Validation in WSL

Run:

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_interface_api.py
make test
```

Restart the launcher. To inspect a real task with explicit references, copy its ID from Task history and run:

```bash
TASK_ID="task-your-real-id"
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/artifacts" | .venv/bin/python -m json.tool
```

For a repeatable backend fixture without changing real plans, run this in the project root:

```bash
PYTHONPATH=src .venv/bin/python - <<'PYTEST'
import hashlib
import tempfile
from pathlib import Path
from geoagent_harness.task_history import append_task_event, inspect_task_artifacts
with tempfile.TemporaryDirectory() as directory:
    project = Path(directory)
    root = project / 'task-history'
    (project / 'plans').mkdir()
    artifact = project / 'plans' / 'demo.json'
    raw = b'{"scope":"inspect"}\n'
    artifact.write_bytes(raw)
    append_task_event(root=root, task_id='task-demo', event_type='request', summary='Inspect fixture')
    append_task_event(root=root, task_id='task-demo', event_type='artifact_reference', summary='Fixture plan', artifact_path='plans/demo.json', artifact_sha256=hashlib.sha256(raw).hexdigest())
    def status():
        return inspect_task_artifacts(root=root, task_id='task-demo', project_root=project)['links'][0]['status']
    assert status() == 'matched'
    artifact.write_bytes(b'changed')
    assert status() == 'mismatch'
    artifact.unlink()
    assert status() == 'unavailable'
    print('PASS: matching, changed and missing evidence')
PYTEST
```

Local checks: five task-history unittest tests and Python compilation passed. Full API/Python suite remains for WSL. Frontend was unchanged from the previously built v19.

## ZIP summary

- Added bounded read-only artifact identity verification in the backend and API.
- Added tests for matching, altered, missing and symlinked evidence.
- Updated documentation and status; retained cumulative Checkpoint 21 changes.
- Next: validated semantic relationships and automatic links from trusted save operations, followed by context retrieval and intent reasoning.
