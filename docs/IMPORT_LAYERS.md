# Import layers and the Phase 0 gate

R1, [issue #66](https://github.com/wanggiya/action-charter/issues/66), 2026-11-05.
This is a static development check, not an execution-policy or sandbox boundary.
It does not import application modules, run operations or move records/packages.
R6 now supplies native package owners and an audited compatibility manifest; the
initial measurements below are retained as history.

R7's [CLI extraction](CLI_COMMAND_STRUCTURE.md) adds native command modules and nine
compatibility adapters. Current strict graph: **862 modules / 3,091 internal imports,
zero upward and dynamic-import debt**; 400 audited adapters (61 package roots), 462
native modules. The R6 counts below describe its completion snapshot.

R8's [HTTP extraction](HTTP_ROUTER_STRUCTURE.md) now measures **893 modules / 3,209
internal imports, zero upward and dynamic-import debt**. Its seven additional audited
adapters bring the total to 407 (61 package roots), with 486 native modules. Earlier
R6/R7 measurements remain their completion snapshots.

R11 [retirement and public boundaries](R11_COMPATIBILITY.md) removes 290 obsolete
adapters: **613 modules / 3,016 internal imports**, zero upward/dynamic debt, 496
native implementation modules and 117 explicit supported boundaries (60 package
roots, 57 aliases). The original 407-entry R6 inventory remains immutable history;
`r11_compatibility.json` exhaustively partitions it. Ordinary callers use native
owners; the [compatibility audit](../scripts/check_compatibility.py) checks caller
regressions. New implementation cannot be hidden under an old public package root.

## Run the check

From the repository root:

```bash
.venv/bin/python scripts/check_import_layers.py
.venv/bin/python scripts/check_import_layers.py --json
```

The normal check compares the measured dependency graph with exact recorded debt.
It also runs in `make test` through `tests/test_import_layers.py`; the existing CI
pytest job therefore checks it without another dependency or workflow change.

For the final Phase 0 layer gate:

```bash
.venv/bin/python scripts/check_import_layers.py --strict
.venv/bin/python scripts/check_compatibility.py
```

**Strict mode now passes:** R6 removes the remaining upward dependencies and replaces
the reviewed dynamic API export lookup with fixed literal imports. Phase 0 remains
open for entrypoint/server/storage work and owner checkout cutover.
All commands are read-only and exit nonzero on regression/configuration errors.
There is no command that automatically regenerates or accepts the baseline.

## Rule and current layout

`tests/architecture/import_layers_policy.json` explicitly maps today's module prefixes
to the proposed layers in [the restructure plan](product-direction/RESTRUCTURE_PLAN.md#2-target-layers-and-the-dependency-rule).
R1 began with a conceptual mapping; R6 creates the native package directories.

```text
L6  HTTP / CLI / chat / MCP adapters and demo/test composition
 |  L5  shared task actions
 |   |  L4  agent roles and orchestration
 |   |   |  L3  capabilities, registry and recipes
 |   |   |   |  L2  data services and sandbox workers
 |   |   |   |   |  L1  core policy, ledger, verification, storage/model/workspace platform
 |   |   |   |   |   |  L0  shared contracts
 +---+---+---+---+---+---> same-layer or downward dependencies
```

Dependencies within a layer are permitted. Upward imports are violations. Same-layer
cycles and transitive behavior are not proven safe by this rule. Specific CLI modules
under data/operation packages are adapters at L6; their underlying packages retain
their data/capability level. The application root is an exact mapping, not a catch-all:
a new top-level package must receive an explicit reviewed classification.

## What is measured

Initial measurement, 2026-11-05:

| Item | Count |
|---|---:|
| Python modules under `src/geoagent_harness` | 412 |
| Internal import occurrences | 1,933 |
| Distinct upward source/target/kind dependencies | 109 |
| Upward import occurrences | 128 |
| Non-literal import expressions needing review | 1 |
| Compatibility module aliases, still scanned | 23 |
| Non-MCP modules importing `mcp_server.settings` (including CLI adapters) | 36 |

The [baseline](../tests/architecture/import_layers_baseline.json) now has empty upward
and dynamic-review lists. Before R6 it listed each remaining dependency, occurrence
count, reason and follow-up task, without wildcard exemptions. Initial categories:

| Follow-up | Distinct dependencies | Work to inspect |
|---|---:|---|
| R2 | 33 | Shared settings/schema still owned by MCP; 32 settings dependencies plus one schema dependency below L6 |
| R3 / P0-5b | 5 | Metadata clients still reach task-action transaction wrappers |
| R3 | 1 | Storage contract imports a Planner result type |
| R4 | 12 | Lower-layer readers/errors/DTOs/redaction reach higher-level owners |
| R4 / R6 | 7 | Ledger/domain references to role contracts or observer ownership |
| R5 | 10 | Lower-layer code reaches shared task orchestration |
| R6 | 41 | Other orchestration/domain/client-port ownership to resolve before moves |

These are triage categories, not instructions to fix all entries in one change.
They count source/target/kind pairs, not lines or files. Removing direct HTTP imports
did not automatically remove upward coupling to the new `task_actions` owner.

## Current R6 result

The strict scan covers **826 modules / 3,037 internal import occurrences**, with zero
upward dependencies and zero dynamic-import debt. Of these, 435 are native modules;
391 are temporary historical compatibility adapters, including 61 package roots.
`tests/architecture/r6_module_owners.json` binds each adapter to its native owner and
reviewed source SHA. The checker rejects missing owners, changed wrapper source and
top-level business definitions hidden in an adapter. Native lower layers importing
these L6 adapters still fail the ordinary layer rule. The increased file count is
compatibility overhead, not another implementation of each service; R11 owns retirement.

Synthetic checker tests retain their original frozen topology in
`tests/architecture/import_layers_fixture_policy.json`; the actual repository is always
checked against the live policy. [R6 ownership, evidence and manual acceptance](R6_COMPLETION_AND_ACCEPTANCE.md).

## Baseline maintenance history

R2 follow-up (2026-11-05): [platform configuration](PLATFORM_CONFIGURATION.md) removes
all 33 R2-category pairs plus the Executor's client-settings dependency. Its resulting
baseline was **75 pairs / 87 occurrences**, down from the initial 109 / 128 above.
New platform/contracts owners are explicitly L1/L0; no existing classification was
relaxed and no new upward edge was accepted. That scan had 421 modules and 28
compatibility aliases. The single dynamic review remains unchanged. The initial
measurement and triage above are preserved as history; strict mode still rejects debt.

R3 follow-up (2026-11-05): [shared metadata and neutral plan contracts](STORAGE_REPOSITORIES.md#r3-transaction-and-plan-contracts)
remove ten further pairs: five storage clients and five Planner-type dependencies.
Its resulting baseline was **65 pairs / 68 occurrences**, with 424 modules, 29 aliases
and the same reviewed dynamic import. Policy/classifications are unchanged; only
removed/reduced debt is trimmed. R3's shared error identity is a prerequisite for
broader R4 work, not a claim that all reader/error/projection boundaries are finished.

R4 follow-up (2026-11-06): [shared data access and neutral contracts](DATA_ACCESS_BOUNDARY.md)
remove all 12 directly assigned R4 pairs, including 13 import occurrences. The current
baseline at R4 completion was **53 pairs / 55 occurrences**, with 434 modules, 35 aliases and the same
dynamic review. The policy/classifications are unchanged; no new/increased dependency
is accepted. Three mixed R4/R6 observer/role-type pairs remain recorded for R6 ownership
review; remaining action/orchestration dependencies belong to R5 and subsequent moves.

R5 follow-up (2026-11-06): [shared task composition and CLI delegation](TASK_ACTIONS.md#r5-shared-composition-and-evidence-boundaries)
remove all ten directly assigned R5 pairs (12 occurrences). Its resulting baseline was
**43 pairs / 43 occurrences**, with 443 modules and 37 aliases. Its 213 CLI service
import rewrites and 146 explicit lazy exports add no upward edge or dynamic-import
review. Existing policy/classifications and the single source-bound review remain.
Existing R6 ownership debt remains recorded; strict mode still correctly rejects it.

R6a follow-up (2026-11-06): [shared execution primitives](SHARED_EXECUTION_PRIMITIVES.md)
remove eight more pairs/occurrences: four recipe-control imports, two planner-topology
imports and two role-schema imports. The current baseline is **35 pairs / 35 occurrences**,
with 447 modules, 40 visible aliases and the same source-bound dynamic review. No new
upward dependency, classification change or dynamic-import exemption was accepted.
One mixed observer/evidence-builder dependency and the remaining R6 ownership work
stay recorded; R6a is not a zero-debt exit or completion of physical package moves.

- Imports inside functions, branches, exception handlers and `TYPE_CHECKING` count.
  Absolute and relative imports, aliases and `from package import child_module` are
  resolved against the source-file inventory. Missing internal targets and syntax
  errors fail instead of being silently skipped.
- Baseline identities exclude line numbers so comments/formatting do not create debt.
  Occurrence counts still distinguish separate statements, including two on one line.
- New/increased upward dependencies fail. Removed/reduced dependencies also require
  shrinking the baseline, so an obsolete entry cannot permit later reintroduction.
- Each debt record requires a reason and follow-up. The baseline binds the exact
  policy SHA-256; changing classifications requires explicit review of both files.
  Do not reclassify a module merely to make its imports pass.
- Compatibility `sys.modules[__name__]` aliases are reported and scanned, not exempted.
  A lower layer importing an old HTTP alias still creates an upward dependency.
- Common `importlib.import_module` and builtin `__import__` calls, including directly
  imported/renamed functions, are inspected. Literal targets use the same rules.
  Non-literal targets require an expression review bound to the entire source-file
  SHA-256. A source-text edit invalidates the old review until it is reconsidered.
- The source-review digest uses UTF-8 text with Python's universal-newline
  normalization. A line-ending-only change retains the same review; changes to code,
  comments or other text invalidate it. This is not a raw-file integrity ledger.
- The former reviewed expression was the API's legacy `__getattr__` export resolver.
  R6 replaces it with allowlisted literal imports while preserving public behavior;
  no expression review is currently required.

This is AST analysis, not Python interpretation. Runtime reflection, reassigned
importer functions, executable strings, custom loaders, external dependencies and
subprocess code are not fully resolved. Same-layer cycles, semantic ownership and
runtime import costs require separate review. Models/credentials/data are never read.
Existing policy, exact authorization and independent verification remain authoritative.

## P0 and R work are one backlog

The updated [P0/R inventory](product-direction/RESTRUCTURE_PLAN.md#current-p0r-gap-inventory--2026-11-05)
records overlaps and remaining work, including P0-2b (project-ID workspace/config),
P0-5b (ledger/concurrency contracts), R7/R8 (thin entry points), and R12 (server seams).
P0-3 and P0-6 are implemented foundations, not requests to rebuild them. Real workspace
cutover remains owner-controlled; R1 does not meet the source-only-root gate.

## Verification

R6 final strict graph passes; final full `make test`: **2,688 passed (728.54 s; 13 existing spatial warnings)**.
Frontend/Compose and relocated fixture browser/API/CLI/terminal also pass.
[Current acceptance and remaining limits](R6_COMPLETION_AND_ACCEPTANCE.md). Earlier
R1 counts below are the initial checker evidence, not the current suite total.


Synthetic fixtures prove permitted/downward dependencies pass and new/increased,
removed-but-stale, unclassified, malformed and unreviewed dependencies fail. They also
prove scanning never executes source, aliases do not hide reverse dependencies,
policy changes need review, strict mode passes a clean graph, and neither mode rewrites
the baseline. Existing lightweight-import tests remain independent.

Focused R1 + existing import-boundary checks: **23 passed (4.69 s)**. Final full
`make test`: **2,501 passed**, 13 existing spatial warnings, **722.32 s (12:02)**.
Normal baseline check passes; strict mode returns 1 as expected for the recorded debt.
Documentation checks validated 255 local links/anchors and the active roadmap size.
No frontend build/browser journey was repeated for this static development check;
application and frontend source are unchanged. These are automated fixture checks,
not new live-model/database acceptance. Full timing output is in
`/tmp/actioncharter-r1-full.log`; durable results are also recorded in CURRENT_STATUS.
