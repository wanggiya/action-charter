# CLI command ownership and R7 validation

R7, [issue #75](https://github.com/wanggiya/action-charter/issues/75), 2026-11-08.
Implementation and required automated checks are complete. Owner manual acceptance
and Git integration remain pending.

R11 follow-up: maintained launchers and new package entrypoints now use native
`apps.cli.main`, `apps.chat.workspace` and `apps.mcp.server` directly. Historical
installed/module entrypoints remain supported exact aliases. The original CLI
command and help snapshots are unchanged. [Compatibility boundary](R11_COMPATIBILITY.md).

## Structure and behavior

```text
geoagent_harness.cli              historical entrypoint / exact module alias
          |
apps/cli/main.py                 app construction and named callback exports
          |
apps/cli/registry.py             explicit registration in historical order
          |
command groups / small registrars
          |
existing task actions and shared services
          |
existing policy, execution, verification and records
```

The public CLI stays flat: users do not need new command prefixes. The existing
`postgres` and `chat` command groups retain their syntax. `./actioncharter` remains
the terminal workspace entrypoint; this restructuring does not change its interface.

The old 7,463-line main module now has a 142-line composition owner and a 290-line
explicit registry. Its 110 command/helper definitions live in 24 responsibility
modules, including four Builder modules. Eight existing small CLI registrars move
intact into the CLI application package. The largest command module is 783 lines;
every CLI implementation module stays below 1,000 lines.

| Module group under `apps/cli/` | Existing commands |
|---|---|
| `planning`, `approvals` | Intent/planning, plan digests and exact decisions |
| `workflows`, `workflow_tools`, `planning_tasks` | Existing dispatch, durable state, recovery and saved-chat actions |
| `history`, `method_memory` | Task context, reviewed history and current method-note controls |
| `recipes`, `recipe_planning`, `exports` | Recipe definition, approval/execution, proposals and static exports |
| `spatial`, `raster`, `geoserver` | Existing spatial commands and bounded service workflows |
| `postgis_inspection`, `postgis_promotion`, `postgis_rollback`, `postgres` | Existing database inspection and governed lifecycle commands |
| `builder/inspection`, `builder/review`, `builder/promotion`, `builder/activation` | Existing experimental Builder lifecycle, without new authority |
| `discovery`, `tabular`, `operations`, `skills`, `schemas` | Existing data/catalog/skill/contract commands |
| `critic`, `releases` | Evidence assessment and recorded release artifacts |
| `settings`, `workspace`, `interface` | Manifest/write availability, workspace migration and interface serving/projection |
| `common` | The unchanged typed failure renderer only |

Command groups do not import one another's dispatch implementations. The registry
owns composition; the common module does not become a second service layer. Existing
command-local imports and the lazy `task_actions.command_actions` catalog retain their
binding behavior. CLI definition loading does not start a model, database or server.
Existing optional-GIS import tests remain authoritative; this adds no new runtime.

No command body, parameter, authorization condition, output formatter, exit behavior,
stored/generated entrypoint string or execution engine is changed. Existing services
still authorize, execute, verify and record work. No new operation, agent, feature,
dependency, UI design or model-approver implementation is added.

## Compatibility and evidence

The public `geoagent_harness.cli` resolves to the native main module. All 110 original
named command/helper functions remain exported. Legacy `python -m geoagent_harness.cli`
and the installed `geoagent` entrypoint still use the same app. Eight moved registrar
paths retain exact aliases; older aliases point to the current native owners in the
source-bound manifest. The old `workspace_cli`, data/discovery/tabular/PostgreSQL,
registry and interface CLI imports remain supported.

Before editing, the snapshot captured 150 top-level commands, all 165 help screens
(including subcommands), full option/default/type metadata and 110 function ASTs.
`tests/architecture/r7_cli_contract.json` stores compact baseline hashes. New tests
compare exact ordered metadata/help and unchanged function signatures/bodies, check
module sizes/import direction and exercise both public/native entrypoints. Different
`python -m` invocations correctly show their own module names in Usage.
The baseline used Python 3.12, Typer 0.27.0, Rich 15.0.0 and Click 8.4.2; help rendering
uses 120 columns with color disabled.

Focused ownership/CLI/optional-dependency/layer checks: **47 passed**, including five
new tests. Existing CLI/Builder/workspace/action regression group: **227 passed**.
Frontend validation passed (5.09 s build; existing bundle-size warning).
The isolated relocated browser/API/CLI/terminal journey passed with zero page errors
and one authorized temporary write. The installed `geoagent inspect-csv` sample smoke
check returned six rows/five columns without a model call.
Strict gate: **862 modules / 3,091 internal imports, zero upward or dynamic-import
debt**; 400 temporary compatibility adapters (61 package roots), 462 native modules.
R6 measurements remain historical; R11 still owns compatibility retirement.

The initial new entrypoint test compared the invoked module name literally and failed;
its comparison now normalizes that expected name/padding difference. All original
tests and expected values remain unchanged. No production behavior was altered for it.
Final `make test`: **2,693 passed (730.42 s; 13 existing spatial warnings)**. The isolated cross-interface journey passes.
Final documentation audit: 536 local links and 170 fragments across 37 changed Markdown
files pass; roadmap is 15,805 bytes (below 64,000), and whitespace checks pass.
Automated fixtures do not establish new local-model quality or live-database acceptance.

## Manual validation after R7

Owner decision 2026-11-08: defer these manual checks until the R series is complete.
They remain preparation for that combined pass; automated checks still run per task.

From the repository root, with the existing environment installed:

```bash
.venv/bin/geoagent --help
.venv/bin/geoagent inspect-csv --help
.venv/bin/geoagent postgres --help
.venv/bin/geoagent inspect-csv sample_orders.csv
```

Help should retain the existing command names/options. The public sample should
report six rows and five columns. `python -m geoagent_harness.cli` remains supported
for scripts; users do not need to adopt the native package path.

For frontend/terminal continuity, keep your normal launcher running:

```bash
bash scripts/start_actioncharter.sh
```

Open `http://127.0.0.1:5173`. In a new chat send
`Run a new read-only inspection of sample_orders.csv`. If Inspection on send is OFF,
click Execute once. Confirm six rows/five columns, then open Execution History and
reopen the outcome. In a second terminal run `./actioncharter`, use `/chats`,
`/open NUMBER`, `/history` and `/view NUMBER`; the same recorded result should appear.
Refresh the frontend and confirm no regeneration or repeat execution.

Use the [R6 disposable-write and edit-invalidation checks](R6_COMPLETION_AND_ACCEPTANCE.md#manual-validation-after-r6)
for authorization acceptance. No live PostgreSQL/PostGIS mutation is required for this
structural test. Record actual errors/run IDs; do not hand-edit saved authority files.

## Next handoff

R8 decomposes the remaining HTTP handlers into thin routers over the same task actions.
Do not repeat the CLI extraction or change command semantics during that work. Keep
P0-2b project identity/owner cutover, P0-5b ledger/concurrency, R12 server seams and final
R11 compatibility retirement as explicit remaining Phase 0 gates. Git remains owner-managed.

## Fresh-install CLI dependency contract (PR #82, 2026-11-12)

The original command/help snapshots remain unchanged. Their verified runtime is
Typer 0.27.0, Click 8.4.2 and Rich 15.0.0; the package now pins those versions.
CI's former open ranges resolved Typer 0.29.1/Click 8.5.1, changing parameter
introspection and help formatting. Future upgrades need an explicit compatibility
review, rather than silently accepting or regenerating historical snapshots.
Fresh-container tests confirm all CLI contract checks pass with the pinned toolchain
and newer non-CLI dependencies. No command body or entrypoint changes.
