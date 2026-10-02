# Checkpoint 21I — stored Planner recipe references

## ZIP summary

- Saving a reviewed Planner-derived recipe now submits the active task ID.
- After existing approval verification, deterministic compilation and immutable storage succeed, the backend appends its exact file-byte reference to that task.
- Recipe history-reference failure is a visible partial failure; the saved recipe remains saved. Refresh reopens context after a successful reference.
- 23 focused task/Planner tests, Python compilation and frontend typecheck/build passed locally. Full API suite remains for WSL.

## Confirm the preceding denied test

Copy the task ID from Task history:

```bash
TASK_ID="task-your-real-id"
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/artifacts" | .venv/bin/python -m json.tool
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/relationships" | .venv/bin/python -m json.tool
```

Expected: plan and approval file links matched; relationship exact_plan; decision denied; decision_verified false; execution_authorized false. That means the recorded denial matches this plan and still blocks execution. Empty arrays mean no explicit links were recorded, not successful verification. An unavailable/mismatch finding needs investigation; do not approve to bypass it.

## Validate this slice

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py tests/test_planner_selected_scope.py
make test
corepack pnpm@10.17.1 --dir interface build
```

Restart the launcher after applying. Keep the previously denied plan denied. To exercise recipe saving, start a fresh task, generate and review the conversion-only plan using a fresh output name, save, prepare its approval scope and deliberately record approval only if you agree with that scope. Independently verify approval, compile the governed recipe, review it, then Save reviewed recipe. Stop there: no recipe approval or execution is required for this reference test.

The save-reviewed-recipe Network response should contain task_reference.status recorded. Task history should gain a Stored evidence reference event. GET artifacts should list the workflow-recipes file as matched. Recipe storage remains separate from recipe approval and execution.

## Remaining

The relationships endpoint still covers recorded plan/approval relationships only. A matched recipe file is byte verification, not yet proof that its definition corresponds to the source plan. Exact definition checks and run/outcome references remain backend follow-ups. Checkpoint 21 stays open; no further UI redesign is included.
