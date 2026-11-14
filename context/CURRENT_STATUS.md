# Current implementation status

Updated: 2026-11-13. [Immediate handoff](WORK_RESUME.md),
[active roadmap](PRODUCT_ROADMAP.md), [Phase 0 closeout](../docs/P0_CLOSEOUT.md).

## Phase and closeout

Phase 0 closeout is merged in PR #85 (c03f11d). Phase 1 began on 2026-11-13.
[P1-B1–B3](../docs/BENCHMARKS.md), tracked by #86–#88, merged in PR #89 (48cc101).
B4 (#90) now adds [27 definitions](../benchmarks/README.md) and opt-in disposable
database fixtures over the typed loader, process-bounded runner/CLI and evidence
checks. Three definitions are explicit gaps; one references optional local data.
B5 (#91) adds a four-task fixture CI gate, sanitized report CLI and source/settings
provenance. [Real-model baseline](../benchmarks/results/README.md) is recorded:
8 passed, 11 failed, 4 timed out, 1 skipped, 3 unsupported, versus 23 fixture passes.
No real Critic assessment completed. B5 verification passed; integration is pending.
Provider/egress changes remain
unfinished. Git integration is owner-managed; no new agent role or frontend redesign.

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
agent, operation or navigation redesign is added by the benchmark work.

## Verification and next work

PR #92 fixture-packaging fix: Git-visible source-only CI/GitHub/frontend-required
`make test`: **2,929 passed**, 13 existing spatial warnings, 899.28 seconds.
Five exact synthetic GIS assets are now includable in Git; CI validates all required
fixtures before its fast subset. Owner commit/push and remote checks remain pending. Final report, fixture CI, context and
link checks passed; evidence/logs are in [WORK_RESUME](WORK_RESUME.md). The strict
source gate has zero debt: 623 modules/3060 imports, 506 native implementations,
290 retired/117 public boundaries. No frontend code changed.

Benchmark runs retain private task state and immutable content-free results under
workspace `benchmark-runs`. Expected answers are withheld; unknown execution is
never counted as zero. Skips/unsupported gaps are not counted as capability passes.
Positive synthetic writes need a manifest requirement, operator opt-in and ordinary
exact authorization. Read-only safety/local-data tasks cannot inherit that authority.
Database cases additionally require a disposable-runtime opt-in. They use generated
credentials and a private Unix socket to a fresh network-disabled, bounded container;
no owner connection is used, and no image is pulled. Both actual disposable DB cases
and automatic expiry/removal passed. Table scores inspect exact recorded independent
verification receipts, not a new live query. The analytical worker remains a fixed
process boundary, not a general code sandbox. B4 results are fixture/temporary-service evidence. B5 separately records a real
local-model baseline, with failure and Critic limits in the linked reports; neither
is live owner-database acceptance.

Next: owner integration, then M1/M2 provider/egress, M3c provider checks,
B6 comparison and X closeout under the [Phase 1 plan](../docs/product-direction/PHASE_1_PLAN.md).
Phase 1 is not complete. Optional local diabetes data was not read in B4.

## Record navigation

[Documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md),
[historical status](../docs/development/STATUS_HISTORY.md),
[combined owner acceptance](../docs/R_SERIES_ACCEPTANCE.md).
This overview feeds model context; historical next steps are not current scope.

<!-- historical-checkpoints -->

# Checkpoint history

Historical checkpoint descriptions moved to [docs/development/STATUS_HISTORY.md](../docs/development/STATUS_HISTORY.md) (2026-11-01) to keep this file within the context loader's size limit. Add new history entries there, not here.
