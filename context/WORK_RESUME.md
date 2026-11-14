# Work resume — P1-B5 implemented, measured and verified (2026-11-13, #91)

Owner authorized B5 on all pending B4 changes; main remains 48cc101 (PR #89).
[Issue #91](https://github.com/wanggiya/action-charter/issues/91),
[protocol/results/pilot](../benchmarks/results/README.md). No Git actions, secrets,
owner datasets/state, browser cache or live service/database changes. `.claude/`
untouched. No overlapping issue/PR. Preserve all B4/B5 changes.

Implemented four-task offline CI gate with exact pass/count assertions, sanitized
read-only benchmark report CLI, runtime/source/settings/package provenance and
operation selectors robust to extra preinspection. Duplicate evidence errors;
expected numbers/tolerances/hashes and request/operation schemas unchanged. Native
runtime count 623 / 506 implementations; layer gate 3060 imports, zero debt.

Reference qwen3.5:9b (installed) run only via loopback, 120 s model ceiling, 1024
output tokens, reasoning none, json_schema. Task declarations unchanged: added
120 s/3 calls; original CSV 60 s/2 calls. Fresh projects, synthetic writes and owned
disposable DB enabled, no local data. Owner qwen3:4b-instruct selection/.env unchanged.
Original selector pilot was preserved and cancelled safely after false conversion
score (extra inspection shifted step number); new @skill/skill_id checks fix it.
Corrected baseline may be warm due to pilot. No hidden retry or prompt tuning.

Corrected control 1a1c60a808884872bf18fca33fba1431: 23 passed/1 skip/3 gaps.
Actual 6937acf3ce8741e7824ae7f61e43b041: passed=8, failed=11, error=0, timeout=4, skipped=1, unsupported=3.
40 model calls, 7 corrections, 1564.88 s total; reported partial 124317 prompt /
2643 completion tokens across 11 of 23 calling tasks. 13 timeout observations
include advisory calls, distinct from 4 task deadline statuses. Critic: 9 unavailable,
1 unknown, 17 not requested, none complete; existing fresh-workspace 15 s review
limit applies below model ceiling. PostGIS completed/verified 3 operations before
review deadline; join content was correct but destination filename wrong. Five
negative cases returned no proposal/zero operations; not scored from prose as refusal.
No model memory/context-overflow or comparative performance claim.
Both control/model source SHA-256 bf88e2d57b94c3b2b8c9a7a798ec4135d0583064408039fc70b5a6458fae003b
and source_unchanged=true. No tests/builds concurrent with real measurement.
Current raw project /tmp/actioncharter-b5-baseline-k810n1sq (temporary; may clear at reboot).
Exported JSON/Markdown in benchmarks/results retain content-free evidence.
Pilot raw project /tmp/actioncharter-b5-baseline-zbuyx2mc; exported pilot is incomplete.
All disposable fixtures cleaned; verify final label inventory before closeout.

Full source-only CI/GitHub/frontend-required make test: **2,928 passed**, 13 existing
spatial warnings, **906.58 seconds**; /tmp/actioncharter-b5-full.log;
snapshot /tmp/actioncharter-b5-clean-o0t3n9g3. Current runtime/test/fixture bytes
match the completed snapshot. Final report tests: 11 passed (4.02 s); standalone
CI gate: 4 passed, no skips. Selector/suite/contract/layer gates: 104 passed.
Context checks: 15 passed; all 400 local doc links resolve; diff whitespace clean.
Strict gate: 623 modules/3060 imports, zero debt. Compatibility: 506 native,
290 retired/117 public, zero errors. Both baseline exports/Markdown reproduced
from saved records; source fingerprint matches measured runtime; no private fields.
All 27 tasks retain original values/tolerances/hashes/requests after selector fix.
Final Docker fixture label inventory empty. No frontend changed or browser run.
Logs: /tmp/actioncharter-b5-report-final.log, /tmp/actioncharter-b5-ci-final.log,
/tmp/actioncharter-b5-context-final.log, /tmp/actioncharter-b5-layers-final.log,
/tmp/actioncharter-b5-compatibility-final.log. Model log:
/tmp/actioncharter-b5-baseline-corrected.log. No model/test run remains active.

Next: owner validates quick CI and saved reports, then handles Git integration.
After B5, M1/M2, M3c, B6 and X remain; Phase 1 is not done.
No new processing operations, agent roles, learning or provider/egress capability.

---

# Work resume — P1-B4 implemented and verified (2026-11-13, #90)

B1–B3 merged by owner in PR #89, 48cc101. Tracking: [#90](https://github.com/wanggiya/action-charter/issues/90).
Started with only unrelated `.claude/` untracked; left untouched. No branch/stage/
commit/push/merge, owner secret edit or live database operation performed.

Added 27 definitions: eight synthetic health/statistics, one optional local diabetes
reference (not read), eight spatial/engineering, seven safety and three explicit
gaps. [Suite guide and commands](../benchmarks/README.md), [runner contracts](../docs/BENCHMARKS.md).
Independent arithmetic expectations and export hashes are not model input. Added
write_mode/runtime/requires_gis, positive-write opt-in and separate disposable DB
opt-in. Read-only safety/local-data tasks never gain write authority from those flags.
Checks add literal-key/validation selectors, expected hashes and no-file-output facts.
Fixed null output receipts in PG scoring; scoring errors preserve known execution.

Disposable adapter: cached postgis/postgis:16-3.4, no pull, fresh UUID/ownership label,
network none, private Unix socket, generated credentials, non-root/read-only/cap-drop,
bounded tmpfs/CPU/RAM and fixed in-container lifetime. No owner profile/address used.
Both actual fixture workflows passed: CSV preflight/import/export (all 3 checks),
vector inspect/load/validate (both checks); cleanup removed both containers. Separate
short-lifetime test proved automatic container expiry/removal. No fixture containers
remain in the final read-only label inventory. Host-crash scratch leftovers remain a
documented limit; this is Linux/Docker evidence, not cross-platform certification.

Verification so far: 129 focused runner/suite/compatibility/layer checks passed;
87 final lifetime/boundary checks passed. Strict source gate: 622 modules/3055 imports,
zero debt. Compatibility: 505 native, 290 retired/117 public, zero errors.
Full source-only CI/GitHub/frontend-required make test: **2,917 passed**, 13 existing
spatial warnings, **809.40 seconds**; log /tmp/actioncharter-b4-full-retry.log;
snapshot /tmp/actioncharter-b4-clean-7xe883lf. First attempt was externally terminated
(signal 143, about 32%, no reported test failure); it is not counted as a pass.
Source export excludes owner config, private data/state and `.claude/`; current
production Python and fixture bytes match the completed snapshot. Final context
checks: 15 passed; all 380 local documentation links resolve; diff whitespace clean.
No frontend changes, no extra interface/browser run; no actual Ollama calls.

Logs: /tmp/actioncharter-b4-gates.log, /tmp/actioncharter-b4-boundaries.log,
/tmp/actioncharter-b4-db-final.log, /tmp/actioncharter-b4-lifetime.log.
DB smoke state: /tmp/actioncharter-b4-db-7o65xfyn/state/benchmark-runs/.
Temporary generator/debug scripts are not source and should not be rerun.

Next: owner can run the documented fixture CLI checks and integrate B4.
Then B5 actual model baseline; M1/M2, M3c, B6 and X remain. Phase 1 is not complete;
no new agent/skill, learning or unrestricted execution added.

---

# Work resume — P1-B2/B3 implemented and verified (2026-11-13)

Owner authorized B2/B3 together on pending B1 changes. All B1 changes preserved;
main remains c03f11d. No overlapping PR/task found. Tracking: #86 B1, #87 runner,
#88 checks. Owner manages all Git actions; no branch/stage/commit/push/merge performed.
[Benchmark guide](../docs/BENCHMARKS.md) owns commands, scope and limits.

Runner: benchmark list/run CLI, per-task process/project/state, staged input hashes,
minimal context, shared Planner/save/review/authorize/run/Critic services. Expected
answers are withheld from prompts. All injected clients share the call budget;
worker deadline/Ctrl+C stops the process group and preserves uncertain state.
Synthetic writes require explicit CLI opt-in plus normal exact authorization;
local-data tasks skip unless explicitly included and cannot enable fixture writes.
Local models only until M1/M2. Database/services/shell/install/code generation are
not admitted. This is fixed-process containment, not a container/MicroVM sandbox.
Immutable content-free results and private raw task state use benchmark-runs through
the existing workspace resolver. Separate Critic status, counts, tokens/resources,
retry/timeout observations and source-version provenance (null if unavailable).

B3 checks actual completed outcomes: columns/explicit step, integer row counts,
finite numeric tolerance, output hash+receipt, exact committed PostgreSQL/PostGIS
validation receipts and deterministic refusal with zero operations/outputs. Missing,
ambiguous or tampered evidence cannot pass; no DB queries or model scoring. Gold-set
scoring and disposable DB execution adapters remain future suite work.

Verification: full source-only CI/GitHub/frontend-required make test: **2,903 passed**,
13 existing spatial warnings, 777.77 seconds. The full snapshot preceded the final
localized diagnostic/staging-budget/column-selector refinements; **117 final focused
current-source checks passed** (27.79 s), including B1, B2/B3, R7 snapshots, R11 and
layer checks. Those cover two added boundary cases after the full run. Strict gate:
621 modules/3049 imports, zero debt. Compatibility: 504 native, 290 retired/117 public,
zero errors. Installed CLI fixture smoke passed in a disposable project.
Final context checks and 370 local documentation links passed. An unrelated
untracked .claude/ appeared during this turn; left untouched and outside task scope. All endpoint
checks use a fake local server; no real-model performance/quality or live DB claims.
No frontend changed; interface/browser checks not repeated.

Owner validation confirmed by read-only evidence inspection: run a476845b8c32437dacf9d01ce55526c4
is complete, one fixture task passed, one operation, 3 rows/3 columns. Saved result
matches summary/current definition; both checks independently recomputed as passed;
summary hash unchanged. Fresh disposable CLI fixture passed; 78 contract/runner
checks passed (15.46 s). No owner run was replayed, authorized or modified.
Log: /tmp/actioncharter-p1b23-owner-validation.log.

Next: owner can integrate B1–B3; fixture verification needs no repetition. B4 expands tasks/disposable DB
adapters; B5 measures actual local-model baseline. M1/M2 providers/egress remain.
Phase 1 is not complete; no new roles, permissions, data operations or learning added.

Logs: /tmp/actioncharter-p1b23-full.log; /tmp/actioncharter-p1b23-final-gates.log;
/tmp/actioncharter-p1b23-cli.json. Source-only export:
/tmp/actioncharter-p1b23-clean-4aeis4wy. Temporary test logs are not source records.

---

# Work resume — P0-C1–C4 implemented and verified (2026-11-13, #84)

Owner authorized all P0-C tasks. Started on clean main at 20b7a38 (PR #83 merged).
[Tracking #84](https://github.com/wanggiya/action-charter/issues/84),
[closeout guide and frontend acceptance](../docs/P0_CLOSEOUT.md).

P0-C1: owner had already completed stable-ID workspace adoption. Read-only verify
reported seven empty legacy folders; removed only these empty folders. Now
source_only=true, no legacy entries, migration complete, changed_since_migration.
No record moved/edited/deleted; no new backup/cutover or rollback performed.

Follow-up: owner could not locate the notice. Read-only GETs to both running ports
8765/5173 returned 73 valid + one policy-rejected record. The notice was below
the long Saved plans list. Moved labelled notices directly below Refresh records,
before both lists; browser checks now require that order and visibility without
scrolling. Frontend validation and the updated isolated browser journey passed
(zero page errors/approval/execution calls). The running frontend serves the notice
component. No owner records or backend logic changed in this follow-up.
Logs: /tmp/actioncharter-p0c-notice-interface.log and
/tmp/actioncharter-p0c-notice-browser.log; screenshot:
/tmp/actioncharter-p0c-saved-records.png.

P0-C2: shared display inventories isolate malformed/unsafe/policy-rejected recipes,
plans and approval/link records, preserving valid entries. Saved records/Advanced
show bounded blocked diagnostics and all-invalid states without actions. Matching
bad plan evidence blocks the definition link. Approval/execution and CLI authority
inventory remain strict. No new agent, operation, CLI command or Phase 1 feature.
All 74 owner recipe hashes unchanged: 73 valid + one blocked format mismatch.
R8 historical snapshot bytes preserved; two intentional display coordinator AST
expectations recorded explicitly in the existing test. No blanket snapshot update.

P0-C3: verified PR #65 delivery. #60 already closed; closed #61–#64 as completed.
No other issue closure. P0-C4: working-method/status/roadmap/README/CHANGELOG updated;
former status overview preserved with rebased links and source hash in STATUS_HISTORY.
PR #82 supplies owner-reported overall R-series acceptance; individual traces and
optional live write checks are not invented. PA1/PA2 remains owner data-only work.

Verification:
- Source-only exported make test with CI/GitHub/frontend-required flags: **2,827
  passed**, 13 existing spatial warnings, 769.57 seconds.
- Final seven inventory cases passed, including corrupt matching-plan assertions;
  48 final focused inventory/HTTP/compatibility/context checks passed. All 392 local
  documentation paths resolve; original overview/history preservation verified.
- Frontend typecheck/build passed (existing chunk-size warning); strict layer and
  compatibility checks passed (zero debt/errors; 290 retired, 117 retained).
- Final isolated stable-ID/relocated-state browser/API journey passed: valid/invalid/
  all-invalid lists and long-filename containment; unchanged fixture files; zero approval/execution calls/page errors.
  No owner browser profile/cache or live service used. This is fixture evidence,
  not a new real-local-model benchmark.

Next: owner restarts usual launcher and reviews Saved records + valid recipe in
Advanced, then handles Git integration. No stage, branch, commit, push or merge
performed. Phase 0 consolidation exit checks passed; P0-C2/C4 acceptance/merge is
still pending. After merge begin PHASE_1_PLAN: P1-B1 benchmark contracts and P1-M1
provider foundations in task-sized work, not automatic Phase 1 expansion here.

Logs: /tmp/actioncharter-p0c-full-final.log,
/tmp/actioncharter-p0c-final-inventory.log, /tmp/actioncharter-p0c-interface-final.log,
/tmp/actioncharter-p0c-browser-final.log. Screenshot: /tmp/actioncharter-p0c-recipes.png.
Source-only export: /tmp/actioncharter-p0c-clean-cvp67mbc; pre-edit snapshots:
/tmp/actioncharter-p0c-before. Temporary logs are not durable source records.


---

# Work resume — PR #83 fixture-path fix verified (2026-11-13)

Current authorized scope: repair PR #83 CI only, on `cleanup/p0-closeout` at
`835f09d`; initially clean. No Git mutations, live-data changes or further migration.
The push and PR Python jobs both fail the same six tests. Two fixture helpers still
read `PROJECT_ROOT / "skill-definitions"`, removed by this PR's runtime cleanup.
Canonical YAML copies remain byte-identical in `examples/extension-lifecycle/`.
Update those two test helpers, retain every assertion and removed runtime marker.
Other source/test references already use canonical examples. Do not implement the
separate P0-C2 inventory bug or Phase 1 work in this fix.

Applied only two fixture-path changes; all 28 `assert` ASTs and existing rejection
checks remain unchanged. Six previously failing cases pass. Canonical YAML bytes
match the deleted historical copies exactly. No other test/script source-fixture
references to those root paths remain.

Full verification: exported tracked HEAD source plus these uncommitted changes to
`/tmp/actioncharter-pr83-clean-9octmjb6`, excluding local config/private data/runtime
records; reused existing Python/Node dependency links, verified imports use exported
source. `CI=true GITHUB_ACTIONS=true NO_COLOR=1 ACTIONCHARTER_REQUIRE_FRONTEND_TESTS=1
make test`: **2,820 passed**, 13 existing spatial warnings, 774.85 seconds. This
checks the source-only state without leftover runtime copies masking failures.
No new backend/frontend feature or test skip; no production/schema/authority change.

Next: owner stages the two test files plus CHANGELOG/WORK_RESUME, commits/pushes the
current branch and watches new PR #83 checks. Old checks still refer to 835f09d;
GitHub must receive the fix before rerunning can verify it. Keep Git commands in
conversation. No Git mutation or live state/database/service change performed.
Snapshot: /tmp/actioncharter-pr83-before.
Failure logs: /tmp/actioncharter-pr83-python.log and /tmp/actioncharter-pr83-push.log.
No previous edit or full run was repeated after the coding server restart.
Full run log: /tmp/actioncharter-pr83-full.log; focused: /tmp/actioncharter-pr83-focused.log.

---

# Work resume — Phase 0 closeout, then Phase 1 (2026-11-12)

R-series merged (PR #82, `8a509dd`). Owner workspace cutover done: stable project ID
`7b3e2655-…`, state root `~/.local/share/actioncharter/workspaces/geoagent-skill-harness/state`,
backup `~/.local/share/actioncharter/backups/geoagent-skill-harness/20261112T205838Z/`
(checkout.tar verified, three dev sessions with 6 links preserved). `workspace-verify`:
`changed_since_migration` (expected after launch), `source_only: true`.

Pending in the working tree: 12 runtime-marker deletions from the cutover (expected;
canonical skill definitions remain in `examples/extension-lifecycle/`) → task P0-C1.

Known bug found after cutover (pre-existing, not caused by it): `GET /api/v1/recipes`
returns 503 because one stored recipe (`planner-d53f96031ec0276c…`, 2026-11-02,
`inspect_vector` on `sample_orders.csv`) fails the current format policy and the
inventory is all-or-nothing. 73 of 74 recipes valid. → task P0-C2. Do not edit or
delete the stored file.

Next: follow [PHASE_1_PLAN.md](../docs/product-direction/PHASE_1_PLAN.md) — section 0
(P0-C1…C4), then lanes A (benchmark) and B (model providers) in separate worktrees.

# Work resume — PR #82 console snapshot fix verified (2026-11-12)

Owner pushed prior fixes as `f540793`. GitHub GIS/agent/skill-runner/Compose and HTTP
snapshot checks now pass. Only R7 exact CLI help snapshot fails, identically in push
and PR jobs 131030032204 / 131030055964. Scope remains PR #82 only; do not work on #79
or unrelated tasks. No Git mutations authorized; owner commits/pushes manually.

Cause reproduced exactly: `GITHUB_ACTIONS=true` makes Typer's import-time
`FORCE_TERMINAL=True`; Rich formats help at 80 columns instead of the snapshot's
120, despite CliRunner's COLUMNS/terminal_width arguments. Local hash c09b9a...;
GitHub/reproduction hash c0fb1095... matched. Prior verification pinned dependencies
but did not simulate GitHub's import-time console environment.

Fix is test-only: scope Typer FORCE_TERMINAL=False and MAX_WIDTH=120 to the snapshot
fixture via monkeypatch. Do not change saved snapshots, CLI production behavior or
workflow flags. New subprocess regression starts with CI/GITHUB_ACTIONS, forced
colors and TERMINAL_WIDTH=77 before imports and checks all 165 original help screens.
Focused hostile-environment R7/R8 checks: 17 passed. Fresh-dependency container
checks also passed: 17 in 12.96 seconds, with CI/GITHUB_ACTIONS enabled and no
network during tests. Full suite under CI/GITHUB_ACTIONS/NO_COLOR/frontend-required
flags: **2,820 passed**, 13 existing spatial warnings, 791.15 seconds. Strict
source/compatibility gates passed with zero errors; historical help snapshot bytes
remain unchanged. No frontend/application/CI workflow or dependency change in this
follow-up. Only the R7 test and documentation changed.

Next: owner commits/pushes the four modified files on the current branch, then watches
new PR #82 checks. The old f540793 checks remain red until a new commit is pushed;
rerunning old-source checks does not include this fix. Keep Git commands in the
conversation. No staging, commit, push, merge or issue operation was performed.
Logs: `/tmp/actioncharter-pr82-help-repro.log`, `/tmp/actioncharter-pr82-console-focused.log`,
`/tmp/actioncharter-pr82-console-full.log`, `/tmp/actioncharter-pr82-console-fresh.log`.
Snapshots of this slice: `/tmp/actioncharter-pr82-console-before`.

---

# Work resume — PR #82 CI fixes verified; owner Git actions next (2026-11-12)

Owner requested PR repair and Git instructions, explicitly excluding #79 and unrelated
issues. Branch `cleanup/r-series-consolidation`, starting head `a1f0094`; initially
clean. PR #82 is mergeable but blocked by CI. No branch/stage/commit/push/merge action.

Three observed causes in latest runs (43166189091 / 43166189074):
1. CI resolved Typer 0.29.1 / Click 8.5.1; frozen CLI parameter/help contracts were
   captured with Typer 0.27.0 / Click 8.4.2 / Rich 15.0.0. Pin that verified toolchain.
2. R8 catalog snapshot embeds installed versions, e.g. psycopg 3.3.4; CI has 3.3.8.
   Fix only probe metadata using its original fixture. Production inventory stays
   live; regression test checks differing host metadata, preservation and restoration.
3. GIS `--read-only` fixture cannot create `/workspace/workflow-state` for action
   audit. Add isolated 16 MiB tmpfs, mode 0700 and UID/GID 1000, only to GIS CI runs.
   Preserve non-root, no network, no capabilities and read-only source/input policy.

Focused R7/R8 checks: 16 passed. New disposable GIS image built with fresh dependencies;
all five actual YAML GIS commands passed against copied public vector/raster fixtures,
including conversion planning without output and controlled path-escape rejection.
Final verification:
- `make test`: 2,819 passed, 13 existing spatial warnings, 805.69 seconds.
- Fresh-image CLI/HTTP checks: 16 passed in 7.26 seconds, with Pydantic 2.14.3 and
  psycopg 3.3.8 (the CI versions) alongside the pinned CLI toolchain.
- All five actual hardened GIS YAML commands passed; no output raster created.
- `make interface-validate` passed (existing chunk-size warning only).
- Strict layers: 614 modules / 3021 imports / zero dependency debt; compatibility:
  290 retired / 117 public boundaries / zero errors. Historical CLI/HTTP snapshots
  are byte-identical to HEAD. YAML, dependency pins, doc links and whitespace passed.

Next: owner reviews/stages the eight modified files, commits and pushes the current
branch to update existing PR #82, then watches the new remote checks. Local fixes
are verified; the unchanged old remote failures remain until that push. PR is
mergeable (no merge conflict) but blocked on those checks. Existing PR description
explicitly keeps #79 separate and does not auto-close it. No new issue/PR is needed.
Keep actual Git commands in the conversation, not in documentation.
Logs: `/tmp/actioncharter-pr82-full-tests.log`, `/tmp/actioncharter-pr82-gis-build.log`,
`/tmp/actioncharter-pr82-gis-contracts.log`, `/tmp/actioncharter-pr82-fresh-contracts.log`.
No owner environment install or existing service/database change. The disposable
`actioncharter-pr82-gis-test:local` image is a test artifact, not a deployment.
No workspace configuration, identity, migration or #79 code changed.

---

# Work resume — recorded inspection quality reports ready for owner validation (2026-11-11)

Export-control follow-up: fixed the 8 px vertical offset between report format and
Download workflow report. A scoped CSS margin reset preserves both 38 px heights.
Isolated browser checks: MD/PDF, outline/solid, 1000/640/360 px widths; zero offset
when on one row, existing narrow wrapping retained. Frontend typecheck/build passed.
CSS-only follow-up; backend suite evidence below belongs to the prior implementation.

Current task: P0 report-completeness bug [#81](https://github.com/wanggiya/action-charter/issues/81),
created with explicit owner permission. Implementation/automated verification done;
owner real-file report acceptance remains pending. [Scope, budgets and exact manual
steps](../docs/INSPECTION_QUALITY_REPORTS.md). This is a demonstrated Phase 0 bug,
not a new statistical/agent phase. Preserve all pending R1–R12/P0-2b and owner work.

Cause: completed diabetes run `3a7eac1962b741e6b3a9448324fc1f03` recorded 101,766
rows/50 columns using only a path argument. It had missing counts/types but no
analytical profile; the report path ignored metadata-only facts. Interface Report
also assumed readiness evidence, and could retain an early report after completion.
The owner run was inspected read-only; no original source/run/report was rewritten.

Delivered: bounded one-pass distinct/once-only/repeated/excess value counts,
hash-based whole-row duplicates, candidate markers, numeric count/mean/min/max/sample
SD. Shared output/report module `data/tabular/basic_profile.py`; candidate numerical
moments reuse guidance. Exact counter limits: 500k entries / estimated 64 MiB;
overflow means unavailable, not partial/exact or zero. Ordinary outcomes stay 16 KB.
Legacy reports show saved facts and explicit not-calculated checks. Readiness adds
basic appendix within budget; workflow handoff retains it when omitted there. UI
metadata Report uses shared handoff and refreshes on run status changes. Existing
MCP/CLI/terminal/report-operation paths reuse the same projection. No new public
operation/schema, model call, agent role, execution authority or inferred P-value.

Verification (fixtures/fake models):
- `make test`: 2,816 passed, 13 existing spatial warnings, 785.18 s. Collected the
  initial eight new cases; final focused 10 cases also cover redaction/MCP parity.
- Final focused broader set: 75 passed; final report set: 10 passed.
- `make interface-validate`: passed, existing chunk-size warning only.
- Strict layer/compatibility checks: 614 modules / 497 native / 3021 imports,
  zero debt/errors; 290 retired / 117 public boundaries retained. Historical
  retirement manifests/contracts preserved; module census updated for one new owner.
- Stable-ID + relocated-state isolated browser/API/CLI/PTY passed, zero page errors;
  basic report MD equals CLI report, PDF works, downloads cause no execution/analysis.
  Uses temporary profile and project-local browser dependencies; no normal cache.
- Synthetic 101,766 rows/50 columns: all 50 profiles, 101,766 distinct encounters,
  50,883 repeated entities; 7.47 s direct scan, 15,286 compact bytes, peak process RSS
  57,448 KiB. Not a real-data/model/comparative benchmark.
- 374 local doc links and whitespace checked. Full test log:
  `/tmp/actioncharter-report-completeness-tests.log`; browser log:
  `/tmp/actioncharter-report-browser.log`. Slice snapshots: `/tmp/actioncharter-report-before`.

Next: owner restarts usual launcher, newly inspects `test/diabetic_data.csv` read-only,
checks Outcome → Report → MD/PDF for source/rows, missingness/markers, cardinality,
duplicates and numeric summaries. Reopen the old run: missing checks must remain
not calculated; no refresh-time computation. Interpretive goals and actual
inferential methods remain the existing explicit analysis path, not invented report
content. Keep issue #81 for owner acceptance. Other Phase 0 manual acceptance and
real workspace cutover below remain separate; this fix does not close them.

No Git stage/commit/push/merge, installs, secret edits, live DB/service changes or
real workspace migration. Previous independent handoff/environment/Git notes below
are preserved history/follow-ups, not actions authorized or executed here.

---

# Work resume — R-series acceptance closeout; two owner checks remain (2026-11-10)

Current task is documentation/acceptance closeout, tracked under existing R11 #80.
Owner confirmed the six-step startup/read-only `sample_orders.csv`/refresh recovery
journey passed. Record as OWNER-REPORTED, not agent-observed or benchmark evidence;
no chat/run ID, model or timing provided. Two required manual checks remain:
Execution History navigation and frontend/terminal continuity. Fresh-file write test
optional and NOT manually tested. No new R-series coding task unless an actual
regression appears. See docs/R_SERIES_ACCEPTANCE.md#acceptance-record for exact steps.
Real backup/cutover #79 remains unapproved/unperformed, separate from R-series
manual closure. Phase 0 source-only-root gate still open. No Git/package/runtime
changes authorized by this documentation task; preserve all existing pending work.

2026-11-10 doc review rechecked source/compatibility gates (613 modules, 3016 imports,
290 retired/117 retained, zero debt/errors) and read-only local install metadata:
both geoagent-skill-harness 0.1.0 and actioncharter 0.9.0 records; no venv actioncharter
console script; repository ./actioncharter exists. Existing environment/Git notes below
are preserved follow-ups, not instructions executed in this task. Do not refresh the
environment or expand R-series scope without a request. Prior independent test evidence
below is preserved; no full suite/frontend/browser repeat for doc-only edits.
Documentation audit passed: 50 changed/new Markdown files, 620 local links and 183
fragments; roadmap 17,194 bytes, whitespace clean. No code or runtime changes.

Handoff for the next agent. Read-only verification plus test runs; nothing committed,
pushed, migrated or changed in code. Branch `main` (`fe15a33`, PR #65 merged), with all
R1–R12, P0-5b and P0-2b work **uncommitted**: 755 changed files (+4,488/−72,734) and
529 untracked files. No open PR.

## Verification (re-run independently on 2026-11-10, fixture tests)

| Check | Result |
|---|---|
| `make test` | 2,808 passed, 13 existing spatial warnings, 790 s |
| `scripts/check_import_layers.py --strict` | 613 modules, 0 upward dependencies, baseline passed |
| `scripts/check_compatibility.py` | 290 retired, 117 retained public, 0 errors |
| `make interface-validate` | typecheck + build pass (chunk-size warning only) |
| `bash -n scripts/start_actioncharter.sh`, `docker compose … config --quiet` | pass |
| Wheel build | builds; contains `apps/` (621 files) |
| Secret pattern scan of diff + untracked files | nothing found; `.env`, `.secrets` ignored. gitleaks not installed — run it before pushing if available |
| Root runtime folders | still present (cutover pending) but git-ignored; none appear untracked |

Status: R-series automated work complete. Owner startup/read-only/recovery passed;
only history and terminal continuity remain required in manual acceptance
([R_SERIES_ACCEPTANCE.md](../docs/R_SERIES_ACCEPTANCE.md)) and the real workspace
cutover ([OWNER_WORKSPACE_CUTOVER_PLAN.md](../docs/OWNER_WORKSPACE_CUTOVER_PLAN.md),
#79). Phase 0 exit "repo root contains source only" is not met until the cutover.

## Fix before Git

1. Stale local install: `.venv` has two dist-infos (`geoagent_skill_harness-0.1.0`,
   `actioncharter-0.9.0`); `.venv/bin/geoagent` still points to `geoagent_harness.cli`
   (works only through a retained compatibility path); `actioncharter` command missing.
   ```bash
   .venv/bin/pip uninstall -y geoagent-skill-harness actioncharter
   .venv/bin/pip install -e ".[dev]"
   ```
2. Issues #60–#64 still open although delivered in PR #65:
   `gh issue close 60 61 62 63 64 -c "Delivered in PR #65"`

## Git plan (owner runs or explicitly asks an agent to run)

Push to a branch now (backup + CI); merge only after owner manual acceptance.

```bash
# stop other agents working in this folder first
git switch -c cleanup/r-series-consolidation
git add AGENTS.md context docs CHANGELOG.md README.md
git commit -m "Record R-series decisions, showcase workloads and model-participation policy"
git add -A
git status   # only src/, tests/, scripts/, interface/, config; no data/runtime folders
git commit -m "R-series: layer boundaries, platform config, storage/ledger contracts, CLI/HTTP split, execution context, compatibility cleanup, stable project identity

Closes #66 #67 #68 #69 #70 #71 #72 #73 #74 #75 #76 #77 #78 #80"
git push -u origin cleanup/r-series-consolidation
gh pr create --base main --title "R-series consolidation (R1–R12, P0-5b, P0-2b identity)" \
  --body "make test: 2,808 passed locally (fixture tests). Layer check 0 violations; compatibility 0 errors; frontend build OK. Owner manual acceptance and real workspace cutover pending."
gh pr checks --watch
```

Then: owner runs R_SERIES_ACCEPTANCE.md on the branch → fix on the same branch if
needed → `gh pr merge --merge --delete-branch` → `git switch main && git pull && git fetch --prune`.

- #79 (P0-2b) intentionally not in "Closes": real cutover not done.
- Stale remote branch `origin/cleanup/phase0-structure` (merged in #59) can be deleted:
  `git push origin --delete cleanup/phase0-structure`; consider
  `gh repo edit --delete-branch-on-merge`.

## Next after merge

1. Real workspace cutover per OWNER_WORKSPACE_CUTOVER_PLAN.md (backup first; needs
   explicit owner approval). Then close #79 and mark Phase 0 done in WORKING_METHOD.md.
2. PA1: owner archives governor/senator sources (data only, `data/input/`, manifest with
   URL, time, SHA-256) — see [SHOWCASE_WORKLOADS.md](../docs/product-direction/SHOWCASE_WORKLOADS.md).
3. Phase 1: benchmark (tasks from showcase workloads H, E1/E3, PA gold set, G1) and
   model providers M1–M2 ([MODEL_PROVIDERS_PLAN.md](../docs/product-direction/MODEL_PROVIDERS_PLAN.md)).
   One branch and one PR per task from then on.

Recent direction decisions (2026-11-05/06), all in `docs/decisions/`: server autonomy,
showcase workloads and Personal/Platform editions, model participation in authorization
(experimental model approver, Phase 7 shadow / Phase 8).

# Work resume — owner cutover preparation ready; approval pending (#79)

2026-11-09. Current scope: prepare/review only; NO real backup, archive, identity
adoption or migration authorized/performed. Existing P0-2b issue #79 reused; no new
issue/PR. Overlap check: no open PR; #79/#80 remain open, branch main. All existing
R1–R12/P0-2b and owner changes preserved. No Git/secret/live-service changes.

Plan docs/OWNER_WORKSPACE_CUTOVER_PLAN.md. Read-only real inventory: legacy_path,
source/state both current checkout, no config or identity marker. 44 runtime roots,
2,129 regular files, 526 dirs, 27,742,154 bytes /26.46 MiB; six symlinks in these three
.local/interface-acceptance sessions: 20261005T174714Z-7330e5bf,
20261005T235717Z-bb7882a9, 20261006T022502Z-4dfd6a45. Each links .venv and
interface/node_modules to real dependency directories. Do not dereference/delete them.
No hardlinks/special/unreadable entries. Existing migration preview rejects links.
No identifier references outside those sessions across 740 regular runtime files.

Three SQLite DBs (tasks, write-policy, successful-workflows) passed immutable read-only
quick_check; no sidecars observed, metadata stable. Eight stored locks not held,
project lease absent. No listeners 5173/8765; no matching Compose working-dir-label
containers. These observations do NOT certify all custom/remote writers stopped.
.env root keys were examined by NAME only, no values disclosed/changed; host launcher
excludes them from its allowlist. No inherited overrides in this inspection. Recheck
actual launcher exports. Credential files under .secrets/.aws were not opened. Runtime
bytes were screened only for the three session IDs; no chat payloads or configuration
values were disclosed.

Proposed active state /home/jay/.local/share/actioncharter/workspaces/geoagent-skill-harness/state;
backup /home/jay/.local/share/actioncharter/backups/geoagent-skill-harness/<unique-id>/.
Not created. Nearest existing parent same filesystem, ~35.34 GiB free; reserve/recheck
256 MiB for measured snapshot. Plan: stop writers, verified independent no-follow backup,
preserve WHOLE three dev sessions separately, clean preview, UUID adoption + metadata
backup, verified migrate --archive-legacy, verify BEFORE launch, then owner smoke test.
Rollback automatic only while unchanged/prelaunch; preserve newer work after startup.
12 tracked runtime markers/files would move; Git left to owner.

Synthetic TEMP fixture (44 root names, 3 fake DBs, 3 fake sessions/6 links) passed link
rejection, archive preservation, stable adoption, copy/verify/archive exact_copy/source_only,
immediate guarded rollback and UUID/evidence preservation. No real record copies or
operation execution. Code/tests unchanged; no repeat full suite/frontend needed for
this documentation/read-only slice. Prior R11: 2,808 tests (859.92 s), frontend/browser
passed; owner manual acceptance still pending. Phase 0 NOT complete.
NEXT: owner review/approval of exact cutover plan/paths and preservation actions. Do not
perform cutover merely because preparation was approved. Re-inventory before any real
copy. Temporary reports /tmp/actioncharter-cutover-{inventory,checks,references,rehearsal}.json
are volatile; essential facts are in the durable plan. Final documentation audit: 50
changed/new Markdown files, 610 local links / 176 fragments pass; roadmap 16,911 bytes;
whitespace clean. Config/identity/audit DB files absent and proposed destinations not
created. No Phase 1/new features started.

Earlier implementation evidence follows for continuity.

# Work resume — R11 verified; combined owner acceptance next (#80)

2026-11-09. https://github.com/wanggiya/action-charter/issues/80 (owner approved).
R11 implementation + required automated gates COMPLETE with supported-compatibility
scope. 290 obsolete adapters removed; 117 supported boundaries retained (60 public
package roots, 57 aliases); all 496 native implementation modules remain. Strict:
613 modules / 3016 imports, zero upward/dynamic debt, no ordinary native legacy callers.
Historical R6 inventory unchanged; r11_compatibility.json partitions all 407 records
and binds unchanged schema/CLI/HTTP/MCP/registry/generated-SDK contracts. Source gate
rejects restored/unclassified aliases and new implementation under old public roots.
Maintained callers, package entrypoints and launchers use native owners. Minimal native
worker image context passes -I -S profile check with fake Docker; SDK loader retains
reserved old namespaces. No actual image build or live-service validation.

FINAL make test: 2,808 passed, 13 existing spatial warnings, 859.92 s (14:19), session
67131 exit 0, /tmp/actioncharter-r11-resumed-full.log. The interrupted earlier run and
/tmp logs were unavailable on resume; no final result claimed for that run. Fresh
frontend passed (5.44 s build; existing bundle warning), resumed-interface log, session
8756 exit 0. Fresh stable-ID relocated browser/API/CLI/terminal passed, zero page
errors and one authorized TEMP write, resumed-browser log, session 50160 exit 0.
Both log prefixes /tmp/actioncharter-r11-. Static compatibility and strict gates pass.
Earlier final focused group 87 passed; 15 new R11 cases. Three obsolete adapter-only
parameter rows replaced by exhaustive retirement coverage. Functional, schema and
authority assertions preserved. All evidence is TEMP fixtures, not actual local-model/
live-DB acceptance. No production changes after source freeze during this rerun.
Final documentation audit: 49 changed/new Markdown files, 602 local links and 176
fragments pass; roadmap 16,723 bytes <64,000; whitespace clean. Owner identity/config
and both action-audit DB files remain absent after all tests.

Guides: docs/R11_COMPATIBILITY.md + docs/R_SERIES_ACCEPTANCE.md; decision
2026-11-09-r11-public-compatibility.md. Do NOT claim literal zero shims. R-series
implementation/automated gates complete under the owner's approved public/historical
compatibility requirement. NEXT: owner combined manual acceptance from that guide;
restart launcher first to load native modules. Owner real backup/adoption/cutover is
SEPARATE explicit scope, still pending. Phase 0 NOT complete: source-only real-root
exit and owner acceptance remain. Do not start Phase 1, new agents/features or real
model benchmark work until owner direction and remaining Phase 0 gates are settled.
No Git stage/commit/push/merge, secret changes, live DB/service changes or real migration.
Preserve all pending R1–R12/P0-2b and owner designs. DO NOT rerun one-time rewrite or
removal scripts; future compatibility changes require explicit partition review.

Previous completed task evidence follows for continuity.

# Work resume — P0-2b local identity verified; R11 next (#79)

2026-11-09. https://github.com/wanggiya/action-charter/issues/79 (owner approved).
Local stable identity implemented: shared UUID/source/state object resolver, offline
adoption/rebind CLI, UUID write-owner scope, immutable legacy audit-scope provenance,
verified state cutover/guarded rollback. No owner workspace adoption/migration, secrets,
live service/DB or Git mutations. Preserve pending R1–R12 and owner designs.

25 new identity cases; focused existing regression group 208 passed; final identity/
CLI/container group 37 passed in 8.97 s. Initial focused fixture HTTP socket hit sandbox;
permitted rerun passed. Original CLI snapshot preserved; fixture owner-FD wrapper
forwards explicit scope while retaining checkout isolation. Strict 903 modules / 3305
imports, zero upward/dynamic debt. Frontend passed (4.59 s build, existing warning).
Final make test PASSED: 2,796 tests, 13 existing spatial warnings, 816.47 s (13:36),
session 50384 exit 0, /tmp/actioncharter-p02b-full.log.
Relocated legacy browser passed /tmp/actioncharter-p02b-browser.log; stable-ID browser
passed /tmp/actioncharter-p02b-stable-browser.log, zero page errors and one explicitly
authorized TEMP write each. Optional ACTIONCHARTER_TEST_STABLE_IDENTITY exercises
adoption before fixture API startup. Relative state/source rename disposable check passed.
Automated gates complete; no production changes after full-suite source freeze.
Only the optional stable-ID browser fixture flag was added while Python tests ran.
Real checkout read-only CLI status remains legacy_path, UUID null, authority false;
identity/config and both action-audit DB files absent. Final audit: 46 changed/new
Markdown files, 579 local links / 176 fragments pass; roadmap 16,395 bytes <64,000;
git diff --check clean.

Guide docs/PROJECT_IDENTITY.md and decision 2026-11-09-stable-project-identity.md.
Real owner backup/cutover remains separate explicit owner action. Cross-filesystem
source transfers and container alias provisioning are intentionally unsupported;
legacy deployments unchanged. R11 compatibility/public/stored-reference retirement
review is next. Do not blindly remove the 407 adapters or alter historical digests.
Owner manual combined validation deferred until all R-series work completes.
Phase 0 NOT complete. No new agent/data/UI/autonomy features. Originals in
/tmp/actioncharter-p02b-before. Do not run transition commands on owner checkout.

Previous completed task evidence follows for continuity.

# Work resume — R12 complete; P0-2b and R11 remain

2026-11-09 local date. R12 implementation + required automated gates complete,
issue #78 (owner approved creation): https://github.com/wanggiya/action-charter/issues/78.
Owner manual validation explicitly DEFERRED until ALL R-series work is complete.
Preserve all pending R1–R12/P0-5b and owner AGENTS/design changes. No Git branch/stage/
commit/push/merge/publication, live DB/service, secret or real workspace migration.

Frozen Actor/RunContext/Budget/PolicyDecision contracts; scoped local policy/UTC clock/
no-issue credential broker/context-copying queue and audit ports. 70 fixed task entries,
ordinary CLI/HTTP and ALL 27 MCP ingresses carry context. Original external request/tool
schemas, fixed data-service identities and exact authorization stay intact. Explicit
event keys consume claims before dispatch; uncertain completion never allows replay.
Record links supplement old canonical artifacts without rewriting hashes. Query-only
lookups and standalone proposal-only CLI preserve purity using bounded transient
telemetry (512 events, no data/prompts). Actual processing/mutations/keyed events durable.
HTTP/MCP bind their service profiles explicitly. MCP uses traces/.action-audit through
its existing writable mount; local/controller uses workflow-state. No container mounts
or permissions broadened. Namespaces/source paths do not imply cross-process delegation.

FINAL make test: 2,771 passed, 13 existing spatial warnings, 793.66 s (13:13),
/tmp/actioncharter-r12-final-full.log (session 77441 exit 0). Frontend passed 4.36 s
(existing bundle warning), /tmp/actioncharter-r12-interface-final.log. Final relocated
fixture browser/API/CLI/terminal passed, zero errors, one authorized TEMP write,
/tmp/actioncharter-r12-final-browser.log (session 62288 exit 0). Strict 902 modules /
3,288 imports, zero upward/dynamic debt; 407 adapters (61 package roots), 495 native.
35 new contract cases; MCP/container/context 116, MCP/security 106, recovery/parity 97.
All fixtures, NOT real-local-model/live-DB acceptance. Both checkout audit locations
(workflow-state/action-ledger.sqlite3 and traces/.action-audit/action-ledger.sqlite3)
ABSENT after final suite. Final audit: 43 changed Markdown files / 572 local links / 176 fragments pass;
roadmap 16,143 bytes < 64,000; whitespace clean.

Guide docs/EXECUTION_CONTEXT.md and decision 2026-11-08-action-context-and-local-services.md.
Living docs/status and Working Method Status updated. Durable entry/tool fixtures:
tests/architecture/r12_entrypoints.json (70/20 modules) and r12_mcp_tools.json (27).
Initial suite caught 7 purity/clone/timer regressions; fixed without weakening assertions.
Two hand-copy fixtures now copy audit state; controlled independent evaluation clones
omit source-bound private claims. Thread composition and read-only deployments tested.
21 initial test-only checkout claims preserved at
/tmp/actioncharter-r12-test-audit-preserved.sqlite3 then removed; no original/user ledger
existed initially. Browser now waits Writes: ON and preserves failure diagnostics.
Earlier 2,767/2,769-test gates preceded final MCP/readonly changes; final gate above counts.

NEXT: P0-2b stable project-ID ownership (configuration portion already done); owner's
real offline backup/cutover remains a SEPARATE explicit owner action. R11 compatibility
retirement LAST after callers and required public/stored/generated references are
accounted for; never rewrite historical hashes or blindly delete required paths.
Phase 0 still NOT complete; do not start Phase 1/new agents/data/UI/autonomy features.
Manual combined acceptance stays deferred. R9/R10 reuse delivered P0-3/P0-6.
Originals /tmp/actioncharter-r12-before; DO NOT rerun /tmp/r12_integrate.py or
/tmp/r12_query_boundaries.py against current files.

Earlier task evidence below is history, not active instructions.

# Work resume — P0-5b complete; R12 next

2026-11-08 local date. P0-5b implementation + required automated gates complete,
issue #77 (owner approved creation): https://github.com/wanggiya/action-charter/issues/77.
Owner explicitly defers MANUAL validation until ALL R-series work is complete.
Preserve all pending R1–R8 and owner AGENTS/design changes. No Git branch/stage/commit/
push/merge/publication, live DB/service, secrets or real workspace migration performed.
Phase 0 feature freeze; experimental model approver remains future/off/unimplemented.

Four platform/storage modules define immutable records, attempt/events, closed
write-policy/success-index units and trusted context-scoped provider factories.
22 existing native production clients now use these persistence owners. Domain
schema/hash/scope/redaction/authority checks, local ownership/session leases and
existing SQLite/file layouts remain. Separate immutable evidence from mutable
status/annotation projections. Locks/exclusive create/SQL rollback preserve local
concurrency; uncertain storage never permits replay. No new agent/operation/UI or
remote/distributed backend. 32 canonical/digest helper ASTs + three table-DDL strings
match pre-edit snapshots. Existing test assertions untouched for this task.

Focused integration 127 passed; readers 77; histories/lifecycle 63 (overlapping groups).
27 NEW ledger contract cases + three existing frontend workspace checks pass.
Final make test: 2,736 passed, 13 existing spatial warnings, 750.12 s (12:30),
/tmp/actioncharter-p05b-full.log. Frontend passed, 5.16 s build (existing bundle
warning), /tmp/actioncharter-p05b-interface.log. Relocated fixture browser/API/CLI/
terminal passed, zero page errors, one authorized TEMP write,
/tmp/actioncharter-p05b-browser.log. These are fixtures, not new real-model/live-DB
acceptance. Strict: 897 modules / 3,239 imports, zero upward/dynamic debt; 407
compatibility adapters (61 package roots), 490 native modules. Final links/whitespace
audit: 41 changed Markdown files / 561 local links / 175 fragments pass; roadmap
15,910 bytes < 64,000, whitespace clean. Initial new test used an incorrect schema import; fixed
before final gates. No guard weakened. Session 32648 completed exit 0.

Guide docs/LEDGER_CONTRACTS.md + decision 2026-11-08-specialized-ledger-contracts.md.
R9/R10 criteria reconciled against delivered P0-3/P0-6: shared PostGIS lifecycle stays
in L2 data because it depends on DB inspection; pure policy/ledger below it. App is
48 lines over workspace controllers/store. Do not rebuild either or claim live-DB
acceptance. README/status/changelog/architecture/roadmap/working-method Status updated.

NEXT: R12 explicit actor/run/idempotency context and policy/credential/queue/clock
interfaces with local implementations; no standing server authority. Read current
server design before defining the bounded issue (issue creation needs owner approval).
P0-2b stable project ID + owner real backup/cutover remain separate. R11 compatibility
retirement LAST, after callers and required public/stored/generated references are
accounted for; never rewrite historical hashes. Phase 0 NOT complete; do not start
Phase 1 or add new agent/data/UI features. Manual guide remains deferred.

Temporary /tmp/actioncharter-p05b-before holds originals. DO NOT rerun one-time
/tmp/p05b_*.py extraction or finish scripts against current source. Durable contract
acceptance is tests/test_specialized_ledgers.py; no temporary scripts needed to run it.
Earlier text below is history.

Previous completed evidence: R8 implementation + required automated gates complete, issue #76:
https://github.com/wanggiya/action-charter/issues/76. Owner explicitly DEFERS MANUAL
validation until ALL R-series work is complete. No owner testing required now. Keep
manual guide for combined pass. Preserve all pending R1–R8 and owner AGENTS/design
changes. No Git branch/stage/commit/push/publication, live DB/service, secrets or real
workspace migration. Phase 0 feature freeze; model approver future/off/unimplemented.

Native apps/http: composition 172 lines, transport 84, dispatcher 103, error mapping 133,
ten router areas / largest 198. Explicit immutable roots + trusted public service bindings;
routers import neither server nor other routers. Public interface_api.server exact alias.
24 existing coordinators moved unchanged into six task-action owners; 16 request schemas
and limits into contracts. Two former inline cache/reference operations in existing
execution owner. Same locks/cache, failure scopes, origins/body bounds, selected-model
context, statuses/headers/errors, routes and authority. No new agent/operation/UI/dependency.
Strict graph: 893 modules / 3,209 imports, zero upward/dynamic debt; 407 adapters
(61 package roots), 486 native modules. R11 owns retirement. All six original execution definitions unchanged.

Final make test: 2,709 passed (713.38 s; 13 existing spatial warnings); /tmp/actioncharter-r8-full.log.
Existing API/workspace/action/model/layer group: 146 passed; boundary group: 76 passed,
including ten new cases. All 104 pre-edit request/error responses match; 16 schema digest,
24 coordinator ASTs and four serializer/origin/logging/model-scope method ASTs match.
Frontend passed (6.06 s build; existing warning). Relocated fixture browser/API/CLI/PTY
passed with zero page errors, one authorized TEMP write; /tmp/actioncharter-r8-browser.log.
These are fixtures, not real-local-model/live-DB readiness. Initial HTTP run hit sandbox
socket PermissionError; permitted rerun passed. First probe caught missing ValidationError
import; new cache-failure test caught wrong exception-clause placement. Fixed before
source freeze/fullsuite, no guard weakened. Five existing Critic mock targets and
monotonic clock fixture now patch actual owners; old assertion ASTs all unchanged.

Guide: docs/HTTP_ROUTER_STRUCTURE.md. Decision: docs/decisions/2026-11-08-http-router-ownership.md.
README/status/changelog/architecture/roadmap/working-method Status updated. R6/R7 guides
now explicitly defer manual checks until all R-series work is complete. Final audit:
545 local links / 171 fragments across 39 changed Markdown files pass; roadmap 15,963
bytes < 64,000; whitespace clean.

R8 handoff, superseded above: R9/PostGIS and R10/frontend reuse delivered P0-3/P0-6; do not rebuild them. Trace
R12 actor/run/idempotency/policy/credential/queue/clock seams alongside P0-5b specialized
append-only ledger/concurrency contracts before claiming the next bounded task/issue
(owner approval needed for issue creation). P0-2b stable project ID and OWNER real backup/
cutover remain separate. R11 compatibility retirement LAST after callers and stored/
generated references accounted for; do not delete required public paths or rewrite
historical hashes. Phase 0 not complete; do not auto-start Phase 1 or server autonomy.

Temporary /tmp/actioncharter-r8-before holds old server, two test files, execution and
owner/route/inventory snapshots. DO NOT rerun /tmp/r8_extract.py against current source.
Durable tests/architecture/r8_http_contract.json and tests/http_contract_probe.py preserve
pre-edit evidence. Earlier text below is history.

2026-11-03 bug fix: new-chat filename questions previously omitted required frontend
context diagnostics, so saved clarification appeared as a Zod failure. Complete new
responses and narrowly normalize older clarification chat/receipt responses on read,
without rewriting/replaying. Shared read-only lead-in now accepts do/run/perform and
on/of; trailing actions retain general planning. All 106 focused tests passed; final
make test: 2,327 passed, 13 existing spatial warnings, 621.88 s. Interface validation
and relocated fixture browser/API/CLI/PTY passed, zero page errors. Browser assertions
now check the actual rendered clarification/error absence, not only stored CLI state.
An initial full run was stopped after sandbox-blocked HTTP fixture sockets; permitted
full run passed with no code changes. No real local-model quality claim.
Latest owner receipt was proposal_only with no run; checked read-only. No live mutations.

Active compatibility fix: task-local metadata follow-ups resolve the active source or ask
for a file. Inspector suffix contracts are shared by registry/source routing, plan/graph/
recipe validation and dispatch. Legacy mismatches fail before execution; an explicit
metadata follow-up can create a separately validated compatible proposal. Historical
records/digests are unchanged. Decoder/schema focus preserves stored capability metadata.
53 targeted regressions pass. Final full suite: 2,317 passed, 13 existing spatial
warnings, 693.78 s. Interface validation and relocated fixture browser/API/CLI/PTY
passed with zero page errors. New isolated source tests also pass. Earlier broad runs
exposed capability-metadata regressions and an outdated decoder assertion; corrected. See INSPECTION_SOURCE_COMPATIBILITY.md.
No live records, model settings, secrets or databases changed; no Git mutations.

P0-2 active slice: planning SQLite, legacy chat JSON, saved plans and durable interface-run
history now resolve through the configured workspace. Production readers receive source
project identity explicitly; partial-output recovery uses source data/output. Defaults,
record bytes, digests and explicit low-level root overrides remain compatible. Missing/empty
relocated file stores with legacy records fail closed; no automatic copies or real moves.
External-root fixtures and test-only offline copies pass. Relocated browser/API/CLI/PTY
journey passed with zero page errors, including scoped history and continuation. Final
make test: 2,295 passed, 13 existing spatial warnings, 562.44 s. Interface validation
passed. The preliminary run was interrupted while correcting the authorization fixture;
the final full suite passes. See [storage map](../docs/WORKSPACE_STORAGE.md).
Remaining after that earlier slice: authority/evidence (now implemented above), other lifecycle
stores, verified offline migration/ownership/rollback and source-only-root exit check. Do not configure real relocation
yet. No Git, live-data, secrets or model-setting mutations. User owns issue/branch/PR.
Prior fixes: explicit read-only inspection wording (2,287 tests); execution/Critic status
separation and bounded review setting (2,275 tests). See REQUEST_DIAGNOSTICS.md.

2026-10-30 latest: inspection-led typed analysis goals and report metric coverage.
User chose agent-proposed goals. Planner advises over recorded fields/source; backend
rejects wrong sources/unknown fields/identifier inference. Per-chat goal cards expose
prerequisites/capability gaps, and Prepare uses normal planning without execution.
New readiness reports state calculated/uncomputed metrics; no invented precision or
P-values, no classifier/categorical-test/causal operation added. See
[implementation and validation](../docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md).
Local qwen3.5:9b advice test passed in one call: 67.6067 s, 2,212 prompt /
463 completion tokens, reasoning none, 1,200 output cap. It used saved aggregate
metadata/header-only temporary inputs; this is not fresh-source clinical acceptance.
A generated title remained imprecise, so contract acceptance is not scientific endorsement.
Earlier model failures identified long rationales and numeric methods on category codes;
length-aware structured decoding, role-constrained fields and safe field-specific
correction diagnostics now enforce those boundaries. Focused tests and isolated
browser/API/CLI/PTY pass; interface validation passes. Final permitted make test:
2,254 passed, 13 existing spatial warnings (564.92 s). Focused role-guard tests
pass after decoder tightening. No live data, model preferences or Git mutations.


## Active delivery — 2026-10-29

2026-10-30 latest: Settings → Model service now saves reasoning effort per project
without restart, backend pins request settings and shared client sends actual choice.
Ordinary quality/statistical report requests use inspection + derived Outcome Report;
legacy generate_report requires PostGIS validation and is excluded for unrequested
analytical reports. Explicit legacy reports bind missing task identity before review,
with validation/authority unchanged. Background telemetry independent of parent scope.
Real qwen3.5 report request returned inspect_csv after one correction (66.7773s +
37.1815s), no execution. Do not claim universal/one-shot model reliability. Current
acceptance/limits and operator steps: REQUEST_DIAGNOSTICS.md. Final checks: 2248
tests passed (13 existing spatial warnings), interface validation and isolated
browser/API/CLI/PTY passed. No live DB, environment/secrets edits or Git mutations.

2026-10-30 follow-up: real failed request recorded 22,605 bytes/120.0765 s, model
qwen3.5:9b, reasoning unset, output cap 1024; API peak ~211 MiB and system available
minimum ~3.49 GiB. No proof of model OOM. Numeric-summary wording now keeps analysis;
eligible inspect-only requests use the focused profile. Failure message links directly
to scrollable diagnostics; sent reasoning/default is visible. No hidden config change
or automatic retry. Matched focused-prompt comparison: unset reasoning timed out
at120.1398s; explicit none returned inspect_csv in38.5694s (2827/230 tokens), with
1024 output cap. Recommend explicit operator override, no silent model config change.
Checks: make test 2244 passed (13 existing spatial warnings), interface validation
and isolated browser/API/CLI/PTY passed. Current measurements: REQUEST_DIAGNOSTICS.md.

[Latest request diagnostics](../docs/REQUEST_DIAGNOSTICS.md): content-free per-chat turn/
model-call SQLite records, phase/role, tokens/timing/resource sampling, failure retention,
UI export, CLI/terminal parity and failed first-chat discovery implemented. Existing
model/configuration diagnostics preserved separately. Full-file inspect reproduction
returned one inspect_csv proposal (52.872s, 2835 input/252 output tokens); no execution.
Review cap now 60s bounded by existing model/180s coordinator limits; Single full-source
selection experiment still failed after one policy correction, so do not claim F5
closed or local-model reliability solved. Worker/model/GPU RAM remains unknown.
Earlier lost failures cannot be reconstructed. Verification: 2,237 full-suite tests,
interface validation and browser/CLI/PTY diagnostics/export/refresh passed; final
telemetry/conversation inventory checks 53 passed. No live data, secrets or Git actions.

[Full-data contracts, manual steps and remaining gates](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md).
F1 qualified streaming row-local preparation/ancestor aggregation; F2 typed read-only
PostgreSQL mapping preflight/per-column nulls; F3 disposable full-source roundtrip;
F4 saved analytical/technical handoff across UI/CLI/MCP implemented. Preflight repeats
before import; no authority from context, no live database changes, no Git actions.
Final checks: make test 2,230 passed (13 existing spatial warnings); interface
validation and isolated browser/CLI/PTY including JSON/PDF/handoff passed. Complete
saved-run full-source DB roundtrip reconciled every projected value; final terminal
report history fix passed 18 focused tests; strategy/discovery 27. No live changes.
F5 partial: actual qwen3.5:9b Single/Three planned and executed full-file selection with
all 101,766 records matching; advisory reviews unavailable at the existing 15s budget.
Do not claim complete seven-step real-model reliability or independent Critic success.
See acceptance guide for limits and JSON versus PDF-export support. Existing pandas
joins/calculations stay bounded. Current documents preserve the original plan below.

## Original planning record — 2026-10-29

[Canonical full-data delivery plan](../docs/POSTGRES_DATA_WORKFLOW.md#next-implementation-full-data-analytical-and-engineering-handoff--2026-10-29).
User wants the complete full-source analytical/engineering journey, registered agent
skills, PostgreSQL with a justified table design and analytical + technical documents.
Dependency order F1 full-file selection/filter/null/codebook preparation -> F2 typed
mapping/schema preflight -> F3 create-only disposable DB import/inspect/export -> F4
source-linked analytical report and actual-schema technical handoff -> F5 real-model
Single/Three comparison, UI/CLI/history/recovery acceptance. Blend T03/T04/T05/T13.
Current DB cap 200k rows/64 MiB does not enlarge 10k-row/8 MiB pandas preparation.
Planner/skills choose/propose/interpret; shared services enforce typed execution and
validation; Critic assesses evidence only; registry/MCP/CLI/UI expose the same contracts.
No new permanent agent, arbitrary SQL or permission from conversation/preflight. Keep
sample preliminary; full 101,766-row source is the target. Live DB writes require
explicit permission. At the time of this planning record only documents changed; implementation started with F1
call-path/limit audit, not a claim that future skills already work.

## Readiness assessment/full-data slice — 2026-10-29

Timeout follow-up: quality-only inspect_csv planning now uses the shared bounded
table-inspection-focused-v1 instruction profile instead of ~10 KB of general rules.
Typed schemas/validators and saved-plan authority remain unchanged. Isolated fixture
11,218 message bytes / 3,870 decoder bytes; no actual-model latency claim. Diagnostics
include prompt_profile and the interface shows it on failure. Timeout preservation/
one-call regression added. See linked guide for restart/retry instructions; full CSV
size is distinct from planning context and timeout does not establish context overflow.
Timeout follow-up verification: make test **2,219 passed** (13 existing spatial
warnings), focused planner regressions, interface validation and complete isolated
browser/terminal acceptance passed with zero page errors. Actual model latency remains
unverified; no data execution, model/config switch or automatic retry was added.

[Implementation, scope and manual acceptance](../docs/READINESS_ASSESSMENT_AND_FULL_DATA_TEST.md).
Existing analytical/profile services attach typed readiness-assessment-v1 without new
source reads/model calls: scope/hash, missingness, explicit unknown key/duplicate checks,
mapping coverage, fields and bounded group findings. Pure group percentages now shared
with existing views; complete denominators precede display limits. Outcome Report and
Markdown/PDF reuse existing presentation; compatible statistics/figures included within
budget, omissions explicit, original evidence retained. CLI/MCP share the contract;
inspect-table --report is a fresh read, saved chat /report is not. Existing Planner,
Critic and statistics skill updated; bounded review projection used in Single/Three
roles. Exploration rejects unselected sample substitution after model output.
Full-file read-only reference check passed for 101,766 rows/71,518 patients/30 age-
readmission groups and mean stay 4.395986871843248, quality/mappings/missingness; original
hashes unchanged. Local-model/user acceptance, domain interpretation and full-scale
authorized PostgreSQL/preparation acceptance remain open. Do not substitute the sample
or claim all T03/T04/T05 complete. No Git/live DB changes or new permanent agent.
Final make test **2,218 passed** (13 existing spatial warnings), interface validation,
75 focused source/report regressions and complete isolated browser/terminal journey
(zero page errors) passed; final report-copy tests passed separately. Full-file check
also reconciled all 50 fields and 42 admission/readmission groups. Readiness report
display truncation/statistical appendix omissions are explicit; original complete
groups/statistical evidence retained. No actual-model evaluation repeated in this slice.

## Shared table-source consolidation — 2026-10-29

[Structure, compatibility and repeatability](../docs/TABLE_SOURCE_CONSOLIDATION.md).
CSV/TSV and XLSX/flat-record parsers now emit typed bounded batches to TableInspection,
which owns common preview/counters/guidance/analysis/result assembly. Trusted format
catalog drives suffix policies, registry and relevant Planner reader metadata. New
read-only MCP list_operation_contracts exposes the same registry. Additive validated
table-source-v1 records original identity, selection, sparse observed types/nulls and
explicit analytical string view; old snapshots/digest inputs unchanged. Default
percentile labels now survive CLI/MCP revalidation identically. No new dependency,
agent, Git mutation, image build or live service/database change. Comprehensive Docker
dataset-profile protocol and task-action/request consolidation remain separate work.
User manual acceptance pending. Final make test **2,209 passed** (13 existing spatial
warnings); interface validation, isolated browser/terminal journey (zero page errors)
and minimal worker imports without site packages passed. No model evaluation repeated
for this slice; revised catalog prompt behavior needs manual validation.

## Statistical figures and table-format readers — 2026-10-29

[Combined implementation/validation](../docs/TABLE_FORMATS_AND_STATISTICAL_FIGURES.md).
User manual acceptance of this and previous slices is pending. T05 adds pure recorded
group-mean SVG figures (selected measurement, counts/no CI), coefficient heatmaps with
selection/clear, Report/PDF figures and existing advisory Critic/self-review alongside
Statistics. Caps/omissions explicit; full report tables preserved. No model/source call
on figure or assessment viewing. PDF charts are generated locally from closed escaped
SVG, not user SVG/URLs; tall figures scale to fit landscape pages.
T08 extends stable inspect_csv via a bounded record adapter using existing Accumulator:
XLSX selected sheet/header or cell_range, JSON record arrays/wrapper key, JSONL/NDJSON.
Original hashes/query selection preserved. Native preview/types and separate null/empty
counts; analytics uses explicit string view. Formulas/errors/macros/external links,
nested/new/duplicate JSON keys and unsafe paths reject. New formats require Execute,
never inspect-on-send; CSV transforms remain CSV-only. Reopened/grouped views inherit
the exact source selection; changing it requires a new inspection. CLI inspect-table,
MCP existing tools and relevant Planner schema/skill guidance use the shared contracts.
Declared table-formats/dev deps installed without cache: openpyxl 3.1.5, defusedxml
0.7.1, et-xmlfile 2.0.0. No Docker image rebuild, arbitrary code, Git/publication or live
DB changes. New synthetic text examples under examples/table_formats; XLSX generated
only in temporary tests. Initial browser passed JSON/JSONL/XLSX, figures, PDF and
advisory/history journeys; final verification below after completion. First full suite
had one stale CSV/TSV-only error-message expectation; updated to assert all six formats
while retaining TIFF rejection. Explicit range/scope follow-up tested separately.
Next format candidates: Parquet then T11 text/documents; see open limits in guide.
Actual local-model checks found omitted selectors, stale fields/source and misleading
free prose. Added generic explicit-source/selector/statistical-argument decoding and
independent pre-storage coverage checks, plus strict complete-descriptive proposal mode
when source/fields/design are supplied. No post-generation argument rewriting. New
suffixes also added to existing source-existence reference detection. Final qwen3.5:9b
XLSX and JSONL proposals passed once each (~60/62 seconds); source/fields/means verified
on synthetic temporary data. Free prose remained stale, so bound descriptions now use
validated-argument confirmations and retain sanitized original wording in diagnostics.
Final make test **2,204 passed** (13 existing spatial warnings), focused selector/field/
receipt tests and interface validation passed. Complete isolated browser passed with
zero page errors; new-format executions, PDF/figures, advisory/history/terminal paths
verified. Final figure field-cap caption update was built/typechecked afterward.
Visual review caught inherited global SVG fills; generated figures now preserve their
own encoded colors instead of recoloring background/cells through generic result CSS.

## T05 recommendations and review/report evidence — 2026-10-28

[Implementation, real-model evidence and manual steps](../docs/T05_ANALYTICAL_ADVICE_AND_REVIEW.md).
Extended existing field-guidance service with bounded registered analysis opportunities;
next-analysis questions use recorded advice-only mode with strict null plan/no actions.
Updated statistical skill and runtime Planner/Critic/coordinator guidance. Statistical
question is optional untrusted context; report adds definition/computed-finding sections,
Summary shows question. Shared Critic projection retains source/specification/counts/
grouping and explicit omissions within its budget. No raw preview rows or report mutation.
Final make test 2,186 passed (13 existing spatial warnings); focused prompt/evidence,
frontend validation and complete isolated browser passed (zero page errors). Existing
17 KB calculation-prompt budget retained by shortening overlapping manifest wording.
Actual installed qwen3.5:9b reasoning=none passed advice, grouped description and Pearson
in one call each (~33/40/45 seconds), synthetic temporary project only. Exact selected
fields and independent numerical answers checked; model proposals were not workflow-
dispatched. Actual Critic-model quality not evaluated. Remaining T05 chart-export and
interpretation/consolidation gaps documented; do not mark whole checklist complete.
No installs, Git/publication, live database/service changes or new permanent agent.

## Inspection-to-analysis follow-up — 2026-10-28

Followed T03/T05 in IMPLEMENTATION_TODO. Shared field guidance now adds at most eight
closed descriptive starter specs, standard-library-only for fixed worker compatibility.
Only complete nonconstant numeric measurement candidates within statistical magnitude/
row limits qualify; ambiguous codes, markers, missingness and filtered profiles need
explicit specifications. Existing response budgets trim explanations, not source scans.
Shared Outcome component offers optional measurement/group selections and prepares a
normal Planner request. No automatic send, calculation, exclusion, write or authority.
Browser verifies one-step proposal, separate Execute, recorded groups/report and CLI
history reopening. Real diabetic sample: 5,000 rows, ten age groups, mean 4.6592,
sample variance 9.647384836967394; every group mean independently checked with stdlib
statistics. Actual-model response quality still needs user validation. See
[manual steps/limits](../docs/INITIAL_FIELD_GUIDANCE.md#inspection-to-analysis-follow-up--2026-10-28).
No Git, dependency installation or live database changes.
Verification: make test 2,182 passed (13 existing spatial warnings), interface validation
passed (existing bundle advisory), complete isolated analytical browser journey passed
with zero page errors. No actual-model generation was included in this follow-up.

## Initial field guidance and Summary rows — 2026-10-28

[Implementation/validation](../docs/INITIAL_FIELD_GUIDANCE.md). Fixed Summary/Regression
Facts: shared dd width:100% + flex was collapsing dt; scoped full-width grids now keep
horizontal labels and stack values at <=520px panel width. Tabs scroll when narrow.
New standard-library field_guidance shares the existing comprehensive role classifier,
uses fixed counters during ordinary full CSV verification, and emits source-bound
advisory measurement/grouping/identifier/review shortlists. Cardinality/response bounds
explicit; no sample inference, dataframe or additional model pass for initial hints.
Comprehensive local/Docker result enrichment shares the builder; future worker build
copies the module; old fixed worker profile outputs are supported. No image rebuild.
MCP recommend_table_fields, CLI table-guidance and terminal /guidance registered; agent
recorded context includes bounded aggregate evidence. Advice-only conversation schemas
allow message+null plan; attempted action changes reject and inspection-on-send does
not replay. Existing compose-message event prepares the optional question, never sends.
UI uses shared FieldGuidance in ordinary/comprehensive Overview. Old snapshots unchanged.
Full tests/browser evidence recorded below after completion. Real 5,000-row scan returned
50 fields and expected families (explanations fit the existing metadata output budget).
Actual local-model advice not evaluated: Ollama /api/ps had no loaded models. No Git,
live database/service mutation, extra dependencies or cross-chat memory changes.
Verification: full 2,179 passed before final narrow codebook/source binding changes;
final guidance/conversation/calculation 95 passed, profile/discovery/terminal follow-ups
passed. Interface validation and final isolated browser passed, including wide/narrow
Summary screenshots and source-hash-bound question with no dispatch. Old current-plan
review prompt budget preserved by keeping the manifest instruction short. No model
load was forced. Temporary screenshots /tmp/actioncharter-statistics-summary-{wide,narrow}.png.

## Statistics pages and Markdown/PDF reports — 2026-10-28

[Acceptance, architecture and remaining scope](../docs/STATISTICS_PAGES_AND_REPORTS.md).
StatisticsPanel now uses existing result-page tabs, larger typography, readable
diagnostics and a format selector. StatisticalReport/report-document project the same
recorded Markdown into page/PDF without HTML/remote resources. report-pdf lazily loads
pdfmake and bundled fonts, paginates and partitions wide tables without dropping data.
New backend reports have structured evidence/numeric tables; old snapshots retain their
original text. Added optional covariance method through existing inspect_csv/MCP/CLI,
Planner coverage/grammar/catalog and Matrices view; explicit ddof/missingness/counts.
Report source filters retained. PDF dev validation uses pypdf (declared dev extra);
frontend dependency/lock files declare pdfmake/types. Installs used no browser cache.
First PDF browser check independently parsed four pages and matched source/P-values/
matrix/limitations. Visual review caught and fixed white native select + inherited
cyan article styling. Final material/wide-matrix acceptance is recorded below.
Final full suite 2,174 passed; focused 25 passed; interface validation passed. Browser
pages/material/download/restoration and independently parsed four-page PDF passed;
nine-column continuation retained all fields/final value. Real 5,000-row covariance
matched pandas and descriptive variances. No actual-model covariance evaluation.
No Git, release or live-service mutation. Continue T03/T04/T06 and formats/documents
as separate coherent slices; do not mark T05/T09 wholly complete.

## Typed statistical family — 2026-10-27

Regression-omission follow-up: statistics-v2 constrains the single-inspector proposal
branch to actual requested methods/regression and explicit covariance requirements;
typed variables remain model-generated and all backend checks remain. plan=null
still permits concrete semantic clarification. Prunes unused decoder definitions;
generic omission guidance no longer always recommends calculate_csv_columns. The
full isolated browser journey and interface validation passed. Local qwen3.5:9b
synthetic acceptance is being recorded below after validation, not assumed from fixtures.
The real-model probe exposed a second bug: covariance matched unbounded variance,
adding describe; the model then treated patient cluster IDs as numeric columns.
Word-boundary matching fixes the requirement; regression-only grammar removes unused
columns/by/percentiles/ddof selectors. Variables still come from the model. Full suite
2,169 passed before this final narrow correction; focused statistics/scope checks passed.
Final actual-model checks passed with qwen3.5:9b, reasoning_effort=none, max_tokens=1024:
synthetic ~55s; exact diabetic sample request ~69s, 5,000 rows/4,260 clusters/R² .3190629671.
Temporary copy/read-only service only; no workflow dispatch, authority or data writes.
Final focused 20 passed. Browser statistics-v2 and interface validation passed. Test
logs /tmp/actioncharter-statistics-{model-check-final,real-model-check}.log; no downloads.

Timeout follow-up: user saw 26.6 KB/120.1s/one-schema statistics-v1 generation timeout.
Measured a comparable fresh request at 24,861 prompt bytes: mandatory rules alone
11,095 JSON bytes. focus_statistics_instructions now applies only to statistics-only
inspect_csv scope with acquisition OFF; replaces irrelevant instructions/examples,
filters recipes, keeps operation allowlist, schema validation, deferred IDs and history.
Fresh request tests cap prompt at 16 KB. Do not claim actual Ollama latency is verified.
Restart instructions and regression-only retry are in the acceptance document.
Follow-up checks: 19 statistics/scope cases and interface validation passed. Full suite
had 2,167 passes and one deferred-ID regression from an earlier in-memory prompt version;
the field was restored and the failed test rerun through make test PYTEST_ADDOPTS=--lf.

[Implementation, limits and copyable acceptance](../docs/TABLE_STATISTICS_ACCEPTANCE.md).
Existing inspect_csv.analysis.statistics feeds StatisticsAccumulator from the verified
scan; shared MCP table_statistics/linear_regression, CLI table-statistics and terminal
/statistics read support. Planner schema coverage requires actual declared methods;
unused definitions pruned for ordinary inspections. Runtime contract statistics-v2:
restart launcher. Outcome Statistics reads immutable run evidence, not interactive
group state. Optional statistics/dev dependencies declare SciPy/statsmodels; installed
in this development venv with approved no-cache pip. Minimal Docker profile worker is
unchanged. Known-answer/real-5,000-row checks and isolated browser journey passed;
full backend verification passed 2,168 tests. Interface validation, isolated browser
and focused Planner/MCP checks passed; details in the acceptance document.
Do not stage/commit/push or touch live services. T01/T03 consolidation remains partial;
T06 generated analytical code, T08 formats, T11 documents/word clouds remain open.

## Exact-scope recovery and durable assistance — 2026-10-27

Concrete T02 bug: usePlanRun looked only at last 50 global receipts, then filtered by
chat/plan. New workflow/runs latest action requires exact conversation+plan, scans
bounded metadata before choosing, and leaves unrelated receipts untouched. Frontend
uses it, preserves matching evidence on refresh failure and polls restored active runs.
Terminal /run with no known ID uses the same scoped service; never auto-starts/cancels.
Unreadable/budget failures mean unavailable evidence, not an empty history. Global list
and historical scan caps remain explicit limits. Fixed execution_assistance tuple-key
persistence typo; cached receipt rereads no longer require another helper invocation.
Browser passed recovery behind 55 unrelated fixtures, pending->completed read-only
reconnection, retained evidence through a simulated 503, controlled timeout preservation,
history and terminal journeys. No real model-quality/remote-worker reliability claim.
[Audit/acceptance](../docs/T01_EXECUTION_AND_BUILDER_AUDIT.md#t02-exact-scope-recovery-delivered--2026-10-27).
Preserve all existing changes; no staging/Git/dependency/live-data changes authorized.
Verification: full make test 2,150 passed before terminal convenience addition;
subsequent focused recovery/assistance/history/CLI suite 22 passed including new
terminal isolation cases. Interface validation and full isolated browser journey passed.

## Adjustable charts, optional 3D and T02 state clarity — 2026-10-27

User found the compact grouped chart too small. GroupedChart now defaults Comfortable
with Compact/Large presets and shared 2D/percentage behavior. Optional 3D columns for
two grouping fields uses SVG projection, rotation/elevation controls and exact clickable
facts; height is count or percentage, not a third selected variable. No new dependency.
T02 slice: one executionBlockReason presentation helper mirrors existing header gates,
provides disabled reasons via tooltip/description/graph status, and saved-proposal restore
notice distinguishes restoration from execution. Backend authority is unchanged.
Browser acceptance now tests refresh before Execute (no invented Outcome/run), history
read-only reasons, resizing and 3D values/rotation. Full timeout/recovery and T01/T03
consolidation remain open. Preserve existing uncommitted changes; no Git/live DB actions.
Full make test: 2,145 passed. Frontend validation and isolated browser journeys passed;
real-sample 3D marks independently reconcile every observed age/gender group to 5,000.

## Group title/chart correction and T01 start — 2026-10-27

User reports stale table naming and oversized/unsuitable percentage charts. Titles now
show applied group/table fields; drafts keep old results with an explicit apply notice.
Shared GroupedChart replaces duplicated ordinary/session group-percentage presentation,
with count/overall/within-primary denominators, 0–100% axes and bounded 680px/360px area.
Preserve extra numeric/distinct plots and source/authority contracts.
[Actual T01 call paths/decisions](../docs/T01_EXECUTION_AND_BUILDER_AUDIT.md): distinct
analysis schemas/runtimes are not interchangeable; legacy Builder executor runs pytest
in a declared no-network container, but its boundary differs from fixed analytical worker.
Audit/compatibility inventory continues; no new code generation, installation, T02 fix
or broad consolidation claimed. Preserve all pre-existing documentation and code changes.
Verified: make test 2,145 passed; frontend typecheck/build passed; analytical browser
checks applied titles, 25% overall versus 50% within-primary, 0–100% axes and chart bounds,
plus frontend/terminal/history journeys. Real-sample browser cell reconciliation passed.
No live services/input mutations, dependency installations or Git operations.

## Age × gender table in ordinary CSV Outcome — implemented, 2026-10-27

User prioritizes the visible cross-field table before structural work. Found renderer
only connected to DatasetViewExplorer; ordinary GroupExplorer displayed flat records.
Reuse DatasetCrossTab there and in recorded two-field Overview groups; label ordinary
Explore tab Groups and both explorers' selectors Rows (vertical)/Columns (horizontal).
Keep other summaries in Detailed measures and chart mode. Existing services perform
explicit source-verified full-file reads, not preview aggregation or LLM calls.
Real 5,000-row browser acceptance reconciles every age/gender cell independently;
20,000-row journey checks count/percentage/swap and existing terminal/history behavior.
Frontend validation passed. No original input/live database or Git mutations.
Final verification: make test 2,145 passed; make interface-validate passed; final-build
20,000-row analytical/CLI/history and real 5,000-row browser journeys passed with no
page errors. Additional measures/filters and numeric coverage are collapsed so the
cross-table is easier to reach. Browser profiles and test projects are isolated.
[Exact frontend steps](../docs/DIABETES_REAL_TEST_FLOW.md#age-by-gender-cross-tab--2026-10-27).

## Consolidated next-work checklist — documentation only, 2026-10-27

[Implementation TODO](../docs/IMPLEMENTATION_TODO.md) consolidates the overlapping
plans. Start T01 actual ownership/Builder audit; diagnose restored graph/Execute T02;
extract shared contracts/registry T03–T04; deliver descriptive analytical report T05
and audited Builder-to-qualified-method reuse T06. Auto/manual routing, common formats,
association/regression, document/word-cloud and image/point-cloud branches have explicit
dependencies and acceptance. T14 scoped memory must pass before T15 autonomous Linux.
Do not require every future format before controlled data tests. Existing implementations
are distinguished from open tasks; final memory organization/curator role remain open.
Only docs changed; application work/tests/Git/live services were not performed here.

## Expanded science/formats and memory-before-Linux — docs only, 2026-10-27

[Requirements and acceptance](../docs/DATA_SCIENCE_FORMATS_MEMORY_AND_REMOTE_PLAN.md).
User wants substantive statistics (percentiles, SD/variance, correlations/matrices,
regression coefficients/P-values/R-squared, justified causal methods), not only initial
inspection or engineering receipts. Request JSON/PDF/Markdown/XLSX/DOC, PDF-to-Markdown
when useful, ordinary/geospatial images/rasters, LAS/point clouds and depth data.
Use shared adapters/method families and audit existing statistics before adding code.
Record corrected Builder role graph, qualified reports and service transfer; remote/
simulated Linux autonomous work with PostgreSQL/PostGIS comes AFTER scoped memory,
correction/recall and reusable-method foundations. Learning != automatic weight training.
All are recorded targets, not implemented by this change. Only documentation changed.

## Reuse existing Builder — documentation only, 2026-10-27

[Audit and integration plan](../docs/BUILDER_REUSE_AND_CAPABILITY_INTEGRATION.md).
User correctly recalls existing Python generation: Builder contracts/model boundary
2026-08-28, activation 09-01, exact-file verification 09-02. Earlier discussion overstated
the absence of generation. Legacy path proposes candidate Python + explicit developer
lifecycle; missing is normal-chat gap -> isolated analytical execution -> qualified skill
reuse. Audit/reuse schemas/materialization/tests/installer/worker, not another parallel
system or compulsory Builder agent. Do not wire source activation directly into chat.
Only docs changed; no application code, tests, installs, Git or live-service operations.

## Composition and agent structure clarification — documentation only, 2026-10-27

[Concrete operations and project graphs](../docs/COMPOSITION_IMPLEMENTATION_AND_AGENT_STRUCTURE.md).
User asks whether composition is just replacing age with another field. Existing
aggregate_csv is parameterized by actual column names, metrics and source/dependencies;
not age-specific and not arbitrary pandas execution. Record schemas/registry/dispatcher/
service ownership, one-context versus role-context tradeoffs and optional code path.
Only documentation changed; no runtime implementation, tests, staging or Git operations.

## Generalization direction — documentation only, 2026-10-27

[Consolidation plan](../docs/GENERALIZATION_AND_CONSOLIDATION_PLAN.md) records the
user's concern about backend/special-case growth. Preserve typed operations, recipes
and templates; they are not obsolete and workflow composition is not code generation.
Next implementation must first trace shared responsibilities/state restoration, then
consolidate task actions, contracts, registry-driven composition and acceptance fixtures.
Keep agents responsible for method choice; optional bounded Python fills genuine gaps.
Record Auto/manual routing with Planner recommendations and coordinator limits, common
format/report/database goals, compatibility invariants and measurable acceptance.
No application code, tests, dependencies, Git or live services changed for this request.


## Inspection planning timeout — 2026-10-27

User's real sample read-only inspection hit Planner generation timeout: 31.4 KB,
ten schemas, 120.1 seconds. Focus initial descriptive schemas to inspect_csv only
for explicit read-only analytical requests; keep analysis/full-file statistics and
existing allowlist/authority. Mixed requests/current writer workflows remain broad.
No automatic retry or increased timeout. Regression exercises actual request with
injected timeout and confirms one call, one schema, analysis retained, no approval.
Restart required; installed Ollama acceptance remains pending. See task-mode document.
Verified: full make test 2,145 passed with local socket access; interface validation
passed. Restricted sandbox HTTP-test failures were socket permission errors.

## Manual task modes — 2026-10-26

[Implementation, limits and exact validation](../docs/TASK_AGENT_MODES.md).
Conversation gear selects Single/Three; unset legacy chats are preserved. One model
called sequentially, separate role journals in Three, primary self-review in Single.
Shared governed services, own-chat review binding, frozen run mode, recorded reports
and measured effort; no auto switching, new agent containers, training or live writes.
Real 5,000-row disposable PostgreSQL and browser mode comparisons passed using model
fixtures; installed-model acceptance remains manual. Full backend suite: 2,141 passed,
with final report guard covered by focused tests. No Git mutations.

## Real diabetes acceptance — 2026-10-26

[Exact frontend flow and reference](../docs/DIABETES_REAL_TEST_FLOW.md): actual input
paths under data/input/test; sample 5,000 rows/50 fields, 4,260 patients, 506 repeated
patients, zero duplicate encounters/entire rows; mean days 4.6592; readmitted counts
555 / 1,967 / 2,478 for <30 / >30 / NO. Sample is exactly the first 5,000 full-source
rows, not proven representative; payer_code is entirely ?. Added governed
decode_csv_codes for the supplied sectioned mapping file, preserving raw codes/rows
and verifying each label. Real temporary PostgreSQL round trip passed every projected
value: selection 13 columns → decoding 16 → database/export 17 with explicit marker.
Browser found/fixed silent loss of mapping facts at the saved-preview byte limit; trim
preview rows first, retain counts/coverage. Original sources and live services unchanged.
Verified: 2,130 full-suite tests plus 3 independent-reference tests; interface validation,
real 5,000-row disposable database round trip and real-data browser preparation passed.
Manual real-model frontend planning remains a distinct acceptance; automated proposals
are fixtures/operator-authored. No clinical inference, imputation, row exclusions or Git.

## Governed PostgreSQL operations — 2026-10-26

[Delivery, limits and manual validation](../docs/POSTGRES_DATA_WORKFLOW.md). Six typed
operations now cover allowed-schema discovery/inspection, fresh-table import, fresh CSV
export, and exact-key boolean marker delete/restore. Existing registry/Planner/graph,
recipe authorization/execution/verification, MCP and CLI share services. Database-only
evidence persists snapshots; approved DB steps have one-attempt claims. No arbitrary
SQL, append/replace, schema creation or live-service change. Disposable real PostgreSQL
acceptance includes readiness inspection, verified codebook join, intermediate import/
export, snapshot/hash/null/type checks, rollback and cancellation. Browser review tests
use an unreachable DB and prove authorization alone never executes. Full-source pandas
preparation limits and domain interpretation remain explicit follow-ups; start with the
5,000-row sample. Verified: 2,120 backend tests, interface validation, disposable PostgreSQL acceptance,
database authorization browser checks and complete frontend/CLI/PTY regression passed.
Optional fresh-import deletion marker also passed focused/runtime checks.
No Git mutation/publication or dependency download performed.

## Cross-tabs delivered; database round trip planned — 2026-10-26

[Real-data targets](../docs/REAL_DATA_NEXT_TARGETS.md#two-variable-cross-tabs-and-postgresql-round-trip--2026-10-26)
now records row/column two-field tables, named percentage bases and frontend/terminal
parity, plus authorized ordinary-tabular PostgreSQL import/query/export and reconciliation.
Unload means export, not delete. Cross-tab presentation is delivered in frontend/terminal using saved groups; no
database operation or new executable tool implemented. Next milestone combines preparation/codebook joins, readiness reporting
and a disposable-database round trip, preserving the existing authorization boundary.

## Outcome page, field details and terminal charts — 2026-10-26

User wants frontend parity with `/columns age`, a large Outcome page covering the graph
area, direct graph return, visible frontend workflow history and usable terminal charts.
This delivery changes presentation of saved evidence: main Outcome workspace, searchable
field details with category counts/percentages and applicable numerical/missingness facts,
plus discoverable field/group ASCII charts. No new source scan is needed for those views. Verified: 2,109 backend tests, frontend
validation, combined browser/real-PTY charts and legacy table/chart/map regression passed.
[Next real-data targets](../docs/REAL_DATA_NEXT_TARGETS.md) records Target | Requirement |
Functions/ability to add | Expected outcome for quality, preparation, comparisons,
statistics, engineering/recovery and later method knowledge. Those targets are not claims
of implementation; prioritize the readiness report and descriptive comparisons first.

## Persistent terminal and chat workflow history — implemented, 2026-10-25

[Delivery and combined acceptance](../docs/TERMINAL_AND_CHAT_HISTORY.md): start
`./actioncharter` for the full-screen/persistent plain terminal, sharing the running API's
chats/model/settings. Workflow history records immutable workflow/analysis/view snapshots
and linked runs; opens historical read-only graphs/Outcome without replacing current
work. Continue creates a new validated draft revision, restoring selected views without
copying authority. Explicit terminal review/availability/authorization/Execute use the
shared backend; normal messages never dispatch workflow execution. Prior overwritten
history cannot be recreated. SQLite snapshots deduplicate payloads, remain bounded and
scoped per chat. Verified: 2,108 backend tests; frontend validation; combined browser
and real-PTY acceptance (read-only sample execution, outcomes/history, restore/continue).
No new dependencies/agent framework or original-data/live-service/Git mutation.

## Interactive analytical selection — 2026-10-25

[Outcome/CLI grouping and selected-column views](../docs/COMPREHENSIVE_INSPECTION_DELIVERY.md#interactive-selected-columns-and-grouped-percentages--2026-10-25)
now use an explicit source-bound shared read: Table age alone/age+readmitted; Groups
one/two fields, counts, percentages of all rows or within the first group, table/chart
and denominator details. Last table and grouping saved separately per chat; views do
not rescan, Apply does. MCP `explore_dataset_view`, CLI `chat explore`/`chat result`
share the service. No LLM calls, original-data writes, authority or chat-proposal changes.
Verification: 2,101 full-suite tests, 15 focused tests, frontend validation and actual-Docker
browser/CLI group-percentage journey passed. Full/sample comparisons verified 10 age
groups and 30 age/readmitted pairs each; original sources unchanged. Worker image rebuilt.
Real full/sample independent Docker checks passed; richer statistics, historical-workflow
navigation and persistent terminal UI remain subsequent work. Preserve prior designs.

## Frontend/CLI continuity — implemented slice, 2026-10-25

User requires both interfaces to continue the same project/chat. [Commands, semantics
and acceptance](../docs/COMPREHENSIVE_INSPECTION_DELIVERY.md#frontend--cli-continuity--2026-10-25):
`chat list/show/send/receipt/result` use the running loopback API and its model settings,
shared chat/proposal state and submission receipts. Six readable recorded-result views
plus JSON do not rescan. Refresh saved chat reloads frontend state and list without
clearing an unsent draft; unsaved graph edits block refresh. No auto-retry, write enable,
authorization or workflow dispatch; explicit exploration still runs bounded reads.
Verification: 2,097 backend tests passed; frontend validation and bidirectional/CLI-new-chat
browser journey passed. New code is `src/geoagent_harness/chat/`; no new dependencies.
Chart selectors match existing result controls. Browser-local presentation/drafts are
not synchronized. Statistical relationships and full health-task acceptance remain open.

## Next user-facing task — quality to useful analysis

2026-10-25, documentation only: [post-inspection professional workflow and acceptance
criteria](../docs/DIABETES_EXPLORATORY_ANALYSIS_TASK.md) records grain/provenance →
quality report → explicit analysis specification → validated preparation → full-source
group comparisons → supported relationships/uncertainty → reproducible results/pipeline.
Prediction is a later separate objective. First audit/reuse existing tools; next proposed
product work is matching Chart controls to the existing UI, improving group exploration,
and readable CLI views over the same scoped saved results (no rescan merely to view).
Keep denominators, repeated patients, code definitions and missingness explicit. Planner,
shared services/MCP and Critic have complementary duties; no new mandatory agent chain.
No implementation/data processing authorized by this documentation request; do not infer
new statistical capabilities, clinical validity, learned knowledge or write authority.

## Implemented 2026-10-25 — comprehensive inspection and Docker runtime

[Delivery, boundaries and validation](../docs/COMPREHENSIVE_INSPECTION_DELIVERY.md):
all-field CSV/TSV type/role profiles, full matching-file numerical summaries and category
counts, MCP/CLI shared service, recorded interactive Outcome and left-to-right analytical
graph. Default comprehensive jobs use a fixed Docker worker; legacy specialized duplicate
checks remain bounded local services. Actual Docker isolation/cancellation/concurrency and
full 101,766-row / 5,000-row comparisons passed. User frontend retest remains; statistical
relationships, approved sampling, domain memory/RL and flexible-role server tests are open.
Verification commands/results are in the delivery guide: full suite 2,092 passed,
19 focused tests passed, frontend validation and actual-Docker real-data browser passed. Worker image was built from
cached Python, no dependencies downloaded. Actual local-model full-source journey took
86.5 seconds; latency remains a limit. Real-file browser journey used actual Docker and
a model fixture; no browser-cache access. New shared service/worker code is under
`tabular/dataset_*` and `sandbox/`, UI under `DatasetOutcome.tsx`. Existing user changes
remain. No Git staging/commit/push or live database/service mutation.
Earlier design-only handoffs below are preserved history, superseded for implemented scope.

## Latest agreed scope — integrated real-data frontend delivery

2026-10-25: user asks whether the delivery includes Executor containers and requests a
resume record. Yes: [integrated delivery plan](../docs/REAL_DATA_FRONTEND_DELIVERY_PLAN.md)
is the latest scope/order authority. Complete type-aware all-field inspection, appropriate
calculations, shared MCP/API/CLI capabilities, the tool-driven analytical role, mostly
left-to-right graph, interactive Outcome and an Executor-managed Docker profiling worker
with private scratch/artifact handling and proven isolation. These are one coherent
real-data frontend delivery; neither a standalone Docker pilot nor UI-only metadata
satisfies it. Earlier sandbox-first or analytics-only summaries below are historical.
Next implementation starts with actual coverage/runtime/UI audit and typed profile/job/
artifact contracts, then shared profiler plus minimal Docker path, isolation/parity,
agent-loop integration, Outcome/graph and full/sample real-data browser acceptance.
No extra worker agent or mandatory LLM Executor container; reuse services. MicroVM,
all-operation migration, relationship inference/adjusted models, flexible-role groups and
server evaluation remain subsequent work. Sampling writes require a registered operation
and normal authority; no permission bypass from scratch. Memory/RL/release remain separate.
This turn changed documents only: no runtime/frontend code, data, tests, model calls,
container builds/startup, dependency installation or Git mutation.


## Latest design handoff — Executor sandboxes and comprehensive inspection

2026-10-25: latest request is documentation and next-step explanation only. Read
[Executor sandbox/workspace plan](../docs/EXECUTOR_SANDBOX_WORKSPACE_PLAN.md) and
[typed inspection/Outcome backlog](../docs/COMPREHENSIVE_DATASET_INSPECTION_PLAN.md).
Worker lifecycle belongs to Executor responsibility, implemented by reusable services;
a calculation worker is a container/MicroVM runtime, not an additional reasoning agent.
Reuse execution/validation services. Existing local analytical subprocesses are not
per-job Docker sandboxes; Compose containers do not make the local launcher path isolated.
Proposed Docker first, fresh job environment, selected read-only inputs/private scratch,
no worker network/secrets/socket, hard quotas and verified output/artifact contracts.
Manager stays trusted; models cannot configure arbitrary mounts/commands/permissions.
MicroVM is a later runtime adapter; no new scheduler/agent framework now.
Next coding slice: audit paths/images/runtime and define job/artifact contracts, pilot
one CSV profile through Docker, then isolation and result-parity acceptance before
claiming containment. Preserve comprehensive automatic type-aware profiling, left-to-right
graph and interactive Outcome as the linked functional backlog, not already completed.
Sampling writes still need a registered operation plus normal authorization. Flexible
roles/groups/structured handoffs and simulated Linux-server evaluation follow one working
full journey; memory/RL remain separate. This turn changed docs only: no container build,
startup, data processing, dependency install, runtime/frontend code or Git mutation.


## Latest implementation — analytical graph and inspector, 2026-10-25

User reports analytical chat works but graph/info do not show actions. Read
[graph/inspector handoff](../docs/ANALYTICAL_GRAPH_AND_INSPECTOR.md).
Saved session now projects discovered inputs, actual action journal and findings into
an automatically selected read-only graph. Node clicks populate information with paths,
strategy, source hashes, coverage, computed profiles/checks and separate advisory text.
Timeline shows recorded actions. Existing plans remain selectable; analytical view
cannot Execute/Authorize. Restore uses saved facts, not model/source replay; new chat
clears them. Startup scope guard prevents unrelated restoration overriding this view.
Extended browser test exposed missing provenance IDs on old analytical message pairs;
new writes are fixed and a narrowly corroborated read projection supports affected old
sessions without editing text on read. Foreign provenance remains rejected. Targeted
28 analytical/privacy tests and complete/partial browser journeys passed. Final make
test: 2,086 passed (13 existing Rasterio warnings); interface validation passed. No Git/live-service changes.
The user's actual saved profile was inspected read-only: 101,766 rows, 71,518 distinct
patients, time_in_hospital mean 4.39598687184326, min 1/max 14; hash and query are saved.
User can reopen that chat after launcher restart/refresh without regenerating analysis.


## Latest implementation — bounded analytical role loop, 2026-10-25

Read [analytical loop and role/server handoff](../docs/BOUNDED_ANALYTICAL_LOOP.md).
User authorizes discovery/assessment/tool-driven explanation first, then flexible
roles/agents, better communication and isolated Linux-server testing after the data
journey works. Roles are responsibilities; shared services remain authority boundaries.
Implemented scoped directory discovery, operation-specific assessment, MCP/CLI tools,
stage-specific analytical action loop and persisted evidence/partial results in chat.
Conversation adapter keeps the workflow unchanged; explicit exploration can perform
read-only tools without Execute. Saved evidence restores without new model/source calls.
Input test folder was empty; originals were not moved. Temporary real-input acceptance
passed 101,766 source / 5,000 sample rows: streaming profile eligible on the full file,
existing dataframe calculation needs an alternative, sample byte eligibility passes
with runtime row checks still required. Schemas match; provenance remains unverified.
Final validation: full make test 2,083 passed (13 existing Rasterio warnings); final
focused 40 passed, analytical-session 11 passed; interface validation and isolated
browser journey passed with zero page errors. Actual synthetic qwen3:4b-instruct trial
passed 5,000 rows / 2,500 distinct patients / mean 3 in 3 model + 3 tool calls (~21.1s,
7.6 KiB peak prompt). Repro script scripts/analytical_loop_model_evaluation.py. This
single trial does not establish general model reliability.
Synthetic/fake-client/browser paths passed; earlier small-model trials exposed argument
omissions, repeated assessments, unsupported units/sample claims and timeout. See guide
and final validation entry for current evidence; do not claim universal model reliability.
Sample creation/authorization adapter, statistical models, arbitrary natural-language
continuations, live journal streaming and conversation-loop cancellation are not added.
Next: retest with user files, then complete sample-write proposal and statistical stages;
only after successful data journey design role scheduler/structured communication and
isolated server evaluation. Memory/RL remain separate. No Git/live-service/dependency work.


## Latest report — invalid `columns` field, routing reproduction pending

2026-10-24: operator reports another model schema rejection (41.1 KiB / 12 schemas /
planner correction). Latest two receipts were inspected read-only: failed, run_id=null.
Failed prompt content is not stored; requested exact submitted message via clarification.
Do not claim original routing cause known or repeat model/context-size speculation.
Frontend now uses confirmed receipt status: failed with no run says failure before
dispatch, recorded run directs to History, unconfirmed transport status stays uncertain.
No backend routing change in this update. Full exact-profile baseline remains tested,
but reproducing the newly reported request requires its text. Continue that investigation
when supplied; do not treat the error-message fix as a complete routing fix.
Frontend validation and isolated browser confirmation passed with zero page errors.
No data, dependency, Git or live-service changes.


## Latest fix — analytical routing and restored-state clarity

2026-10-24: reported profile timeout/refresh confusion investigated without modifying
user records/data. Stored exact profile had zero model calls; a later failed receipt
had no run. Refresh restored saved work, not a successful retry. Cannot prove failed
call wording/settings or context overflow from these records.
Complete profiles now route deterministically through direct conversation and submit;
new health analytical_planning_revision=table-profile-routing-v2 prevents sending a
profile to an older running API. Explicit selected-method requests remain separate.
Frontend reads pending receipts without resend and labels failed/restored state.
Read [recovery instructions](../docs/TABLE_EXPLORER_ACCEPTANCE.md#profile-timeout-and-refresh-recovery--2026-10-24).
Targeted 41 routing/inspection/quality tests and isolated old-API/timeout/refresh browser
journey passed; frontend validation passed. Final make test: 2,074 passed, 13 existing
Rasterio warnings.
No live-data, dependency or Git changes. Resume the real-data task after launcher restart
and browser refresh, expecting Exact inspection workflow · no model call.


## Current handoff — Columns/Explore implemented, 2026-10-24

User authorized implementation of the first coherent analytical slice. Read
[delivered controls and exact retest](../docs/TABLE_EXPLORER_ACCEPTANCE.md) first, then
[full task](../docs/DIABETES_EXPLORATORY_ANALYSIS_TASK.md). Backend now supports bounded
exact quality_columns, duplicate_rows, composite duplicate_key and per-group distinct
counts. MCP profile_table advertises typed AnalysisOptions; workflow/CLI share services.
CSV Results has searchable Columns and explicit Run analysis in Explore; source and
codebook checks are preserved. Plain completed CSV inspections can request these views.
No model call for controls; Planner quality schema/proposal integration is fixture-tested,
not a new actual-model reliability evaluation. Real-data temporary acceptance passed:
101,766 rows, 71,518 patients (54,745 once-only / 16,773 repeated), zero duplicate rows,
unique encounter key; declared '?' counts weight 98,569 / race 2,273 / payer 40,256.
Final checks: make test 2,070 passed (13 existing Rasterio warnings); interface validation
passed; isolated browser passed with zero page errors, including budget-error recovery.
No new dependencies installed. Inventory pandas 3.0.5 / NumPy 1.26.4; SciPy/statsmodels/
scikit-learn absent. Statistical methods, durable exploration saving, automatic promotion
to workflows and backend cancellation of these synchronous reads remain undelivered.
Next: user frontend retest, then spread/quantiles with explicit methods and independently
validated association/uncertainty tools before one adjusted model. Memory remains parked.
No Git mutations or live-data changes. Earlier proposal-only notes below are history.

## Latest task expansion — full exploration, documentation only

2026-10-24: user requests a durable complete-task design including statistics,
relationships, frontend/structural observations and the next implementation order.
Read [full task and resume instructions](../docs/DIABETES_EXPLORATORY_ANALYSIS_TASK.md)
before earlier quality-only plans. Endpoint is quality → descriptive statistics →
relationships/uncertainty → one interpretable adjusted analysis → reproducible report.
Next coding session audits current tools/dependencies/UI, then adds shared primitives,
typed MCP/API/CLI access, audited Columns/Explore UI, Planner integration, association
methods and one bounded model-fit operation, with independent acceptance per slice.
Repeated patients, missing policies, statistical assumptions and diagnostics are gates.
Package/documentation search is optional and cannot auto-install or expose arbitrary
functions. No new agent, RL or memory redesign required. This turn changes documents
only; no datasets processed, model calls, frontend/runtime edits, tests or Git mutations.

## Latest direction — quality and interactive exploration, documentation only

2026-10-24: user requests recording the next design and explaining the first test
task. Read [table quality/exploration plan](../docs/TABLE_QUALITY_AND_EXPLORATION_PLAN.md).
Next proposed implementation: shared exact quality/group contracts → focused MCP/API/CLI
exposure → audit/propose frontend Columns/Explore controls → Planner integration →
independent real-diabetes acceptance. Distinguish distinct, once-only and repeated values;
count encounters and distinct patients separately. Preserve missing/codebook policies.
These are new general features prompted by data testing, not model training or current
completed functionality. No runtime/frontend changes or data/model calls in this update.
Memory remains parked; no Git mutations. Older delivered analytical baseline follows.

## Current handoff — analytical implementation, 2026-10-24

Latest user authorized implementation until real diabetes retesting is possible.
Read [acceptance and exact prompts](../docs/ANALYTICAL_INSPECTION_ACCEPTANCE.md).
Implemented runtime Ollama selection, typed source references, codebook-aware complete
profiles, explicit full-file aggregate export, shared MCP/CLI access, bounded post-run
LLM assistance and Results profiles/table/groups. Real-file temporary acceptance passed
101,766 encounters / 71,518 patients / 30 groups with validated_success; original data
and live services untouched. Full tests: 2,064 passed; final focused 124 passed; interface validation passed;
isolated browser journey passed.
Actual small-model assistance passed a synthetic numeric-summary trial after decoder
and argument fixes; no claim of general model reliability. Use existing launcher, then
frontend prompts in the acceptance guide. General lazy intermediates and automatic
mid-run adaptation are not delivered. Other transforms retain older size limits.
Memory designs remain parked. No Git mutations or dependency installations performed.
Older proposal-only entries below describe previous turns, not current runtime status.


Updated: 2026-10-23. Handoff only; never execution authority.

## Latest sequence — complete process before role flexibility

Read [delivery-order clarification](../docs/ANALYTICAL_EXECUTION_DELIVERY_PLAN.md)
first. Record current plan: finish real diabetes analytical journey with existing roles;
then make roles independently callable and selectively orchestrated; evaluate combined
versus separate roles before unrestricted flexibility. Independent roles still use
shared validation/permission services. No obligatory multi-agent chain for simple reads.
Next proposed implementation slice is the Ollama Settings selector: audit/present minimal
UI, backend discovery/runtime settings, request-pinned model selection and tests.
Then typed table references, codebooks/full-data services, bounded execution reasoning,
frontend audit/agreed improvements and end-to-end health-data acceptance. Memory parked.
Latest request is documentation and next-step explanation only; no coding, frontend
edits, model requests, data operations or Git work performed in this turn.

## Latest five-stage plan — documentation only

Read [analytical execution delivery](../docs/ANALYTICAL_EXECUTION_DELIVERY_PLAN.md)
first: Ollama discovery/runtime selection -> typed table/intermediate references ->
codebook-aware full-data operations -> bounded execution-time LLM reasoning -> frontend
audit/proposal then agreed implementation and real task acceptance. User asks to record
and assess architecture, not start coding. Keep one user entry and selectively invoked
roles rather than obligatory multi-call chains. Codex supports subagents; ZeroClaw has
named identities/specialist delegation, so do not call them single-agent-only/roleless.
Proposed comparisons need same-model/task evidence; no benchmark superiority claimed.
Memory choices remain parked; Critic/knowledge-agent separation is not decided here.

## Latest step-4 feedback and MCP explanation — read first

[Analytical inspection/codebook plan](../docs/ANALYTICAL_INSPECTION_AND_CODEBOOK_PLAN.md)
is the latest actionable proposal. User stopped before step 5: path recognition,
IDS_mapping.csv interpretation, full-file profiles/aggregation and useful table views
need improvement. No runtime/frontend changes before agreement. First audit actual
paths/readers/codebook and reproduce UI before presenting/implementing frontend edits.
Backend owns shared analytical logic; MCP is its typed tool adapter, not a data/memory
store. Existing discover_dataset delegates to shared discovery workers; approved MCP
recipes can persist evidence through runner services. Latest turn documents only;
no data inspection/execution, model call, tests, Git or live-service mutation performed.

## Latest instruction — memory options parked; prepare data testing

Read [the current decision/data-test handoff](../docs/MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
first. User clarifies that content/priority change while old versions remain recoverable
by default, not immutable never-delete storage. Preserve separate/common memories and
combined Critic-curator/separate knowledge-agent alternatives; no final role/architecture
choice. A+separate-agent is a recorded prior proposal, not an implementation mandate.
Next priority is controlled data-test preparation using current capabilities; do not
keep expanding memory instead. Metadata, processing and visualization limits differ.
This turn is documentation only; no tests/data downloads/runtime or Git work performed.
Prior broader pre-demo learning gates are not claimed complete by the order change.

## Latest design direction — read before older notes

2026-10-23: [revised memory A](../docs/MEMORY_A_GROWING_SHARED_JSON.md) is the latest operator direction. Separate Planner/Critic memories feed a shared JSON that must not forget and may update content/priority. A separate knowledge-management agent works on shared memory and produces/revises domain knowledge and graph links. This supersedes Critic-only curation, temporary shared-board forgetting and backend-only A/B assumptions for A. B remains unchanged. No choice of A versus B, JSON transaction schema, runtime implementation or cross-chat expansion is approved. Documentation/comparison only; no code or Git actions.

## Latest state and user instruction

The user asked to continue until checkpoint 28 is completed. The agreed engineering
implementation and acceptance are now complete. Read docs/development/checkpoints/CHECKPOINT28_CLOSEOUT.md
for the final matrix, manual acceptance, raw-report paths and limitations. It
supersedes earlier open-stage notes without deleting checkpoint history.

Preserve all uncommitted changes. Do not stage/commit/push/merge/publish/release,
modify live PostGIS/GeoServer data, install dependencies or use shared browser
caches. Leave the pre-existing untracked docs/development/checkpoints/CHECKPOINT25_MANUAL_GIT.md untouched.
No such action was performed during this work.

## What is implemented

- Shared no-follow discovery source access, streaming CSV and metadata-only TIFF /
  closed GPKG / lowercase SHP package readers. Progressive metadata, full hash,
  observed source consistency and durable evidence; not immutable capture.
- Rich bounded raster technical metadata, compared with gdalinfo fixtures. No
  automatic full-file statistics/histograms. Opacity endpoint labels/readout and
  mouse/keyboard checks; the original reported symptom is not reproduced.
- Exact supported Inspect submissions prepare typed workflows with zero model
  calls/configuration. OFF prepares only; ON can probe/execute permitted reads.
  Normal UI sends in both modes use durable receipts. General direct conversation
  compatibility remains; explicit method selections still use Planner.
- 1–4 distinct local sources, <=1 GiB aggregate package bytes, existing serial
  coordinator, source/contract/chat binding, separate results, cancellation,
  partial failure and no replay. TSV defaults to tab. Existing stricter gates stay.
- CLI discover-dataset and MCP discover_dataset use discovery/service.py and the
  same worker. CLI submit-inspection shares the durable coordinator; --execute is
  explicit permitted-read execution. Legacy inspectors retain old contracts and
  custom-root compatibility; the new MCP discovery requires project data/input.
- New workflow requests omit competing recorded-view schemas. Actual display and
  saved-fact explanations keep their view path. Graph drag state now survives
  React selection renders, with motion still updated per frame. Grouped disabled
  actions retain the existing outline material.

## Final verification

- make test: 2,045 passed / 13 Rasterio library warnings / 200.79 seconds.
- 53 focused exact-route/result-view/MCP checks passed after final relative-root
  and stricter-gate coverage. Early failed full run found message provenance
  (fixed) plus sandbox socket restrictions; do not call that early run passed.
- make interface-validate passed, existing ~758 KB bundle advisory.
- Final browser groups: 15 submit/batch, 10 spatial, 4 execution and 6 Planner /
  recipe / graph. Actual shared services, fixture model completions, isolated
  browser profiles/temporary datasets, no page errors or live-service calls.
- Original paired local-model trial: 24 attempts, OFF 10/12 and ON 10/12, 14 model
  calls/two corrections per side. Both failed vector planning twice. Original
  failure report retained. After schema correction, separate vector retest 4/4,
  one call/task, no corrections. Do not combine versions into a new 24/24 trial.
- Recommendations remain experimental OFF: no reliability/call-count benefit
  established. Success retrieval exists on both sides of the comparison; this
  does not isolate all memory or prove arbitrary failure recovery/domain recall.
- Exact temporary TIFF submit: zero model calls, correct metadata, same run on
  duplicate submission, 1.359 s total. Not an all-file/competitor benchmark.
- Earlier CSV/TIFF 16/64 MiB measurements and >8 MiB GPKG/SHP worker cases remain
  in the discovery guide. Configured 1 GiB guards are not proven real-data scale.
- Historical CURRENT_STATUS suffix and byte bound preserved; git diff --check
  passed. No Git mutation, live-data change, new dependency or shared cache change.

## Reports and recovery

Key metrics above and in CHECKPOINT28_CLOSEOUT survive loss of /tmp. Raw reports:
/tmp/actioncharter-checkpoint28-closeout-paired-model.json (includes failures),
/tmp/actioncharter-checkpoint28-vector-correction-model.json,
/tmp/actioncharter-checkpoint28-exact-submit.json.

After interruption inspect git status and these documents first. Restart with
bash scripts/start_actioncharter.sh and refresh localhost:5173. Submission health
revision is inspection-batch-v5; Planner revision remains inspection-source-v2.
Open Execution History before retrying. Interrupted work never restarts itself;
partial metadata remains unverified. Do not retry writes without inspecting
actual targets and fresh exact authority. Reports/notes do not grant approval.

## Next numbered work and limits

Checkpoint 29: private sourced domain definitions/methods, applicability, bounded
retrieval, corrections/supersession and provenance in one conversation. Design:
docs/development/checkpoints/CHECKPOINT29_PRIVATE_KNOWLEDGE.md defines the ordered implementation and
acceptance, extending docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md. No checkpoint-29 implementation was
started here. Cross-chat/project sharing stays 30+ and separately decided.

Engineering closeout is not demo readiness or a cleared learning/private-memory
gate. Domain knowledge, general learned benefit/RL, unrestricted code generation,
streaming large GeoJSON, full statistics, broad real-data scale and hardened
multi-user/desktop packaging remain explicit future work. Start with synthetic
knowledge acceptance before broader realistic-data/demo preparation.

## Latest design discussion — learning process

The operator requests a human-learning analogy before committing to a stack. See
[the domain learning design](../docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md) learning-process clarification: explain,
predict, practise, check, diagnose, revise and test transfer. Summaries/retrieval
alone do not establish learning. Recorded documentation only; no runtime or
cross-chat scope change. Map the checkpoint-29 slices to this loop before coding.

### Resume this discussion in the next Codex session

Read this handoff, docs/development/checkpoints/CHECKPOINT29_PRIVATE_KNOWLEDGE.md and the final
learning-process clarification in docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md
before proposing work. Inspect git status and any applicable AGENTS.md; preserve
existing changes and the user-owned docs/development/checkpoints/CHECKPOINT25_MANUAL_GIT.md.

The user's central objection is that previous answers listed desired capabilities
and infrastructure without specifying a learning method. Do not answer this by
merely proposing another memory table, summarizer, agent or postponed checkpoint.
Start with a worked example and explain how a conditional lesson is formed,
challenged, practised, corrected and transferred. Human learning is a design analogy,
not a claim of equivalent cognition or measured agent improvement.

Next design deliverable: map each learning function to its concrete input, output,
source of feedback, stop/failure condition and owner. Walk through one synthetic
rainfall example, an incompatible case and an unseen compatible case. Explain how
this modifies the existing checkpoint-29 slices before implementation. Prefer the
existing Planner/Critic roles and shared services; no separate Builder is required.

A reusable method needs rationale, applicability, parameters, checks and exceptions.
Summarization/recall alone is insufficient. Knowledge acquisition, executable
capability acquisition and policy/model learning are different mechanisms. Record
capability gaps honestly; do not promote an unexecutable procedure into a tool.
Cross-chat project knowledge and adaptive/RL method selection have been discussed,
but no scope expansion or implementation is authorized by this documentation request.
Do not treat model agreement, successful execution or fixed ranking as proof of
correct domain reasoning or learned benefit. Keep uncertainty and failed examples.

Latest user request: preserve this discussion in documents so another Codex session
can continue. Documentation only. No code, dependency, live-service or Git changes
are requested. User handles Git and publication; historical context never grants
execution authority.

## Latest memory design — 2026-10-23

Read docs/ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md before further design. The user
wants role-specific Planner/Critic memories and agent-led semantic checking, backed
by reliable service-managed records. Use structured contributions, a bounded curator
role (initially Critic), explicit permissions/applicability/status indices and shared
references. Tier, evidence status and access scope are separate; retrieval counts
never prove correctness or broaden sharing. Domains/keywords aid discovery and are
not unique record IDs or permission labels. Propose automatic local persistence and
minimal versioned export/restore without requiring user Git or SQLite administration;
private backup and sanitized portable sharing are distinct. Reconcile these designs
with checkpoint 29 and the worked learning exercise before code. Documentation only;
no cross-chat scope expansion, runtime, Git or live-service actions authorized here.

## Latest operator clarification — memory design is not settled

2026-10-23: the user explicitly says the discussed memory parts remain unsettled.
Read the open-decision table near the start of
[the role-memory proposal](../docs/ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md).
Earlier imperative wording in design notes is a proposed direction, not approval
of the curator role, separate stores/views, tier rules, sharing defaults, numeric
budgets, domain vocabulary, storage/backup policy or export format/delivery scope.
The desire to export knowledge is recorded; the implementation remains undecided.
Continue with worked scenarios and tradeoffs to resolve choices before coding.
Latest instruction authorizes documentation only; no code or Git actions.

## Latest alternatives and ratio clarification — 2026-10-23

The role-memory design now records scenario A (separate role/shared files plus journal
and recovery) versus B (one transactional store with role views and file exports).
Both use existing Planner/Critic memory functions, source-linked domain records and
graph edges; neither requires new memory subagents. Project paths/tables are proposals,
not delivered code. No choice is settled. Existing same-chat restrictions remain.
The ratio explicitly discussed was agent reasoning versus service responsibility;
no numeric split was selected. Context-tier budgets, ranking weights and sharing
permissions are separate questions; none has an approved ratio/formula. Read the final
sections of docs/ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md before continuing. Latest
instruction authorizes document updates and explanation only, not runtime or Git work.

## Latest request — isolated A/B memory trials and knowledge portability

2026-10-23 documentation only: see the final curation/experimental-comparison section
of docs/ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md. User proposes testing separated A/B
memory implementations with a switch that need not ship. Recommended design: one
interface, file/transactional adapters, test-only selector, isolated states/caches and
identical tasks/settings; no two branches, dual writes or new memory agents required.
Existing Critic optionally proposes source-linked lessons, corrections and practice
cases; per-claim evidence status matters. User wants acquired knowledge exportable to
a clean platform. Record a versioned selected package with provenance/graph edges,
conditional methods and synthetic checks. This is external knowledge transfer, not
Ollama training or automatic installation of executables; other platforms need a
compatible importer. Both architecture and timing remain unsettled; cross-chat gates
remain. No runtime switch, Git branch, package, model call or live change was requested.

Latest request recorded: compare former diagrams with revised A. See docs/MEMORY_A_GROWING_SHARED_JSON.md for explicit graphs, change table, proposed version-preserving updates and unresolved questions. A growing store is not an ever-growing prompt; source history is retained while retrieval is bounded. No-forgetting shared retention must not silently turn into pruning or be replaced by SQLite.

## Concrete health data-science assignment prepared — 2026-10-23

See [readmission assignment](../docs/HEALTH_DATA_SCIENCE_READMISSION_TASK.md). Task: auditable retrospective recorded early-readmission cohort and subgroup analysis, not just CSV inspection and not a clinical deployment. Original UCI data is not present/downloaded. Next: acquire user/source files, verify codebook/cohort, define an independent oracle, then execute a bounded workflow and expose full-file gaps. Numeric-only calculation inputs, source-specific missing codes and 8 MiB/10,000-row transforms need explicit assessment. Memory remains parked; no analysis, model call, Git or live-service change performed.
