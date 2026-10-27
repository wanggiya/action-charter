# Real-data work after inspection — acceptance targets

2026-10-27 design: [generalization/consolidation](GENERALIZATION_AND_CONSOLIDATION_PLAN.md)
records how to pursue these targets through shared contracts/adapters and reusable skills,
instead of binding product behavior to the diabetes data or adding per-dataset services.

2026-10-26: [real diabetes frontend test flow](DIABETES_REAL_TEST_FLOW.md) now records
actual files, measured expectations, sectioned-codebook decoding and temporary database
round-trip acceptance. Earlier proposed/unverified statuses below remain historical.

Recorded 2026-10-26. Use the existing diabetes source, supplied codebook and sample as
an engineering/science acceptance task, preserving originals. This table joins the
[existing diabetes task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md), not a replacement
checkpoint sequence or a claim that every row below is implemented.

| Target | Requirement | Functions/ability to add | Expected outcome |
| --- | --- | --- | --- |
| Useful Outcome workspace | See results across the graph area and return without regenerating; choose a specific field such as age | **This slice:** Outcome as the main workspace page; field browser/search and detailed numerical/category/missingness views; explicit graph return and frontend history access | Age bands, counts and full-matching-source percentages are directly visible; the workflow is retained |
| Terminal visual inspection | Inspect distributions without a graphical browser or new model call | **This slice:** discoverable field charts, F5 chart shortcut, saved grouped-percentage charts with named denominators, richer `/columns FIELD` frequencies | `/chart age` and `/chart groups within` show bounded text charts agreeing with recorded frontend facts |
| Dataset meaning and row grain | Understand collection/population scope, encounter keys, patient repeats and what labels mean | Reuse supplied codebooks/provenance checks; add a compact editable, versioned analysis specification and a record of unresolved definitions | A named analytical question with explicit row/patient grain and verifiable assumptions |
| Unified data-readiness report | Assess missing markers, uniqueness, duplicates, types, numerical distributions and code coverage across the complete source | Reuse existing exact quality/profile/group tools; compose results into one source-bound report with coverage and unavailable checks | A reproducible report identifying usable fields and actual issues rather than a generic model summary |
| Reliable ID/codebook joins | Decode admission codes without duplicating or dropping encounters | Expose validated many-to-one mapping/joins, duplicate code checks, unmapped-code counts and before/after row reconciliation | Readable categories with documented unmatched values and unchanged intended row grain |
| Explicit preparation policy | Treat meaningful categories separately from missing values; no invented clinical exclusions | Versioned missingness, type and exclusion policies; before/after row/patient counts; preview proposed transformations before retained writes | An analysis-ready view whose transformations can be explained and rerun |
| Descriptive population comparisons | Compare age, admission source, prior utilization and recorded readmission categories | Extend existing grouping with convenient cross-tabs, row/column/overall percentage bases, totals, missing/sparse-group visibility and saved queries | Correct counts and interpretable denominators for each comparison; grouped unique-patient totals are not incorrectly added |
| Group distribution analysis | Understand skew and variation rather than only group means | Bounded per-group count, mean, sample SD, median, quartiles/range with declared exactness/budgets; comparison plots based on these aggregates | Useful length-of-stay/prior-use comparisons that do not treat codes or age bands as continuous measurements |
| Relationship and uncertainty analysis | Quantify differences while accounting for repeated patients and missingness | Small validated typed association/effect-size tools; supported patient-cluster uncertainty methods with seed/resource controls; assumption and sparse-data diagnostics | Effect estimates and uncertainty with recorded methods, references and limitations; unsupported cases fail explicitly |
| One interpretable adjusted analysis | Separate unadjusted patterns from associations conditional on selected variables | A deliberately scoped statistical-model operation, categorical references, missingness policy, patient-cluster support where available, convergence/rank/separation checks | A reproducible exploratory adjusted result with diagnostics; no causal or clinical-performance claim |
| Prediction only when justified | Prevent patient overlap and future-information leakage | Explicit target/timing audit, patient-disjoint evaluation, a simple baseline, appropriate evaluation and subgroup/calibration checks; separate from exploratory fitting | Honest out-of-sample evidence, or a clear finding that the available data/design is unsuitable |
| Communicate supported findings | Statements must trace to computed facts rather than fluent invented numbers | Planner explanations over bounded evidence; Critic checks claim support and assumptions; link report statements to saved tables/checks | A concise findings report that distinguishes facts, interpretations and unknowns |
| Reproducible engineering pipeline | Prepare, join, validate and rerun compatible inputs reliably | Reuse typed operations/recipes; add missing schema/key/schema-drift checks, provenance manifests and deterministic reconciliation | An end-to-end inspect → prepare → compare → verify process usable from frontend, terminal and CLI |
| Retained outputs and handoff | Save useful cleaned tables/reports without overwriting originals or silently granting permission | Add only needed typed export/format operations; fresh targets, checksums, schema/count verification and normal Allow writes → Authorize → Execute | Verified deliverables that another analyst can use, with source and transformation history |
| Larger-data feasibility | Decide execution strategy from operation/data characteristics, not just model context size | Extend existing assessment with measured chunk/cardinality/resource strategies; approved sampling with method/seed/source identity only when needed; explicit progress/cancellation | Full-file results when feasible and clearly sample-scoped results otherwise, with no silent substitution |
| Recovery and operational checks | Failures must identify partial outputs and permit deliberate safe recovery | Exercise existing durable runs/cancellation/retry; add gaps only after the end-to-end task reveals them; input/hash/authority checks before reuse | No automatic repeat of writes or reuse of expired/mismatched authority; recoverable recorded attempts |
| Portable, reusable domain methods | Reuse verified preparation habits without spreading raw patient data or unsupported assumptions | Later opt-in knowledge/method extraction, scoped evidence/expiry/conflict handling and reviewed export/import; retain the recorded memory designs | Transferable, qualified method knowledge rather than a claim that model weights were trained by using the dataset |

## Working order and evidence

First complete a **data-readiness report**, then a small prespecified set of descriptive
readmission comparisons (age band, admission source and prior inpatient use). Reuse
implemented primitives before adding services or agents. Statistical uncertainty and
adjusted analysis require actual tested methods; do not claim them from chart output.
Prediction and portable domain memory are later, separately validated objectives.

For each stage record the request/specification, independently established expected
answer, actual result/source hashes, denominator/exclusions, resource use, model calls,
user interventions and any missing capability. Compare equivalent frontend, terminal
and CLI requests. Small known-answer fixtures precede temporary sample/full-data copies.
The existing full-file inspection check is not evidence of arbitrary massive-data scale.

Do not silently remove unusual rows, decode clinical labels without a supplied definition,
invent chronology or assign numeric meaning to identifiers. Read-only calculations need
no dataset-write authorization; saving a new/overwritten dataset still does. No live
PostGIS/GeoServer operation, Git mutation or publication is authorized by this plan.

## Two-variable cross-tabs and PostgreSQL round trip — 2026-10-26

User-requested next design; documentation only, not implemented by this update.

### Cross-tab presentation

For two categorical fields such as age and gender, put one field on rows and the
other on columns; each cell contains the count for that combination. Provide swap
axes, totals, and count / row percentage / column percentage / overall percentage
controls with explicit denominators. Keep missing/unknown categories visible and
use supplied codebook labels where available. A single field keeps its frequency
table. Numeric fields need explicit bins or an explicitly selected aggregate;
never silently treat identifiers or bands as continuous measurements.

Frontend and terminal/CLI must agree. Preserve and reopen the selected view; support
bounded displayed categories, horizontal navigation and a readable terminal fallback
for wide tables. Display bounds must not truncate the population used for aggregation;
report undisplayed categories and coverage. Zero-count combinations and undefined
percentages must be distinguishable. Use known-answer fixtures to verify counts,
marginal totals, missingness, percentage denominators and axis swapping.

### Authorized PostgreSQL import and export

The real-data task should extend beyond inspection: load a prepared tabular dataset
into a PostgreSQL table, query/check it, then export a selected result to a new local
file. Here **unload means export**, not DROP, TRUNCATE or deletion of database rows.
Any destructive cleanup is a separately scoped, explicitly authorized operation.
Existing spatial/PostGIS capabilities must be inspected and reused where compatible;
they do not establish that ordinary CSV-to-PostgreSQL import/export is implemented.

| Target | Requirement | Functions/ability to add | Expected outcome |
| --- | --- | --- | --- |
| Prepare a loadable table | Preserve identifiers, explicit null markers and declared types | Source-bound schema mapping, bounded preview and preflight validation | Reviewed database schema with no silent coercion or lost leading zeros |
| Import into PostgreSQL | Review connection profile, schema/table and create/append/replace effects | Typed import operation, credential references, identifier validation, transaction/staging strategy and progress/cancellation | Verified table, row reconciliation and recorded partial-output/recovery status |
| Inspect/query stored data | Repeat useful analysis after loading | Bounded, validated read-only table discovery and query/aggregation contracts | Database counts, nulls, keys and grouped results agree with the prepared source |
| Export from PostgreSQL | Save a selected table/result without changing database rows | Typed export with approved local target, bounded streaming/resource strategy and manifest | Reopenable output with verified schema, row count and declared precision/null semantics |
| Complete the round trip | Compare semantic data, not just byte layout | Deterministic checks for counts, keys, selected values/aggregates and encoding/types | Source → prepared data → database → exported data reconciles, or differences are explicit |

Use the existing Allow writes → Authorize → Execute flow for database imports and
file exports; bind authority to the exact reviewed operations, source and destination.
An export reads the database but writes a file, so it still requires write authority.
Read-only queries may execute through the normal read-only path. Context text, model
output and old approvals cannot authorize writes. Never expose passwords in graphs,
chat, evidence, exports or logs. Define safe append/retry behavior before claiming
retry support; transaction boundaries and partial completion must be explicit.

Acceptance uses temporary fixtures and a disposable test database, not the user's
live service without explicit permission. Include a failed import, cancellation and
a deliberate retry to verify no silent duplicate inserts or automatic write replay.

### Coherent next real-data workflow

1. Inspect full-file quality and establish row grain/codebook meaning.
2. Preview explicit missing/type policies; join codebooks and reconcile row counts.
3. Compare age × gender/readmission using cross-tabs and descriptive aggregates.
4. Produce a source-linked readiness report with unresolved issues.
5. With explicit authority, create a prepared output and import into a test database.
6. Inspect the loaded table, export a selected result with authority, then reconcile.
7. Save a reusable validated workflow with provenance and visible recovery options.

This is an engineering/descriptive-analysis milestone. Association tests, uncertainty,
models, scheduling/incremental ingestion and portable domain learning remain separate
extensions; neither a successful chart nor a successful import proves those abilities.

### Cross-tab delivered slice and durable next steps — 2026-10-26

Two-field Outcome → Groups → Group table now displays a cross-tab with count,
row/column/overall percentages, totals and swap axes. It uses all recorded grouped
counts. Display pages cap rows at 25 categories and columns at 12, keeping full
marginal totals/denominators; one-field frequency tables and group charts remain.
The grouping selection is already saved/shared through the existing API/history.
Cell measure and swapped orientation are local display settings, not new saved queries.
No new MCP operation, model call or source read is required to pivot a saved grouping.

Terminal `/groups age gender` calculates and saves the shared grouping;
`/columns age gender` is an explicit alias for that full-file read-only calculation.
`/crosstab count`, `/crosstab row`, `/crosstab column` and `/crosstab total swap`
render recorded groups without recalculation. Noninteractive `chat result --view groups`
returns the matrix too. Terminal display caps at 25 row / 12 column categories and
announces truncation; frontend category pages expose remaining groups. Raw selected
source rows still belong in Table (or `/tablefields`), not in the group matrix.

Preserve this execution order after table acceptance: full-file quality/row-grain and
codebook review → explicit preparation policies → reconciled codebook joins →
descriptive comparisons → readiness report → authorized test-database import →
read-only database validation → authorized export → semantic round-trip reconciliation.
Then assess incremental ingestion, schema drift and safe recovery before more complex
models. These database and statistical extensions remain planned, not implemented by
this presentation change. Never infer authority from this documented sequence.

Manual acceptance:

1. Reopen a comprehensive profile; Outcome → Groups: choose age and gender (or
   readmitted), then Apply grouping. Confirm fields occupy opposite axes and counts
   reconcile with matching records. This calculation is read-only.
2. Select row, column and overall percentages; verify a few cells against counts and
   named denominators. Swap axes; the same combinations must keep the same counts.
3. Reopen the same chat in `./actioncharter`; `/groups` shows the shared saved grouping.
   Use `/crosstab column swap`; compare it with the frontend. Display-only changes
   must not request a model, execute a workflow or require authorization.
4. Reopen a recorded grouped view through Workflow history; inspect the matrix while
   Apply grouping remains disabled. Return to the current workflow without regeneration.

Acceptance evidence: numerical fixtures cover margins, all percentage bases, missing
categories, zero/undefined cells, swaps, and display bounds retaining complete totals.
The isolated browser/CLI/real-PTY journey verifies the same 20,000-record cross-tab,
frontend display controls, saved selection/history and terminal rendering. Dataset
originals and live databases are untouched.

Validation closeout: `make interface-validate` passed (existing bundle-size warning);
isolated browser + CLI + real-PTY acceptance passed. `make test` outside the socket-
restricted sandbox passed 2,110 tests; its one failure was an earlier dropdown-icon
import unsupported by the component test loader. The loader now resolves that import,
and the corrected test passed separately and via `pytest --lf`. The 18 focused
view/chat tests passed. Existing 13 raster fixture warnings remain. No live database
or Git mutation was performed.

## PostgreSQL operation delivery update — 2026-10-26

[Delivered slice and acceptance](POSTGRES_DATA_WORKFLOW.md) supersedes the earlier
“not implemented” status for ordinary-table discovery/inspection, create-only CSV
import/export and exact-key marker delete/restore. The disposable fixture now combines
readiness inspection and existing many-to-one preparation with authorized import/export
and deterministic checks. This is not completion of clinical interpretation, maximum-
scale preparation or a polished combined findings report. Preserve the ordered next
tasks above and validate the supplied 5,000-row sample before attempting full-source
preprocessing. No live database change, Git action or publication was performed.

The real-sample acceptance now closes the sectioned-codebook preparation gap through
`decode_csv_codes` and verifies all projected rows after database export. Source-only
readiness evidence and manual real-model acceptance are recorded in
[the exact test flow](DIABETES_REAL_TEST_FLOW.md). Unknown-code handling is explicit;
raw `?` markers and clinical labels are preserved, not silently cleaned. A polished
combined report and domain-specific cohort/statistical decisions remain later work.
