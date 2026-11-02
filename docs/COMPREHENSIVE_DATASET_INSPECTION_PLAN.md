# Comprehensive typed dataset inspection and Outcome — proposed follow-up

**Implementation update — 2026-10-25:** the CSV/TSV profiling, shared typed tool,
Docker job pilot, recorded graph and interactive Outcome portions are implemented.
See [delivered scope and acceptance](COMPREHENSIVE_INSPECTION_DELIVERY.md) for tested
boundaries and remaining limitations. The original design below is preserved history;
it is not evidence that every planned operation or future sandbox adapter is complete.

## Latest scope clarification — integrated delivery

[Real-data frontend delivery](REAL_DATA_FRONTEND_DELIVERY_PLAN.md) is the latest
coordinated scope/order. It includes the Executor Docker worker together with typed
comprehensive profiling, agent behaviour, graph and interactive Outcome. This document's
technical requirements remain relevant; its earlier standalone ordering does not replace
the complete user-facing acceptance target. All additions remain planned, not delivered.


Recorded 2026-10-25 from the discussion after analytical graph delivery. Documentation
only; the functions below are not claimed complete. Keep the existing
[full health analysis task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md) and
[Executor sandbox plan](EXECUTOR_SANDBOX_WORKSPACE_PLAN.md) connected.

## Why current inspection is insufficient

Current profiles compute numerical statistics only for explicitly selected fields.
The model choosing a few fields does not provide a complete dataset inspection. Empty
mean/min/max entries can mean not requested, not applicable or failed; these states must
be distinguished. Backend type-aware profiling should cover every field, with models
interpreting recorded evidence instead of deciding whether basic columns get inspected.

Current analytical graph/inspector integration is implemented, but the latest operator
requests remain open: predominantly left-to-right layout and clicking analytical Outcome
to open an interactive results workspace, not only an information summary.

## Proposed inspection contract

Report both storage/observed form and analytical role, with evidence, confidence and
an override. Preserve source strings and leading zeros; inspection must not rewrite
inputs or silently coerce codes into numerical measurements.

| Example | Observed form | Analytical treatment |
| --- | --- | --- |
| patient_nbr / encounter_id | Integer-like identifier | Distinct/repetition/key checks, no mean |
| admission_source_id | Integer-like coded category | Frequencies and supplied codebook labels |
| time_in_hospital | Integer-like measurement candidate | Numeric summaries/distribution; units need evidence |
| number_inpatient | Nonnegative count candidate | Numerical and zero/frequency summaries |
| age | Ordered bands | Ordered categorical profile, no invented exact ages |
| weight | Bands plus possible missing markers | Category coverage/missingness; no invented precise weights |

Data-type compatibility alone does not establish semantic meaning. The profiler should
propose plausible roles from schema, definitions and observed patterns, flag uncertainty
and allow correction. Avoid asking users to classify every field before any useful view.
Consequential ambiguity must remain visible; do not infer clinical definitions or units.

For every field: valid/invalid counts, raw empty versus declared-missing markers, missing
percentages, distinct/once-only/repeated values where supported, distributions, codebook
coverage and classification evidence. Candidate markers such as ?/None/Unknown require
reported raw frequency and explicit interpretation, not silent recoding.

For suitable numerical fields: count, mean, min/max, standard deviation, median, quartiles
and range/distribution. Record algorithms, denominator, missingness and exact/approximate
status; use bounded streaming or a validated disk-backed method where appropriate.
Report unavailable metrics explicitly when limits prevent them; never use first-preview
rows as full-source statistics. Do not multiply model calls per column to obtain basics.

For categorical/band/identifier fields: frequencies/proportions, rare/unexpected levels,
ordering where defined, uniqueness/repetition and relevant checks. Repeated patients are
not duplicate encounters. Reconcile row/patient denominators and retain unknown groups.

## Shared capabilities and temporary storage

Implement calculations in shared services and expose typed MCP tools so all compatible
agents can access the same profiles, quality checks and exploration functions. Preserve
API/CLI parity and existing compatible contracts. Registered capabilities and installing
packages remain separate from authorization.

Use an Executor-managed workspace for bounded intermediates, disk-backed calculations
and verified scan reuse where measurements justify it. Artifact records bind source,
query/version, schema, owner, size and expiry. A temp directory alone is not a sandbox.
Internal scratch and retained sampling/export have different effects; retained outputs
require normal write authorization. See the sandbox plan for enforced runtime boundaries.

## Frontend requirements

- Mostly left-to-right: request → discovery → inputs → assessment → profile → outcome.
  Input sources precede consumers. Backward edges represent actual feedback, not a
  layout accident. Retain actual tool evidence; never invent steps to improve appearance.
- Clicking Outcome opens a useful Results page with Overview, searchable Columns,
  distributions/missingness, table/group exploration and Checks. Reuse current tabs/style
  after inspecting actual components; preserve the existing inspector for compact facts.
- Show observed type and analytical role, source/sample scope, full coverage, denominators,
  transformations and calculation policy. Separate not applicable/not calculated/failed.
- Link meaningful chart/table selections to details; make source/query/checks inspectable
  without exposing only a raw JSON dump. Charts use complete calculated summaries.
- Restore saved results without execution. Changing a view must not cause repeated scans;
  an explicit new analytical query uses bounded services and verifies source bindings.
- Verify useful resizing, scrolling, labels and sparse/unknown-group visibility. Avoid
  adding chart types before the underlying profile and Outcome interaction are useful.

## Acceptance and sequence

Audit field coverage and current operation limits, then define typed full-profile results
and sandbox-compatible job/artifact contracts. Ship shared numerical/category/identifier
profiling with independent fixture checks, MCP/API/CLI parity, then connect Outcome and
correct graph layout. Use the Docker pilot sequence rather than claim a folder provides
containment. Complete real-file and existing 5,000-row sample comparisons in temporary
projects; then user frontend acceptance and the rest of the health-data task.

Check empty/mixed/constant fields, invalid numeric strings, numeric-looking IDs, leading
zeros, bands, missing markers, duplicates, resource limits and source changes. Compare
independent calculations across complete eligible inputs and record algorithms/tolerances.
Keep original data, live services, user changes and Git ownership intact. No claim of
Tableau parity, clinical validity, unrestricted generated code or current sandbox delivery.
