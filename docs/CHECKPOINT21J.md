# Checkpoint 21J — exact recipe/source-plan definition

## ZIP summary

- Extracted the existing deterministic Planner-to-recipe mapping into one shared backend module. Compilation and history verification now call the same mapping; the interface wrapper preserves its existing error messages.
- Extended GET task relationships with recipe_relationships. A recipe must match the complete reconstructed definition from one recorded plan, including skill sequence, dependencies, arguments, outputs, summary and original request.
- Rechecks file-byte references, recipe schemas and canonical recipe filenames before comparing definitions. Names or ID prefixes alone never establish a relationship.
- Tests cover exact matches, changed arguments/request/outputs, altered bytes and missing source plans. 24 focused tests and Python compilation passed locally. Full API/Python suite remains for WSL. No frontend change.

## Validate

```bash
.venv/bin/pytest -q tests/test_task_history.py tests/test_task_relationships.py tests/test_planner_selected_scope.py tests/test_planner_agent.py tests/test_interface_api.py
make test
```

Restart the launcher. For a task that already saved a reviewed Planner-derived recipe after v24:

```bash
TASK_ID="task-your-real-id"
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/artifacts" | .venv/bin/python -m json.tool
curl -sS "http://127.0.0.1:8765/api/v1/tasks/$TASK_ID/relationships" | .venv/bin/python -m json.tool
```

Expected: recipe file matched in artifacts, and recipe_relationships contains relationship exact_definition with the exact source plan path. execution_authorized stays false. An approved plan may have decision_verified true at inspection time; that is not recipe approval or run authority.

For the previously denied task, the denial remains exact_plan/denied/decision_verified false. Its recipe_relationships should be empty if no recipe was saved. This is expected; do not change the denial merely to populate that list. Use the separate deliberately approved recipe-storage fixture from Checkpoint 21I if you want a live recipe relationship test, or run the deterministic temporary tests above.

An unlinked recipe means no unique complete source definition was found. Findings identify unavailable, altered or invalid evidence. No files or approvals are modified by inspection.

## Boundaries and remaining work

This verifies relationships among explicit references, not the legitimacy of task assignment or executable skill policy. The endpoint now reports verification_scope recorded_plan_approval_and_recipe. Existing approval relationships remain intact. Original execution boundaries must independently verify current authority.

Next: recipe execution/outcome references and exact result relationships, then finish Checkpoint 21 recovery acceptance. Task-history discovery needs a prominent task-centered entry point during the later interface redesign; current deep Inspector navigation is too difficult, as confirmed by the user. Backend work remains the priority.
