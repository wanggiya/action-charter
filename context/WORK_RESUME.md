# Work resume — checkpoint 28 accepted

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
implementation and acceptance are now complete. Read docs/CHECKPOINT28_CLOSEOUT.md
for the final matrix, manual acceptance, raw-report paths and limitations. It
supersedes earlier open-stage notes without deleting checkpoint history.

Preserve all uncommitted changes. Do not stage/commit/push/merge/publish/release,
modify live PostGIS/GeoServer data, install dependencies or use shared browser
caches. Leave the pre-existing untracked docs/CHECKPOINT25_MANUAL_GIT.md untouched.
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
docs/CHECKPOINT29_PRIVATE_KNOWLEDGE.md defines the ordered implementation and
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

Read this handoff, docs/CHECKPOINT29_PRIVATE_KNOWLEDGE.md and the final
learning-process clarification in docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md
before proposing work. Inspect git status and any applicable AGENTS.md; preserve
existing changes and the user-owned docs/CHECKPOINT25_MANUAL_GIT.md.

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
