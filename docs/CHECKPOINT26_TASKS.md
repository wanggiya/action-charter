> Superseded approach, preserved as checkpoint history. The operator now requires one conversation = one task with private memory. Use [current behavior and acceptance](CHECKPOINT26_CONVERSATIONS.md); separate task creation and cross-chat linking below are no longer supported.

# Checkpoint 26.1 — task separation across planning chats

This slice implements task boundaries, not the complete memory architecture or checkpoint 26 orchestration scope. Cancellation, retry/resume, indexed core memory, curator corrections and method templates remain unfinished work.

## Implemented behavior

- Active task and New task controls separate goals within one chat; an existing task can explicitly continue in a new chat.
- Tasks retain the latest validated proposal and bounded shared history without regeneration. Transcript entries carry task and source-chat IDs.
- New tasks do not inherit another task's plan/history. Dataset context is limited to sources referenced in the active request/title, included task history or plan.
- History OFF excludes previous task messages from the model but preserves records and the active typed plan.
- Switching clears workspace approval/execution state. A recovered proposal is not a recovered authorization token. Backend authority/digest/expiry checks remain unchanged.
- A graph that differs from the task plan must be explicitly bound using **Use current workflow for active task**, after validating edits, or replaced by **Open conversation plan**. Binding uses existing deterministic validation and grants no authority.
- Task create/select/bind/list/read makes no model call and executes no operation. No dependency, extra model or background worker is installed.

## Durable state and compatibility

`planner-workspace/tasks.sqlite3` uses standard-library SQLite transactions and full synchronous commits to save conversation/task updates together. Revision comparisons reject stale updates. Legacy `planner-conversations/*.json` remains readable; explicit task adoption leaves its original bytes untouched. Prior legacy work becomes a separate recoverable task before new work starts. The workspace becomes authoritative for adopted conversations; deleting it would lose later turns that are absent from the old JSON snapshot.

Limits: 128 stored tasks and 128 adopted conversations, 2 MB per record, 64 MB database, 100 messages per task/conversation. Cross-chat continuation does not remove the task's 50-turn bound. Read and history-off never delete data. Task archival/closing and project-memory export/deletion are future work. Back up SQLite consistently or stop the launcher before copying the workspace; legacy JSON alone is insufficient.

Workspace records are ignored by Git and container build contexts. Unsafe symlinks and non-regular/linked database files reject. SQL is internal and parameterized; model text cannot become executable SQL.

## Shared CLI/API

The existing `/api/v1/planner/conversation` endpoint gains `list_tasks`, `create_task`, `select_task`, `bind_task_plan`. Task-managed turns require active task ID and expected conversation/task revisions. Legacy turns retain their previous contract and existing origin checks.

```bash
.venv/bin/python -m geoagent_harness.cli planning-tasks --project-root .
.venv/bin/python -m geoagent_harness.cli planning-conversation-read CHAT_ID --project-root .
.venv/bin/python -m geoagent_harness.cli planning-task-create CHAT_ID --title "Inspect orders" --expected-revision 0 --project-root .
.venv/bin/python -m geoagent_harness.cli planning-task-select CHAT_ID TASK_ID --expected-revision CONVERSATION_REVISION --expected-task-revision CURRENT_ACTIVE_TASK_REVISION --project-root .
```

Replace placeholders with returned IDs/revisions. Omit expected-task-revision only if no task is active. `planning-task-bind-plan --help` describes binding a bounded PlannerResult JSON. Planning task IDs are distinct from the older Advanced Task history event IDs; workflow-event correlation is future work.

## Frontend acceptance

1. Start the normal launcher and open Planner. Enter task title **Vector inspection**, then **New task**.
2. Send: `Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.` Check the declared input and operation.
3. In the same chat, enter **Orders CSV**, then **New task**. The previous operation disappears and Execute stays disabled until a new saved plan exists.
4. Send: `Inspect sample_orders.csv. Return row count and column names. No writes.` Check the CSV input and operation.
5. Select Vector inspection, then Orders CSV. Each stored plan opens without regeneration.
6. Click **New chat**, select Vector inspection, and expand **Task history across chats**. Source-linked excerpts remain available. Send a clarification within this task.
7. Refresh: the active task and saved plan should recover without execution. History OFF excludes previous task messages from future model requests.
8. Separately, authorize a temporary-fixture write workflow, switch away/back, and check that the workspace requires authorization again. Selection must create no output. Do not use live services for this check.

## Automated checks

`make test` covers task isolation, shared history/history-off, stale revisions, legacy adoption, explicit binding, atomic rollback, storage safety and CLI/HTTP parity. `make interface-validate` checks frontend types/build.

`corepack pnpm@10.17.1 --dir interface browser:test:26-tasks` uses private browser storage and a temporary backend/data root. Only model replies are deterministic fixtures; persistence, policy, saved plans and authorization use actual services. Live-model response quality/time remains separate operator acceptance. No live GIS services are used.

Validation: `make test` passed **1,526 tests**; `make interface-validate` passed. The five-group task browser journey passed with actual task persistence, authorization and real pandas execution/validation on temporary fixtures. Only model replies were substituted. No page errors or live-service calls occurred.

The existing six-group checkpoint 24 browser regression also passed (typed planning, graph edits, exact authorization, real pandas execution, bounded outcomes and restart/history recovery). Workspace operations are disabled while a task transition is pending.
