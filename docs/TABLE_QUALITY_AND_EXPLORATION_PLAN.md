# Table quality and interactive exploration — next delivery

## Implemented foundation — 2026-10-24

[Columns/Explore acceptance](TABLE_EXPLORER_ACCEPTANCE.md) records the delivered first
slice: bounded exact quality/duplicate checks, grouped distinct counts, shared typed
MCP/CLI access and interactive CSV pages. Statistical relationships and the full task
remain pending. This status supersedes proposal-only wording for those specific features.

## Expanded task scope — 2026-10-24

The latest [full exploratory-analysis task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md)
extends this foundation through descriptive statistics, relationships/uncertainty and
one interpretable adjusted analysis. It records agent/service/MCP boundaries, frontend
observations, dependency/search policy and ordered acceptance. The descriptive-only
first task below is preserved as the earlier scope; it is no longer the full endpoint.
All additions remain proposed, not implemented or validated by this documentation.

Recorded 2026-10-24 after the first real diabetes retest. Design only: this update
adds no runtime features, frontend changes, data reads or model calls. Existing
[analytical acceptance](ANALYTICAL_INSPECTION_ACCEPTANCE.md) remains the implemented
baseline; the capabilities below must not be advertised as already complete.

## Purpose and architecture

Real-data testing exposed missing general analytical functions. Implement them, then
return to the same dataset for acceptance. Do not hardcode diabetes column names,
clinical assumptions or expected counts into production services.

The shared backend owns validated calculations. MCP exposes typed tools; the interface
and CLI call the same services. Planner interprets questions, selects tools and explains
recorded facts. Direct frontend exploration requires no model call. This improves the
small model's available evidence/tools; it does not train the model or add an agent.
Critic may assess evidence using its existing role, without duplicating calculations.

Keep source scope, source/codebook hashes, query, denominator, coverage, limits and
result provenance explicit. Historical context and model text never authorize execution.
Read-only analysis needs no write approval; export retains Allow writes → Authorize →
Execute. No arbitrary library-function execution, generated Python, dependencies or RL.

## Dependency-ordered implementation and acceptance

1. **Shared quality/analysis contracts and services.** Separate basic inspection from
   optional expensive checks. Define exact/estimated/unavailable status and resource
   exhaustion explicitly. Add missing-token rules, repetition metrics, row/key duplicate
   checks and per-group distinct counts. Preserve current compatible calls and bounds;
   do not silently substitute preview statistics or unbounded in-memory sets.
   Acceptance: independent full-source reference calculations agree on temporary
   fixtures, including empty/all-missing columns, repeated patients, duplicated keys,
   invalid tokens, changed sources and exceeded budgets. Group counts reconcile.
2. **Typed MCP/API/CLI exposure.** Extend profile_table compatibly; use separate focused
   contracts for quality checks, group exploration and bounded table pages. Final new
   tool names follow repository conventions after inspecting existing support.
   Acceptance: equivalent requests through each entry point give equivalent analytical
   facts and explicit coverage. Reject unsafe paths and mismatched source bindings.
3. **Frontend quality and exploration.** Inspect the actual interface and present the
   proposed layout before editing. Preserve existing style and Results tabs; provide
   searchable Columns/quality content and an Explore area within that structure.
   Controls select group fields, exact filters, measures and chart/table presentation.
   Acceptance: grouping/filtering requires no chat regeneration or LLM call, settings
   and denominator are visible, cancelled/stale responses cannot replace newer views,
   and bounded displays never imply bounded calculation coverage.
4. **Planner integration.** Supply compact schema, column roles, supplied definitions
   and available measures. Planner uses the same typed requests, clarifies ambiguous
   meaning and reports missing capability instead of inventing results.
   Acceptance: matched conversational/direct requests agree; model failures preserve
   current work. Record model, calls, latency and interventions separately from service
   correctness. No guarantee that arbitrary small-model wording will succeed.
5. **Real-data acceptance.** Run the task below, compare independent reference results,
   then document actual performance and remaining gaps. Use synthetic fixtures for
   automated checks and temporary copies for real-file verification. Browser tests use
   isolated profiles and existing project-local assets. No live-service changes.

These are slices of the current analytical follow-up, not a declaration that memory
checkpoint 29 or the entire health-data assignment is complete.

## Metric definitions to settle before implementation

- Distinct count: number of distinct non-missing values under the declared token policy.
- Unique-value count: values occurring exactly once. Do not label every distinct value
  as unique. Candidate key requires no missing values and one occurrence per row.
- Repeated-value count: number of values with frequency greater than one. Also expose
  rows in repeated groups and excess occurrences, with clear labels.
- Duplicate rows: excess rows beyond one per identical full-row group. Duplicate keys
  use the same definition for explicitly selected key fields; specify missing-key rules.
- Missing: report raw empty cells separately from declared markers such as `?`.
  Do not automatically equate literal `None`, Unknown or unmapped IDs with missing.
- Group measures: encounter/row count, non-missing count, distinct patients, numeric
  summaries and explicit percentages. Distinct-patient counts across groups need not
  sum to global distinct patients when patients occur in multiple groups.
- Group fractions: specify global, filtered or within-group denominator. Readmission
  fraction requires an explicitly defined outcome and eligibility policy, not a guess.
- Exact high-cardinality checks need a bounded strategy, such as temporary disk-backed
  state with cleanup/quotas. Current category caps cannot establish identifier uniqueness.
  Select the strategy after profiling existing code; do not promise unlimited exactness.

## First test task — encounter quality and readmission exploration

**Stakeholder deliverable:** a reproducible data-readiness report and exploratory group
summary for a hospital analytics team. Establish whether the source supports useful
comparisons before building a prediction model. No treatment recommendations or causal
claims; this task is not a finalized clinical cohort.

Inputs: existing diabetic_data.csv and sectioned IDS_mapping.csv under data/input.
The source and codebook remain unchanged. First run the deterministic service path;
then repeat representative questions through Planner to isolate model failures.

### A. Establish row grain, quality and meaning

1. Record source identity, full row/column coverage and codebook identity.
2. Check encounter_id candidate uniqueness and missingness. Count distinct patient_nbr
   and show encounters-per-patient distribution. Repeated patients are not automatically
   duplicate records. Check exact duplicate rows separately.
3. Build a searchable quality inventory for all fields: reported/observed type,
   missing markers, distinct and repetition status, category/numeric summaries.
4. Inspect age, weight, race, gender, payer_code and medical_specialty. Preserve
   age/weight bands as categories. Propose `?` as a policy for review, display its
   actual frequency first, and keep raw versus interpreted counts visible.
5. Decode admission_source_id, admission_type_id and discharge_disposition_id using
   supplied mappings. Show unmapped values rather than inventing labels. The current
   mapping file does not define every other column's clinical meaning.

Known baseline from earlier independent acceptance: 101,766 encounters, 50 columns,
71,518 distinct patients, 101,766 distinct encounter IDs. Other quality counts must be
computed independently; this design does not invent expected duplicate/missing totals.

### B. Explore complete-source populations

Allow one/two group dimensions selected interactively, initially:

| Dimension | Example question |
| --- | --- |
| Admission source | Which sources have the most encounters and distinct patients? |
| Age and readmitted | How do recorded outcome categories differ across age bands? |
| Race or gender | What are group sizes, missingness and recorded outcome distributions? |
| Payer or medical specialty | How much information is absent, and how do observed groups differ? |
| Weight bands | Is coverage sufficient to support any useful comparison? |
| time_in_hospital | What is the stay-duration distribution and mean per selected group? |
| patient_nbr | How often do patients recur? Use frequency summaries, not an enormous ID chart. |

Offer row count, distinct-patient count, mean stay and explicitly scoped percentages.
Retain unknown/missing groups visibly unless a recorded filter excludes them. Duration
is not calendar time: do not offer time trends without a suitable timestamp field.
Bound chart categories while retaining complete result totals and omitted-group counts.

Independent baseline: raw readmitted counts are NO 54,864; >30 35,545; <30 11,357.
Age/readmitted has 30 groups whose encounter counts sum to 101,766. Reproduce these
before expanding to new groupings, and independently calculate new expected results.

### C. Reproduce, explain and optionally export

Keep the source binding, missing-value policy, filters, grouping, measures and
denominators with each result. A representative Planner request is:

> Compare recorded readmission categories by admission source. Show encounter counts
> and distinct patients, include missing/unmapped groups, and use the supplied codebook.
> Do not write files.

This is a future acceptance request, not a claim that the current parser supports it.
Compare it with the identical direct-control query. Explanations must cite calculated
facts and describe limitations. Do not send raw patient identifiers to the model merely
to summarize aggregate results.

Only after read-only acceptance, optionally export a selected summary using a fresh
temporary target and the normal write gates. Reopening must restore recorded results
without execution; source changes must invalidate new reads rather than reuse old hashes.

## Completion gate

Ship a useful Columns/Explore journey, shared typed tools, full-source correctness
evidence, direct-versus-Planner comparison and accurate documentation. Report actual
row coverage, runtime, peak memory, disk use where relevant, failed cases and model
interventions. Do not add a new agent framework, memory scheme or extra chart catalogue
as a prerequisite to this task.
