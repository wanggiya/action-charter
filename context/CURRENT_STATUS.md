# Current implementation status

Updated: 2026-11-18. [Immediate handoff](WORK_RESUME.md),
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
No real Critic assessment completed in that B5 baseline. B4/B5 and packaging fix merged in PR #92
(d045216). [M1 provider profiles](../docs/MODEL_PROVIDERS.md), #93, are implemented
and verified with fixture, browser and real Ollama synthetic evidence. [M2 context
classification/gating](../docs/MODEL_EGRESS.md), #94, is implemented and verified
with temporary fixtures and actual-gateway/fake-model browser evidence.
[M3c qualification](../docs/MODEL_PROVIDER_QUALIFICATION.md), #95, now has a repeatable
synthetic runner. Real Ollama planning and deterministic CSV execution passed through
direct/relay paths and a network namespace restricted to the model broker. Missing/
wrong keys and over-allowance requests were blocked before upstream calls. A real
isolated Critic assessment completed after constraining suggested method operations
to observed IDs, using an explicit temporary 60-second review preference. The product
default remains 15 seconds; earlier timeouts/rejections are retained. Managed local
qualification now covers actual LiteLLM1.109.1 and a separately started Windows
Ollama process with existing weights. Six modes passed across two matching-source
captures after explicitly correcting the secondary cache path. Temporary review
budgets were90s; no data outputs, owner settings changes or model downloads.
The gateway's optional hash-locked environment is separate from .venv/browser caches.
M3c local checks are verified. The first [B6 slice](../docs/REQUEST_DIAGNOSTICS.md),
#96, adds **Reported model tokens** from existing diagnostics: separate input/context
and generated-output figures, bounded chat/submission/workflow scopes, explicit
partial/unknown coverage, and expandable timing/role/model details. CLI and JSON
export reuse the same read-only aggregation; refresh never calls a model. These
are recently retained observations, not lifetime billing or network bytes. Full
offline regression passed 3,075 tests; final frontend layout/export changes passed
interface validation and an isolated fixture browser journey. Saved-profile benchmark
binding and read-only comparison are now implemented/verified. Broader measurements
account for27 declarations per model,54 observations and27 matching recorded pairs:
each model recorded4 passes,7 failures,10 deadlines,3 skips and3 unsupported cases.
Synthetic fresh file outputs were opted in; database/private data stayed excluded.
Phase 1 engineering closeout is recorded in [P1-X #97](../docs/PHASE_1_CLOSEOUT.md);
owner Git integration remains pending. Phase 2 Data Card work is authorized. Other vendors,
remote hosts and public project-data use are unqualified. Git is owner-managed; no
new agent role or frontend redesign.
The B6 first-chat follow-up fixes negative database-write wording selecting a
PostgreSQL schema for CSV inspection/advice. Failed submission receipts retain safe
reasons across refresh without replay; immediate errors scroll into view. The
corrected real local qwen3.5:9b request still timed out with provider-default
reasoning; a separate temporary reasoning-none test passed in39.008s with one call,
no approval/execution and unchanged owner settings. This is not a reliability or
speed-comparison claim. [Retest and limits](../docs/REQUEST_DIAGNOSTICS.md).
Settings now labels the built-in local profile as launcher settings and explains
disabled Save/check controls, with save errors in the editor. Same-endpoint profiles
are allowed. The owner-reported unresponsive Save action is not yet reproduced.
This frontend follow-up passed 44 focused tests, interface validation and an
isolated actual-API/fake-model browser journey; current M2 coverage includes it.

The owner completed real workspace adoption before the P0 closeout. Its earlier
read-only verification reported stable project binding, migration complete,
`source_only: true` and no legacy entries. The current coding-session checkout now
refuses **Copied project identity**: its ownership marker does not match the visible
filesystem identity. The owner confirmed the same error in the launcher terminal.
Read-only diagnosis found matching source/state inodes, source path and owner UUID,
but device number changed2128 to2096, consistent with a WSL remount. Recovery is
not implemented. No ownership marker, rebind or state configuration was changed.
The isolated D1 checks below do not certify this checkout's ownership.
`changed_since_migration` means saved state has changed normally
since the certificate; it is not a new exact-copy/backup certification. That earlier adoption
removed seven empty legacy directories only, not records. It performed no new cutover,
rollback, secret edit, package installation or live database/service write.

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

[Data Card foundation](../docs/DATA_CARDS.md), P2-D1 #98, reuses existing bounded
readers. One typed projection supplies source/digest/selection, population scope,
field types/candidate roles and available quality/numerical facts to Planner context,
CLI/MCP and Overview. Cards exclude preview rows; explicit query literals are not
anonymized and the gateway classification is unchanged. Preliminary samples and
unknowns stay distinct. Opening/history restoration derives cards from saved evidence
without source scans or model calls. Automatic freshness/cache/reuse scheduling is
P2-D2; no new agent, container, processing operation or permission. D1 is
implemented/verified with fixture, browser/CLI and bounded real-model evidence. [Phase 2 plan](../docs/product-direction/PHASE_2_PLAN.md).

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

P2-D1: all **3,120 collected offline tests have passing coverage**. Full source-only
make test passed3,114 in1209.77s (13 existing warnings); final80 affected checks
passed22.50s after legacy handling, artifact-budget and analytical-context follow-ups.
There are74 overlapping passes and zero missing IDs; all970 Python source/test files
match the final verified export. This is complete coverage across batches, not one
uninterrupted final-source invocation. Interface validation passed12.06s; isolated
actual-API/fake-model browser and CLI/PTY passed card expansion and refresh/history
restoration with0 page errors/authorization calls. Strict630 modules/3140 imports
and compatibility513 native/117 retained/290 retired passed.

Two real local4B synthetic observations compare absent versus same-turn reader
context: clarification23.167s versus validated inspect_csv proposal34.515s, one
call each, no workflow dispatch/authority. They are functional observations, not a
speed/reliability claim or frozen pre-feature comparison. Final deterministic
follow-ups were tested afterward; no final-source model repetition is claimed.
[Observations](../benchmarks/results/2026-11-18-p2d1-card-context.json),
[scope and manual checks](../docs/DATA_CARDS.md), [handoff](WORK_RESUME.md).


B6 profile binding/comparison: all **3,094 collected offline checks have passing
coverage** across initial/completion batches. Initial1,454 passed before a prepared-
profile qualification regression; fixed verification/reuse passed91 caller checks.
Completion1,765 passed396.01s, with125 overlapping passes and zero missing IDs. No
single uninterrupted final-source full-suite invocation is claimed. Interface,
isolated Settings browser, strict/compatibility and15 context checks passed.
Four real local observations cover two synthetic tasks: descriptive statistics and
Critic passed on both9B/4B; quality9B policy rejection and4B deadline remain failures.
Temporary60s review; no owner setting/data/database change. These observations
precede the final prepared-profile compatibility fix, not a final-source repetition.
The subsequent [broader comparison](../benchmarks/results/2026-11-17-b6-broader-matrix.md)
now accounts for all27 declarations on each installed model with unchanged measured
source, all27 pairs matching recorded conditions, and three pairs passing on both.
Each recorded4 passes/7 failures/10 timeouts/3 skips/3 gaps. Seven deadlines retain
completed execution with unfinished Critic review. Missing proposals and unavailable
models remain failures, and safe field findings do not establish an exact policy
cause. No performance winner or owner-data acceptance is inferred. Full regression
for the optional failure-details contract passed **3,098 tests** in924.32s (13 existing
warnings), from a source-only export. Interface validation passed4.86s; strict628
modules/3130 imports and compatibility511 native/117 retained/290 retired passed.
Final architecture documentation followed measurement; no post-documentation model
repetition is claimed. P1-X now maps this evidence to the six phase exit criteria;
closing measurement does not establish analytical readiness.
[Detailed evidence](WORK_RESUME.md).

B6 first-chat follow-up: all **3,083 collected offline tests have passing coverage**
across initial/completion batches. Initial1,689 passed before a schema-focus
compatibility assertion; final completion1,865 passed (741.03s), repeating affected
callers, with471 overlapping passes and zero missing test IDs. Final85 targeted
Planner/readiness and15 context checks, interface validation, fixture browser and
strict/compatibility checks passed. This is complete coverage, not a single
uninterrupted final-source full-suite invocation. [Accounting and logs](WORK_RESUME.md).

M3c managed follow-up: **3,060 tests passed** in1006.40s,13 existing spatial warnings,
from a source-only export excluding optional environments/private data.130 focused
service/provider checks,15 final context checks, strict layers/compatibility and
repeat/cached-offline optional-installer checks passed. No M3c frontend code change;
prior interface validation retained. [Acceptance manifest](../benchmarks/results/2026-11-16-m3c-acceptance.json)
records six passing real-provider modes across two matching-source captures, with
both failed attempts retained. No single green matrix invocation is claimed.


M2 source-only CI/GitHub/frontend-required `make test` validation gives passing
coverage for **all 3,028 collected tests across three batches**. Initial 1,588 passed
before a nonlocal fake-host fixture was rejected; 496 completion tests passed before
a nested CLI snapshot inherited parent selectors. The final 1,085 passed (237.74 s,
13 existing spatial warnings), including corrected fixtures and the unchanged 165
CLI help snapshots under their original timeout. This is complete collection
coverage, not a single uninterrupted green full-suite invocation.

Final source/export comparison, interface typecheck/build, isolated browser/API/CLI,
strict layers and compatibility passed: 627 modules (510 native), 117 public/290
retired, zero debt. Focused policy/HTTP tests passed; the browser made four synthetic
requests, blocked raw planning before a fifth request and dispatched no workflow.
All model endpoints/data were fake or synthetic; no new real-model quality, timing
improvement or live gateway qualification is claimed. [Exact batch accounting, logs
and final checks](WORK_RESUME.md), [policy and limits](../docs/MODEL_EGRESS.md).

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

Next: P2-D2 source selection and fresh/reusable card lifecycle, then focused
planning efficiency under the [Phase 2 plan](../docs/product-direction/PHASE_2_PLAN.md).
Phase 1 engineering closeout is recorded; owner Git remains pending. Optional local
diabetes data was not read in the B4/B6 measurements.

## Record navigation

[Documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md),
[historical status](../docs/development/STATUS_HISTORY.md),
[combined owner acceptance](../docs/R_SERIES_ACCEPTANCE.md).
This overview feeds model context; historical next steps are not current scope.

<!-- historical-checkpoints -->

# Checkpoint history

Historical checkpoint descriptions moved to [docs/development/STATUS_HISTORY.md](../docs/development/STATUS_HISTORY.md) (2026-11-01) to keep this file within the context loader's size limit. Add new history entries there, not here.
