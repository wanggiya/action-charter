# Real diabetes exploratory analysis — task and implementation handoff

2026-10-26: [real diabetes frontend test flow](DIABETES_REAL_TEST_FLOW.md) now records
actual files, measured expectations, sectioned-codebook decoding and temporary database
round-trip acceptance. Earlier proposed/unverified statuses below remain historical.

**2026-10-26 handoff:** [target/requirement/function/outcome matrix](REAL_DATA_NEXT_TARGETS.md)
records practical science/engineering work after inspection, with implementation status
and validation order. Outcome-page/field-detail/chart presentation is the current slice;
relationship statistics, models and pipeline gaps remain explicit follow-ups.

**Latest requirement — 2026-10-25:** frontend and CLI must continue the same saved
conversation, server-side proposal and analytical evidence in both directions. Use the
shared running API rather than a separate CLI workspace/model. [Implemented commands
and continuity acceptance](COMPREHENSIVE_INSPECTION_DELIVERY.md#frontend--cli-continuity--2026-10-25)
cover readable recorded views, explicit refresh, revisions and receipt recovery. This
implements the continuity portion below; it does not deliver the later statistical task.

## Current handoff — after initial inspection (2026-10-25)

Documentation-only update requested by the user. Comprehensive inspection is now
implemented: see [delivered scope](COMPREHENSIVE_INSPECTION_DELIVERY.md). Earlier
statements below about comprehensive profiling being only proposed are historical.
The next task is **a reproducible quality report and a small set of defensible group
comparisons**, progressing into the statistical stages already specified below.
Do not treat inspection success as proof that this complete analytical task works.

### Professional working process and acceptance tasks

A scientist starts with a question and interprets evidence; an engineer makes the data
and calculations dependable and repeatable. Both preserve the original source and
investigate iteratively. They do not immediately calculate every test or fit a model.

1. **Confirm purpose, provenance and grain.** Review supplied dataset documentation and
   codebook; establish population/time coverage and what readmission labels represent.
   Verify encounter-key uniqueness separately from legitimate repeated patient IDs.
   Record unknown definitions rather than guessing. Acceptance: every table identifies
   encounters versus patients, selected source, scope and unresolved assumptions.
2. **Create a data-readiness report.** Check all fields, empty/declared/candidate missing
   values, duplicates, category/code coverage, numerical distributions and unusual values.
   Distinguish a flagged outlier from an error; do not automatically remove it. Acceptance:
   complete-source counts reconcile, key/duplicate checks are exact or visibly unavailable,
   code mappings retain unknown values, and IDs/bands are not numerical measurements.
3. **Define an analysis specification.** Choose the question, population, grouping fields,
   outcome definition, missingness policy and any exclusions. Start with descriptions of
   all raw readmission labels. A proposed later primary outcome is recorded `<30` versus
   the other labels, subject to an explicit definition, not silent recoding. Acceptance:
   a compact saved specification binds source/codebook identities and exposes denominators.
   Planner proposes reasonable defaults and asks only consequential missing-input questions.
4. **Prepare and validate an analysis-ready view.** Apply documented types, mappings and
   filters; add justified derived variables. Preserve raw labels/IDs and record exclusions
   with before/after row and patient counts. Do not invent dates or chronological encounter
   order. Acceptance: transformations are reproducible and explainable, rejected rows are
   accounted for, and original files remain unchanged. Read-only calculation views do not
   imply dataset-write authority; retained datasets/exports use normal write authorization.
5. **Describe the population and compare groups.** Produce category counts/proportions,
   length-of-stay and prior-use summaries, and encounter/patient counts. First compare age
   band, admission source and prior inpatient use against recorded readmission categories;
   expand to payer/specialty/race/gender/weight as secondary exploration. Acceptance:
   cross-tab row/column/overall percentages identify their denominator, missing and sparse
   groups remain visible, and group counts reconcile to the selected population. Unique
   patients within groups can overlap; their sum need not equal overall unique patients.
6. **Investigate relationships and uncertainty.** Start with effect sizes/distributions,
   then methods whose assumptions can be checked. Account for repeated patients when
   estimating uncertainty; do not present independent-row tests as equivalent. Acceptance:
   method, reference group, missingness/exclusions, dependence handling and limitations are
   recorded; numerical fixtures and independent references verify results. Unsupported
   methods fail explicitly. These capabilities remain proposed, not delivered by this note.
7. **Answer the question and make the pipeline reusable.** Link findings to recorded
   tables/charts/checks; separate calculations from model interpretations. Reopen the same
   analysis without rerunning it, and explicitly rerun on changed inputs with fresh source
   verification. Acceptance: equivalent specifications agree across Planner, direct controls
   and CLI/MCP; changing sources does not silently reuse old results or approval. Optional
   saved reports/tables require normal write authorization. Recipes describe compatible
   processes, not portable authority or proof of learned clinical expertise.
8. **Only then evaluate an adjusted or predictive model if useful.** The existing adjusted
   association stage below requires supported methods and diagnostics. Prediction is a
   separate later objective requiring patient-disjoint validation and field-availability/
   leakage review. Neither an exploratory fit nor its apparent score establishes a valid
   clinical product. Do not add modelling just to make the demonstration look complete.

Engineer emphasis across these stages: explicit schemas/contracts, reproducible ingestion
and joins, key validation, appropriate storage, bounded resources, idempotent output
handling, cancellation/recovery and monitoring for input changes. Scientist emphasis:
question relevance, interpretation, sampling/selection bias, uncertainty and sensitivity
to reasonable choices. These are complementary responsibilities, not extra mandatory
LLM agents or fixed human approval prompts for every analytical choice.

### Product improvements to exercise through this task

- **First audit existing functionality.** Reuse delivered quality/group operations and
  inspection/Outcome contracts. Distinguish missing calculations from missing UI or
  planner access before adding new tools. The earlier implementation order below remains
  the technical sequence; this section defines the user-facing work it should enable.
- **Chart controls:** align selectors, spacing, typography and selected states with the
  existing interface. Inspect the actual controls/browser and explain the intended edit
  before frontend implementation. No frontend changes are authorized by this note alone.
- **Full-file exploration:** select groups, filters, numerical measures and aggregations;
  show distributions, distinct patients, denominators and missingness with interactive
  table/chart details. Selection alone must not trigger repeated costly scans. Routine
  calculations should use shared services without needing another model call.
- **Readable CLI parity:** extend existing `explore-data`/`profile-dataset`, rather than
  building a second analysis engine. Planned readable views: Overview, Columns, Table,
  Groups, Checks and terminal-friendly charts. Structured JSON remains available for
  automation. Terminal presentation need not reproduce a graphical page layout.
- **Recorded-result access:** both interfaces should open a scoped saved result without
  re-executing calculations or calling the model. Pagination/search must identify whether
  they cover loaded rows or the full source. Record exact/approximate/unavailable states.
  HTML/SVG/chart export is an explicit file write, separate from viewing a terminal chart.
- **Agent access and verification:** typed MCP tools expose the shared operations, not
  unrestricted pandas/NumPy namespaces. Planner selects analyses and explains evidence;
  Executor responsibility runs bounded calculations; Critic assesses support/assumptions.
  Verify calculations independently rather than trusting model agreement as verification.

For each acceptance task record: request/specification, expected result computed
independently, actual result and source identity, missing capability or failure, model
calls/time versus calculation time, and necessary user interventions. Test the same
specification through direct controls, Planner and CLI when each entry point exists.
Start with small known-answer fixtures, then temporary copies of the 5,000-row sample
and full file. Sample findings must remain sample-scoped. No new massive-data claim
follows from this dataset alone. Save this evidence to guide the next implementation
slice, rather than redesigning the agent architecture before testing the useful journey.

## Latest proposed follow-up — 2026-10-25

[Executor sandbox/workspace structure](EXECUTOR_SANDBOX_WORKSPACE_PLAN.md) and
[comprehensive inspection/Outcome requirements](COMPREHENSIVE_DATASET_INSPECTION_PLAN.md)
preserve the latest discussion and next implementation order. They extend this task;
they do not claim container isolation or comprehensive profiling already works.


## First implementation slice — 2026-10-24

[Quality and grouped exploration](TABLE_EXPLORER_ACCEPTANCE.md) is now implemented
and independently exercised on temporary real-data copies. Existing profile_table
contracts were extended; no new engine, statistical dependency or agent was needed.
Quality/Explore controls make deterministic requests without an LLM. Full relationship
statistics, uncertainty, adjusted models, durable saved explorations and automatic
analysis-to-workflow promotion remain future work. Original plan text below is history.

Recorded 2026-10-24. **Proposed work, documentation only.** This expands the first
task from quality/group summaries to descriptive statistics, relationships and one
interpretable adjusted analysis. It does not claim those capabilities are implemented.
No data processing, model calls, dependency installation or frontend edits accompany
this document. Existing user changes and checkpoint history must be preserved.

Read alongside [existing analytical acceptance](ANALYTICAL_INSPECTION_ACCEPTANCE.md),
[quality/exploration contracts](TABLE_QUALITY_AND_EXPLORATION_PLAN.md) and the
[original health assignment](HEALTH_DATA_SCIENCE_READMISSION_TASK.md). This is the
latest task scope; earlier descriptive-only boundaries describe the previous proposal.
Memory architecture, RL, arbitrary code generation and new agent frameworks stay parked.

## Task brief and completion target

For a hospital analytics team, investigate how recorded readmission categories vary
with patient characteristics and hospital-use patterns, then assess selected adjusted
associations. Produce a reproducible report showing data quality, cohort/denominator
decisions, descriptive findings, effect sizes, uncertainty and limitations.

Use existing diabetic_data.csv and IDS_mapping.csv. Do not fetch new patient data,
modify originals or query live databases. This historical encounter dataset supports
exploratory association analysis; it does not establish causes, treatment guidance or
current hospital performance. Predictive modelling/deployment is a later task.

Task completion requires the whole read-only journey plus an optional authorized
export: quality → documented analysis policy → descriptions → relationships →
one defensible adjusted analysis → diagnostics → report. A blocked/inapplicable
statistical method must give a precise reason; it cannot be counted as a completed
adjusted-analysis capability. Do not conceal missing methods behind a polished chart.

## Analysis policy before calculating relationships

Record a versioned analysis specification bound to source/codebook hashes:

- Row grain: encounters; patient_nbr identifies repeated patients, not a numerical
  predictor. encounter_id is a key candidate, not a measure of disease severity.
- Outcome: describe all raw readmitted categories first. Proposed primary comparison
  is recorded `<30` versus the other recorded categories, with an explicit statement
  that the label does not prove complete external follow-up. Do not silently recode.
- Population: begin with the complete raw source for quality/descriptions. Clinical
  exclusions, such as disposition-based exclusions, require verified definitions and
  a documented rationale; no invented mortality/hospice code lists or automatic drops.
- Missingness: preserve raw values; distinguish empty, `?`, unmapped and genuinely
  meaningful categories. Show affected counts before applying a proposed policy.
- Variable roles: preserve age/weight bands; IDs are not continuous measurements.
  Separate admission-available variables from end-of-encounter information. Duration
  of stay is not a timestamp. Do not invent chronology for selecting a first encounter.
- Repeated patients: encounter-level uncertainty must account for clustering by patient
  where supported. Do not present ordinary independent-row uncertainty as equivalent.
  A patient-selection sensitivity analysis needs a defensible selection rule.
- Analysis status: exploratory, with a small prespecified primary comparison set and
  separately labelled secondary exploration. Record thresholds and reference categories.

Planner may propose this policy and ask about consequential ambiguity. Show one compact
editable specification rather than a series of repetitive prompts. Direct controls and
the conversational path must use the same specification; analysis choices confer no
write authority. Unsupported domain assumptions remain unresolved, not model-certified.

## Task stages, observations and measurable checks

### 1. Quality and row grain

Inventory every field: raw type/role, missingness, distinct/once-only/repeated values,
frequent values, numeric/band summaries and codebook coverage. Separately check complete
duplicate rows, duplicate encounter keys and encounters-per-patient distribution.
Inspect age, weight, race, gender, payer_code, medical_specialty, admission_source_id,
admission_type_id, discharge_disposition_id and prior-use variables.

Observe whether the interface distinguishes patients from encounters, absent data from
unknown codes, and legitimate repeat visits from duplicates. Exact high-cardinality
checks must expose their strategy/budget; preview counts cannot prove uniqueness.

Baseline from earlier independent acceptance: 101,766 rows, 50 columns, 71,518 distinct
patients and 101,766 distinct encounter IDs. Compute additional expectations independently.
Keep actual duplicates/missingness findings unknown until measured.

### 2. Population descriptions

Produce complete-source frequency/proportion tables and suitable charts for age, race,
gender, admission source, payer, specialty, weight and outcome. Summarize hospital stay
and prior utilization with count, missingness, mean, standard deviation, median, quartiles
and range where defined. Establish exact versus approximate quantile algorithms explicitly.

Observe skew, sparse groups and missingness; do not infer normality from a mean alone.
Use patient-frequency summaries rather than a chart containing every patient identifier.
Reference raw outcome counts: NO 54,864; >30 35,545; <30 11,357. Existing age/outcome
grouping has 30 groups and reconciles to 101,766 encounters.

### 3. Relationships and uncertainty

Prespecified first comparisons: age band, admission source and prior inpatient use
against the recorded outcome. Explore payer, specialty, race, gender and weight secondarily
with visible coverage and sparse-group warnings. Do not manufacture subgroup conclusions.

Capabilities to evaluate and implement deliberately:

- Cross-tabulations with raw counts and selectable row/column/overall percentages.
- Group outcome proportions and absolute/relative differences with stated references.
- Suitable numerical association measures and group distribution comparisons.
- Confidence intervals using an approved method appropriate to the row dependence;
  a patient-cluster bootstrap is one candidate, with explicit seed/resample budget.
- Statistical tests only when their assumptions are satisfied. Ordinary contingency
  tests may be diagnostic/descriptive under repeated patients; no unqualified independent
  encounter inference. Prefer effect sizes and uncertainty to a p-value ranking.
- Multiple-comparison handling for a defined test family, or clearly descriptive-only
  secondary findings. Report method, family and adjusted versus raw results separately.

Observe denominator changes, repeated-patient effects, omitted groups and uncertainty.
Test method selection on small fixtures with known answers and assumption violations;
compare numerical results to an independently specified reference implementation.
Pairwise missingness rules, unavailable/undefined results and exclusions must be visible.

### 4. One interpretable adjusted analysis

Candidate: encounter-level binary logistic regression for the explicitly defined `<30`
outcome, using a small prespecified set such as age bands, admission source and prior
inpatient use, with patient-clustered uncertainty where the implementation supports it.
Final specification follows coverage and method review; do not silently select variables
by p-values. Do not use patient/encounter IDs as predictors or assign continuous values
to arbitrary category codes. Do not automatically add every diagnosis or sparse level.

Record the model matrix, categorical references, missingness/exclusion policy, rows and
patients retained, parameters, solver settings, dependency versions and diagnostics.
Show adjusted odds ratios and intervals as associations; odds ratios are not risk ratios.
Check convergence, separation, rank deficiency, sparse categories and sensitivity to
plausible analysis choices. Non-convergence must yield a failed/limited result, not a
success card. Make patient clustering explicit in the result contract.

If later adding prediction, require patient-disjoint validation and leakage/timing review;
do not advertise exploratory fitted-model performance as a validated predictive product.

### 5. Reproduce and communicate

Report source identity, data policy, cohort flow, all denominators, complete-source
coverage, selected methods, uncertainty, findings and limitations. Link each statement
to recorded tables/checks rather than model-generated numbers. Preserve the analysis
specification so a direct-control request, Planner request and CLI run can be compared.
Reopening saved results must not rerun analysis. New reads verify source bindings.
Optional export uses a fresh temporary target and normal Allow writes/Authorize/Execute.

## Structural responsibilities and proposed tool boundaries

```text
Conversation / interactive explorer / CLI
                  |
        typed analysis specification
                  |
    shared validation + operation registry
                  |
       bounded analytical services
       | quality | summaries | associations | statistical model |
                  |
     recorded results + provenance + diagnostics
                  |
        Results pages and optional Critic review

Planner ---- typed MCP tools ---- same analytical services
```

Backend services calculate; MCP exposes their typed contracts, not library namespaces.
Extend compatible profile_table functionality and separate quality, group/page,
association and model-fit responsibilities where warranted. Reuse registry validation,
worker limits, cancellation and durable-run support after inspecting existing coverage.
Long statistical jobs must report progress and cancel without presenting partial fits
as complete. Evidence persistence remains governed by existing application services.

Planner proposes questions/specifications and explains supplied results. Existing
execution assistance may reason over bounded evidence; it cannot edit or authorize a
running plan. Critic checks evidence, assumptions and claim support; it does not replace
numerical verification or certify clinical validity. No new mandatory LLM chain or role.

Start with an installed-capability inventory. NumPy/pandas provide numerical and table
foundations; a statistics library may be required for tests, uncertainty and regression.
Choose actual packages after checking available dependencies and validating the needed
methods. Installation does not register an approved executable operation.

Optional future documentation search may identify a missing method/package: prefer
primary documentation, send method/schema questions without patient data, retain sources,
and return a proposal with requirements and tests. No automatic downloads, imports of
arbitrary code or dependency installs. Search is not a prerequisite for this first task.

## Frontend design and what to observe

Inspect actual components/browser behaviour and explain proposed changes before editing.
Preserve current style and existing Results navigation where possible; avoid adding all
controls at once. Proposed views can be sections/subpages of current Results tabs:

| Area | Content and interaction | Observe during acceptance |
| --- | --- | --- |
| Overview | Dataset/grain, coverage, quality warnings, analysis-spec summary | Facts distinguish rows, patients and included population |
| Columns | Searchable field list with quality metrics, distributions and definitions | No huge ID lists; missing rules and exactness visible |
| Explore | Group/filter/measure selectors, result table and chart | No model wait for routine changes; denominators and omitted groups clear |
| Relationships | Comparison variables, effect/uncertainty table, suitable plots | No unsupported significance colouring or hidden test assumptions |
| Model details | Compact specification, fit status, estimates and expandable diagnostics | Failures/sparse levels visible; no raw formula dump as the main view |
| Checks/report | Provenance, cohort flow, numerical checks and claim limitations | Reproducible queries and source bindings are accessible |

Use progressive disclosure and resizable panels. Explain costly operations before an
explicit Run analysis action; cheap selections should not automatically launch repeated
full-file scans. Debounce/cancel requests and reject stale responses. Retain a saved
result while a new calculation is pending, clearly marking its scope. Interactive
hover/click details must show the corresponding group denominator and missingness.
Do not render every source row or chart category to imply comprehensive analysis.

## Implementation order and completion gates

1. Inspect existing services/tools, dependency versions, run/cancellation and Results UI.
   Produce a capability-gap table; distinguish implemented, partial and missing pieces.
2. Implement bounded quality and descriptive primitives, then typed MCP/API/CLI exposure.
   Verify exactness, exhaustion behaviour, source changes and direct-entry parity.
3. Implement compact Columns/Explore controls after presenting the audited design;
   connect Planner to the same compact schema and codebook context. Browser-check a
   complete quality/group journey before adding statistics.
4. Add a small validated association/uncertainty toolbox. Establish repeated-patient,
   missingness and multiple-comparison policies and fixtures before real conclusions.
5. Add one explicit statistical-model operation and diagnostics with fixed supported
   families/options; no unrestricted formulas or generated-code execution.
6. Run independent full-file real-data acceptance in temporary copies, then provide
   exact frontend prompts/actions and expected results for the user's own test.
   Record failures and unmet gates before calling the task complete.

At each stage: correctness/coverage first, then latency, peak memory, temporary disk,
cancellation, recovery and frontend responsiveness. Compare the same specification via
direct controls, CLI/MCP and Planner. Track model calls, latency, failures and human
interventions separately from deterministic service performance. Existing baseline
acceptance proves neither new statistical correctness nor massive-data scalability.

Use meaningful synthetic fixtures and independent numerical references with stated
tolerances; ensure missing/constant/sparse fields, repeated clusters, singular fits and
resource limits are tested. Run relevant backend tests and make interface-validate,
and complete interface journeys when browser tools are available. Do not download
dependencies or run the real analysis merely to update this design.

## Resume instruction

Next coding session starts with step 1, then completes coherent slices in order.
Do not jump straight to fitting a model or add new memory architecture. User owns Git:
no staging, commit, push, merge, release or publication. Keep source datasets and live
PostGIS/GeoServer unchanged. Documentation records intentions; it grants no authority.
