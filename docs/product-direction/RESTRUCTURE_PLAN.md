# Code restructure plan — exact steps

Recorded 2026-11-02. **R1–R5 complete; R6 ownership and native package moves implemented
2026-11-07, required automated gates passed; owner manual acceptance pending. R7 CLI extraction and automated gates are complete. R8 HTTP extraction and
automated gates are complete. R9/R10 reuse delivered P0-3/P0-6. P0-5b local ledger contracts
and automated gates are complete; R12 implementation and required automated gates are complete; opt-in local stable identity and required automated gates are complete; R11 retirement and required automated gates are complete; owner cutover remains.** Later explicit owner instructions
govern individual slices. Original scan/step descriptions are retained below.

> **Earlier snapshot, before R1, 2026-11-05** (after P0-2…P0-7, uncommitted at that time;
> superseded by the current P0/R gap inventory below):
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

## Current P0/R gap inventory — 2026-11-05

The [R1 checker and explicit baseline](../IMPORT_LAYERS.md) initially measured 412
modules, 109 upward dependencies / 128 occurrences, one reviewed non-literal importer
and 23 aliases. [R2 configuration](../PLATFORM_CONFIGURATION.md) reduced the graph to
75 dependencies / 87 occurrences; [R3 storage/contracts](../STORAGE_REPOSITORIES.md#r3-transaction-and-plan-contracts)
reduced it to 65 / 68. [R4 data access/contracts](../DATA_ACCESS_BOUNDARY.md), updated
2026-11-06, reduced it to 53 / 55. [R5 task composition](../TASK_ACTIONS.md#r5-shared-composition-and-evidence-boundaries)
reduced it to 43 / 43. [R6a shared primitives](../SHARED_EXECUTION_PRIMITIVES.md)
reduced it to 35 / 35. The [R6b evidence/storage slice](../SHARED_CRITIC_EVIDENCE.md)
reduced it to 33 / 33. The [R6b2 registry/metadata slice](../TRUSTED_REGISTRY_BOUNDARY.md)
reduced it to **26 dependencies / 26 occurrences**, with 456 modules and 45
visible aliases. Its focused checks, confirmed full suite (2,673 passed, 716.81 s), frontend and isolated fixture journey pass. [R6 completion](../R6_COMPLETION_AND_ACCEPTANCE.md),
issue #74, now implements the remaining responsibility splits and package moves:
**826 modules / 3,037 import occurrences, zero upward and dynamic-import debt**.
391 audited compatibility adapters retain historical paths; 435 modules are native
owners. Strict mode passes. Final full suite: **2,688 passed (728.54 s; 13 existing spatial warnings)**; frontend and isolated
fixture browser/API/CLI/terminal journey pass. No new upward dependency is accepted. Native callers no longer
import transport-owned settings/tool-result schemas, task-action storage/read/error helpers
or higher-owned shared request/format/context-redaction definitions.
All ten direct R5 task-action dependencies, eight R6a primitive/type dependencies,
two R6b evidence/storage and seven R6b2 registry/metadata dependencies were removed
before the final ownership pass. The remaining role/domain/client dependencies are now
removed: pure policy/ledger and contracts stay below roles, calculations stay in data,
and the fixed internal MCP client stays in platform infrastructure.
Historical generated candidate strings retain their compatibility imports.
[WORKING_METHOD](WORKING_METHOD.md) owns phase/task status.

| Work | Delivered overlap | Remaining gate / next responsibility |
|---|---|---|
| R1 | Static checker, policy, exact debt records and negative fixtures complete; R6 adds source-bound compatibility audits | Initial full suite: 2,501 passed (722.32 s); strict mode now passes the clean R6 graph. No runtime authority from a layer check. |
| R2 + P0-2b configuration | Platform-owned snapshot/layout with lazy tool/model/client/replay views and five compatibility aliases implemented | Complete: 2,529 full tests (678.41 s), 87 focused + 116 boundary checks, frontend and two fixture browser journeys pass. Personal only; identity/cutover remains below |
| P0-2b identity/cutover | P0-2 resolver, offline copy/verify/cutover/rollback delivered | [#79 local identity](../PROJECT_IDENTITY.md) automatically verified: 2,796 tests (816.47 s), frontend/strict and legacy/stable-ID fixture browser/API/CLI/terminal journeys pass; legacy compatibility, verified rename/state cutover, copied-object rejection. Owner real cutover pending; cross-filesystem/container provisioning future work |
| R3 + P0-5/P0-5b | Shared metadata transaction/identity/bounded JSON helpers and neutral plan/error contracts implemented; five lower-layer clients detached; saved formats/domain validation retained | Complete, [issue #68](https://github.com/wanggiya/action-charter/issues/68): 2,555 tests (708.70 s), 77 focused + 76 existing boundary checks, frontend and isolated fixture browser/API/CLI/PTY pass. Owner manual validation deferred. Specialized ledger/concurrency contracts remain P0-5b |
| R4 | Shared bounded reader/worker/snapshot/rendering, neutral action/format/redaction contracts and root/projection helpers implemented; all 12 direct R4 dependencies removed | Complete, [issue #69](https://github.com/wanggiya/action-charter/issues/69): 2,581 tests (735.04 s), 73 focused + 64 integration cases, frontend and relocated fixture browser/API/CLI/PTY pass. R4 left three mixed observer/role-type dependencies for R6; R6a below removes two |
| R5 + P0-4 | All ten direct R5 dependencies removed; shared validation/save/evidence and fixed spatial functions, explicit coordinator access, atomic archive helpers and lazy CLI service catalog implemented | Complete, [issue #70](https://github.com/wanggiya/action-charter/issues/70): 75 existing, 40 initial boundary/layer, 81 parity/authorization and 178 CLI/parity/boundary cases passed; frontend and final relocated fixture browser/API/CLI/PTY pass; final full suite 2,607 passed (668.71 s), final CLI/intent 198 and corrected intent/boundary/layer 69 passed. Owner manual write check pending |
| R6 | Shared contracts/core/data/platform/role owners and physical moves implemented; old paths retained as audited adapters | [#74](https://github.com/wanggiya/action-charter/issues/74): strict layer gate passes with zero upward/dynamic debt; 94 schema exports unchanged. Automated complete: 2,688 passed (728.54 s; 13 existing spatial warnings); [post-R6 manual acceptance](../R6_COMPLETION_AND_ACCEPTANCE.md) tracked separately |
| R7 | R5 routes 213 service imports through 146 lazy shared exports; R6 preserves late-bound lookup at native owners | Implemented, [#75](https://github.com/wanggiya/action-charter/issues/75): native main 142 lines, registry 290, largest group 783; 150 commands/165 help/110 function ASTs unchanged; 47 focused + 227 existing checks and frontend pass; final make test 2,693 passed (730.42 s; 13 existing spatial warnings); isolated fixture browser/API/CLI/terminal passes. [Guide](../CLI_COMMAND_STRUCTURE.md) |
| R8 | HTTP composition/transport/dispatch/errors and ten routers extracted; 24 coordinators and 16 schemas have shared owners | Implemented, [#76](https://github.com/wanggiya/action-charter/issues/76): 104 response contracts unchanged, 146 API + 76 boundary checks and frontend/strict gate pass; final make test 2,709 passed (713.38 s; 13 existing spatial warnings); isolated fixture browser/API/CLI/terminal passes. [Guide](../HTTP_ROUTER_STRUCTURE.md) |
| R9 + P0-3 | Shared PostGIS lifecycle implemented and verified | [Criteria reconciled](../LEDGER_CONTRACTS.md#r9-and-r10-reconciliation): delivered P0-3; DB-dependent driver stays in data, pure policy/ledger below it. No rebuild |
| R10 + P0-6 | App is 48-line composition over workspaces/store; browser evidence recorded | [Criteria reconciled](../LEDGER_CONTRACTS.md#r9-and-r10-reconciliation): delivered P0-6; retain existing UI |
| R11 | [#80 retirement](../R11_COMPATIBILITY.md): 290 obsolete adapters removed, 117 supported public/schema/SDK boundaries retained; unchanged 496 native implementations | Automated gates complete: 2,808 tests (859.92 s), frontend/source checks and stable-ID fixture browser/API/CLI/terminal passed. Owner-approved public compatibility preserved; literal historical zero-shim claim not made. [Owner acceptance record](../R_SERIES_ACCEPTANCE.md#acceptance-record): startup/read-only/refresh recovery passed; history navigation and terminal continuity pending; manual writing optional. Real cutover separate |
| P0-5b | Local immutable/event/SQLite units wired; existing domain authority and layouts retained | [#77 contracts](../LEDGER_CONTRACTS.md): automated complete, 2,736 tests (750.12 s), frontend/strict gate and isolated fixture browser/API/CLI/terminal pass; owner manual acceptance deferred. Host-local leases only, no remote backend |
| R12 | Existing local execution/policy services; specialized storage now has explicit ports | [#78 completed](../EXECUTION_CONTEXT.md): 70 task boundaries and 27 MCP ingresses, durable event claims, pure query telemetry and local ports; 2,771 tests (793.66 s), frontend/strict gate and final isolated browser/API/CLI/terminal pass. Existing container permissions and tool schemas preserved. No standing server authority implemented |
| P0-7 | Active roadmap and complete indexed history delivered | Maintain links/status, rather than recreating the old checkpoint schedule |

Order: R1–R5 are complete, including P0-2b's configuration portion. R6 ownership/moves
and automated gates are complete; R7 CLI extraction now uses the native owners, with
final make test 2,693 passed (730.42 s; 13 existing spatial warnings); isolated fixture browser/API/CLI/terminal passes.
R8 HTTP extraction and automated gates are complete; R12 server work stays separate; R11 last. P0-2b real cutover is a
separate explicit owner action.
No whole-phase completion until tests, source-only-root acceptance and strict layer
checks pass. R1 does not implement the broader P0-2b/P0-5b/R12 requirements.

## R6 reviewable slices

One active bounded task at a time. These are parts of R6, not new checkpoints or a
GitHub issue for every import. Claim an issue when a slice starts; keep the rest as a
checklist here. Later scopes must be traced before implementation and may be narrowed
further if they are too large. Keep implemented, automatically verified, owner-manual
pending and owner-reviewed/merged states distinct. Open task issues are not a bug count.

| Order | Scope | Measurable acceptance | Status |
|---|---|---|---|
| R6a | Shared cancellation/progress, graph and self-contained evidence/handoff schemas | Eight traced pairs removed; one observer/exception identity; unchanged 12 public schemas, canonical payloads and validators; full/frontend/isolated journey pass | Done, issue #71; subsequent ownership/moves in #74 |
| R6b | Core policy/ledger contracts and evidence-building ownership | Core records obtain validated facts without importing role behavior; fresh registry/version, identity/hash, authority and append-only checks retained; declared dependency targets shrink | Earlier evidence #72 and registry #73 done; #74 implements remaining plan/table/PostgreSQL policy, recipe decisions and ledger owners; automated gates complete, owner manual acceptance pending |
| R6c | Data and adapter/registry boundaries | Data code consumes explicit contracts/ports rather than planner prompt or capability orchestration implementations; typed arguments, package/source bindings and effect gates remain; declared pairs removed | #74 implemented: typed calculation/statistics/source/table contracts, data execution/preflight/text runtime, role-owned analyst; automated gates complete, owner manual acceptance pending |
| R6d | Remaining capability/role/recipe/replay/interop composition | Coordination stays above reusable core/data; typed transport ports preserve exact approval, tool allowlists and runtime checks; remaining upward pairs eliminated | #74 implemented: acquisition/proposals/replay and mechanical binding ownership; recipe action at task layer; fixed internal MCP client at platform; strict graph clean; automated gates complete, owner manual acceptance pending |
| R6e | Physical package paths after responsibilities settle | Move one layer at a time, bottom up; native imports use owners, old references resolve through visible compatibility paths; full suite passes without new debt | #74 implemented: native layer paths and 391 audited compatibility adapters; main CLI/HTTP retained for R7/R8; automated gates complete, owner manual acceptance pending. Alias retirement remains R11 |

For every slice, record target dependencies before editing, run focused checks early,
then the required full suite and relevant frontend/journey checks on its final source.
Shrink only removed/reduced baseline entries; never relax classifications to make a
move pass. Record failures and remaining scope in WORK_RESUME and the living guide.
Source-only owner cutover, specialized storage/concurrency and server seams retain
their P0-2b/P0-5b/R12 gates and explicit authority. No live cutover is implied here.

## 1. Problem found in the current code

The following table is the original 2026-11-02 scan, not the current R1 baseline.

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
**Rule: cross-layer imports point downward; imports within the same layer are allowed.**
R1 checks this vertical rule, not same-layer cycles or semantic ownership.

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

Original planning map and scan sizes are retained below for traceability. The actual
R6 mapping is in [the ownership guide](../R6_COMPLETION_AND_ACCEPTANCE.md#implemented-responsibility-boundaries)
and `tests/architecture/r6_module_owners.json`. Three deliberate refinements: fixed
internal MCP networking belongs to platform rather than external interop; existing
interface projection/demo/testing stay as `apps/` support; method-memory task actions
retain coordination while role-private context moves to `agents/memory/`. Existing
package-level CLI adapters stay explicitly L6 and join the R7 command split.

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

- Review remaining R2–R12 steps against the current R1 baseline and later owner decisions; R1 itself is authorized.
- Package rename (`geoagent_harness` → `actioncharter`): when, or not at all.
- Whether to also move the Python package root (`src/geoagent_harness/…`) or only reorganise inside it (this plan assumes inside).
