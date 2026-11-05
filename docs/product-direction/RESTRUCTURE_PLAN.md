# Code restructure plan — exact steps

Recorded 2026-11-02. **Draft for owner review — not approved, not implemented.**

> **Status re-measured 2026-11-05** (after P0-2…P0-7, uncommitted at that time):
> core packages no longer import `interface_api` (R4/R5 effectively done via
> `task_actions/`); `server.py` 3,724 → 2,460 lines (R8 partly); `App.tsx` 48 lines (R10
> done); PostGIS lifecycle merged (R9 done). **Not done:** R1 (the existing
> `test_import_boundaries.py` checks clean imports, not the layer rule), R2 (files
> importing `mcp_server.settings` grew 34 → 37), R6, R7 (`cli.py` 7,787 lines), R11.
> New step **R12** added below.
Based on a scan of `src/geoagent_harness` on branch `docs/working-method` (with
uncommitted P0-2 work present). Line counts and import counts are from that scan;
re-check before each step.

This turns the target structure in [AUTONOMOUS_PLATFORM_DESIGN.md](AUTONOMOUS_PLATFORM_DESIGN.md#target-code-structure)
into ordered, checkable steps. Each step = one branch + one PR, following
[WORKING_METHOD.md](WORKING_METHOD.md).

## 1. Problem found in the current code

The main problem is not folder names. It is that **core code depends on the transport
layers** (HTTP API, MCP server). Moving folders first would just move this tangle.

| Inverted dependency | Evidence (2026-11-02 scan) | Effect |
|---|---|---|
| Core imports `mcp_server.settings` | 34 files outside `mcp_server/` (postgis, recipes, skills, geoserver, orchestrator, capabilities, operations, …) | Database/file settings live inside one transport; nothing can run without it |
| Core imports `interface_api` | 23 files outside `interface_api/` and `cli.py` (tabular, planner, model, discovery, recipe_catalog, orchestrator, capabilities, operations, intent) | The HTTP layer is effectively the core; CLI/MCP reach through it |
| Storage lives in `interface_api.planning_tasks.database` | 9 files use it (model catalog/telemetry, capabilities, tabular, orchestrator, …) | No storage layer to swap SQLite ↔ PostgreSQL |
| Bounded data reads live in `interface_api.inspection_policy.bounded_read` | 4 files outside it (tabular, discovery) | Safe data access is tied to the API package |
| Core raises `InterfaceApiError` | planner, tabular, discovery | Errors carry HTTP meaning inside core logic |
| `orchestrator.workflow` imports `mcp_server.tools` | 1 file | Workflow execution goes through MCP tool code |
| Very large files | `cli.py` 7,778 lines; `interface_api/server.py` 3,724; `interface/src/App.tsx` 2,683; `builder/` 10,064 | Hard to change safely |

## 2. Target layers and the dependency rule

Package name stays `geoagent_harness` until the identity decision is made (see
[WORKING_METHOD.md open decisions](WORKING_METHOD.md#open-decisions-for-the-owner)).
**Rule: a layer may import only layers below it.**

```
L6 apps/          interface_api (HTTP), cli, chat, mcp_server, mcp_client      ← thin adapters
L5 services/      shared task actions: conversation turn, plan/authorize/execute,
                  submission, run history, assessment                           ← one code path
L4 agents/        planner, critic, executor, builder, intent, context, orchestrator,
                  method_memory, agent_manifest; efficiency (new)
L3 capabilities/  operations, capabilities, skill_registry, skill_definitions,
                  skill_scaffolding, recipes, recipe_catalog, recipe_proposals
L2 data/          tabular, discovery, data cards (new), postgres, postgis, geoserver,
                  skills, skill_adapters, reporting, snakemake_export
   workspaces/    sandbox, run workspace (new)
L1 core/          policy (write_policy, approvals), ledger (trace, operational_history,
                  workflow_state, releases, task_history), verification (verifier)
   platform/      settings, storage, model_gateway (model), workspace paths
L0 contracts/     schemas, schema_registry, spatial_contracts, failures, redaction
```

## 3. Current package → target location

| Current | Lines | Target | Notes |
|---|---|---|---|
| `schemas.py`, `schema_registry/`, `spatial_contracts/` | 1.8k | `contracts/` | No internal deps; move first |
| `failures.py`, `redaction.py` | 0.3k | `contracts/` | |
| `mcp_server/settings.py` (settings part) | — | `platform/settings/` | Step R2 |
| `interface_api/planning_tasks.database` | — | `platform/storage/` | Step R3; joins P0-2 `workspace.py` |
| `workspace.py` (P0-2, in progress) | 0.1k | `platform/workspace.py` | |
| `model/` | 0.8k | `platform/model_gateway/` | Remove its `interface_api` import (R3) |
| `write_policy.py`, `approvals/` | 0.8k | `core/policy/` | |
| `trace.py`, `operational_history/`, `workflow_state/`, `releases/`, `task_history/` | 4.8k | `core/ledger/` | |
| `verifier/` | 0.6k | `core/verification/` | Remove `mcp_server` import (R2) |
| `tabular/`, `reporting.py` | 3.7k | `data/tabular/` | Remove `interface_api` imports (R3–R5) |
| `discovery/` | 0.7k | `data/discovery/` → seed of `data/cards/` | |
| `postgres/`, `postgis/` | 3.6k | `data/databases/` | `postgis` lifecycle merge = P0-3 |
| `geoserver/`, `skills/`, `skill_adapters/` | 3.6k | `data/spatial/` | |
| `snakemake_export/` | 1.7k | `data/export/` | |
| `sandbox/`, `interface_api/inspection_worker.py` | 0.2k+ | `workspaces/sandbox/` | |
| `operations/`, `capabilities/`, `skill_registry/` | 1.5k | `capabilities/registry/` | |
| `skill_definitions/`, `skill_scaffolding/` | 5.0k | `capabilities/skills/` | |
| `recipes/`, `recipe_catalog/`, `recipe_proposals/` | 8.7k | `capabilities/recipes/` | |
| `planner/`, `critic/`, `executor/`, `intent/` | 5.2k | `agents/roles/…` | Role code; manifests stay in repo `agents/*/manifest.yaml` |
| `orchestrator/` (`task_agents.py` = single/three modes) | 0.6k | `agents/runtime/` | Remove `interface_api`, `mcp_server.tools` imports (R4–R5) |
| `context_pack/`, `context_retrieval/`, `interface_api/method_memory*.py` | 0.7k+ | `agents/memory/` | |
| `agent_manifest.py` | 0.1k | `agents/runtime/` | |
| `builder/` | 10.1k | `evolution/builder/` | Large; move as-is, split later |
| `interface_api/` non-HTTP logic (conversation, workflow, workflow_runs, planner_submission, run_assessment, inspection_planning/policy, …) | ~6k | `services/` | Step R5 = P0-4 |
| `interface_api/server.py` | 3.7k | `apps/http/` split into routers | Step R8 |
| `cli.py` | 7.8k | `apps/cli/` split by command group | Step R7 |
| `chat/` | 0.7k | `apps/chat/` | |
| `mcp_server/` (minus settings) | 1.6k | `apps/mcp/` | |
| `mcp_client/` | 0.7k | `interop/` | Later: external-agent connectors |
| `interface_projection/`, `pilot_demo/`, `testing/` | 0.8k | review: keep, move to `apps/`/`tests/`, or delete if unused | Decide in R6 |
| `interface/` (React) | 7.4k TS | `interface/` (path unchanged for now) | `App.tsx` split = P0-6 |

## 4. Ordered steps

Rules for every step:
- **Compatibility shims:** when a module moves, leave the old module re-exporting the new
  one (`from geoagent_harness.platform.settings import *`) so tests, scripts and any
  stored references keep working. Remove shims only in a final cleanup step.
- **No behaviour change.** Stored digests, evidence formats, API routes, CLI commands and
  MCP tool names must not change. If a test needs a changed expected value, stop and ask.
- Done check for each step: `make test` passes **and** the layer check (R1) shows the
  violation count did not increase (and decreased where the step targets it).

| Step | Exactly what to do | Done when |
|---|---|---|
| **R1 Layer check** | Add `tests/test_import_layers.py` (or `import-linter` in `pyproject.toml`) encoding the rule in section 2. Record today's violations as an allow-list baseline. The test fails on any **new** violation. | Test runs in `make test`; baseline file lists current violations |
| **R2 Settings out of MCP** | Create `platform/settings/` with `MCPSettings` (rename later), `load_settings`, `validate_identifier`, `parse_flag` moved from `mcp_server/settings.py`. Point the 34 importing files to it. Leave a shim in `mcp_server/settings.py`. | No file outside `apps/`/`mcp_server` imports `mcp_server.settings`; baseline shrinks |
| **R3 Storage layer** | Create `platform/storage/` with a repository interface and the SQLite implementation taken from `interface_api/planning_tasks.database`, `_get`, `_put`, `_identity`. Use P0-2's `workspace.py` paths. Update the 9 users. | `model/`, `capabilities/`, `tabular/`, `orchestrator/` no longer import `interface_api.planning_tasks` |
| **R4 Data access + errors** | Move `bounded_read`, `probe_action`, `source_skill` from `interface_api/inspection_policy.py` to `workspaces/sandbox/` (or `data/access/`). Add a core error type (e.g. `contracts.errors.HarnessError`); make `InterfaceApiError` subclass or wrap it; core code raises the core type, HTTP layer maps it to status codes. | `tabular/`, `discovery/`, `planner/` do not import `interface_api` for reads/errors |
| **R5 Shared task actions (P0-4)** | Create `services/`. Move from `interface_api/`: conversation turn handling, `prepare/authorize/execute_workflow`, `validate_edit`, `save_interface_reviewed_plan`, `submission_action`, `run_action`, `OutcomeAssessment`. HTTP, CLI, chat and MCP all call `services/`. Move `orchestrator/workflow.py`'s use of `mcp_server.tools` to the service it wraps. | No package below L6 imports `interface_api` or `mcp_server`; baseline for these = 0 |
| **R6 Move packages to layers** | Move packages per section 3, **one layer per PR**, bottom up: `contracts/` → `platform/` + `core/` → `data/` + `workspaces/` → `capabilities/` → `agents/` + `evolution/`. Shims at old paths. Decide `interface_projection`, `pilot_demo`, `testing`. | Each PR: tests pass, layer check clean for moved layer |
| **R7 Split `cli.py`** | Move to `apps/cli/` with one module per command group (planning, workflow, recipes, builder, postgres, discovery, method memory, …); `cli.py` keeps only the entry point. | No CLI module over ~1,000 lines; CLI parity tests pass |
| **R8 Split `server.py`** | Move to `apps/http/` with one router per area (chat, workflow, runs, settings, diagnostics, datasets, …); handlers only parse requests and call `services/`. | No handler contains business logic; interface validation passes |
| **R9 PostGIS lifecycle (P0-3)** | Replace `postgis/promotion/{plan,approval,execution,verification}` + `rollback/*` with one generic plan → approve → execute → verify → rollback lifecycle in `core/` used by `data/databases/postgis`. | Same evidence formats; promotion/rollback tests unchanged and passing |
| **R10 Frontend split (P0-6)** | Split `App.tsx` into workspace modules (Planner, Graph, Results, Settings) with a state store; no visual change. | Browser checks pass; `App.tsx` under ~300 lines |
| **R12 Server seams** | Every task action takes an explicit **actor** (local: `owner`; later user / service / registered automation) and a **run context** (run id, trigger, budget, **idempotency key**). Add interfaces with local implementations: **policy decision** (allow/deny/escalate + reason), **credential broker** (returns nothing locally), **job queue** (in-process), **clock** (injectable). Record actor and run id in evidence. See [SERVER_AUTONOMY_DESIGN.md](SERVER_AUTONOMY_DESIGN.md). | Tests show actor/run id recorded for every action; the same event twice runs once; no behaviour change for local use |
| **R11 Remove shims** | Update remaining imports in tests/scripts; delete shim modules. | `make test` passes with no shims |

Emphasis (2026-11-05):
- **R1 first and real:** a layer-rule test with a recorded baseline; without it later steps re-tangle silently.
- **R2 is one platform configuration**, not only "settings out of MCP": storage layout (`GEOAGENT_*_ROOT`), database, model providers; the server profile is selected through it (pairs with P0-2b).
- **R5 completion:** every transport, including the 7,787-line `cli.py`, calls `task_actions/`.
- **R6:** one layer per PR, shims at old paths, no digest or evidence-format changes.
- **R12** is cheap now and expensive later; do it before Phase 1.

Dependencies: R1 first. R12 after R5 (can run with R6). R2, R3, R4 can run in parallel after R1 (different files). R5
needs R2–R4. R6 needs R5. R7, R8 need R5. R9 can start after R2. R10 is independent
(frontend only) and can run any time. R11 last.

## 5. Where the new features go (after R5/R6)

Built only after the structure above exists, so they land in the right layer:

| New feature | Location | Builds on |
|---|---|---|
| Data Card | `data/cards/` | `discovery/`, `tabular/dataset_profile.py`, comprehensive inspection |
| Run workspace (process / outcome areas, snapshots, promotion by verification, read-only sharing between agents) | `workspaces/run_workspace/` | `sandbox/`, [executor sandbox plan](../EXECUTOR_SANDBOX_WORKSPACE_PLAN.md), `core/verification/`, `core/ledger/` |
| Efficiency (routing, recipe reuse, budgets, metrics) | `agents/efficiency/` | `model/telemetry.py`, `planner/effort_budget.py`, request diagnostics |
| Single / multi-agent modes | `agents/runtime/` | `orchestrator/task_agents.py` ([TASK_AGENT_MODES.md](../TASK_AGENT_MODES.md)) |
| External agents (Claude Code, Codex, …) | `interop/` + `apps/mcp/` | `mcp_client/`, `mcp_server/` |
| Server profile (queue, scheduler, PostgreSQL, login) | `platform/` + `apps/server/` | `platform/storage/` (R3) |

## 6. Open points for the owner

- Approve, change or reorder steps R1–R11.
- Package rename (`geoagent_harness` → `actioncharter`): when, or not at all.
- Whether to also move the Python package root (`src/geoagent_harness/…`) or only reorganise inside it (this plan assumes inside).
