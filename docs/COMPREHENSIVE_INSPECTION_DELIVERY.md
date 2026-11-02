# Comprehensive inspection and Docker worker — 2026-10-25

Implemented scope: CSV/TSV analytical exploration uses a shared all-field profiler,
recorded interactive Outcome and fixed Executor-managed Docker jobs. This extends
[the integrated delivery plan](REAL_DATA_FRONTEND_DELIVERY_PLAN.md); it does not close
the later diabetes relationship-analysis, domain-memory, RL or release work.

## Structure and responsibilities

```text
Conversation / CLI explore-data
          |
          v
Analytical reasoning role (bounded LLM actions, unchanged authority)
          |
   discover -> assess -> profile -> explain
                           |
MCP profile_dataset / CLI profile-dataset ----+
                           |                 |
                           v                 |
               shared typed dataset service <+
                           |
              trusted Executor worker manager
               stage selected files + hashes
                           |
             fixed Docker calculation process
             no LLM, shell tool, network or secrets
             non-root / read-only root and inputs
             private bounded scratch / resource limits
                           |
                 validate report + bindings
                           |
         private immutable JSON artifact + saved chat result
                           |
          graph / Information / tabbed analytical Outcome
```

Planner/Executor/Critic remain responsibilities. This adds a calculation runtime,
not another reasoning agent. Existing explicit grouped non-missing counts and exact duplicate/compound-key quality queries
retain their specialized `profile_table` path and its explicit local subprocess
boundary. Existing metadata inspections and transformations are unchanged. No claim
that every operation now runs inside Docker. MicroVM remains a later adapter with
its own guest kernel; it is not inherently smaller than Docker.

## Results and interpretation

All source fields receive observed types, candidate analytical roles and classification
reasons. Numerical/count candidates get full matching-source valid count, invalid count,
mean, min/max, sample standard deviation and exact linear-interpolation quartiles when
the complete retained values fit the budget. Numeric-looking IDs and coded fields are
not treated as measurements. Interval labels remain ordered categories, preserving text
and leading zeros. Overrides are typed through the shared/MCP/CLI contract; semantic
classification is not an assertion of clinical meaning.

Empty cells and explicitly declared missing tokens are missing; `?`, `NA`, `Unknown`
and other candidate markers are counted separately until a policy declares them.
Numerical calculations exclude nonnumeric/nonfinite values and values above the
supported absolute magnitude of 1e15. Units remain unspecified. Category frequencies,
repetition/distinct counts, codebook mappings and optional grouped measures cover all
matching parsed rows, subject to explicit state budgets. No sample extrapolation.

The model receives at most 16 compact field summaries and 20 groups, with requested
fields prioritized. The saved result retains every field for the frontend. Raw preview
rows and category examples are excluded from this model evidence. Classification name
hints and codebooks are untrusted data. A successful explanation is advisory and is
not a Critic assessment, domain knowledge certification or permission to execute writes.

Outcome tabs are Overview, Columns, Table, Chart, Groups and Checks. Columns selects
any inspected field; Chart uses full-source histograms or exact top-category counts,
with interactive marks. Pie/donut describe displayed categories only. Table remains a
bounded 20-row/16-field preview, clearly distinguished from complete-file summaries.
Groups loads up to 1,000 of at most 2,000 recorded groups. Opening tabs, changing fields
or reopening a saved chat does not rescan data or call the model. Old compact-only
sessions remain readable in Information and explain why a comprehensive Outcome is absent.

## Runtime contracts and limits

- Default `ACTIONCHARTER_ANALYTICAL_RUNTIME=docker`; missing image/daemon fails clearly,
  without automatic host fallback. Trusted explicit `local` compatibility mode uses a
  bounded subprocess and reports **no container isolation**. Browser fixtures use local
  mode intentionally; actual Docker acceptance is separate.
- Image `actioncharter-analytical-worker:local`, pinned to its immutable ID at dispatch.
  Build copies selected standard-library-only sources, excluding datasets, secrets,
  `.env`, Git and browser assets. No image is built for each operation.
- Only verified snapshots of the selected source and optional codebook are mounted,
  individually read-only. No project directory, Docker socket or database credentials.
- Network none, UID/GID 65534, capabilities dropped, no-new-privileges, read-only root,
  one CPU, 512 MiB memory/swap bound, 64 PIDs, CPU time 90 seconds; supervisor deadline
  includes staging. Private noexec scratch 128 MiB and `/tmp` 32 MiB.
- Source up to 1 GiB; source identity verified during staging and after calculation.
  Numeric values retained up to 4,000,000 total for exact quartiles/histograms; unavailable
  results are labelled. Exact identifier/requested distinct counters up to 250,000 per
  field; category counters up to 4,096 per field, shared estimated state bound 64 MiB.
  High-cardinality categorical counts become unavailable rather than sampled estimates.
- Job JSON 16 KiB, report 1 MiB, stderr 16 KiB. Docker jobs are created before attachment
  to avoid a cancellation/create race. Normal success/failure/cancellation removes the
  named job; cleanup failure blocks success and requests inspection before retry.
- Private artifact JSON in `workflow-state/analytical-artifacts`: content hash, owner,
  source/query/runtime evidence, mode 0600. Maximum 128 records / 128 MiB; reaching quota
  requires explicit retention/export/cleanup. Records do not confer execution authority.
  This is a bounded pilot, not an automatic retention/archive manager.

Docker still shares the host kernel. A host/daemon crash can interrupt cleanup and leave
stopped jobs; automated crash recovery and multi-user hardened hosting are not established
by these checks. Worker PID/memory limits are configured and inspected; exhaustive hostile
kernel/resource testing and MicroVM isolation are not claimed. No arbitrary generated Python,
package installation, network research, model fitting or sampling writes are enabled.

## Verification recorded

- Dedicated worker built from the existing cached `python:3.11-slim`; no downloads.
- Actual Docker probes: non-root, input/root writes blocked, host canary/other-job file
  and Docker socket absent, network connection blocked, capabilities dropped,
  no-new-privileges, scratch ENOSPC, memory/PID configuration, concurrent independent
  jobs, cancellation/deadline cleanup. Checks use disposable fixtures only.
- Full diabetes source: 101,766 rows, 50 fields; sample: 5,000 rows, 50 fields.
  All eight numerical/count fields independently matched Python CSV/statistics count,
  mean, min/max and sample standard deviation (relative tolerance 1e-10); distinct
  patients and age/code typing checked. Full source comparison about 12 seconds on this
  laptop. This includes independent validation overhead, not a throughput guarantee.
- Installed `qwen3:4b-instruct` full real-data journey: 5 model calls, 3 tools,
  86.5 seconds, 23.3 KB maximum prompt; correctly selected 101,766 rows, 71,518
  distinct patients and mean stay approximately 4.396. This is one measured case,
  not a reliability guarantee or trained domain knowledge.
- Installed `qwen3:4b-instruct` synthetic journey: 3 model calls, 3 tool calls,
  5,000 rows, 2,500 patients, mean 3; approximately 26.5 seconds, 9.9 KB maximum prompt.
- Isolated browser journey passes analytical Outcome tabs/charts, candidate types,
  left-to-right positions, refresh, saved-plan switching, chat scope and partial failure;
  uses project-local Playwright assets and temporary roots, without browser-cache access.
  The extended journey also passed both real datasets through actual Docker-backed API
  calculations and all-50-field Outcome selection, using a deterministic model fixture;
  the real local-model run above separately validates reasoning/tool selection.
- `make test`: 2,092 passed, 13 existing Rasterio warnings. A subsequent focused run
  passed all 19 dataset/session tests, including the added specialized grouped-count
  compatibility regression. `make interface-validate` passed; production bundle still
  reports its existing size warning. `git diff --check` passed.

Reproduce checks from the project root:

```bash
bash scripts/build_analytical_worker.sh
.venv/bin/pytest tests/test_dataset_profile.py tests/test_analytical_session.py
.venv/bin/python scripts/dataset_worker_acceptance.py --real-data
.venv/bin/python scripts/analytical_loop_model_evaluation.py --real-data
make test
make interface-validate
node scripts/analytical_workflow_browser_check.mjs
```

`--real-data` expects the user's existing files under `data/input/test`; tests copy them
into temporary projects and leave originals unchanged. No live PostGIS/GeoServer access.

## Manual frontend acceptance

1. Start Docker, build the worker once with the command above, then restart the existing
   launcher: `bash scripts/start_actioncharter.sh`. Select your installed working model
   in Settings. This read-only exploration needs no Allow writes or `--enable-write-tools`.
2. Open a new chat and leave the optional skills selection empty. Send:

   > Explore data/input/test. Assess diabetic_data.csv for full-file analysis. Inspect all fields, compute mean time_in_hospital and distinct patient_nbr. Use IDS_mapping.csv for coded admission fields if applicable. Explain observed types, candidate missing markers and numerical findings. No writes.

3. Expect discovery, strategy assessment, profile and Outcome blocks progressing left
   to right. Source selection must be `diabetic_data.csv`, not silently the sample.
   Profile should report 101,766 source rows. A failure/timeout preserves completed
   observations and must not be reported as completed analysis.
4. Click **Analytical outcome** in the graph. In **Columns**, select `time_in_hospital`:
   mean about 4.395986872, min 1, max 14. `patient_nbr` is an identifier, distinct 71,518;
   `age` is an ordered category, `admission_source_id` a coded category. Numeric measures
   are not applicable for these categories. Inspect `weight` and its candidate `?` markers.
5. In **Chart**, select a numerical field, then an age/category field. Try bar and donut,
   click a mark for its counts and click outside to dismiss. These are full matching-file
   distributions, not statistics from the first displayed rows.
6. Check **Table** preview limits, **Checks** source digest/runtime `docker`, and the
   image ID/resource boundary. Drag the result panel divider, expand/restore and close.
   Clicking a profile block should still open Information.
7. Refresh/reopen this chat: same facts without new model calls, scans, approval or run.
   Try a normal inspection plan, switch back to the saved analytical graph, then open a
   new chat to confirm isolation. Do not expect an older compact-only session to acquire
   new statistics without a fresh exploration request.
8. In a separate new chat repeat with `diabetic_sample_5000.csv` explicitly named. Expect
   5,000 rows and an unverified candidate sample warning; no claim that its totals describe
   the full dataset. Stop on failures and retain the reported stage/error for diagnosis.

Next: full health-data quality/relationships task, better categorical/group exploration,
explicit role/missing-policy refinement, bounded approved sampling if necessary, then
private domain knowledge/memory and evidence-based learning evaluation. These remain open.

## Frontend ↔ CLI continuity — 2026-10-25

User requirement: CLI work must continue frontend work and frontend work must continue
CLI work, including saved chat, current server-side proposal and recorded analysis. This
is one project/API workspace, not copied JSON transcripts or a separate CLI agent memory.

Implemented commands connect to the **running existing interface API**, default
`http://127.0.0.1:8765`. No separate CLI model configuration is needed: they use the API's
selected model, capabilities, conversation coordinator, submission receipts and state.
An alternate loopback port is supported via `chat --api-url URL` or
`ACTIONCHARTER_API_URL`. Remote endpoints, redirects and environment proxies are disabled.
The CLI working directory does not choose the API project: the launcher owns that root.

```bash
# Keep the normal launcher running in its terminal; use a second terminal here.
.venv/bin/python -m geoagent_harness.cli chat list

# Copy the desired 32-character chat ID from that list once.
CHAT_ID=replace_with_the_actual_chat_id
.venv/bin/python -m geoagent_harness.cli chat show "$CHAT_ID"
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view overview
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view columns --field time_in_hospital
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view table --offset 0 --limit 10
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view chart --field age
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view groups
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view checks

# Explicitly continue this same chat; a new calculation is possible for exploration.
.venv/bin/python -m geoagent_harness.cli chat send \
  'Continue exploring. Group diabetic_data.csv by age and readmitted. Compute mean time_in_hospital and distinct patient_nbr. No writes.' \
  --chat "$CHAT_ID"

# Omit --chat to create a new chat, discoverable in the frontend chat list.
.venv/bin/python -m geoagent_harness.cli chat send 'Inspect sample_orders.csv. Return row count and column names. No writes.'
```

Use an existing comprehensive analysis chat for `chat result`; an inspection-only plan
without such a record produces a clear unavailable message. `--source filename.csv`
selects among recorded sources; ambiguous choices fail rather than silently choose.
`--field`, `--offset`, `--limit` select/paginate **saved evidence** without scans/models.
Columns covers every profiled field; Table is the saved bounded preview. Chart is an
ASCII count distribution from the same full-source bins/top categories, not a raster
copy of the graphical chart. Groups requires a recorded grouped query; absent groups
are not computed automatically by viewing. JSON is available with `--json` on every
command; result JSON retains statuses, source hash, chat/analysis revision and scope.
Existing `profile-dataset` and `explore-data` standalone commands keep their original
semantics; use `chat send` for frontend-visible conversation continuity.

After CLI work, click the **Refresh saved chat** icon beside Planner agent. It reloads
that chat and the saved-chat list, restores the chat's latest saved proposal/analytical
record and preserves an unsent message. It is disabled while sending/loading or while
unsaved graph edits exist. Refresh is explicit: no polling or automatic replacement of
work in progress. A CLI-created chat appears in the refreshed list; selecting it restores
its own state. Browser-local chart/tab/camera choices are not synchronized through CLI.
Unsaved browser graph edits and drafts are not transmitted to the CLI.

`chat send` preserves the server-side chat proposal; it never substitutes another chat's
workflow. It inherits the chat's selected skills unless `--skill NAME` or
`--automatic-skills` is supplied, and uses the last recorded history setting unless
`--history`/`--no-history` is explicit. The browser's memory-switch preference remains
browser-local; this command does not change that switch or introduce cross-chat memory.
`--expected-revision N` allows deliberate stale-state protection. Revision conflicts
fail without overwriting newer work. Without it the CLI reads the latest revision before
sending; a concurrent change still fails server validation.

Before sending, stderr prints chat/submission IDs and a recovery command. If a response
is lost, **do not resend automatically**. Read status instead:

```bash
.venv/bin/python -m geoagent_harness.cli chat receipt CHAT_ID SUBMISSION_ID
```

All send requests use `inspect_on_send=false`: planning stays planning; explicit
exploration can run its bounded read-only tools. These commands never enable writes,
authorize a workflow or dispatch Execute. Existing governed workflow commands remain
separate. Saved checks do not prove that current source files are unchanged. HTML/SVG
exports, interactive terminal sessions and readable views for every older workflow-run
format are not added in this slice.

Verification: focused tests cover bidirectional state/revision continuity, stale rejection,
receipts, shared-result parity/no rescan, preview scope, unsafe URLs, no automatic retry
and terminal control-character sanitization. The browser journey exercises frontend
analysis → CLI recorded field view → CLI plan continuation → Refresh saved chat →
frontend continuation → CLI read, preserving an unsent draft and chat identity. It uses
temporary fixtures/API/model and project-local Playwright, not personal browser caches.
Chart/field selectors now share existing result-control styling.

Continuity slice verification: `make test` passed **2,097 tests** with 13 existing
Rasterio warnings; `make interface-validate` passed with the existing bundle-size
warning. The extended browser journey passed both directions and a CLI-created chat
continued in the frontend, without page errors. Source data, live services and Git
index/history were unchanged. Full statistical-task acceptance remains subsequent work.

## Interactive selected columns and grouped percentages — 2026-10-25

User acceptance requirement: choose age alone and see age alone; choose age plus
readmitted and see that combination, with percentages rather than unexplained decimal
proportions. Static initial-preview columns and the original saved grouping are insufficient.

Implemented in the analytical Outcome:

- **Table:** choose Column and optional Additional column, then **Load selected columns**.
  A hash-verified full-source read produces a bounded 20-row page containing exactly
  those fields, even when readmitted is outside the original first 16 preview columns.
  Previous/next source pages are explicit reads. Table is individual source rows, not
  category counts; Groups provides summary counts/percentages.
- **Groups:** choose Group by and optional Split by, then **Apply grouping**. Age alone
  gives one row per age band. Age/readmitted gives one row per observed pair. All
  matching parsed source rows contribute, under the original filters/missing policy.
- Display **Rows**, **Percentage** formatted with `%`, and the actual **Denominator**.
  Choose All matching rows, or Within each first-field group. The latter is available
  for two-field grouping: for age/readmitted it means the readmission distribution
  within each age band. One-field age percentages default to the full matching source.
- Group table/chart share the same recorded counts and selection. Changing presentation,
  chart type, metric or percentage basis does not reread the source. Charts offer count
  or percentage; clickable marks show count, percentage and denominator. Pie/donut is
  unavailable for within-group percentages with separate denominators; use bar/column
  or the common overall denominator. Charts require <=100 groups; all groups remain
  accessible in a paginated table (100 loaded groups/page, <=2,000 calculated groups).
- Empty and marker groups remain present. These are **row percentages**, not distinct
  patient percentages. No clinical category is silently removed or recoded. Grouping
  individual identifier fields is blocked; source Table paging can still show selected IDs.
- Draft selector changes are labelled until applied. Previous results remain during
  calculation/failure. Stop waiting cancels the browser request; a backend job may still
  finish within its bound and save a result. No automatic retry or model call.

For count n, total matching rows N, and rows in age band A:

```text
Percentage of all matching rows = 100 * n / N
Percentage within an age band   = 100 * n / A
```

Within-age percentages sum to 100% separately for each age band; they must not be
summed across age bands. Overall percentages sum to 100% across all observed groups.
Rounding display to two decimal places may make displayed sums slightly differ from 100%.

Shared implementation: `/api/v1/analysis/view` and the typed MCP tool
`explore_dataset_view` use `tabular/dataset_views.py` and the same Docker-backed
`profile_dataset` service. Requests identify a chat revision, saved profile digest and
source digest; paths/codebooks are resolved from the saved record, never supplied as
new authority. Full source/codebook hashes must still match. Concurrent chat changes
reject publication. No change to chat transcript/proposal or write authority.

Each chat retains its latest table selection and latest grouping separately in its
bounded project SQLite store. Opening the same Outcome tab restores the saved result
without recomputation. This is not general workflow-version history. Saved results do
not prove present source freshness. A failed calculation preserves the previous saved
selection. New interactive reads do not create an additional full-profile artifact for
every click. Original source and saved inspection remain unchanged.

CLI shares those saved selections:

```bash
# Explicit new group calculation, no model call; use your real chat ID.
.venv/bin/python -m geoagent_harness.cli chat explore "$CHAT_ID" --group-by age
.venv/bin/python -m geoagent_harness.cli chat explore "$CHAT_ID" --group-by age --split-by readmitted
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view groups

# Explicit selected-column page; restore the same table in the frontend.
.venv/bin/python -m geoagent_harness.cli chat explore "$CHAT_ID" --view table --column age --column readmitted
.venv/bin/python -m geoagent_harness.cli chat result "$CHAT_ID" --view table
```

`chat result` reads the saved interactive selection when one exists, otherwise the
original recorded groups/preview. JSON retains both numerical percentage fields;
human terminal groups show percentage signs and name the bases. Table view is still
bounded; it does not claim the loaded rows comprise the full file.

Validation: known-answer fixtures cover empty/marker categories, selected columns
outside the original preview, overall and within-primary percentages, saved restoration
without rescans, changed source/profile/chat rejection and concurrent publication guards.
MCP/CLI view parity is checked against the same saved groups. Actual Docker acceptance
on temporary real-data copies independently confirmed 10 age groups and 30 age/readmitted
pairs for both 5,000 and 101,766 rows, with exact count comparisons and percentage
agreement to 1e-10. Full-file profile plus three selected-view reads and independent
checks took about 43 seconds for the full dataset; this is not single-click latency.
Browser acceptance exercises selection changes, denominators, chart details, exact table
columns, restoration and CLI continuity with an actual Docker-backed temporary API.

Manual retest:

1. Rebuild worker after this update: `bash scripts/build_analytical_worker.sh` (already
   rebuilt during development), restart the existing launcher and refresh the browser.
2. Open your comprehensive diabetes analysis chat and click its Analytical outcome.
3. Table: select age, no additional column; Load selected columns. Then add readmitted
   and load again. Only the selected field(s) should appear beside the row index.
4. Groups: age + None → Apply grouping: expect 10 observed age bands in this dataset.
   Add readmitted → Apply grouping: expect 30 observed pairs. Check Rows and Percentage.
5. Switch Percentage of from All matching rows to Within each age group. For any age
   band, its three readmission percentages should total approximately 100%.
6. Switch Group chart, click a mark, inspect its count/percentage/denominator. Return to
   the table. These presentation changes must not trigger a new calculation.
7. Reopen the tab/chat and compare `chat result ... --view groups`. The same last saved
   grouping should be available. Changed-source errors must preserve the earlier result.

Remaining scope: richer filters/measures, statistical relationships, historical workflow
navigation and a persistent terminal workspace are separate work. No Tableau-parity,
clinical inference or predictive capability is claimed by this grouping improvement.

Final checks for this slice: `make test` passed 2,101 tests with the same 13 Rasterio
warnings. A subsequent focused run passed all 15 dataset-view/profile/CLI tests,
including the added MCP/CLI saved-percentage parity case. Frontend typecheck/build
passed (existing bundle-size warning). Actual-Docker browser acceptance passed without
page errors; saved CLI group percentages matched the frontend grouping. `git diff
--check` passed. No original data, live database, Git index or history changed.

## Main Outcome page and field inspection — 2026-10-26

Outcome now replaces the workflow graph area by default, with an open Planner conversation
retained alongside it on wider screens. Flow graph (header or top navigation) returns to
the existing graph. Results remain mounted while hidden, preserving loaded previews and
view state; another chat/run/source still has its own scope. Analytical field/tab choices
also have optional per-chat/revision browser-session preferences. No source scan/model
call is caused merely by switching pages or selecting a recorded field.

Columns includes a searchable field browser and detailed profile: observed type, candidate
role/reason, missing counts/percentage, distinct and repetition counts, appropriate numeric
summaries, candidate missing markers and top recorded category frequencies/definitions.
For age, band labels and full-matching-source percentages are displayed; a numeric mean
is not invented for age-band text. Counts/percentages for omitted top-category values are
not extrapolated. Legacy metadata-only runs retain their recorded detail/explicit quality
read controls; missing historical statistics are not manufactured.

Workflow history has a visible action in both the Outcome header and graph controls,
opening the existing frontend chat history. Historical Outcome has an explicit Return to
current workflow action as well as Flow graph navigation. At narrow widths, history opens
the Planner/graph view so it remains accessible.

Terminal `/columns age` includes saved category frequencies and percentages. `/chart age`
shows text bars and counts/percentages; `/chart groups total` or `/chart groups within`
shows the saved grouping with explicit overall/within-first-field bases. More than 100
groups must use the table or a refined grouping; they are not silently truncated into a
chart. `/charts` lists commands and F5 opens a recorded chart in full-screen mode.

[Real-data next targets](REAL_DATA_NEXT_TARGETS.md) records Target | Requirement |
Functions/ability to add | Expected outcome. Complete the readiness report and a small set
of descriptive comparisons before claiming inferential/model/pipeline capabilities.

Validation: `make test` passed **2,109 tests**, with the same 13 Rasterio warnings;
`make interface-validate` passed with the existing bundle-size warning. Combined browser/
real-PTY acceptance passed for page width, field details, percentage facts, history,
restoration and terminal age/group charts. Legacy executed-result regression passed
for tables/charts/maps/checks, preserved previews, source-change rejection, delayed
responses/chat scope and graph placement. Browser assets were project-local; tests used
disposable fixtures and no live service calls. Original datasets and Git index/history
were unchanged.

Retest after restarting the existing launcher and refreshing the browser:

1. Open your comprehensive diabetes analysis → Outcome → Columns → age. Inspect band
   frequencies, percentages, missingness and classification. Search/select another field.
2. Click Flow graph, then Outcome again. Confirm the graph/workflow and loaded result
   remain, with age/Columns selected. Outcome should fill the graph area rather than a
   narrow side panel. Workflow history is accessible directly from this page.
3. In `./actioncharter`, open the same chat and try `/columns age`, `/chart age`,
   `/chart groups total`, `/chart groups within` (a saved grouping is required).
4. Use the target matrix to plan the data-readiness report; statistical relationships,
   adjusted models and later domain-method learning are explicitly still future work.

### Compact graph navigation — 2026-10-26

Graph to view now sits below the workflow title, beside a matching 32px Refresh
and Workflow history action group. Narrow graph panels wrap that action group
together; status counts sit underneath. Refresh uses a refresh icon, and the
selector has a dropdown indicator. Existing source groups/history behavior remains.
Validated with interface typecheck/build and isolated browser checks at 1600,
1100 and 850px, including source menu opening and the read-only outcome journey.
