# Checkpoint 21M — recovery notes and closeout acceptance

## ZIP summary

- Persist active task ID with interface execution progress.
- Append history-only running and failed attempt notes. Reopening stale running progress classifies it as interrupted through the existing recovery logic and appends a bounded interrupted task note.
- Sequential repeated recovery reads do not duplicate the same attempt/state note. Notes use attempt identity rather than treating a mutable progress snapshot as immutable evidence.
- No retry, approval restoration, execution restart or success evidence is created by recovery.
- Added temporary note tests and an API recovery regression test. 27 focused task/Planner tests and Python compilation passed locally. Full API suite, including the new regression, remains for WSL.
- Documented Advanced as a selectable task/plan/decision/recipe/run/outcome relationship graph in INTERFACE_DESIGN_DIRECTION.md.

## Validate in WSL

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py tests/test_planner_selected_scope.py
make test
corepack pnpm@10.17.1 --dir interface build
```

The API regression test simulates a stale running attempt using temporary files, reopens it twice and checks one interrupted task note and no execution. Do not kill a real database-writing run just to test interruption.

## Closeout checklist

1. All commands above pass in the real project environment.
2. Restart launcher and inspect the existing denied task. Its exact_plan denial stays blocked; no recipe or outcome is invented.
3. In a separate fresh task, deliberately review a conversion-only plan with a fresh target, save it, approve that exact scope, compile/store the recipe, approve its exact recipe scope and execute through the existing normal flow if you choose to do a live acceptance run. Never reuse the denied task. Enable write tools only for this deliberate run using the launcher option already documented.
4. Inspect this task's artifacts/relationships: matching plan, decisions, recipe, result/evidence; exact_definition and exact_recorded_outcome; exact_identity execution approval link. Check final_status and actual output metadata. Structural relationships alone do not prove physical output validity.
5. Stop both services normally, restart, reopen the task and the durable run without executing again. References/relationships should remain inspectable. Approval may expire; that must not erase history or permit a rerun.
6. Confirm the temporary interrupted-attempt regression passed. An exception-only attempt remains failed/interrupted, not successful. Recovery guidance requires inspecting outputs before any new approval/target; no automatic retry.
7. Review git status/diff, stage only source/tests/docs and commit to a feature branch. Push, create a PR, wait for all required CI checks and merge with a merge commit. Do not commit runtime task history, outputs, ZIPs or build/dependency folders.

Checkpoint 21 remains **implementation delivered; acceptance pending** until these checks are satisfied. Report live-model failures or broken artifact links before calling it complete. Additional frontend polish is deferred; next planned backend milestone is reviewed context retrieval and intent reasoning in Checkpoint 22.

## Current boundaries

Attempt notes are audit history, not authority. Records can fail to append when history is full/invalid/unavailable; original durable progress remains the recovery source. Concurrent recovery readers are not claimed to provide exactly-once note delivery. No automatic resume is implemented. Outcome verification checks stored structural identity, while run-time approval and physical output checks remain separate existing boundaries.
