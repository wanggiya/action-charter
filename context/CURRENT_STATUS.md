# Current implementation status

Updated: 2026-11-13. [Immediate handoff](WORK_RESUME.md),
[active roadmap](PRODUCT_ROADMAP.md), [Phase 0 closeout](../docs/P0_CLOSEOUT.md).

## Phase and closeout

Phase 0 closeout is merged in PR #85 (c03f11d). Phase 1 began on 2026-11-13.
[P1-B1–B3](../docs/BENCHMARKS.md), tracked by #86–#88, now provide typed definitions,
read-only loading, a process-bounded runner/CLI and deterministic evidence checks.
The current suite is one synthetic example; B4 expansion, provider/egress changes
and real-model baseline remain unfinished. B1–B3 Git integration is owner-managed
and still pending; no new agent roles, permissions or frontend redesign.

The owner completed real workspace adoption before this task. Read-only verification
now reports stable project binding, migration complete, `source_only: true` and no
legacy entries. `changed_since_migration` means saved state has changed normally
since the certificate; it is not a new exact-copy/backup certification. This task
removed seven empty legacy directories only, not records. No cutover, rollback,
secret edit, package installation or live database/service write was performed.

R1–R12 are delivered/reconciled in merged PR #82. Its description records **owner-
reported overall manual acceptance**; per-step IDs/model/timings were not supplied.
Optional fresh-file authorization was not separately reported. Automated fixture
results below are not a real local-model performance benchmark.

## Product boundary

ActionCharter remains a local single-operator alpha for governed spatial and tabular
workflows, with broader service/CLI coverage than the default graph. It is not a
packaged desktop application or hardened multi-user service. Models propose and
assess; typed services, deterministic policy, exact operator decisions, runtime
validation and durable evidence establish permission and results. Conversation,
data, model text, historical approvals and package installation never grant authority.

## Planner and execution

Planner is the primary entry beside the editable graph. Each chat restores its saved
workflow and recorded runs without regeneration or execution. CLI, HTTP, chat and MCP
reuse task-action services; native implementations sit behind strict import layers.
Existing operation contracts, schema/SDK boundaries and historical digests remain
supported; 290 obsolete adapters are retired and 117 explicit boundaries retained.
See [architecture](ARCHITECTURE.md), [task actions](../docs/TASK_ACTIONS.md),
[execution context](../docs/EXECUTION_CONTEXT.md) and
[compatibility](../docs/R11_COMPATIBILITY.md).

Direct read-only Execute and opt-in inspection-on-send retain their existing scope.
Writes need Allow writes, exact authorization and independent execution checks.
Bare filenames resolve under `data/input`; normalized safe relative paths remain
supported. Input format/source mismatches reject before execution. Plan edits,
expiry and mismatched evidence cannot reuse authority. Cooperative cancellation,
durable history and recovery proposals do not automatically repeat writes.

## Saved records and state

Saved recipe/plan lists now isolate record-local failures. Malformed, unsafe or
policy-rejected records appear as unavailable with bounded/redacted reasons and no
approval/execution actions; usable records remain visible. An all-invalid list shows
findings, not a 503 or an empty success. Root ownership/global-budget failures still
fail closed. Bad approval or matching-plan evidence never becomes verified authority.
Listing does not repair, delete or authorize stored records. Existing approval and
execution validation and the CLI authority-verification inventory remain strict.

The owner's 74 recipe files were read without changing their hashes: 73 usable,
one blocked CSV/vector format mismatch. This is read-only inventory evidence, not
an execution test. [Closeout behavior and acceptance](../docs/P0_CLOSEOUT.md).
Workspace state remains outside source after explicit offline adoption; source
relocation/container mapping beyond local stable identity is future provisioning.

## Data, reports and interface

Registered spatial inspection/conversion, bounded tabular transformations/statistics,
PostGIS lifecycle operations and installed adapters retain their existing contracts.
Library discovery produces non-executable candidates, not unrestricted dispatcher
entries. Database writes still require explicit scope and credentials; no new live
PostgreSQL/PostGIS/GeoServer acceptance is claimed. Default ports remain 5173/8765.

[Recorded inspection quality reports](../docs/INSPECTION_QUALITY_REPORTS.md) reuse
saved evidence in Markdown/PDF. New scans collect bounded basic missingness,
distinct/repeated values, whole-row duplicates and numerical candidates. Legacy
reports explicitly distinguish unperformed checks from recorded facts. Inferential
statistics require the supported typed analysis and its recorded result; ordinary
inspection is not a complete data-science study. [Analysis/report coverage](../docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md)
and [full-data delivery (F5 partial)](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md) retain
limits. Cross-chat knowledge, RL, autonomous capability acquisition and release
packaging are not made complete by consolidation.

Current graph, result tabs, report downloads and terminal/history continuity keep
existing behavior. Unavailable-record notices reuse existing UI surfaces. No new
agent, operation, navigation redesign or Phase 1 provider/benchmark feature is added.

## Verification and next work

B2/B3 full source-only `make test`, with GitHub/frontend-required flags:
**2,903 passed**, 13 existing spatial warnings, 777.77 seconds. Later focused gates
verify current diagnostic/budget refinements and explicit step selection. Strict
source gate has zero debt; compatibility retains 290 retired/117 public boundaries,
now 621 modules/504 native. Tests use temporary synthetic projects and a fake local
endpoint, not real-model quality or live-database acceptance. No frontend changed.

Benchmark runs retain private task state and immutable content-free results under
workspace `benchmark-runs`. Expected answers are withheld; unknown execution is
never counted as zero. Skips/unsupported gaps are not counted as capability passes.
Optional fixture writes pass ordinary exact authorization; local-data writes and
live services are not admitted. Table checks inspect exact validation receipts, not
current live targets. The worker is process-contained, not a general code sandbox.

Saved owner fixture run and both checks independently rechecked: passed, 3 rows/3
columns, one operation; fresh isolated CLI and 78 runner/contract checks passed.
Next: integrate B1–B3, then B4 suite/disposable adapters,
B5 actual local-model baseline and the M1/M2 provider/egress lane under the
[Phase 1 plan](../docs/product-direction/PHASE_1_PLAN.md). Phase 1 is not complete.

## Record navigation

[Documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md),
[historical status](../docs/development/STATUS_HISTORY.md),
[combined owner acceptance](../docs/R_SERIES_ACCEPTANCE.md).
This overview feeds model context; historical next steps are not current scope.

<!-- historical-checkpoints -->

# Checkpoint history

Historical checkpoint descriptions moved to [docs/development/STATUS_HISTORY.md](../docs/development/STATUS_HISTORY.md) (2026-11-01) to keep this file within the context loader's size limit. Add new history entries there, not here.
