# R6 ownership, layer moves and post-R6 validation

R6 completion task, [issue #74](https://github.com/wanggiya/action-charter/issues/74).
Updated 2026-11-07. R6 implementation and required automated gates are complete.
Owner manual acceptance/review and Git integration remain pending. Manual validation
is prepared below, after implementation as requested.

Counts in this guide are the R6 completion snapshot. Subsequent CLI ownership and
current layer counts are recorded in the [R7 guide](CLI_COMMAND_STRUCTURE.md).

## Implemented responsibility boundaries

```text
apps / existing CLI and HTTP adapters
                 |
            task_actions
                 |
       agents / evolution roles
                 |
     capabilities: registry, recipes, skills
                 |
       data / workspaces workers
                 |
     core policy, ledger, verification
                 |
       platform facilities / contracts
```

Contracts are layer 0. Core and platform are layer 1; data/workspaces layer 2;
capabilities layer 3; agents/evolution layer 4; shared task actions layer 5;
application adapters layer 6. Same-layer imports remain allowed; lower layers do not
import higher implementations. The diagram shows the general dependency direction,
not a requirement to pass every request through every layer.

| Native owner | Responsibility retained |
|---|---|
| `contracts/` | Existing workflow/registry/recipe/evidence/PostgreSQL/table/statistics types, finite calculation definitions and path-spelling rules |
| `core/policy/` | Shared plan/table/database/recipe checks, exact plan/recipe decisions and envelope validation |
| `core/ledger/` | Existing trace/history/release, recipe identities and record loading/storage |
| `core/verification/` | Existing independent verification |
| `platform/` | Existing configuration/workspace/storage/model gateway and fixed internal MCP networking |
| `data/` | Existing table calculations/profiles, spatial tools, databases, discovery and static export |
| `workspaces/sandbox/` | Existing fixed readers/workers and finite snapshots/rendering |
| `capabilities/` | Existing registry, recipe composition/dispatch and skill contracts |
| `agents/roles/`, `agents/runtime/`, `agents/memory/` | Existing model roles, acquisition, analytical reasoning, proposal/replay coordination and private context |
| `evolution/builder/` | Existing experimental Builder lifecycle; no new generated-code authority |
| `apps/` | Existing MCP/chat adapters and demonstration/test support |

Main `cli.py` and `interface_api` remain in place for R7/R8. The fixed internal MCP
client is platform infrastructure behind the existing injectable client protocols;
it is distinct from MCP server tools and future external-agent integrations.

Planner generation/correction stays in the role. Shared `core.policy.plan` retains all
workflow restrictions and invokes the existing pure table/PostgreSQL contract checks.
Data preflight/calculation execution stays with data code. Approval still reloads the
current trusted registry, checks exact scope and binds the existing write session.
Recipe history/release uses record contracts and core readers, not model interpretation.
Acquisition, recipe model generation, analytical dialogue and replay coordination have
role owners; runtime text transforms remain data operations.

No new operation, agent, UI feature, dependency, server authority or model-approver
implementation is introduced. P0-2b real cutover and P0-5b ledger/concurrency contracts
remain separate from file ownership. The owner's experimental model-approver design
is preserved as future, unimplemented work.

## Compatibility and the layer gate

Historical import and entrypoint strings remain supported. Leaf modules alias the
actual native modules, preserving classes, exceptions, locks and ContextVars. Package
roots retain public export facades; native callers use the new owners. Package resources
retain their bytes. Workers/terminal entrypoints retain their invocation behavior.

`tests/architecture/r6_module_owners.json` records 391 historical adapters, including
61 package roots, with explicit native owners and reviewed source hashes. Those files
are application compatibility adapters, not live core implementations relabelled to
hide a dependency. The checker separately verifies:

- Both adapter and owner exist; an adapter's source hash matches the reviewed record.
- Adapters contain no top-level business classes/functions; package export hooks remain.
- Native lower layers cannot import an adapter classified at layer 6.
- All native owners remain classified by their actual responsibility; no catch-all
  layer assignment or upward-dependency exemption is introduced.

The graph currently has **826 modules, 3,037 import occurrences, zero upward imports
and zero dynamic-import debt**. Native implementations account for 435 modules; the
temporary adapters account for the remainder and retain the R11 retirement gate.
The strict check passes. API lazy export lookup now uses fixed literal imports with
the same allowlist, fallback, cache and errors; HTTP router decomposition remains R8.

The pre-move sample of **94 schema exports** has identical JSON schemas. A checked-in
hash fixture prevents silent changes. A source audit found **1,918 of 1,921 original
top-level definitions unchanged apart from imports**. The three intentional changes
are literal API export routing and two source-root helpers needed after moving files.
Source Python bytes grew from 2,991,783 to 3,142,936 (about 151 KB), principally retained
compatibility exports. This does not add processing functions or duplicate engines.

The CLI's established late-bound service lookup is preserved at native package paths.
Fixture imports/mock targets follow implementation owners or retain original binding
sites; assertions and expected data/authority outcomes are not weakened. Synthetic
checker fixtures use a frozen declared topology so their original negative assertions
remain independent of the real project's compatibility adapters.

## Automated evidence and current status

- 94 schema-export comparisons pass; strict import gate passes.
- Initial focused core/approval/registry/import group: 66 passed (3.53 s).
- Existing boundary/ledger/executor regression group: 207 passed (10.12 s).
- New ownership + CLI binding groups: 48 passed (4.98 s), including 14 new ownership
  cases; all non-entrypoint legacy leaf aliases are checked in a bounded process.
- Isolated early fixture-binding corrections: 15 passed (3.01 s).
- Public-port/ownership group: 42 passed (6.36 s); recipe/parity/workspace/spatial
  group: 96 passed (24.68 s). All 35 failures from the diagnostic full run passed
  in replay (15.19 s), with all existing assertion ASTs unchanged.
- Shared-reader partial-result case passed (12.23 s).
- Frontend validation passed (4.28 s build; existing bundle-size warning).
- Initial and final frozen-source relocated browser/API/CLI/PTY journeys passed with
  zero page errors and one authorized temporary write per journey.
- Compose configuration validation passed without starting a container or service.
- Final documentation audit: 35 changed Markdown files, 526 local links and 169
  fragments pass; active roadmap is 15,675 bytes (below 64,000). Whitespace check passes.

The first full run stopped after 190 passes at a CLI mock targeting a re-export.
The broader diagnostic full run finished with 35 failures / 2,653 passes (678.16 s).
Failures were repaired by preserving original mock binding sites/public service ports,
pointing two reader mocks at the shared reader, and restoring the mixed recipe API
namespace at task-action level. A missing legacy API alias for that new task module
was added. The pure capability composition still imports no task/role behavior.
All 35 diagnostic failures now pass; final frozen-source `make test`: **2,688 passed (728.54 s; 13 existing spatial warnings)**.
The import sweep initially tried a `__main__` module, which intentionally starts MCP;
entrypoints are now excluded from import sweeps and exercised as bounded processes.
The first new tool-allowlist assertion was corrected to the existing approved-tool name.
No production guard was relaxed. The final full suite and frozen-source
browser/API/CLI/terminal journey both pass.

The wheel build backend is not installed in this development environment; no new
dependency was downloaded and no wheel/install/release acceptance is claimed here.
These automated checks use temporary data and fake models/adapters, not new real-local-
model or live-database acceptance. Manual write acceptance remains pending.

## Manual validation after R6

Owner decision 2026-11-08: defer these manual checks until the R series is complete.
Retain them for that combined acceptance pass; automated task checks remain required.

Use the existing launcher: `bash scripts/start_actioncharter.sh` with your usual
options. Restart it after implementation so the API loads the current Python files;
keep its terminal running. Open `http://127.0.0.1:5173` (API remains on 8765). Use new
chats and disposable outputs. No workspace relocation is needed for these checks.

| Check | Action | Expected result |
|---|---|---|
| Startup | Run `bash scripts/start_actioncharter.sh` with your usual options; open the existing frontend | Interface/API connect; previous chats remain available |
| Explicit read | Send `Run a new read-only inspection of sample_orders.csv` | Inspect-on-send follows its setting; otherwise click Execute once. Expect 6 rows and columns `order_id`, `region`, `amount`, `customer_id`, `unused`; no write approval required |
| Model planning | In a new chat ask: `Inspect sample_orders.csv, then select order_id, region and amount into data/output/r6_manual_orders.csv. Prepare the workflow; do not execute.` Use another fresh name if this output already exists | A typed inspection/selection proposal appears; actual column arguments and fresh output path are visible. This exercises the configured model, unlike the explicit metadata shortcut |
| Write gate | Review the proposed output, switch Allow writes ON, then Authorize and Execute | Exact decision required; fresh CSV has 6 rows / 3 selected columns. No launcher restart is needed just to enable writes. Installation/history/model text does not approve it |
| Edit invalidation | Prepare another disposable-output workflow, authorize it, then edit an argument through the normal UI | The earlier decision cannot execute the edited workflow; fresh review/authorization required |
| Restore | Open Execution History → completed run → View outcome, switch chats, refresh/restart, then reopen it | Same workflow and recorded outcome return without regeneration or execution |
| CLI continuity | In a second terminal run `./actioncharter`, then `/chats`, `/open NUMBER`, `/history`, `/view NUMBER`; return to frontend | Both interfaces show the same recorded task/results; browsing does not rerun writes |
| Catalog | Open Settings → Operations & libraries | Current builtin/installed operations remain visible; browsing does not reinstall or run them |

For each check record pass/fail, actual error text, run ID and whether model planning,
authorization or execution occurred. Do not modify stored plans/approvals by hand.
Cancellation, malformed records, expiry, changed inputs, wrong package digests and
partial-output recovery are covered by automated fixtures; a later manual cancellation
check can use a sufficiently long disposable run. No live database test is required
for this structural acceptance; any such test requires separate explicit authority.

## R7 handoff

R6 automated gates pass; R7 can start directly from these native owners.
The main CLI is currently 7,463 lines. Split commands into planning, workflows/runs,
recipes, Builder, database, discovery and history/settings groups, leaving a small
entrypoint. Reuse `task_actions.command_actions`; preserve options, help, exit codes,
JSON/text output, lazy optional dependencies and the same shared services. Add no
operations or interface redesign. Keep HTTP routers (R8), temporary compatibility
retirement (R11) and server seams (R12) separate. Git and publication remain owner-managed.

Start R7 by inventorying parser registrations, helper dependencies and command outputs;
then extract one command group at a time into `apps/cli/`. Retain `geoagent_harness.cli`
as the public entrypoint, and do not make command modules import one another's dispatch
implementations. Explicitly include the four L6 CLI adapters currently nested under
data/discovery, data/databases/postgres, data/tabular and capabilities/registry.
Exit checks: no CLI implementation module above roughly 1,000 lines, all existing
options/help/output/exit-code tests retained, optional agent CLI imports stay lightweight,
strict layer gate stays clean, full backend/frontend checks and cross-interface journey
pass. Existing `test_*cli*.py`, `test_task_action_boundaries.py` and
`test_agent_cli_optional_dependencies.py` provide the compatibility baseline.
