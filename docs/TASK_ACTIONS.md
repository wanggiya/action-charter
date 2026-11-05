# Shared task actions

P0-4, [issue #61](https://github.com/wanggiya/action-charter/issues/61).
This consolidates existing behavior; it adds no processing operation, agent or permission.

```text
Frontend / terminal chat -- HTTP -- interface_api.server
CLI commands ------------------------------+
Existing MCP tools ------------------------+
                                           |
                              task_actions (shared implementations)
                                conversation + planner_submission
                                artifacts + workflow review/authorization
                                workflow_runs + exact execution
                                recorded results + assessment
                                           |
                              existing registry / policy / runners
                                           |
                              workspace records + durable evidence
```

## Entry points and ownership

| Responsibility | Shared implementation | Existing callers |
|---|---|---|
| Chat turns, task context and method controls | `task_actions.conversation`, `planning_tasks`, `chat_history`, `method_memory`, `method_helper` | HTTP and planning/memory CLI commands |
| Inspection-on-send submission and receipt | `task_actions.planner_submission`, `inspection_planning`, `inspection_policy` | HTTP; terminal chat through the same HTTP boundary |
| Saved plan, plan/recipe decisions and compilation | `task_actions.artifacts`, `contracts` | HTTP compatibility exports and shared workflow actions |
| Typed edit, current workflow review, authorization and execution | `task_actions.workflow` | HTTP and durable-run worker |
| Durable start/list/read/cancel/recovery proposal | `task_actions.workflow_runs` | HTTP, `workflow-runs` CLI; terminal chat through HTTP |
| Exact approved dispatch and evidence | `task_actions.execution`, `approved_recipe`, `approved_workflow` | Workflow actions and existing approved-execution MCP tools |
| Deterministic operation tool actions | `task_actions.data_tools` | Existing MCP wrappers and fixed spatial orchestrator; same allowlist |
| Recorded result views and reports | `task_actions.result_preview`, `result_exploration`, `spatial_views`, `run_assessment`, `execution_assistance` | HTTP/CLI/chat; existing MCP `workflow_report` reads the same run |
| Completed-source Snakemake workflow export | `task_actions.snakemake_workflow` | Existing workflow actions |

Request classes, action names, routes, CLI options, MCP tool names, response fields,
canonical artifact bytes and digest algorithms retain their previous contracts.
The historical `Interface…` class/function names remain available where compatibility
requires them. `TaskActionError` and the historical `InterfaceApiError` are the same
exception type.

The old service modules under `interface_api` and operation/approved-execution modules
under `mcp_server` are compatibility aliases to the actual shared modules. They do not copy
implementations or create separate locks, active-attempt sets or context variables.
Production callers import their shared owners directly. Public interface package
exports resolve moved actions without loading the HTTP server.

## Boundaries that remain enforced

- Model, transcript, recipe and data text never grant authority.
- Read-only supported inspection still executes without a fabricated write approval.
- Writes still require enabled session policy and current exact decisions. Durable
  start rejects combined approval; its worker independently rechecks the review and
  recorded decisions. Existing synchronous compatibility behavior is unchanged.
- The registry, typed arguments, source/target paths, immutable hashes, expiration,
  session binding and validation still control dispatch.
- Cancellation remains cooperative at operation boundaries. Recovery prepares a new
  validated proposal; it does not replay writes or transfer old authority.
- Reopening history, outcomes or MCP reports does not dispatch operations.

This is a backend consolidation, with no navigation or visual redesign. The terminal
continues to use the active API for chat and interactive work, preserving its live
session policy. The local `workflow-runs` CLI also uses the shared implementation.
MCP's existing narrower tool surface is preserved; this work does not add a generic
MCP start/cancel/authorize endpoint.

## Limits and remaining consolidation

Legacy Advanced/assurance/release and some inventory functions still live in
`interface_api.server`; splitting HTTP routers is separate work. Shared configuration
still uses the historical `mcp_server.settings` module. P0-5 [repository contracts](STORAGE_REPOSITORIES.md)
now wrap operational metadata, durable-run storage and saved-plan access while retaining
their SQLite/file formats. This task does not complete
the whole-project import-layer restructuring, prove local-model quality, or prove
live database behavior.

## Verification

`tests/test_task_actions.py` checks module/exception ownership, absence of reverse
HTTP/CLI/MCP-tool imports, and a fresh interpreter loading the actions without the HTTP
server. Temporary legacy-root and relocated-root journeys compare identical review
digests, execute once through CLI, reopen the same run through shared actions and the
terminal HTTP client, and compare HTTP/MCP reports. Disabled writes cannot create
approval or output files. These checks make no model or database calls.

The existing workflow, approval, session, cancellation/recovery, saved-chat, inspection,
Snakemake and browser/API/CLI/PTY suites provide the broader compatibility checks.
Final verification: **2,447 tests passed**, 13 existing spatial warnings, **688.52 s**.
Frontend validation and relocated fixture browser/API/CLI/PTY passed with zero page
errors. The new ownership/import/parity checks add 28 cases. An initial full run stopped
at an intent fixture still patching the old server registry; the three such patches
were moved to the shared artifact owner, with assertions unchanged, before the final
passing full run. Logs and remaining owner acceptance are recorded in CURRENT_STATUS
and WORK_RESUME. No live model/database check or real-record cutover was performed.

For a manual smoke check, restart the existing launcher with your usual options;
there is no new setting for this refactor. In a new Planner chat, send
`Run a new read-only inspection of sample_orders.csv.` If Inspection on send is ON,
wait for its recorded outcome; otherwise click Execute once. Check the row count and
columns, refresh and reopen the chat/run, and confirm that the same outcome remains
without another execution. Optionally open `./actioncharter`, use `/chats` and
`/open CHAT_ID`, then `/history` and `/run RUN_ID` to inspect that same record.
Existing write tests still use the normal enable → exact Authorize → Execute flow;
use disposable local output targets rather than live databases for this smoke check.
