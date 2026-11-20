# Work resume — OWNER PRIORITY: first public post by 2026-11-29 (2026-11-20)

Read [LAUNCH_POST_PLAN.md](../docs/product-direction/LAUNCH_POST_PLAN.md). Until the
post, only two tasks run, in parallel and in separate worktrees:
- **P2-DEMO** (due Wed 11-25): polish the demo path (Data Card → approval → report →
  clear refusal); acceptance 5/5 real-model runs in a fresh demo clone. UI polish on
  that path only; no new operations, agents or authority changes.
- **P2-0**: identity check after WSL device-number change (see PHASE_2_PLAN.md).
All other Phase 2 work waits until after the post. Commit locally on the task branch;
do not push (owner integrates).

# Work resume — P2-D3/K inspection-scope repair verified (2026-11-20, #102)

Phase2. Owner authorized continuation; issue102 already open, no overlapping PR.
Preserve all pending P2-0/D2/D3 changes. Git is owner-managed. No Git mutation,
owner secrets/settings/identity edit, dependency/image installation or live DB/
service write. Owner manual testing remains deferred. No new role or operation.

Delivered: six pinned know-how files and one bounded L3 loader; focused descriptive
schemas, receipts in existing UI/CLI/MCP and standalone Planner provenance. A real
failed inspection exposed inspect_postgres_table chosen with CSV arguments. The
conversation generation schema and post-parse/recipe checks now bind clearly
inspection-only proposals to inspect_csv; broader requests/current mixed workflows
retain scope and full global operation policy. Shared conversation paths are covered;
legacy standalone Planner shares the loader but keeps its plan-only contract.
Removed redundant scope prose after a12KB regression; no limit raised/exclusion.

Verification: all3,224 final-source offline IDs passed across four disjoint make test
file groups823/812/748/841, no exclusions/missing/unexpected IDs. Command durations
329.039/191.256/226.591/236.838s, not summed wall time or one invocation. Durable
coverage: benchmarks/results/2026-11-20-p2d3-validation.json. Source/tests/skill assets
match frozen export/tmp/actioncharter-d3-final-rrdjg6w8. Full group logs/tmp/
actioncharter-d3-batch{0,1,2,3}.log. Jobs completed; do not rerun them unnecessarily.
Frontend typecheck/build passed (Vite4.34s, existing chunk warning); actual-API/
fake-model browser valid plan, know-how receipt and refresh same plan/receipt with
zero new calls/submissions/approval/execution/page errors. Screenshot inspected:
/tmp/actioncharter-d3-context.png; log/tmp/actioncharter-d3-browser.log. Fresh profile,
no user cache. Strict634 modules/3178 imports/zero debt; compatibility517 native/
117 retained/290 retired. Final15 doc/context/bounds/redaction checks,507 local Markdown targets, preserved
status-history suffix, whitespace and997 source/test/skill-asset comparisons pass;
details are in the durable report.
Actual wheel/image build remains unverified (optional build tooling unavailable).

Real paired scope check: benchmarks/results/2026-11-20-inspection-scope.json.
Pre-scope source53606022 matches retained diagnostic exactly; same common guidance,
synthetic3-row input, existing local qwen3:4b-instruct, reasoningnone/60s/512 tokens.
Before invalid after2 calls/92.965s; after valid inspect_csv proposal1 call/22.572s.
Three actual provider calls, zero workflow dispatch/authorization. Private0600/tmp
synthetic replies confirmed wrong reader; never add them to source. One fixed-order
pair, uncontrolled warmup/load: no broad reliability or statistical speed claim.
Older failures/timeouts/correction caps remain in benchmarks/results and guide.

Next: representative D3/K method qualification (especially health analysis/report/
refusal and broader requests), then M3 routing under docs/product-direction/
PHASE_2_PLAN.md; do not claim the whole D3/K or Phase2 exit is met by this single
regression. No blind repeats/full B6 matrix. Skills-first, code for demonstrated
missing guarantees/abilities. Owner-deferred acceptance guide: docs/AGENT_KNOWHOW.md.
No owner diabetic-data read or live PostGIS test occurred in this slice.

---

# Work resume — P2-0 implemented and automatically verified (2026-11-18, #100)

Owner merged PR #99 (f237372). P2-0 issue#100 created with approval. Git remains
owner-managed. No branch/stage/commit/push, real identity/config/state edit, secret
change, download, model call or live database/service write.

Delivered: platform/project_recovery.py + thin project-identity CLI options
--preview-recovery / --recover-device / --backup-root / --expected-digest / --offline.
Private verified active-state + original-metadata backup precedes one atomic marker
replacement. UUID/legacy scope/history/claims/config/owner stay unchanged. Strict v1
remains until reviewed recovery; v2 uses kernel filesystem ID + inode, not transient
device number. New adoption uses v2 where usable, strict v1 otherwise. Existing
migration/rename/rollback stay compatible. Original-volume confirmation is necessary
for legacy enrollment; no clone-proof, cross-filesystem or remote guarantee.

Verification COMPLETE; full/focused/browser jobs exited0:
- Full make test:3,160 passed,13 existing spatial warnings,935.56s. Disposable
  source-only export/tmp/actioncharter-p20-validation-lmggmvo0; log/tmp/actioncharter-
  p20-full.log. Interrupted earlier full job lost its /tmp files; no result claimed.
- Final145 affected identity/recovery/workspace/compatibility checks passed59.09s;
  /tmp/actioncharter-p20-final-focused.log. Full export preceded only the final
  backup-parent fsync guard + added fault case. Full3160 plus final145 (144 overlap)
  cover all final3,161 collected IDs,0 missing/unexpected. Not one uninterrupted
  final-source invocation. Coverage/tmp/actioncharter-p20-coverage.json. Final
  source/test bytes match synchronized isolated export; no CI/test exclusions changed.
- make interface-validate passed (build4.64s, existing chunk warning). Final isolated
  actual-API/synthetic-CSV browser passed restored graph/outcome + refresh, same
  run,0 page errors,0 planning/dispatch/authorization calls. Log/tmp/actioncharter-
  p20-final-browser.log; fixture/tmp/actioncharter-p20-browser-6oBeBf. No user cache.
- Strict631 modules/3144 imports/zero debt; compatibility514 native/117 retained/
  290 retired/zero errors. Final context12 passed0.47s after final doc sync;
  log/tmp/actioncharter-p20-final-context.log. Local Markdown file targets
  and whitespace checks passed. Temporary files may disappear on reboot; keep
  these evidence totals and docs/PROJECT_IDENTITY.md as the durable record.

IMPORTANT owner state: earlier pure preview found matching paths/inodes and1,446
files/26,480,480 bytes during the device-number mismatch. On resume, read-only
project-identity status is now STABLE without recovery or any marker edit, consistent
with device numbering returning after restart. Do NOT recover a stable checkout.
Owner launcher/history acceptance is still pending: start normally, reopen a saved
chat/graph/outcome and refresh without regeneration. Recovery commands in the guide
apply only to a reviewed future mismatch; never initialize/rebind/reset this history.

Next: owner startup/history check, then P2-D2 source selection + freshness/reuse before
planning -> D3 + K focused context/agent know-how -> M3 routing -> H + S -> H2.
Phase2 targets/skills-before-code decision are in docs/product-direction/PHASE_2_PLAN.md.
P2-0 is platform enforcement; no new agent/skill/model execution role was added.

---

# Work resume — P1-X and P2-D1 implemented/verified (2026-11-18, #97/#98)

Owner authorized both implementations and creation of issues97/98 (created). No
Git branch/stage/commit/push/merge, secret/owner-setting/live DB change or download.
Preserve all pending M1/M2/M3c/B6 and owner .claude. Git integration remains owner.

P1-X engineering exit evidence: docs/PHASE_1_CLOSEOUT.md. Phase2 dependencies:
docs/product-direction/PHASE_2_PLAN.md; AGENTS now points to it. D1 guide/manual
checks: docs/DATA_CARDS.md. Current status/roadmap/README/CHANGELOG updated.

D1 adds two shared modules: L0 contracts/data_cards.py and L2 data/discovery/cards.py.
Bounded pure projection (8KB/32fields) over existing readers; no scanner/cache or
new role/container/operation/authority. Source/digest/selection/population, candidate
types/roles, available quality/numeric facts; nulls stay unknown, no raw row/category
examples. Explicit selection literals are not anonymized; egress raw fallback stays.
Existing Planner same-turn discovery and recorded context, CLI/MCP and Overview
reuse it. Normal/latest run responses derive cards; original workflow/profile
artifacts store original evidence without consuming budgets for duplicate cards.
Analytical model input avoids a duplicate card; full profile retains it for display.
Malformed optional legacy details omit cards without breaking original saved facts.
Opening/expanding/refreshing adds no source scan, model call or operation replay.

Verification COMPLETE, no tests/models left running:
- Full make test:3,114 passed,13 existing warnings,1209.77s. Frozen source-only export
  /tmp/actioncharter-p2d1-clean-u609f0bo; log/tmp/actioncharter-p2d1-full.log.
- Final80 affected checks passed22.50s after narrow legacy/artifact/context follow-ups;
  log/tmp/actioncharter-p2d1-completion.log. Added6 cases after full collection;74
  overlapping passes. Final3120 collected/3120 passing coverage,0 missing/unexpected
  IDs. Not a single uninterrupted final-source invocation. /tmp/actioncharter-p2d1-
  coverage.json; collected IDs/tmp/actioncharter-p2d1-collected.log. All970 final
  Python source/test files match synchronized export. No test exclusions/CI changes.
- Focused60 passed15.10s; final analytic/card30 passed9.90s; legacy21 passed2.25s.
  Logs/tmp/actioncharter-p2d1-{final-focused,final-analytical,legacy-guard}.log.
- make interface-validate passed12.06s (existing chunk warning). Short isolated
  actual-API/fake-model browser plus CLI/PTY passed card expansion + refresh/latest,
  0 page errors/0 authorization calls; no personal browser cache. Screenshot visually
  inspected. Logs/tmp/actioncharter-p2d1-{interface,final-browser}.log. Full hero
  journey/owner health data not exercised by this short synthetic check.
- Strict630 modules/3140 imports/zero debt; compatibility513 native/117 retained/
  290 retired/zero errors. Final context15 passed0.80s in synchronized source-only export; local Markdown
  targets/public observation privacy/whitespace checks passed. Direct checkout
  context checks6 failed/9 passed because ownership guard reports Copied project
  identity; not a D1 code failure. See operator blocker below.

Real local4B observations: benchmarks/results/2026-11-18-p2d1-card-context.json;
1 call/context, reasoningnone/90s/768tokens. No reader context -> clarification
23.167s,2081 input/58output; same-turn preliminary card -> valid inspect_csv proposal
34.515s,2505 input/214output. Actual reader checks3rows/3fields/hash. No workflow
or authority, owner data/configuration, dependency or DB change. This is current-code
context ablation, not frozen pre-feature code or a speed/reliability improvement.
Deterministic budget/legacy/artifact/context follow-ups happened afterward, tested
with final fixtures; no final-source real repetition claimed. Do not rerun B6 matrix.

Operator verification blocker: current coding-session checkout read-only command
.venv/bin/geoagent project-identity --project-root . exits2 with Copied project
identity. platform/project_identity.py and workspace.py unchanged. Do not edit or
initialize/rebind ownership markers or move state. Asked owner asynchronously to
run same read-only command in usual launcher terminal, distinguish mounted-session
identity from actual workspace problem. Owner confirmed the same error. Read-only
diagnosis: source/state expected st_dev2128, actual2096; source inode783 and state
inode327492 both unchanged; exact source path and state-owner UUID match. This is
consistent with WSL device renumbering after restart; current v1 guard treats it as
a copy. No ownership marker, state/config file or identity code changed. Existing
initialize/rebind are not a valid recovery for this same-path/device-change case.
A separately reviewed offline remount recovery preserving UUID/history/ledger claims
is needed; do not initialize fresh state or bypass the identity check. If same error there, resolve
through a separately reviewed offline ownership recovery before manual frontend/data
testing; do not interpret guard message as permission to reset existing state.

Next: P2-D2 source selection + freshness/reuse scheduling BEFORE planning, then D3
focused context/recipe routing, M3 role budgets and measured CSV/Excel/diabetes hero
journey. D1 does not provide a fresh card before every Send or an automatic cache.
Identity helper requires independently obtained digest/selection; it is not a cache.
Broader dictionary/reader-version lifecycle needs D2. No RL/cross-chat/server/live DB
work is authorized implicitly. Owner decides Git integration; issues remain open for
owner PR linkage. P1-X closes engineering evidence, not every model-quality gap.
Temporary logs/exports may disappear on reboot; public observations and guides stay.

---

# Work resume — B6 implemented/verified; P1-X closeout next (2026-11-17, #96)

Owner authorized continuation. Reused open#96; no new issue, Git action, secret/
owner-setting/live DB/data change or dependency/model download. Preserve all pending
M1/M2/M3c/B6 changes and owner .claude content. Owner controls Git integration.

This slice adds optional bounded failure facts to existing L0 BenchmarkResult and
L6 worker/report/comparison: safe stage/category/correction/known reason, selected
fixed policy codes and schema findings. Existing trusted Planner field formatter,
eight-entry cause cap, six findings of1024 chars; unknown names masked, no raw
model/exception/data/credential export. Legacy unknowns remain. No new agent,
operation, authority, dependency, interface control or native module.

Broader REAL installed-model measurements COMPLETE: all27 declarations per model,
54 observations,27 matching recorded pairs;3 pairs passed on both. Each model
(qwen3.5:9b, qwen3:4b-instruct):4 passed/7 failed/10 deadlines/3 skipped/3 gaps.
Seven deadlines retain completed execution with Critic unfinished; never relabelled
as passes. Quality9B rejected after correction with only a response-level field-rule
finding (exact cause unknown); quality4B planning deadline. Two unavailable-provider
failures do not establish RAM/context overflow. Missing proposal is not a verified
refusal. All failures kept, no automatic timeout/write replay or performance winner.

Evidence: benchmarks/results/2026-11-17-b6-broader-matrix.{json,md}; results index and
docs/BENCHMARKS.md. JSON568133 bytes; source unchanged DURING measurements:
a66b86c82de06fc0d7bbdb9ccea5a2329f82aaa4a741ad30d8af6b0a5373008e.
Final docs removed two stale architecture-status sentences AFTER measurement; that
file is fingerprinted agent context. Native Python/manifests/tasks/settings unchanged;
no post-documentation model repetition claim. Measured architecture preserved in
clean export below. Controller37545 exited0; do NOT restart it. Private audit root
locator/tmp/actioncharter-b6-broader-root; no raw job export. Existing task deadlines
and call bounds; reasoningnone/120s/1024, temporary60s Critic (owner/default15 unchanged).
Only fresh synthetic fixture writes opted in under normal exact-scope approval;
DB/private data opt-ins off. No fixture tests overlapped real measurement.

Verification:
- **make test:3,098 passed,13 existing warnings,924.32s**, uninterrupted source-only
  export /tmp/actioncharter-b6-matrix-clean-m4yh7ke7; CI/GITHUB_ACTIONS/frontend-required,
  -x -rA. Session58908 exited0; log/tmp/actioncharter-b6-matrix-full.log. All967 Python
  source/test files match checkout. No test exclusions/CI changes introduced.
- Focused136 benchmark/qualification/privacy passed93.95s; final16 findings/report
  checks passed8.04s. Logs/tmp/actioncharter-b6-matrix-{focused,final-findings}.log.
- make interface-validate passed4.86s (existing chunk warning), log/tmp/actioncharter-
  b6-matrix-interface.log. No frontend edits this slice; prior isolated actual-API/
  fake-model Settings browser evidence retained, no new owner Save reproduction.
- Strict628 modules/3130 imports/zero upward debt; compatibility511 native/117
  retained/290 retired, zero errors. Public capture metadata/privacy checks and
  local Markdown targets pass. Final context/bounds/redaction15 checks passed0.56s;
  log/tmp/actioncharter-b6-matrix-context.log. Final equality check confirms967
  Python source/test files match; only documented ARCHITECTURE status text changed
  among runtime-provenance inputs after measurement. Whitespace check clean.

B6 is implemented/verified within local/synthetic scope. P1-X is NEXT, not started:
one closeout issue (not yet authorized/created), reconcile Phase1 exit evidence and
remaining limits; owner Git handoff, then Phase2 Data Card/focused context and the
agreed health CSV/Excel hero journey. Do not start Phase2/RL/cross-chat memory or
live database work implicitly. Phase1 is not marked complete by this B6 slice.
M1 owner-reported Save-provider behavior remains unconfirmed; remote/public/vendor
coverage and private-data analytical acceptance unqualified. Existing old pilots and
B5 baseline stay history, not evidence of improvement on matching source/options.

---

# Work resume — B6 broader measurements complete; final regression running (2026-11-17, #96)

The real matrix FINISHED as a recorder: 54 observations/27 comparisons, all27 pairs
matching recorded source/settings/input conditions. Each installed model (qwen3.5:9b,
qwen3:4b-instruct) recorded4 passes/7 failures/10 deadlines/3 skips/3 gaps. Three
pairs passed on both. Seven deadlines preserve completed execution with Critic call
unfinished; no timeout is relabelled a pass. Exact quality9B policy cause remains
unknown beyond safe response-level field-rule finding; quality4B deadline. Two
provider-unavailable failures are not a RAM/context diagnosis.

Public evidence: benchmarks/results/2026-11-17-b6-broader-matrix.{json,md}. JSON568133
bytes; all reports validated at recording, source SHA
a66b86c82de06fc0d7bbdb9ccea5a2329f82aaa4a741ad30d8af6b0a5373008e.
Controller session37545 exited0; do NOT restart it. Private temp project locator
/tmp/actioncharter-b6-broader-root retained for audit only. Summary renderer:
/tmp/actioncharter_b6_matrix_summary.py. No raw job/response/endpoint/key export.
Generation120s/1024/none, temporary60s Critic; existing task budgets retained.
Synthetic fresh file writes opted in only for declared fixture tasks; DB/private
data opt-ins off. No fixture tests overlapped; no owner settings/secret/live DB/
Git/dependency/model change. Source stayed fixed throughout. Old pilots preserved.

FINAL OFFLINE REGRESSION NOW RUNNING: session58908; source-only clean export
/tmp/actioncharter-b6-matrix-clean-m4yh7ke7; log/tmp/actioncharter-b6-matrix-full.log.
CI/GITHUB_ACTIONS/frontend-required, PYTEST_ADDOPTS=-x -rA, explicit export src
PYTHONPATH; make test. Do not launch a duplicate. Interface validate passed4.86s
(existing chunk warning), log/tmp/actioncharter-b6-matrix-interface.log. Strict628
modules/3130 imports/zero debt; compatibility511 native/117 retained/290 retired.
Earlier focused136 checks and final16 findings/report checks passed as below.
No new native module, agent, operation or permission. .claude owner content untouched.

Next: finish/poll regression; source/export equality, final context/Markdown checks;
update CURRENT_STATUS/roadmap/phase Status and this handoff with final evidence.
B6 measurement gate complete, final validation pending. P1-X not yet claimed or
started; closeout preparation stays within#96. Phase2 not started. Owner manages Git.

---

# Work resume — B6 broader measurements in progress (2026-11-17, #96)

Owner authorized broader comparison and closeout preparation; existing open issue96
reused, no overlapping PR. Preserve pending M1/M2/M3c/B6 and .claude. No Git actions,
owner settings/secret/live database changes or new package/model downloads allowed.

Added optional BenchmarkFailureDetails in existing L0 contract; existing L6 worker
captures safe stage/category/correction/known reason/policy code and bounded schema
findings via existing Planner formatter. Eight-entry cause-chain cap, six findings/
1024 chars each, unknown field names masked. No raw exception/response/data copied.
Existing reporting/comparison render these optional facts; legacy unknowns preserved.
No new native module, agent, operation, authority or UI. Census remains628/511/117/290.

Focused benchmark/qualification/privacy136 passed93.95s; final findings budget/report
checks16 passed8.04s. Logs /tmp/actioncharter-b6-matrix-{focused,final-findings}.log.
All source edits must finish before real runs; source consistency is measured.

Next measurement protocol: existing27 task declarations, both installed qwen3.5:9b
andqwen3:4b-instruct, sequential profiles, reasoningnone/120s/1024 tokens and uniform
TEMPORARY60s Critic timeout. Synthetic fresh file outputs may be authorized only for
tasks explicitly marked fixture. Disposable database opt-in stays OFF; both DB tasks
must skip. Optional owner diabetes data stays OFF/missing; three declared gaps remain
unsupported. No owner data/dB/service configuration used. Every case persists progress;
no failed/unknown write is retried and no expired authority reused. Record all failures,
not just successes. Entire model suite can take tens of minutes; communicate progress.

Broader matrix is NOW RUNNING (tool session37545). Controller:
/tmp/actioncharter_b6_broader_matrix.py; log /tmp/actioncharter-b6-broader-matrix.log.
Progress is atomically retained after every case in
benchmarks/results/2026-11-17-b6-broader-matrix.json (complete:false until all54
profile/task observations and27 comparisons finish). Private temp project locator:
/tmp/actioncharter-b6-broader-root. Do not restart/retry cases on recovery; inspect
recorded state/process first. No native source, agents, task definitions, pyproject,
context/ARCHITECTURE.md, SKILLS_INDEX or DECISIONS edits while running; source hashes
are checked. Other documentation/evidence is outside that runtime fingerprint.
Clean test export already prepared: /tmp/actioncharter-b6-matrix-clean-m4yh7ke7.

No concurrent fixture/full tests during real measurements. After all model cases,
validate/retain sanitized comparison evidence, run full make test and final gates,
update current status/roadmap/phase Status and handoff. P1-X not started; Phase2 not
advanced. Do not claim full eligibility/private-data or performance superiority.

---

# Work resume — B6 profile binding/comparison implemented and verified (2026-11-17, #96)

Owner authorized continuation; existing open issue96 reused, no overlapping open PR.
Preserved pending M1/M2/M3c/B6 and untracked .claude. No Git branch/stage/commit/push/
merge, owner profile/secret edits, dependency installation or live database changes.
No new agent role, processing operation, execution authority or interface navigation.

Implemented --profile ID benchmark selection over existing L1 provider/preferences,
without changing active Settings selection. Implicitlocal honors launcher/project
model and reasoning choices. Whole-run model/settings/allowance/review timeout pinned;
selected env credential only, no secret value in stored jobs/reports. Guarded secret
files stay runtime-resolved against configured credential root, no copy/frozen-secret
claim. Workers create one temp profile or verify/reuse an already prepared identical
profile; mismatch refuses without overwrite. Loopback/M2 gates unchanged.

L0 benchmark context adds optional non-secret profile/revision/fingerprint/review
metadata; task records bind full staged-input manifest hashes. Old reports retain
unknown fields. One new L6 apps/benchmark/comparison.py; CLI compare RUN_A RUN_B
renders validated JSON/Markdown over local recorded evidence. Mismatched/unknown
conditions surfaced; deltas only matching passes; no performance winner inferred.
Token sides stay separate. Legacy benchmark token coverage is task-level; partial
calls within an incomplete task are not reconstructed. Existing chat diagnostics
call-level reporting remains separate. No new dependencies or UI controls.

Real local scope: four SEQUENTIAL runs, TWO shipped read-only tasks; no concurrent
fixture tests. UniformNone/120s/1024 tokens and explicit temp60s Critic review;
normal15s/owner settings unchanged. h-describe passed all4 deterministic checks with
complete Critic on9B/4B (106.94s/103.28s;2 calls each). h-quality9B plan policy rejected
after one correction (70.16s,0 operations);4B hit task deadline during correction
(120.07s,unknown execution/usage). Both failures retained, no automatic timeout retry.
Matching recorded pair conditions and unchanged source during all4 observations;
not full27-task comparison/repeated speed evidence/private-data acceptance.
[Capture](../benchmarks/results/2026-11-17-b6-profile-observations.json),
[descriptive comparison](../benchmarks/results/2026-11-17-b6-h-describe-001.md),
[quality comparison](../benchmarks/results/2026-11-17-b6-h-quality-001.md).
Observations precede the final prepared-profile compatibility correction: fresh-worker
behavior unchanged semantically; not a claimed final-source real-model repetition.
Original measured worker copy: /tmp/actioncharter-b6-measured-worker.py.

Verification — complete collection coverage across batches:
- Initial clean-export make test1454 passed, then qualification fixture failed when
  worker tried saving its pre-staged profile (574.60s). Fixed by read-only equality
  verification/reuse, with mismatch refusal. Final91 benchmark/qualification caller
  tests passed97.94s; /tmp/actioncharter-b6-binding-callers.log. Earlier115 focused
  benchmark/privacy/R11 tests passed49.71s before this final compatibility correction.
- Completion make test: **1765 passed**,13 existing spatial warnings,396.01s. Reused
  1329 completed unaffected checks and repeated125 prior affected tests plus all
  remaining/new checks. Union: **3094 collected/3094 passing**,125 overlap,0 missing/
  unexpected IDs. Not one uninterrupted final-source full-suite invocation. No CI,
  Makefile or committed test exclusion changed. /tmp/actioncharter-b6-binding-coverage.json;
  /tmp/actioncharter-b6-binding-{full,completion,collected}.log. Source-only export:
  /tmp/actioncharter-b6-binding-clean-eqv6t9v6; all71 final changed source/test/tooling
  files match completed export. Final documentation follows verification.
- Interface validate passed4.37s (existing chunk warning); no new UI. Existing
  isolated Settings browser passed persistence/shared endpoints/errors/CLI parity,
  2 synthetic calls,0 workflow calls/page errors/secret leaks. No owner Save-report
  reproduction claimed. /tmp/actioncharter-b6-provider-browser.log.
- Strict628 modules/3127 imports/zero debt; compatibility511 native/117 retained/
  290 retired/zero errors.15 context/bounds/redaction passed0.51s; whitespace and
  local Markdown targets verified. /tmp/actioncharter-b6-binding-context.log.

[Commands/limits](../docs/BENCHMARKS.md#saved-provider-runs-and-comparison-p1-b6-96).
Read-only owner config inventory found existing ollama-test (qwen3.5:9b), loopback,
raw allowance, activeprofilelocal, reasoningnone, review15. No endpoint/key printed.
Manual CLI test can use that profile, with Ollama running; frontend/API not required:
.venv/bin/geoagent benchmark run --profile ollama-test --task h-describe-001 --project-root .
Then report returned run_id; compare TWO actual returned IDs. Real observations used
TEMPORARY60s review, not the owner's15s; Critic availability is separate from score.

B6 remains IN PROGRESS for complete controlled-suite profile measurements, then P1-X
closeout. Do not claim2-task observations complete the full suite. P1/Phase2 not
advanced; real diabetes acceptance belongs early Phase2 as agreed. M1 Save-provider
owner report still unconfirmed, though isolated journey and stored profile exist.
All Git integration stays with owner. Prior work follows.

---

# Work resume — B6 first-chat routing/reason fixes verified (2026-11-17, #96)

Owner reported the first new CSV inspection/advice Send failed without a reason.
Read-only owner telemetry showed one qwen3.5:9b Planner call timed out120s with
prompt23780 bytes/schema5317, unknown tokens and no run. The assistant-supplied
sentence reproducibly routed “Do not write files or modify any database” to the
PostgreSQL inspection schema. Source selection now ignores only explicit prohibited
effects, preserves positive work, and focuses CSV inspection-plus-advice on inspect_csv.
Plain metadata behavior and explicit evidence-report scope remain compatible.
Final decoder, deferred-schema repair, deterministic policy and authority unchanged.

Existing submission receipts now store a safe category/fixed reason. Legacy failed
receipts recover a matching retained diagnostic category on read without rewriting
storage. Missing diagnostics stay unknown. Immediate errors scroll into view;
refresh recovery retains the actual reason and never resends planning/execution.
No new agent, operation, dependency, fallback, timeout retry or automatic model-setting
change. Preserve all pending M1/M2/M3c/B6 and owner .claude content. No Git action,
owner settings/secret change or live data/database write was made.

Real local functional evidence: corrected exact sentence supplies inspect_csv with
11439 prompt bytes. Provider-default reasoning still timed out121.128s, one call.
A separate explicit TEMPORARY reasoning-none invocation passed39.008s, one call,
2466 input/225 output tokens and an inspection proposal; no approval/execution.
Not a controlled speed or reliability comparison: load/cache uncontrolled and
fixture tests overlapped. Neither invocation was an automatic retry. Initial /tmp
controller import failed before inference; explicit PYTHONPATH fixed that setup.
[Sanitized observations](../benchmarks/results/2026-11-16-b6-first-chat.json).

Verification — complete collection coverage, not one uninterrupted final-source run:
- Initial clean-export make test:1689 passed before the metadata schema-focus
  compatibility assertion stopped it (676.33s). Narrowed the new path to advice;
  final85 Planner/readiness checks passed29.91s. Sandbox-only HTTP socket refusals
  were rerun with sockets enabled. /tmp/actioncharter-b6-first-chat-compatibility.log.
- Completion make test: **1865 passed**,13 existing spatial warnings,741.03s.
  Ignored154 fully completed unaffected files (1218 checks), repeated all21 prior
  affected conversation-caller files plus the remaining suite. No Makefile, CI or
  committed test exclusion changed. Union: **3083 collected/3083 passing**,471
  overlapping passes, zero missing/unexpected IDs. Evidence:
  /tmp/actioncharter-b6-first-chat-coverage.json; initial/full and completion logs
  /tmp/actioncharter-b6-first-chat-{full,completion}.log. Source-only export:
  /tmp/actioncharter-b6-first-chat-clean-5kdxt5v7. Final changed source/test/tooling
  files match that completed export. Documentation updates follow verification.
- Earlier focused68 passed183.33s; final15 context/bounds/redaction passed0.56s.
  Interface typecheck/build passed4.48s, existing chunk warning. Final fixture browser
  passed usage scopes/export/old API/chat isolation AND visible first-send timeout,
  reason across refresh, no replay, no page errors/workflow actions. Logs:
  /tmp/actioncharter-b6-first-chat-{focused,context,interface,browser-final}.log.
- Strict627 modules/3119 imports/zero debt; compatibility510 native/117 public/
  290 retired/zero errors. Whitespace and local documentation link targets checked.

[Exact manual retest](../docs/REQUEST_DIAGNOSTICS.md#failed-first-submissions--b6-follow-up-2026-11-16):
restart launcher for code, refresh, Settings → Model service → Reasoning effort →
None · no thinking → Use reasoning setting. The saved reasoning preference applies
without another restart. Resend the same CSV inspection/advice message once. The
proposal is not inspection evidence: use Execute for actual results. Inspect latest
submission diagnostics; past timeout usage remains unknown. Reopening past failure
never constitutes a successful retry. Owner model settings were deliberately untouched.

B6 remains IN PROGRESS: saved-profile benchmark binding/comparison then X closeout
are next. No Phase2 feature started. M1 owner Save-provider unresponsiveness remains
unconfirmed. Git integration stays with the owner. Prior work/evidence follows.

---

# Work resume — P1-B6 reported model-token usage slice verified (2026-11-16, #96)

Owner authorized [issue #96](https://github.com/wanggiya/action-charter/issues/96).
Preserved pending M1/M2/M3c and untracked .claude changes. No Git staging, branch,
commit, push, merge, live data/database change, secret edit or dependency install.
No new real-model call was needed for this read-only reporting slice.

Added **Reported model tokens** to Request diagnostics. Input/context and generated
output stay separate; no unqualified total, lifetime billing or byte-transfer claim.
The existing telemetry read aggregates at most100 recent records, deduplicates calls,
uses explicit chat/submission/run links, exposes truncation and missing collection,
and distinguishes unknown, known zero and stopped-before-dispatch. Timing sums model
calls without double-counting parent intervals; output rate includes waiting/load/
context and is not native decoding speed. Role/model details are collapsed by default.
The summary precedes older diagnostics controls so figures fit the narrow panel.
CLI diagnostics and JSON export share the backend projection; Zod preserves additive
metadata. Older APIs keep individual records usable with a restart hint.

Validation:
- Source-only CI/GitHub/frontend-required make test: **3,075 passed**,13 existing
  spatial warnings,895.44s; /tmp/actioncharter-b6-usage-full.log. Export:
  /tmp/actioncharter-b6-usage-clean-6321hoek. Backend/CLI final sources covered.
- Final frontend hierarchy, short control labels and passthrough export adjustments
  were made after that suite. Final interface typecheck/build passed4.82s (existing
  chunk warning); /tmp/actioncharter-b6-usage-interface-final.log. Browser fixture
  journey passed: visible figures, three scopes, exact API/export projection parity,
  old API fallback, chat isolation, no page errors or workflow actions. Screenshot
  /tmp/actioncharter-reported-model-usage.png inspected. Browser log:
  /tmp/actioncharter-b6-usage-browser-verified.log. This is fixture evidence,
  not a new real-model efficiency benchmark or one final-source full-suite invocation.
- Focused telemetry/egress/diagnostics/Planner caller tests119 passed29.74s;
  /tmp/actioncharter-b6-usage-focused-final.log. No full-suite rerun required for the
  separately verified frontend-only final changes.

Final gates: strict627 modules/3117 import occurrences/zero debt; compatibility510
native/117 public/290 retired/zero errors.15 context/bounds/redaction checks passed;
local Markdown link targets and git diff whitespace checked. Final frontend/browser
sources copied into the completed export; this does not imply a full-suite rerun.

[Behavior, limits and manual validation](../docs/REQUEST_DIAGNOSTICS.md).
Next: finish B6 saved-profile benchmark binding and controlled provider comparison,
then X Phase1 closeout. B6 is IN PROGRESS; this slice does not complete it. M3c local
qualification remains as recorded below; remote/public/vendor qualification absent.
M1 owner Save-provider unresponsiveness is still unconfirmed; do not mark it fixed.
Git integration remains the owner's responsibility. Restart the normal launcher to
load the additive backend projection, then inspect existing chat diagnostics; no
Authorize/Execute/model retry is needed simply to view usage.

---

# Work resume — P1-M3c local qualification implemented and verified (2026-11-16, #95)

Existing owner-authorized issue95 reused. M1/M2 and .claude changes preserved. No
Git staging/branch/commit/push/merge, owner settings/secrets/database edits, browser
cache access or model/image download. Only synthetic three-row CSV workflows.

Optional LiteLLM1.109.1 is installed under ignored .local/qualification/venv. Its
117-package hash lock targets Linux x86_64/Python3.12. Installer uses isolated
cache/wheels, leaves .venv alone, passes repeat and UV_OFFLINE=true runs. About
658MiB environment/627MiB download cache. No normal-launcher change or new agent.

scripts/qualification_services.py manages real LiteLLM and a separate Windows
Ollama process. Private child env/HOME/cache/temp/logs, ephemeral ports,420s lifetime
and owned process cleanup. Gateway has no retries/fallbacks/callbacks; generated key
by env reference. Valid-body auth probes prove missing401 and native wrong-key400/
no_db_connection refused before upstream; narrow exception only pinned managed
runtime+exact type+zero dispatch+passing correct-key workflow. Generic400 fails.
Core authorization/client policy unchanged. Shutdown happens before key-log scan.

Windows controller allocates its port on Windows (Linux-free can be host-reserved),
uses PID/start-time guarded process-tree cleanup, records binary identity, reuses
cached weights with no cloud/pruning/pulls, checks blob size/mtime/exact-manifest
inventory. Version-only preflight passed. First workflow used the default empty
cache and failed model lookup with zero operations. Read only OLLAMA_MODELS user
setting to locate actual custom cache, then explicitly reran only secondary.
PrivateHOME/key files deleted with temporary state; normal Windows service untouched.

All SIX modes passed across TWO matching-source captures: direct, compatible relay,
auth relay, isolated worker, actual LiteLLM and owned second Windows Ollama server.
Accepted Planner/execution/Critic on each, one operation/zero data outputs. Matched
runner/worker/controllers/task/native-source fingerprints; unchanged source during
both runs. Prior matrix retains failed secondary attempt; corrected capture is a
separate explicit run, not an automatic retry or single green invocation.
Both models installed: primaryqwen3.5:9b, secondaryqwen3:4b-instruct. Temporary review
budget90s; production default15s retained. No speed/general reliability claim; full
fixture regression overlapped the development exercise. Same runtime vendor and
laptop, separate actual process; vLLM/LM Studio/remote/public coverage unqualified.

[Acceptance manifest](../benchmarks/results/2026-11-16-m3c-acceptance.json),
[exact retained captures](../benchmarks/results/README.md),
[setup/validation and limits](../docs/MODEL_PROVIDER_QUALIFICATION.md).
All earlier Nov15 and Nov16 pilot/configuration failures are retained. Every original
capture complete:false; acceptance_complete:true explicitly combines the two.

Validation: source-only CI/GitHub/frontend-required make test **3,060 passed**,13
existing spatial warnings,1006.40s. /tmp/actioncharter-m3c-managed-full.log; export
/tmp/actioncharter-m3c-managed-clean-qbkpbswg. All58 final changed source/test/tooling files match the tested export. Focused
130 passed10.27s;15 context checks passed0.66s. Strict627 modules/3116 imports/zero
debt; compatibility510 native/117 public/290 retired/zero errors. Installer repeat
and cached-offline checks passed. No M3c frontend change; prior interface checks
retained.444 local Markdown links resolve; whitespace clean. Capture hashes match
acceptance; both private preflight directories/test keys were removed. All owned
services/test processes stopped. .local optional files ignored; source manifests/scripts/tests/evidence only.

Next: B6 provider-profile benchmark comparison, then X Phase1 closeout. M3c local
work is implemented/verified, owner Git integration pending. Keep explicit nonlocal
profiles blocked; no public/owner-data approval follows from local qualification.
M1 unresponsive Save-provider report is still unconfirmed. Do not mark it fixed.
No B6 issue/implementation, Git action or next-phase feature was started.

---

# Work resume — P1-M3c available checks verified; external qualification gaps remain (2026-11-15, #95)

Owner approved [issue #95](https://github.com/wanggiya/action-charter/issues/95).
Preserved all pending M1/M2 and untracked .claude content. No Git staging/branches/
commits/pushes/merges, owner profile/secret edits, real dataset/database writes,
package installation or image changes. M1 unresponsive Save report is unconfirmed.

Added scripts/qualify_model_providers.py over the existing benchmark worker and
shared profile/Planner/workflow/Critic services. Fixed synthetic three-row CSV,
only inspect_csv, no writes/database skills. Temporary projects/profiles, explicit
optional review preference, allowlisted child environment and private HOME/cache.
Default workflow240s/3 calls; request120s/max1536 tokens/reasoning none. Product
Critic default15s unchanged. No automatic timeout retry; existing bounded Planner
correction remains. No new role, routing, product route or native source module.
Worker additions: trusted operation narrowing, Unix model transport, planning-stage
marker, Critic error code and content-free qualification schema/operation findings.

Real direct qwen3:4b-instruct and qwen3.5:9b through compatible/auth relays and a
separate user/network namespace planned/executed correct inspections with no data
outputs. Missing/wrong synthetic keys401; missing reference/over-allowance requests
refused pre-send with zero upstream calls. Onlylo in namespace, different identity,
external ENETUNREACH, successful model access through fixed-route private Unix
broker. Network isolation only: host filesystem/broker/model are outside that
boundary. Relays share Ollama; custom auth relay is not LiteLLM.

Preserved default15s timeouts and explicit60s rejected Critic responses. Diagnosis:
valid assessment schema/status, but three method operations were not observed IDs.
Fix: shared Critic generation schema enumerates successful observed operation IDs;
stopped runs permit no method. Final status/subset validation remains unchanged.
One final isolated REAL workflow passed with explicit TEMPORARY60s: Planner64.654s,
3112prompt/215completion; Critic53.385s,1176prompt/262completion, accepted inspect_csv.
Two model calls, no correction/retry; exactly one operation, zero data outputs.
Source fingerprint unchanged during this accepted run. Ollama0.32.4/Python3.12.3/
httpx0.28.1. Five sanitized JSON captures retained, including all earlier failures.
No speed/general reliability claim; fixture tests overlapped some real development
checks. Each report complete:false because full five-mode qualification is missing.

Verification:
- Source-only CI/GitHub/frontend-required make test: **3,044 passed**,13 existing
  spatial warnings,876.87s; /tmp/actioncharter-m3c-full.log.
- Final three-file difference (Critic service/test and runner provenance) copied to
  that completed export; make test affected callers: **166 passed**,95.70s;
  /tmp/actioncharter-m3c-completion.log. Full-suite plus final-difference validation,
  not a claimed single final-source green invocation. Earlier focused166/55/140
  checks passed. Export /tmp/actioncharter-m3c-clean-a6ef1lye excludes private
  data/settings/secrets/.claude. No concurrent real model during the full suite.
- Interface typecheck/build passed6.00s, existing chunk warning;
  /tmp/actioncharter-m3c-interface.log. No new M3c frontend behavior/browser journey.
- Strict gate627 modules/3116 import occurrences, zero debt; compatibility510 native/
  117 public/290 retired, zero errors. Final15 context/bounds/redaction tests passed
  1.19s;433 local Markdown links resolve; whitespace clean. All52 final changed
  source/test/UI/script/example files match the tested export. No test/model process
  remains running. /tmp/actioncharter-m3c-context-final.log.

[Guide and exact rerun commands](../docs/MODEL_PROVIDER_QUALIFICATION.md),
[retained observations](../benchmarks/results/README.md). No test/model run remains
required after final checks. All source changes remain unstaged for the owner.

Next: M3c stays OPEN: actual LiteLLM authenticated gateway and independent second
runtime/host are not installed/configured. Public API/data-card check not claimed;
explicit nonloopback profiles remain blocked. Do not call relay evidence independent
provider qualification. Choose a reviewed, pinned real gateway/runtime setup, then
use the existing runner with synthetic data. B6 profile comparison and X Phase1
closeout follow the remaining qualification gate. Do not silently advance to Phase2.


---

# Work resume — P1-M2 implemented and verified (2026-11-15, #94)

Owner authorized [issue #94](https://github.com/wanggiya/action-charter/issues/94).
All pending M1/UI changes preserved. No Git staging/branches/commits/pushes/merges,
owner secret/settings edits, real dataset reads or live service/database writes.
M1 owner's unresponsive Save action remains unconfirmed; same-endpoint profiles
passed isolated browser tests and remain allowed. Do not mark that report resolved.

One new L1 module platform/model_gateway/egress.py, existing L0 provider contracts,
private ModelRequest context-part fingerprints and 14 conservative construction-site
wrappers. Copy, classify and enforce before credentials/completion HTTP. Serialized
labels, mutations/appends/schemas and unknown parts cannot lower raw fallback.
Fixed compatibility check is none; most conversations/evidence remain raw. No Data
Card generation, new agent/role, per-role routing or execution authority. Settings
and diagnostics show active/effective allowance, required class and blocked/allowed
verdict. Ordinary nonloopback generation capped none; explicit nonloopback profiles
remain blocked pending M3c. Implicit MODEL_DATA_ALLOWED is pinned with request config;
existing implicit Docker host bridge retained as operator-trusted local runtime.
Monitoring stays best effort. Scoped/standalone configured calls reuse existing
records; rootless embedders use content-free logging. Started allowed calls record
unknown dispatch until outcome, never false no-send evidence on interruption.
HTTP policy refusals use 403 and allowance-specific guidance. [Guide](../docs/MODEL_EGRESS.md),
[decision](../docs/decisions/2026-11-14-model-egress.md), [profiles](../docs/MODEL_PROVIDERS.md).

All **3,028 collected tests have passing coverage across three batches**, proved by
/tmp/actioncharter-m2-final-coverage.json (141 overlapping passes):
- Initial source-only CI/GitHub/frontend-required make test: 1,588 passed before an
  old nonlocal fake hostname was blocked (695.15 s), /tmp/actioncharter-m2-full.log.
- Completion: 496 passed before a nested pytest inherited parent file selectors
  and exceeded 60s (147.76 s), /tmp/actioncharter-m2-completion.log.
- Final: **1,085 passed, 13 existing spatial warnings, 237.74 s**,
  /tmp/actioncharter-m2-remainder.log. Fresh source export /tmp/actioncharter-m2-final-e42vb201.

Four fixture files now use loopback instead of nonlocal mock names; timeout/error/
structured-output assertions preserved. Nested R7 child clears PYTEST_ADDOPTS only;
60s and all165 help hashes unchanged. One diagnostic recursion was interrupted,
no model/product timeout change. This is complete coverage, not a claimed single
uninterrupted green full-suite invocation. No test remains running.

Focused gateway/privacy/compatibility 135 passed (10.85 s), caller/config/conversation
135 passed (28.03 s), final audit checks77 passed (11.88 s), HTTP guidance137 passed
(34.98 s). Interface typecheck/build passed (5.34 s build, existing size warning).
Final strict gate627 modules/3115 imports, zero debt; compatibility510 native,
117 public/290 retired, zero errors. Final isolated browser actual API/gateway plus
fake HTTP model passed save/select/persistence/CLI, synthetic none success and raw
planning refusal: 4 synthetic calls, no fifth HTTP request, zero workflow dispatch,
page errors or key leakage. Screenshot /tmp/actioncharter-m2-blocked.png. No owner
browser/cache or real model calls. Logs /tmp/actioncharter-m2-{http-guidance,browser-final,
interface-final,layers-final,compatibility}.log. Earlier B5 real-model limits unchanged;
this is not a speed/quality improvement or real LiteLLM/provider qualification claim.

Final checks: 15 context/bounds/redaction tests passed (0.74 s), 404 local
Markdown links resolve, whitespace clean. All 48 changed source/test/UI/script/
example files match the final tested export. .claude/settings.json unchanged and
unstaged; no new Git actions. Final log /tmp/actioncharter-m2-context-final.log.
Next: owner manual gate validation/Git integration, then M3c real-provider checks,
B6 profile comparison and X Phase1 closeout. M3c not started. Manual fallback for
unconfirmed profile Save: select local, stop launcher, run MODEL_DATA_ALLOWED=none
bash scripts/start_actioncharter.sh, ask a planning explanation (not an exact
model-free inspection), confirm raw/none/blocked/Not attempted in diagnostics,
then stop and restart normally. Keep writes OFF. No stored review edits or secrets.

---

# Work resume — P1-M1 implemented and verified (2026-11-14, #93)

Settings feedback follow-up: owner could change models but Check was disabled;
read-only running API showed selected=local/revision0/no explicit profiles. Owner
then reported Save looked enabled but unclickable with no console error. Root cause
not confirmed. Same-endpoint profiles are allowed: isolated actual API browser saved
two successfully. Label local as launcher settings, explain disabled Save/check and
unapplied profile choices, validate reserved/invalid IDs locally and display save
errors beside Save. No backend/authority change or owner preference mutation.
Only ModelSettings, its browser test and docs changed after the original export.
Follow-up checks: targeted make test 44 passed (2.48 s), interface typecheck/build
passed (3.91 s build, existing chunk-size warning), final isolated browser passed
missing-field/ID validation, inline conflict, shared-endpoint save, persistence, CLI
parity and format check (2 fake calls, 0 workflow actions/page errors/key leaks).
Logs /tmp/actioncharter-m1-settings-feedback-{tests,build,browser}.log. No full-suite
rerun for this frontend-only feedback change; original batch evidence is below.
M2 not started.

Owner authorized M1; B4/B5+packaging fix merged as d045216 (PR #92). Started clean
main except .claude/settings.json; left unchanged. [Issue #93](https://github.com/wanggiya/action-charter/issues/93)
created with approval. No Git mutations, owner secrets/model preferences/workspace
writes or live database changes. No new agents or execution authority.

Implemented three native modules: contracts/model_providers (L0), platform/model_gateway/
profiles (L1), task_actions/model_providers (L5). Reused gateway/catalogue, lazy config,
request pinning, CLI settings, HTTP settings and ModelSettings UI. Config canonical
workspace model-providers.json via existing atomic JSON + metadata write transaction;
no schema migration. Env/project .secrets references only, privately resolved at send.
Typed profiles, compatible or optional Ollama discovery, explicit synthetic format
check with shared configured timeout capped120/<=3 attempts/<=64 output tokens.
No user-request format downgrade/retry; actual typed validation unchanged. Active
profile/model/limits pin per request; CAS and stale-check guards preserve updates.
Explicit profiles loopback-only; ordinary unclassified requests count raw. Legacy
MODEL_* host semantics preserved; M2 context-part tagging/egress not implemented.
Public diagnostics have profile ID/kind/location, never keys/URLs; successful secret
reflection is rejected. Existing benchmark local stays implicit environment until B6.
CLI models profiles/save/use/list/select/check shares actions with HTTP/Settings.
[Guide](../docs/MODEL_PROVIDERS.md), [decision](../docs/decisions/2026-11-14-provider-profiles.md),
[example](../examples/model-providers/local-proxy.json). B5 evidence untouched.

Verification: final focused security/compat group 61 passed (28.92 s), earlier
105 and 112 focused groups passed; latest privacy group 40 passed (4.22 s). Current
strict gate 626 modules/3091 imports, zero debt; compatibility 509 native/117 public,
290 retired, zero errors. Historical R7/R8 snapshot bytes preserved, only additive
models group/three provider POSTs/one GET asserted separately. Interface typecheck/
build passed (existing chunk-size warning). Isolated browser actual API+CLI, fake
model endpoint, temporary workspace/browser profile passed: persistence, auth,
synthetic schema->object check, reload, return to legacy; 2 synthetic calls, zero
workflow actions/page errors/key leakage. Screenshot /tmp/actioncharter-m1-settings.png.
No owner browser/cache; local cached browser binaries only. Latest source scripts
include scoped matching button styles and exact execution-action audit (history-list
POSTs are reads). Browser final log /tmp/actioncharter-m1-browser-final.log.

Real Ollama qwen3.5:9b synthetic connection only: initial15s legacy probe timed out;
retained /tmp/actioncharter-m1-real-smoke-15s.json. Explicit follow-up at configured
120s: legacy valid JSON29.478s, temporary profile valid JSON2.823s, each29prompt/
6completion tokens. Second call may be warm: compatibility proof, not performance
benefit or full workflow qualification. No owner selection/.env changed, no real
proxy key/gateway qualification claimed. M3c remains. Final evidence:
/tmp/actioncharter-m1-real-smoke.json and /tmp/actioncharter-m1-real-smoke-final.log.

Full source-only CI/GitHub/frontend-required make test started in export
/tmp/actioncharter-m1-clean-etrrlf_d (HEAD + Git-visible tracked/new source, no ignored
inputs/config/private state/.claude). Initial run: 2,766 passed before one obsolete
test_task_actions guard assumed every new native service had a legacy HTTP adapter
(963.03 s, 13 existing spatial warnings), /tmp/actioncharter-m1-full.log. Corrected
that guard to assert model_providers is native and has no legacy adapter; did not
create/retire an adapter or weaken historical compatibility manifests. No production
source changed. Completion make test selected the corrected file and every remaining
test: **208 passed in 56.60 s**, /tmp/actioncharter-m1-completion.log. Collection/set
accounting proves all **2,959 unique tests** have passing coverage (15 overlapped);
/tmp/actioncharter-m1-coverage.json. This is two-batch completion, not a claimed
single green full-suite invocation. No test remains running.

Final checks: 15 context/bounds/redaction tests passed (0.69 s), 390 local Markdown
links resolve, whitespace clean; all 25 changed source/test/UI/script/example files
match the tested export. .claude/settings.json remains unchanged and unstaged.
Logs: /tmp/actioncharter-m1-final-gates.log, /tmp/actioncharter-m1-interface-final.log,
/tmp/actioncharter-m1-layers-final.log, /tmp/actioncharter-m1-compatibility.log.
Next: owner manual provider validation/Git integration, then M2 egress, M3c real
provider qualification, B6 profile comparison and X closeout. No M2 work started.

---

# Work resume — PR #92 fixture packaging fixed and verified (2026-11-13)

Owner committed/pushed B4/B5 as a002609 on feat/p1-benchmark-suite-baseline; PR #92
open. Both remote failed checks (push and PR) show the same four offline test
failures: input/grid.tif missing. Global GIS ignore rules also excluded all four
Shapefile sidecars. Definitions/plans were committed without these inputs; earlier
local exports included ignored files and missed the packaging gap.

Fixed .gitignore with five exact synthetic asset exceptions, CI full-inventory
metadata preflight, one regression and focused docs. Assets unchanged: 1,065 bytes.
Git check-ignore verifies five assets are Git-visible; private GIS/.env/secrets stay
ignored. The preflight checks all required source fixtures before the fast subset,
without reading optional private inputs or dispatching missing-data cases.

Verification: Git-visible export /tmp/actioncharter-pr92-clean-t067_muq was built
from HEAD + tracked fixes + only Git-visible new fixtures, no ignored local inputs.
Full CI/GitHub/frontend-required make test: **2,929 passed**, 13 existing spatial
warnings, **899.28 seconds**; /tmp/actioncharter-pr92-full.log. Focused tests: 21
passed (57.99 s), including all four formerly failing cases and missing-asset
rejection before dispatch. Both working/exported standalone CI gates passed all 4
cases. Final context/link/whitespace checks passed; runtime source/model baseline
unchanged. No frontend code change, image build, model run or live service operation.
Remote logs: /tmp/actioncharter-pr92-failed.log and
/tmp/actioncharter-pr92-push-failed.log. No test run remains active.

Owner still needs to stage the five source fixtures plus the ignore/preflight/test/
documentation fix, commit and push to the existing PR branch, then watch fresh
checks. No Git staging/branch/commit/push/merge performed here. .claude/ untouched;
M1 and unrelated issues not started. Do not rerun the old GitHub commit expecting
these unstaged local fixes to appear. Git instructions are in the conversation.

---

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
