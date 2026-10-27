# First realistic health data-science assignment — retrospective readmission review

2026-10-26: [real diabetes frontend test flow](DIABETES_REAL_TEST_FLOW.md) now records
actual files, measured expectations, sectioned-codebook decoding and temporary database
round-trip acceptance. Earlier proposed/unverified statuses below remain historical.

## Columns and grouped exploration delivered — 2026-10-24

See [current acceptance and frontend instructions](TABLE_EXPLORER_ACCEPTANCE.md).
Real-file checks now distinguish 54,745 once-only patients from 16,773 repeated patients,
verify encounter-key uniqueness and zero duplicate entire rows, and confirm declared
missing counts against independent counters. Grouped distinct-patient measures and
Columns/Explore controls are delivered; inferential/adjusted analysis is not yet delivered.

## Latest full task — 2026-10-24

Use [the exploratory-analysis implementation handoff](DIABETES_EXPLORATORY_ANALYSIS_TASK.md)
for current scope: quality → explicit analysis policy → descriptions → relationships
and uncertainty → one adjusted analysis → diagnostics/report. It expands the earlier
descriptive-only task without claiming statistical tools are already delivered.
Observe repeated-patient dependence, missingness, field timing and denominator changes.
No data reads, package installs, model calls or frontend changes in this design update.

## Next task refinement — 2026-10-24, proposed

[Quality and interactive exploration](TABLE_QUALITY_AND_EXPLORATION_PLAN.md) defines
the next delivery and first acceptance task: establish encounter/patient grain,
missingness/uniqueness/duplicates and code coverage; explore admission source, duration,
payer, specialty, race, gender, age and weight; compare direct and Planner results.
New quality/grouping tools and controls are proposed, not delivered by this note.
The first deliverable is a data-readiness report and reproducible descriptive summaries,
before clinical exclusions, predictive modelling or interpretation of associations.

## Implemented analytical slice — 2026-10-24

Operator authorized implementation after the recorded proposal. See
[delivery and exact real-data retest](ANALYTICAL_INSPECTION_ACCEPTANCE.md).
Ollama Settings selection, hash-bound source queries, sectioned codebooks, complete-file
profiles/group export, shared MCP/CLI services and compact Results views are implemented.
Optional bounded post-run execution assistance is implemented; automatic mid-run
adaptation and a general lazy dataframe engine remain open. The actual diabetes inputs
passed independent full-file comparisons and normal authorized execution in a temporary
project. Earlier proposal-only statements below are preserved discussion history.
Memory/role-flexibility decisions remain parked; no checkpoint-29 completion claim.


Prepared 2026-10-23. Task definition and capability assessment only. No dataset has
been downloaded or processed, and no clinical result is claimed. Memory prototypes
remain parked. Preserve user changes and Git ownership.

## Latest step-4 feedback — analytical inspection proposal

The user reports downloading the data and reaching inspection, then stopped before
step 5. [Analytical inspection plan](ANALYTICAL_INSPECTION_AND_CODEBOOK_PLAN.md)
records requested codebook-aware full-file profiles/aggregation and frontend audit
before edits. This supersedes treating a sample-only journey as full-data acceptance.
Prior “no dataset downloaded” statements describe the earlier preparation, not the
user's current report. No analysis or backend improvement has been executed here.

## Stakeholder, question and deliverable

Scenario: a hospital quality-analysis team wants an auditable assessment of recorded
early readmissions among diabetes-related inpatient encounters before commissioning
more detailed review. Question: which sufficiently populated age/prior-inpatient-use
groups have higher recorded <30-day readmission proportions, and how much confidence
can we place in those comparisons given data quality and coverage?

This is a retrospective analytical assignment using historical public data, not an
outreach deployment or a recommendation about individual treatment. No claim that an
observed association identifies a cause, preventable readmission or current hospital
performance. A current operational decision would require current local data and
appropriate validation.

Data: UCI Diabetes 130-US Hospitals, 1999–2008, diabetic_data.csv plus IDS_mapping.csv
and definitions. Source: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
Original research: https://pmc.ncbi.nlm.nih.gov/articles/PMC3996476/
Source files are not in the workspace as of this preparation. Record acquisition date,
hashes, license/attribution, actual headers/codes and documentation before analysis.
The published study's final cohort differs from the raw UCI dataset; do not expect
identical row counts or reproduce its result without reproducing its cohort definition.

## Analysis contract to establish before looking at subgroup results

- Unit: hospital encounter. Patient identifiers are linkage fields, not features;
  repeated patients do not become distinct people. Report unique patients and repeated
  encounters if supported, or explicitly identify the missing capability.
- Target: recorded readmitted value <30; retain >30 and NO as distinct raw categories.
  Preserve literal spelling/case from actual input. Unknown/missing outcomes are not
  zero. NO means no recorded readmission, not proof of no subsequent admission anywhere.
- Cohort: define eligible discharge dispositions from the supplied mapping and primary
  documentation, including treatment of death/hospice and other statuses. Publish the
  inclusion/exclusion flow and denominators. Do not invent codes or silently choose a
  first/last encounter using row order; chronology must be justified by documentation.
- Baseline analysis: describe all eligible encounters, acknowledge patient dependence,
  and use patient-aware sensitivity/evaluation if inferential/modeling work follows.
- Groups: supplied age bands and a predeclared prior-inpatient-use grouping (0, 1, 2+).
  Initial descriptive flagging requires at least 100 eligible encounters per group;
  this is an analyst-selected stability screen, not a clinical standard. Show counts
  and uncertainty/sensitivity limitations instead of ranking tiny groups by rate.
- Report recorded early-readmission count / eligible encounter count per group. Keep
  sample and full-population results explicitly separated. Associations are descriptive,
  unadjusted and may reflect confounding, coverage and repeat encounters.

## Work products and checks

1. Data/source manifest, working data dictionary, missing/code-quality report and
   duplicate/linkage assessment. Distinguish source missing codes from valid categories
   and unperformed tests; do not replace all unusual strings with a common null.
2. Cohort flow table with explicit exclusions; counts reconcile to the input.
3. Grouped counts/proportions and selected mean hospital-stay summaries, with missing
   counts and actual denominator definitions. No claimed causal medication effects.
4. Clear comparison charts with sample sizes and notes; a plot is not the sole output.
5. Exported tables plus exact workflow/parameters, formulae, source identity and checks.
6. A short stakeholder memo: findings, limitations, what additional data is needed and
   whether a more detailed predictive analysis is justified. Findings remain empty
   until execution and independent verification.

Independent reference calculations should use a separate readable standard analysis
script, run on the same defined cohort; compare counts exactly and floating rates
within a declared tolerance. Do not mirror internal service calls as the sole oracle.
Check target category totals, join row counts, numerator <= denominator and proportions
in [0,1]. Preserve raw files and fail visibly on undocumented category changes.

## Functional and scale stages

A. Inspect the untouched full file and confirm characteristics. Full-file discovery
   is a separate exercise from processing; record elapsed time/memory and evidence.
B. Create a deterministic small exercise subset <=10,000 rows and <8 MiB under a
   documented sampling rule, retaining raw values. It is a functional fixture, not an
   estimate of the complete population. Record subset preparation as external prep
   if ActionCharter cannot perform it; do not claim in-platform full-file processing.
C. Execute the supported cohort/aggregation/export journey in the interface, checking
   shared service/CLI agreement and independently computed answers. Pause at capability
   gaps; do not hand-create outputs and claim the platform produced them.
D. Attempt the defined full-data task against current limits to establish safe refusal
   and actual gaps. Add only targeted approved scale/analysis capabilities, then repeat
   the same correctness contract and measure memory/time. 101,766 rows / ~18.3 MB is
   medium-sized clinical tabular data, not proof of huge-data readiness.

## Current capabilities and observed gaps (code inspected, not executed)

Existing typed operations provide inspection, selection, filtering, missing handling,
CSV joins, group count/mean/sum/min/max, numeric calculations and exports. All
transformation outputs are writes and require normal authority. The current service
uses 8 MiB / 10,000-row bounds; selecting fewer columns does not bypass input bounds.
Current calculations support numeric operands/comparisons, so textual readmission
labels cannot simply be passed to a numeric conditional. Count-based grouping/join
may express some proportions; prove the actual plan before claiming coverage.
Missing handling recognizes empty cells, not all source-specific missing tokens.
Distinct patient counting, semantic recoding, a deliberate encounter-selection policy,
uncertainty intervals and leakage-safe predictive training are not established by the
current primitive list. Inspect support and document gaps before adding operations.
Do not start a broad ML system or unrestricted Python execution as a shortcut.

Later predictive phase, only if needed and supported: define the intended prediction
moment, exclude unavailable-at-that-time inputs, split by patient to avoid overlap,
fit preprocessing on training data only and compare against a simple baseline with
appropriate class-imbalance/calibration metrics. No validated classifier is delivered
by a descriptive analysis. No current clinical-use claim.

## Next concrete step

Acquire the original UCI CSV, mapping and documentation (or use the user's supplied
copy), then create the source manifest and verify the analysis contract against actual
values before generating a Planner request. Downloads and processing were not performed
in this documentation step. Do not mutate live databases/services or add data to Git.
