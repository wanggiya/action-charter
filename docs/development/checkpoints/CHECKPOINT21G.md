# Checkpoint 21G — references from real plan and approval saves

## ZIP summary

- Interface sends the active task ID when saving a reviewed plan or recording a plan approval/denial.
- After the artifact operation succeeds, the backend reads its bounded bytes and appends an exact file reference to the existing task.
- Response task_reference reports recorded, failed or not_requested. History failure leaves the completed save/decision intact and produces a visible task warning.
- Older saved plans reopened without a proven task assignment remain unassigned. No old history is retroactively inferred.
- Seven focused task tests, Python compilation and frontend typecheck/build passed locally. Full API suite remains for WSL.

## Test in WSL

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py
make test
corepack pnpm@10.17.1 --dir interface build
```

Restart both services through the launcher so the API accepts task_id on the save routes.

## Browser validation without execution

1. Generate a fresh plan using only convert_vector and the selected sample_points.geojson input. Example request: `Create exactly one convert_vector step from data/input/sample_points.geojson to data/output/task_reference_demo_01.gpkg. Requires approval true and validation required true. No other steps. Plan only.` Use a fresh filename if needed. Confirm the generated step and arguments before proceeding.
2. Review and save the plan. The active Task history should gain a Stored evidence reference event. Existing actual approval authority remains separate.
3. Prepare its approval request, record **Denied** with a reason, then reopen/refresh Task history. It should include the approval-file reference as well as the history-only decision note. Nothing should run.
4. Copy the task ID. Verify the backend links:

```bash
TASK_ID="task-your-real-id"
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/artifacts" | .venv/bin/python -m json.tool
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/relationships" | .venv/bin/python -m json.tool
```

The plan and approval references should be matched. The relationship should be exact_plan, decision denied, decision_verified false, execution_authorized false. Existing references unrelated to this test may also be listed. The immutable artifact reference stores a file-byte digest; canonical plan identity remains a separate digest.

In browser Network responses, save-reviewed and record-approval should show task_reference.status recorded. Failed is a partial history failure, not an artifact-operation failure; inspect the existing artifact before retrying. Every successful save request can append a reference, including already-stored responses; no new artifact version is created for already-stored plans.

## Remaining

Automatic recipe/run/outcome references, their semantic relationships and broader task recovery are not complete. No new execution authority or redesign is introduced. Continue backend work before the task-centered interface redesign.
