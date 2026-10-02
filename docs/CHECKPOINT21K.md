# Checkpoint 21K — durable task outcome references

## ZIP summary

- When an exact task-derived saved recipe finishes through the existing execution boundary, the backend appends references to its durable run result and evidence. It reads current bounded bytes; execution approval checks remain unchanged.
- Interface sends task_id only when its active recipe digest equals the task's saved Planner-derived recipe. Unrelated runs remain unassigned. History-link failures are visible after the run; retrying execution is not a repair strategy for history failures.
- Extended relationships with outcome_relationships: compare exact recipe identity/digest, step sequence, execution output IDs, status consistency and the complete embedded evidence result. Inspection remains nonexecuting and live_outputs_reverified false.
- 25 focused tests, Python compilation and frontend typecheck/build passed locally. Full API/Python suite remains for WSL.

## Validate without executing

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py tests/test_planner_selected_scope.py
make test
corepack pnpm@10.17.1 --dir interface build
```

Task relationship tests use temporary fixtures. They check exact records and reject wrong recipe digests, wrong skills, different embedded evidence, missing evidence and altered bytes. No model, database write or recipe execution is required.

After restarting the launcher, recheck the existing denied task:

```bash
curl -sS http://127.0.0.1:8765/api/v1/tasks/task-63f0cd2f3f3f42ffa42e16a381822d32/relationships | .venv/bin/python -m json.tool
```

The denial must remain exact_plan and denied with decision_verified false. Empty recipe_relationships and outcome_relationships are expected. execution_authorized stays false.

## Optional live run check

Only if you deliberately choose to execute a fresh, reviewed task-derived recipe in your development environment: use the normal approved execution flow and a fresh target. Do not run the denied task. After the durable response, execution Network response task_references should contain two recorded entries; Task history should include result/evidence references. GET artifacts should show matched bytes; GET relationships should show exact_recorded_outcome with the exact recipe/result/evidence paths and execution_authorized false. A validation_failed outcome can still have an exact record relationship; inspect final_status rather than interpreting relationship as success.

This endpoint verifies stored structural relationships, not actual tool behavior or physical output validity. It does not independently verify the run approval record, prove legitimate task assignment, or authorize a future execution. Current execution authority continues through the existing approval and execution services.

## Remaining

Exception-only or interrupted attempts without a returned durable result do not get fabricated outcome links. Their progress/failure history remains separate. Complete interrupted-attempt recovery, review execution approval relationships and run the end-to-end recovery acceptance before closing Checkpoint 21. Context/intent work follows; UI discoverability remains deferred.
