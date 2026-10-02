# Checkpoint 21 — governed task history

## 21A: immutable task events and derived context

The `task_history` module records a bounded, append-only event sequence per task ID under the local ignored `task-history/` directory. The CLI can append requests, clarifications, selections, decisions, outcomes, failures and artifact references. Every event stores a redacted payload, sequence number, previous event digest, timestamp and canonical content digest in its filename. An exclusive task lock protects concurrent appends. Reads verify the whole chain and reject gaps, edits, unsafe paths and excessive data.

`build-task-context` selects the first event and up to 19 most recent events, with a 12,000-character limit. Its deterministic SHA-256 is over the complete derived package excluding that digest. Each excerpt cites its exact event file and digest. The original records remain authoritative; the context is a replaceable view and does not call a model or execute work. This first slice does **not** automatically record all existing interface actions, become Planner memory, or consolidate approvals. Those integrations remain Checkpoint 21 follow-ups and Checkpoint 22.

Run these commands in the WSL checkout after applying the package:

```bash
.venv/bin/geoagent record-task-event task-demo --event-type request --summary 'Inspect sample_points.geojson and validate the result.' --project-root .
.venv/bin/geoagent record-task-event task-demo --event-type selection --summary 'Selected data/input/sample_points.geojson.' --project-root .
.venv/bin/geoagent build-task-context task-demo --project-root .
.venv/bin/pytest -q tests/test_task_history.py
make test
```

Use a new task ID for a separate task. The commands only record or inspect history; neither grants approval. `task-history/` is ignored by Git because requests and references may be private. The redactor recognizes common credential assignments and URLs; do not enter secrets deliberately into task summaries. Artifact references must use a relative path and SHA-256; recording a reference does not assert that the referenced artifact exists or passed validation.

## Next work in Checkpoint 21

- Correlate interface request, clarification, selection, human decision, execution result and failure events under one stable task identity, without treating a chat entry as authorization.
- Add bounded, exact source references to existing plan, recipe, approval and result artifacts; verify those artifacts before projecting claims into task history.
- Expose a read-only task timeline and context preview in the interface, retaining CLI access and Advanced evidence inspection.
- Add migration/legacy behavior for existing runs without task IDs and test cross-process append, tampering, limits and replay.

## 21B: local interface API boundary

The loopback interface API now accepts `POST /api/v1/tasks/events` with `action: record_task_event`, an event type, and a short summary. Omit `task_id` only for the first `request` event; the server returns a generated task ID. Later events require that existing task ID. `GET /api/v1/tasks/{task_id}/context` verifies the event chain again and returns the same bounded, cited context as the CLI. Cross-origin requests outside the configured local frontend origin are rejected by the existing API boundary.

The `decision` event type is a historical note only. The response says `recorded_history_only`, `approval_recorded: false`, and `execution_performed: false`; it cannot grant recipe or plan authority. Do not use it as a substitute for the existing approval endpoints. Neither endpoint automatically attaches plans, runs, or outcomes, and no model consumes the context yet.

With the local API started on port 8765, a smoke check is:

```bash
curl -sS -X POST http://127.0.0.1:8765/api/v1/tasks/events \
  -H 'Content-Type: application/json' \
  -d '{"action":"record_task_event","event_type":"request","summary":"Inspect sample_points.geojson."}'
# Copy the returned task_id, then:
curl -sS http://127.0.0.1:8765/api/v1/tasks/TASK_ID/context
```

Run `.venv/bin/pytest -q tests/test_task_history.py tests/test_interface_api.py` and `make test` after applying 21B. The focused HTTP test checks that the API returns a task identity and reopens its verified context without approval or execution. Subsequent Checkpoint 21 work will bind actual interface actions to the task and present the timeline/context beside the graph.

## 21C: current task in the interface

Generating a new Planner proposal starts a task history before the model call, records the selected skill/input set, and adds an outcome or failure event after the Planner response. The full request (up to the Planner's 8,000-character limit) remains in the redacted original event; the inspector preview shows a shorter summary with an exact source reference. When the operator records a plan decision, the task history adds a **history-only** note pointing to its approval filename. Existing approval endpoints remain authoritative. A completed or failed governed run adds an event only when the active recipe digest matches the recipe saved from that task's reviewed plan; other runs are not silently assigned to it.

A collapsible **Current task history** section appears in the graph inspector. It displays the bounded context, task ID, event count, source-backed summaries, truncation notice and optional audit digest. Refresh rechecks the original event chain. The current task ID persists through a browser refresh in session storage; the actual events stay in the local ignored `task-history/` directory. Selecting an old saved plan clears the current task ID because old artifacts have no proven task assignment. Switching the graph source does not reassign the task; the pane explicitly says the graph source may differ.

Browser acceptance in the WSL environment:

1. Start the interface normally. Generate a new plan with a short request, one implemented skill and a selected input. The inspector should show a task ID and at least three events (request, selection, planning outcome), or a visible history warning if recording failed. The plan itself remains planning-only.
2. Expand and collapse the task pane, refresh it, then reload the page in the same tab. The same task ID and checked context should reopen. Select another graph source and confirm it does not claim to belong to the task.
3. Record a plan decision. The history receives a decision **note**, while the actual approval status still comes from the separate approval verifier. A denied decision must not enable execution.
4. Run only the exact recipe saved from that task's plan, if appropriate in your test environment. Its result or failure adds a task event; manually opening an unrelated recipe must not gain that event.
5. Run `.venv/bin/pytest -q tests/test_task_history.py tests/test_interface_api.py`, `corepack pnpm@10.17.1 --dir interface build`, and `make test`.

This is a current-session projection, not the final one-decision interface. Historic plans and runs still lack a task relationship. More complete and independently verified artifact references, task recovery across browser sessions, and the post-history conversation layout remain follow-up work in Checkpoints 21–22.

## Task-history startup correction

If the request event cannot be written, the interface now stops before calling the Planner and shows the API error. An HTTP 404 instructs the operator to restart the updated interface API. Once a task exists, a later selection/context failure is shown as a warning while the original request remains recoverable. The task pane must never quietly say “No active task” after an attempted Planner call. This correction does not relax the Planner skill policy; an invented skill still fails, but its task receives a failure event when history is available.

The checkpoint order was revised in `context/AGENT_INTERFACE_SEQUENCE.md`: finish recoverable task identity, add reviewed Intent reasoning, then make the default task-centered interface before expanding tool families.

## 21D: saved-task history recovery

The inspector section is now called **Task history**. Its **Saved tasks** button lists up to 50 recent task histories, independently checking each chain. Invalid histories appear as findings rather than usable context. Empty task directories are omitted. Each context entry exposes its original event path and digest under **Source event**. This checks the history chain; it does not verify every external artifact mentioned by an event.

Selecting a saved task changes the inspected context only. It does not change the graph source, active planning task, approval, or execution scope. This is history recovery, not workflow resumption.

Browser acceptance:

1. Restart the updated launcher and open the graph inspector. Expand **Task history**, then click **Saved tasks**. Existing task histories should show their summary, date and event count.
2. Select an earlier task. Confirm the task ID and context change, the list closes, and the message says history inspection does not resume execution. Expand **Source event** for a context entry.
3. Confirm the current graph and run/approval state did not change. Use **Refresh checked context** to reread the selected history.
4. Stop both services, restart, and open a new browser tab. Use **Saved tasks** to reopen the same task. Its stored events should still be available. No new model call or execution is needed for this test.
5. Run `.venv/bin/pytest -q tests/test_task_history.py tests/test_interface_api.py`, `make test`, and `corepack pnpm@10.17.1 --dir interface build`.

Local verification: four task-history unittest checks, Python compilation, and frontend typecheck/build passed. The full API/Python suite must be run in the project's WSL virtual environment. Checkpoint 21 remains open for artifact relationships and safe task recovery boundaries.

Checkpoint 21D refresh correction: preserve task-context, Inspector and page scroll positions during checked refresh; isolate nested details toggles; add Advanced → Task history navigation. Verify by scrolling the context, refreshing, and opening/closing Source event without collapsing the outer pane.

Checkpoint 21D layout correction: move history selection/refresh controls outside the scrollable context, reserve a stable context height, and disable Inspector scroll anchoring. After this focused fix, prioritize backend task/artifact verification and reviewed context services before further interface redesign.

Graph-source header correction (v19): the screenshots identify Refresh graph sources, not Refresh checked context. Replace option-dependent flex wrapping with explicit responsive grid columns and a constrained selector. Metadata occupies a consistent second row; narrow screens use a deliberate single-column header. Validate by refreshing graph sources repeatedly with long saved names at the same window width. Backend work follows this focused correction.

Checkpoint 21E: explicit task artifact references can be independently checked against bounded current evidence bytes through a read-only API. This verifies file identity only, not semantic relationships or authority. Five history tests passed locally; full WSL suite pending. See `docs/CHECKPOINT21E.md`.

Checkpoint 21F adds read-only recorded plan/approval relationship inspection with authoritative schemas and existing approval verification. Six focused task tests passed; no execution authority is granted. Automatic reference attachment and recipe/outcome checks remain open. See `docs/CHECKPOINT21F.md`.

Checkpoint 21G links actual plan saves and approval/denial records to the active task with file-byte references. Completed artifact operations survive visible history failures. Seven focused task tests and frontend build passed locally; full WSL suite pending. See `docs/CHECKPOINT21G.md`. Recipe/outcome links remain open.

Checkpoint 21H corrects selected-skill Planner prompts, removes unconditional unrelated PostGIS instructions, includes conversion arguments, and allows one fully revalidated policy correction. 54 focused tests passed; full WSL suite and live-model check pending. See `docs/CHECKPOINT21H.md`.

Checkpoint 21I records an exact task reference after storing a reviewed Planner-derived recipe and surfaces history failures without undoing storage. 23 focused tests and frontend build passed locally; full API suite pending. Recipe semantic relationships and outcomes remain open. See `docs/CHECKPOINT21I.md`.

Checkpoint 21J checks full recipe definitions against their recorded source plans using the same backend mapping as compilation. 24 focused tests passed; full API suite pending. Outcome links remain open. Task-history discoverability is explicitly deferred to task-centered UI redesign. See `docs/CHECKPOINT21J.md`.

Checkpoint 21K links task-derived completed run result/evidence references and checks exact recorded outcome relationships without revalidating live outputs or granting authority. 25 focused tests and frontend build passed locally; full WSL suite pending. Interrupted attempts and recovery acceptance remain open. See `docs/CHECKPOINT21K.md`.

Checkpoint 21L records completed-run recipe approval references, verifies their current recipe policy/scope/expiry relationships, and separates historical identity from current permission. 26 focused tests and frontend build passed locally; full WSL API suite and recovery acceptance remain. See `docs/CHECKPOINT21L.md`.

Checkpoint 21M adds attempt/recovery task notes and a closeout acceptance checklist. 27 focused tests passed locally; full WSL API suite and deliberate end-to-end recovery acceptance remain pending. Advanced relationship graph direction is documented. Checkpoint 21 implementation is delivered for acceptance, not yet declared complete. See `docs/CHECKPOINT21M.md`.
