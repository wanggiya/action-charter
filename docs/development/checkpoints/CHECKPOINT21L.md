# Checkpoint 21L — recorded execution approval relationships

## ZIP summary

- Completed task-derived runs append three references: durable result, evidence and the exact recipe-approval file selected at execution.
- Task inspection parses authoritative recipe-approval schemas and checks filename identity. It reports execution_approval_relationships against recorded recipe digests.
- Current approval checking delegates to the existing recipe approval verifier and current skill registry, including policy, required scope, decision and expiry. Inspection never grants run authority.
- Outcome relationships expose execution_approval_path and execution_approval_link independently from the structural result/evidence relationship. A structurally matched outcome without its approval reference remains explicitly unlinked on that field.
- Added approved/denied/expired/wrong-scope/wrong-recipe fixture coverage. Full WSL API suite remains required. Frontend typecheck/build and Python compilation passed locally; focused test result is recorded below.

## Validate without execution

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py tests/test_planner_selected_scope.py
make test
corepack pnpm@10.17.1 --dir interface build
```

Restart the launcher. Recheck the existing denied plan task:

```bash
curl -sS http://127.0.0.1:8765/api/v1/tasks/task-63f0cd2f3f3f42ffa42e16a381822d32/relationships | .venv/bin/python -m json.tool
```

Its plan decision remains denied. execution_approval_relationships and outcome_relationships are empty because no recipe run/approval was recorded for that task. execution_authorized must stay false.

For an optional deliberate fresh approved recipe run, use the existing execution flow. Never run the denied task. After completion, task_references should have three recorded entries. On the task relationships endpoint, execution_approval_link should be exact_identity; inspect execution_approval_relationships for decision_verified_now and its reason. Current approval verification may become false later when it expires or policy changes. That does not rewrite the recorded run. No historical-at-start approval verification is claimed by this endpoint.

## Recovery acceptance still needed

- Restart API/browser and reopen the same task, with unchanged references and relationships.
- Confirm tampered or missing evidence cannot be presented as checked relationships (temporary fixtures cover this).
- Verify interrupted and exception-only attempts remain visible separately, cannot claim durable success, and do not automatically retry writes.
- Check the full WSL suite and one deliberately approved end-to-end task before declaring Checkpoint 21 complete.

No new execution authority, automatic retry or interface redesign is introduced. Task recovery is still inspection-only. Improving task discovery remains an explicit later interface requirement.

Local focused verification: 26 tests passed, including all recipe-approval fixture branches.
