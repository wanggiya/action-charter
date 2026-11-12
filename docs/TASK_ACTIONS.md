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
| Saved plan, plan/recipe decisions and compilation | `planner.service.save_reviewed_plan`, `contracts.actions`, `task_actions.artifacts` decision/adaptor services | HTTP compatibility exports and shared workflow actions |
| Typed edit, current workflow review, authorization and execution | Non-executing validation/edit in `planner.recipe_definition`; review/authority/dispatch in `task_actions.workflow` | HTTP and durable-run worker |
| Durable start/list/read/cancel/recovery proposal | `task_actions.workflow_runs` | HTTP, `workflow-runs` CLI; terminal chat through HTTP |
| Exact approved dispatch and evidence | `task_actions.execution`, `approved_recipe`, `approved_workflow` | Workflow actions and existing approved-execution MCP tools |
| Deterministic operation tool actions | `postgis.fixed_operations` for the four fixed spatial actions, re-exported by `task_actions.data_tools`; other tool actions retain that owner | Existing MCP wrappers and fixed spatial orchestrator; same allowlist |
| Recorded result views and reports | `task_actions.result_preview`, `result_exploration`, `spatial_views`, `run_assessment`, `execution_assistance` | HTTP/CLI/chat; existing MCP `workflow_report` reads the same run |
| Completed-source Snakemake workflow export | `task_actions.snakemake_workflow` | Existing workflow actions |
| Legacy CLI service composition | `task_actions.command_actions` | Main CLI uses explicit lazy service exports; options, outputs and core functions unchanged |

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
`interface_api.server`; splitting HTTP routers is separate work. R2's
[platform configuration](PLATFORM_CONFIGURATION.md) now owns shared settings; historical
MCP modules are compatibility aliases. P0-5 [repository contracts](STORAGE_REPOSITORIES.md)
now wrap operational metadata, durable-run storage and saved-plan access while retaining
their SQLite/file formats. This task does not complete
the whole-project import-layer restructuring, prove local-model quality, or prove
live database behavior.

## R5 shared composition and evidence boundaries

R5, [issue #70](https://github.com/wanggiya/action-charter/issues/70), 2026-11-06.
This completes the ten directly assigned R5 dependencies without new upward imports
or relaxed classifications: **53 -> 43 pairs / 55 -> 43 occurrences**. The graph has
443 modules, 37 visible aliases and the same reviewed dynamic import. Existing R6
cross-layer ownership debt remains explicit; strict mode still rejects it.

- Shared non-executing plan/recipe validation, Snakemake source-plan checks and edit
  projection now use the existing `planner.recipe_definition` owner. Workflow actions
  re-export the same functions. Approval, session policy, execution, leases and recovery
  retain their action owners. Neutral edit/export schemas retain their field rules.
- `planner.service.save_reviewed_plan` owns immutable proposal persistence. The action
  adapter preserves its public signature and registry-loader hook; the intent API
  composes that adapter explicitly. Provenance, selected skills, exact digest, workspace
  paths, exclusive creation and same-result reuse checks remain. Saving never approves.
- Role coordination receives a trusted `ConversationAccess` with the existing lock,
  conversation reader and configured-client factory. No callback comes from API/model
  data. The same active ContextVar, sequential budgets, captured mode, revision guards
  and failed-attempt handling remain; this does not add automatic mode selection.
- Method retrieval uses `storage.completed_runs` for a bounded, owned, completed-only
  snapshot. It no longer invokes a run-action reader that may repair stale execution,
  indexing or Critic state. Retrieval skips ineligible records and retains chat/hash/
  contract/retention checks. Run actions retain interruption recovery and assessment.
- `storage.chat_snapshots` holds the unchanged immutable archive encoder. Dataset
  views and chat actions use it inside the existing transaction, preserving rollback,
  deduplication, scope, encoding and limits. Historical continuation remains an action.
- Neutral outcome/method schemas and `recipes.observations` share the same bounded
  evidence projection/hash between Critic review and method indexing. The projection
  makes no model call or authority decision. Shared prompt bounds preserve the chat's
  configurable private limit hook. Workspace-path error adapters have a shared platform
  owner and an exact compatibility alias.

### CLI delegation

The main CLI's **213 service imports** now use **146 explicit lazy exports** in
`task_actions.command_actions`. Each export returns the original current backend
function, rather than implementing another wrapper or caching a stale binding. Only
the selected service module loads; optional runtimes remain optional. Function/error
behavior, command arguments, exit codes and output formatting remain. An AST comparison
of the entire CLI confirms that only import statements changed.

This catalog is fixed first-party application composition, not an operation package,
agent tool registry or user-supplied callable lookup. Unknown names reject. Existing
MCP tool names/allowlist and planner operation selection are unchanged. Transport,
display/demo adapters and type/error imports retain their appropriate owners. Equivalent
workflow actions share their existing services; broader legacy CLI command contracts
remain broader than the frontend. This is not a claim of identical product surfaces.

The catalog is 595 lines. The main CLI is still 7,466 lines; splitting command groups
is R7, and HTTP router decomposition is R8. Remaining package/role ownership changes
are R6. P0-2b identity/owner cutover, specialized P0-5b storage contracts and R12 server
seams are separate; R5 does not complete Phase 0.

### R5 verification

- Existing recipe/retrieval/mode/view/intent/fixed-operation cases: **75 passed (17.81 s)**.
- Initial new boundary + layer cases: **40 passed (2.58 s)**; there are now 25 new R5
  boundary cases including the later CLI catalog checks.
- Shared API/CLI/MCP, current workflow, Snakemake and authorization cases:
  **81 passed (21.42 s)**.
- All CLI command groups plus shared parity/boundaries: **178 passed (12.89 s)**.
- Final CLI/intent/parity/boundaries after including the two legacy lazy recipe exports:
  **198 passed (13.13 s)**; final corrected intent/boundary/layer cases:
  **69 passed (4.43 s)**. The missing-registry guard is explicitly tested.
- Frontend validation passed: 4.66 s build, existing bundle-size warning.

The relocated fixture browser/API/CLI/PTY journey passed with zero page errors,
including saved outcomes/history, statistics, JSON/XLSX/PDF and one authorized temporary
write. The final journey after all source changes also passed with zero page errors.
Final full `make test`: **2,607 passed**, 13 existing spatial warnings, **668.71 s (11:08)**.
Normal layer check, 466 local links (160 Markdown fragments), roadmap size and whitespace
checks pass; strict mode correctly rejects remaining debt. Earlier collection caught an approval
import cycle and a missing `Path` import; corrected before final validation. Sandbox
HTTP fixture permission failures were rerun with local socket permission. An initial full run stopped after 905 passes on an intent fixture patching the former
registry owner. Three such fixture patch targets now use the shared registry; assertions
and policy checks remain. The final full run uses frozen source after that correction
and the final lazy recipe-export wiring. Fixtures do not establish real-local-model or live
database quality. The owner explicitly deferred the manual write check; do not mark
that accepted. No live services, secret edits or real-record migration occurred.

## Original P0-4 verification

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
`/open NUMBER`, then `/history` and `/view NUMBER` to inspect that same record.
Existing write tests still use the normal enable → exact Authorize → Execute flow;
use disposable local output targets rather than live databases for this smoke check.
