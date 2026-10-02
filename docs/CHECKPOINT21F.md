# Checkpoint 21F — recorded plan/approval relationships

## ZIP summary

- Added read-only GET `/api/v1/tasks/<task_id>/relationships`.
- Rechecks task history, bounded current artifact bytes, authoritative Planner/approval schemas, filename identities, canonical plan digest and exact required approval steps.
- Uses the existing approval verifier for denied/expired records. Inspection always returns execution_authorized false and never records approval or executes.
- Added deterministic coverage for approved, denied, expired, wrong-scope, altered and unrelated records.
- Six task tests and Python compilation passed locally. Full API suite remains for WSL. Frontend unchanged.

## Validate

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py
make test
```

Restart the launcher, copy a real task ID from Task history, then:

```bash
TASK_ID="task-your-real-id"
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/relationships" | .venv/bin/python -m json.tool
```

An empty relationships list is expected for tasks without explicitly recorded plan and approval references. Existing UI history does not automatically supply those references yet. The deterministic test creates temporary fixtures to verify every branch without modifying your real plans or approvals.

## Scope and next work

This independently checks relationships among referenced files. It does not prove that a user legitimately assigned the references to the task, revalidate executable tool policy, or authorize execution. A matching denied or expired approval still relates to its plan, but decision_verified is false. Files are inspected at request time; run-time authority must continue through the existing execution boundary.

Remaining: attach references from trusted artifact save operations, then verify recipes and outcomes. Checkpoint 21 remains open. Context retrieval and intent reasoning follow in Checkpoint 22.
