# Checkpoint 27.3 / 27.4d — evidence notes, analysis and graph layout

Implemented 2026-10-20. Builds on the recorded Results workspace without changing
workflow authority, library installation or execution semantics. This is a bounded
analysis foundation, not Tableau/Google/Snowflake/Databricks parity.

## Graph and write controls

Graph layout is presentation state stored per chat in this browser, separately
from plan digests and execution evidence. Reopening/restoring a chat no longer
clears moved blocks. New operations, result and Critic nodes seek unoccupied space;
dropping onto another block finds a free slot. Existing positions take priority.
Both orientations reserve the displayed block footprint. Escape cancels dragging;
Move still controls whether dragging is enabled. Browser storage restrictions
leave in-session movement available. Clearing browser storage loses layout.

Backward/same-column connections use a return lane. Recorded-result evidence uses
a cyan solid line; the separately labelled Critic advisory branch uses a dashed
cyan line. This is not a general obstacle-avoiding edge router: arbitrary manually
arranged graphs can still have crossings. Zoom retains its existing animated
camera rather than re-rendering the graph on each wheel event.

The warning-labelled **⚠ Allow writes** switch beside Authorize/Execute uses the
same backend session policy as Settings. OFF/ON changes invalidate pending write
authority. ON is availability, not approval; fresh exact authorization and Execute
remain necessary. Administrative locks, an unavailable API and pending updates
disable the control. No overwrite permission is added.

## Charts and deterministic analysis

Chart offers ten views: horizontal bar, column, line, area, pie, donut, scatter,
histogram, box plot and summary statistics. Category/value selection and rows,
count, sum, mean, min and max modes are explicit. Presentation settings are saved
per exact chat/run/operation in this browser; they confer no execution authority.

Default charts use at most the first 20 loaded rows and 32 columns. Grouped sample
results are labelled as sample-only. Missing numeric values are excluded; null
categories remain a separate group. Line/area use displayed row order, not an
inferred time axis. Histogram uses at most ten equal-width bins. Box quartiles use
linear interpolation and min/max whiskers, without outlier classification. Pie
and donut reject negative values and non-positive totals. Numeric display is
approximate; tables retain literal stored values. Sample marks select a source
row; grouped sample marks select their first included row. Histogram/box/summary
views describe distributions and do not imply single-row selection.

**Analyze verified CSV** explicitly reads the recorded artifact through the shared
API/CLI preview service, verifies its original SHA-256 and computes an aggregate
from the complete bounded CSV frame, not its truncated preview. It supports up to
100 groups with existing fields and numeric count/sum/mean/min/max contracts.
Invalid mixed/non-finite/oversized values, changed files, unsafe paths and excessive
group counts reject. Null numeric groups remain null (sum is not invented as zero).
Complete results identify source row count, group count and verified scope; their
marks are not linked to arbitrary sample rows. Neither analysis nor viewing runs
a workflow or invokes a model. Counts represent rows, not numeric non-null count.

Use the existing CLI `workflow-runs --request-file ... --project-root ...` with
`action: preview`, exact run/plan/step identity and optional `analysis`:

```json
{"group_by":"region","value":"amount","aggregation":"sum"}
```

This is an optional field in the preview request, not a standalone executable
operation. Existing artifact limits still apply (8 MiB/10,000 rows/100 columns and
bounded pandas memory); this is not an unrestricted query engine. No SQL or Python
expression is evaluated. Full data filtering belongs to the existing validated
workflow operations, not an invisible visualization transformation.

## Geometry and attributes

New vector inspections capture WGS84 Point/MultiPoint, LineString/MultiLineString
and Polygon/MultiPolygon geometry, including polygon holes and bounded attributes.
First-layer bounds: 32 examined features, 2,048 vertices, 12 attribute columns,
160 characters per value and a 64 KB feature payload. A feature exceeding a limit
is omitted whole, with skipped counts; geometry is not silently simplified.
Durable per-step projections additionally fit within 12 KB by omitting whole
features and recording truncation; the larger original operation evidence remains
separate. Legacy non-geometry intermediate previews retain their existing limits.
Unsupported/invalid/empty geometry and non-WGS84 CRS remain explicit.

Map shows boundaries/lines/points, keyboard feature selection, pan/zoom/Fit extent
and a selected attribute panel linked to the feature table. Polygons render below
lines and points, holes remain unfilled, nearby points use nearest-point selection.
Old point-only snapshots still render. Opening old results never rereads current
geometry. Attributes are literal text, including HTML-like strings. All snapshots
remain private recorded data; attribute capture is not a sharing/export action.

This remains an offline longitude/latitude diagram: no tiles, distance accuracy,
reprojection, live PostGIS query, raster display or multi-layer controller is
claimed. Those require the later visualization expansion gate below.

## Optional Critic enrichment

A successful existing Critic assessment may supply a bounded reusable-method note.
The same response is indexed against the exact retained source/evidence; no second
model call is added. Notes are separate from immutable baseline names/tags/method
identity and deterministic validation. Recipe details expose them in an advisory
disclosure with limitations, model and source run. Bounded own-chat Planner retrieval may
include the matching advisory note as untrusted context; it cannot change scope
or execution authority. Indexing failure preserves the
assessment and baseline recipes, and reports unavailable note indexing. The
original chat visibility boundary applies; no cross-chat retrieval is added.
No note implies generalized applicability, installation or execution authority.

## Planner fixes found during actual-model evaluation

Selected operations now include their registry-declared prerequisite/verification
closure. In particular, choosing vector_attributes_to_csv makes inspect_vector
available; it does not approve either operation. Planner receives bounded safe
existence-only references for filenames explicitly supplied in the current turn,
so it need not request a repeated source path. Missing/unsafe paths are not
invented, dataset contents are not inspected by this check, and full validation
still runs before storage and execution. An explicitly requested inspection may
not silently disappear from a returned transform plan. Repeating a known single
source-path question receives one correction; genuine missing semantic questions
remain valid. A narrow explicit inspect/export/group-sum sequence uses typed
argument decoding and a three-operation skeleton; the model supplies semantic
arguments, while existing services allocate omitted output paths and bind required
gates. Backend validation remains authoritative. These guards are not a
general proof that a workflow fulfills arbitrary prose. Existing workflows and
authorization rules remain intact. Occupied proposed CSV targets receive a bounded correction
before review; fixed example filenames are omitted so normal allocation remains
fresh. No existing output is overwritten.

## Acceptance

Automated checks use temporary fixtures and isolated browser profiles, never normal
browser caches or live databases. The expanded Results journey checks all ten
chart views, a 1,500-row verified sum versus sampled values, stale artifact refusal,
polygon holes/lines/attributes, linked selection, repeated insertion, orientation,
resize/expand and layout restoration. Separate write-policy and recovery journeys
exercise toggle invalidation, cancellation and conservative recovery. Local-model
quality is measured separately; see the evaluation report rather than treating
fixture responses as model reliability.

## Later visualization expansion (28.3, after 28.1/28.2)

1. A renderer-library integration with measured bundle/performance/accessibility
   limits; grouped/stacked bars, bubbles, heatmaps and richer temporal axes.
2. Multiple spatial layers, declared-CRS transformation, category/numeric styling,
   legends and optional explicitly configured basemaps; retain offline operation.
3. Shared filter/query specifications, linked cross-filtering across charts/maps,
   persistent analysis views and multi-chart dashboard layouts.
4. Raster/large-data rendering, export and presentation controls, accepted against
   fixed representative fixtures and resource budgets. No product parity claim
   without comparative evidence.

The current small SVG renderers extend existing code without a new dependency.
They should not become an attempt to recreate a general chart/GIS engine. Evaluate
established rendering libraries at the next breadth/performance gate.

## Planner schema failure follow-up

Negative scope such as “No PostgreSQL or PostGIS operations” no longer triggers spatial descriptive schemas for a CSV request. Explicit selected skills still retain their schemas; this is prompt scoping, not a change to allowed operations or execution authority. Extra-field findings provide an actionable removal instruction while suppressing unknown names. The reported 19-schema model failure is not yet reproduced against the live model, so this is not evidence that all schema failures are resolved. CSV inspection alone never creates a PostgreSQL table.

Follow-up verification: `make test` passed 1,828 tests, including explicit negative-scope and safe actionable extra-field findings regressions. No live-model or database retry was performed for this follow-up.

### Existing-inspection calculation follow-up

The exact request “Keep the CSV inspection. Add a calculation creating doubled = amount * 2 for every row. Save the result to a fresh CSV under data/output. Do not use PostgreSQL or PostGIS.” now receives the inspection/calculation descriptive contracts and typed two-operation decoder skeleton when revising a single CSV inspection with automatic skill scope. “Do not use” exclusions are recognized, calculation intent includes the explicit calculation-creating assignment, and the validated base inspection supplies the CSV domain when the follow-up omits the filename. This does not infer formula values, grant authority, or widen the selected operation allowlist. Regression tests cover both “CSV inspection” and “inspection”, safe source/dependency and write gates, plus preservation after two invalid replies.

For the narrow “keep [the/current/existing] [CSV] inspection” plus single-calculation revision, with no newly named CSV input, the decoder also binds the existing inspection arguments and original calculation input. A deterministic post-generation check rejects changed inspection settings or sources, including generic example filenames. Other workflows and explicit new-source requests retain the general planning path; no stored plan or historical evidence is rewritten.

Live follow-up verification (2026-10-20): qwen3:4b-instruct, 120-second timeout, 1,024 output-token cap and reasoning_effort=none, temporary saved sample_orders.csv inspection. The exact follow-up returned inspect_csv plus calculate_csv_columns, preserved inspection arguments and original source, and produced doubled = amount * 2. Final request: 17,446 prompt bytes, two descriptive schemas, 43.205 seconds, first attempt. No workflow authorization/execution or database access. Earlier attempts returned valid plans with inspection argument drift; they failed the independent smoke assertion and motivated the source/settings binding. This single successful trial is not a general model reliability claim.

Final revision checks: `make test` — 1,833 passed; `make interface-validate` — passed (existing bundle-size warning). `git diff --check` passed. For manual follow-up testing, clear optional skill selection to Automatic or include calculate_csv_columns; an inspect_csv-only explicit scope intentionally cannot add a calculation.

### Runtime diagnosis and information panel

Planner diagnostics now identify `csv-revision-v3`; errors without a contract marker are shown as legacy API/restart guidance by the current frontend. This identifies the loaded planning code rather than claiming a disk edit changed an already-running Python process. Calculation descriptive scope is also focused when many optional skills were selected, while preserving the full selected allowlist and existing workflow skills. Non-calculation explicit selections retain their previous behavior. The Inspector has an X close button; closing releases its desktop grid column, a deliberate graph-node click reveals it. Node dragging does not reopen it. Workflow/result/authorization state is retained.

Broad-selection live follow-up also exposed an omitted inspection→calculation dependency. The narrow retained-inspection decoder and deterministic check now require calculate_csv_columns.depends_on=[step_1]; source_step still cannot reference inspection metadata. Missing dependencies receive the existing bounded correction rather than being silently inserted or accepted.

Final broad-selection live trial: qwen3:4b-instruct, 120-second/1,024-token settings, all 18 temporary-project capabilities selected; csv-revision-v3 reported two schemas, 17,799 prompt bytes and 47.414 seconds on the first attempt. Independent assertions verified retained inspection arguments, original calculation source, depends_on=[step_1] and doubled=amount*2. No authorization/execution or database calls. Frontend typecheck/build passed; the 15-case Results browser journey passed, including close/reopen and released graph space, with zero page errors.

Final runtime-diagnosis/dependency/UI verification: `make test` — 1,836 passed; `make interface-validate` — passed with existing bundle warning; Results browser journey — 15 passed; `git diff --check` — passed. No Git publication or live database changes.

### Superseding runtime preflight and Inspector interaction

The extra Information button is removed by operator request; block selection opens and X closes the Inspector. The existing close/released-space behavior stays. API health and startup now use the shared loaded `PLANNER_CONTRACT_REVISION`, replacing the hard-coded schema-correction-v52 label. Startup also prints the imported conversation source path. Before a Planner turn, the frontend performs a no-store health read and blocks an older/incompatible revision before sending the model POST, preserving the saved workflow. The legacy diagnostic marker indicates missing version metadata, not proof of model context overflow; prompt/context limits remain a separate model issue. The browser regression simulates an old health response and asserts zero Planner POSTs, then verifies the actual API revision and normal generation. Read/open-chat paths do not gain model calls or this preflight requirement.

Runtime-preflight/UI verification: `make test` — 1,836 passed after updating the health revision assertion; `make interface-validate` — passed with existing bundle warning; Results browser journey — 16 passed with zero page errors; launcher shell syntax and `git diff --check` passed. No live-model rerun was needed for the runtime/UI-only follow-up; the previous calculation trial remains recorded above.

### Chart value inspection

All ten chart views now expose a shared, non-modal detail card with literal plotted values. Pie/donut slices and legends show share of the plotted total, scatter shows numeric axes, histogram bins show bounds/count, box plots show five-number statistics, and summary values show their statistic. Line/area series clicks select the nearest plotted x position. Enter/Space opens details, outside/blank-chart click and Escape dismiss, and changed data/view/axes clear the card. Row linking is retained for row-backed marks; complete verified aggregates and distribution statistics do not invent a single source-row identity. The existing sample/verified-source labels remain authoritative. Presentation only: no backend/model/tool call, permission change, fresh file read or workflow execution.

Chart inspection checks: `make test` — 1,836 passed; frontend typecheck/build passed (existing bundle warning); Results journey — 17 browser cases passed, covering all ten chart types and verified aggregation with zero page errors or added model calls. Path audit found .env/.secrets ignored and no tracked/nonignored untracked archive/private-key paths; this is not a complete secret-content audit. Remaining operator acceptance uses an existing successful run, checks click/dismiss, refresh/restoration and graph layout, and reviews the intended diff before manual Git actions. Optional Critic model reliability and live PostGIS acceptance remain outside the verified claims above.
