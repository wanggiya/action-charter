# Table statistics and analytical reporting

Propose analysis goals from recorded inspection before selecting inferential methods when
no objective is supplied. Name actual candidate fields, question and prerequisites;
use supported methods and label capability gaps. The conversation advice contract is
analysis-goals-v1; it never calculates or authorizes work. A target is only a candidate
until its meaning is confirmed. Do not apply numeric inference to IDs/category codes,
or promise precision/recall, categorical hypothesis tests or causality: those operations
are not registered. Report computed and uncomputed metrics separately. A simple report
request must not silently add statistical models. Prepare a typed calculation only once
its scientific choices are concrete. See docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md.

Use the registered inspect_csv workflow operation with analysis.statistics, or the
MCP table_statistics / linear_regression tools. This guide grants no execution authority.

Analytical inspections now return readiness-assessment-v1: source-bound missingness,
key/duplicate checks, mapping coverage, selected group findings and a deterministic
Markdown report. The full supplied dataset is the target; assess its actual operation
limits before proposing a sample. Never substitute another source silently. Ask for
explicit selection when an alternative is needed; sample creation requires normal
write authorization. A complete selected-file scan does not establish population
coverage. Use duplicate_key for the proposed observation key, duplicate_rows for whole
rows, distinct_columns for repeated entities, declared missing_values and a supplied
codebook. Keep entity IDs textual and age bands categorical. Split exact checks into
separate bounded requests if their combined state exceeds limits; do not omit or
approximate a requested check. Readiness not_requested means unknown, not passed.
Report fields/groups may be omitted to fit output bounds; omissions are recorded and
the original analysis remains available. Use original statistical evidence for methods,
exclusions and inference. Planner interpretation and Critic review are separate advice;
the deterministic report never fabricates domain knowledge or approves an operation.

For required row-local preparation above the default dataframe limits, registered
select/filter/missing/decode/export operations support streaming=true; outputs remain
bounded and require write authorization. Do not use it for unqualified joins or numeric
calculations. Streamed aggregation can consume a validated CSV ancestor. Use the
PostgreSQL skill's full-source mapping preflight and explicit per-column null policy
for a fresh-table handoff. workflow_report exposes measured analytical and technical
documents from saved steps; it does not recompute or convert clinical interpretations
into verified findings.

Use MCP list_operation_contracts(query) to discover registered operations and their
trusted reader contracts; the built-in Planner receives relevant catalog entries
directly. A discovered dependency or function is not an executable operation. Readers
share the same bounded inspection pipeline across CLI/MCP/workflow. New outcomes carry
table-source-v1 with original hash, source selection and observed storage types/nulls;
old outcomes may omit it. Read this evidence alongside the explicit analytical text
view; do not infer native numerical semantics or permission from storage types.

Supported source adapters now include CSV/TSV, XLSX and flat JSON/JSON Lines/NDJSON.
The stable inspect_csv ID is retained. Use analysis.source_options.sheet/header_row for
workbooks, or cell_range with the first range row as header; do not combine a range
with nondefault header_row. Ambiguous sheets require a choice. Formula/error cells, macros and external
workbook links reject. JSON defaults to a record array; source_options.records_key can
select a top-level array. Nested cells/new keys after the first record reject; absent
keys become null. Native source types and original hashes are retained; the current
analytical view uses strings and treats null/empty string as missing explicitly. Do not
silently flatten, evaluate formulas or treat numeric formatting as a text identifier.
CSV-only write/transform operations cannot consume these other formats directly.

1. Inspect source schema, row grain, missing markers and variable meaning. Identifiers
   and category codes are not continuous measurements merely because they parse as numbers.
   Initial CSV inspection returns field_guidance automatically. Reuse this recorded
   evidence when available; MCP recommend_table_fields and CLI table-guidance provide
   the same source-bound fresh-read advice. Explain measurement/grouping candidates,
   identifier exclusions and missing/constant/low-cardinality cautions. These are role
   candidates, not domain truth. Advice alone preserves the current workflow and never
   runs statistics; choosing regression outcomes still requires a concrete objective.
   For next-analysis questions, prioritize at most three recorded analysis_opportunities.
   Name relevant candidate fields, purpose and prerequisites. Resolve flagged meaning/
   missingness before inference; distinguish category percentages of rows from unique
   entities. Check repeated entities rather than infer them from identifier names.
   Use a short explanation and at most one genuinely missing-objective question.
2. Choose only necessary methods: describe, pearson, spearman, covariance, linear_regression.
   Descriptive fields support mean/min/max, arbitrary declared percentiles, SD and
   variance with explicit ddof. Correlation returns labeled matrices and unadjusted
   two-sided P-values, not causal relationships.
   covariance returns a labeled numeric covariance matrix with explicit ddof and
   complete-case row count. A matrix request differs from OLS covariance estimation.
3. For OLS supply numerical outcome/predictors, intercept policy and confidence level.
   No formula strings or implicit category encoding. Nonrobust covariance assumes a
   suitable independent/homoskedastic error design; HC3 addresses heteroskedasticity,
   not repeated observations. For justified repeated groups use cluster covariance
   with the grouping column; few clusters remain an inferential limitation.
4. Missing policy defaults error. complete_cases is an explicit analysis choice with
   reported exclusions across all selected numeric fields, not a modification to data.
   Declare source missing tokens instead of guessing that NA/NULL/? always mean missing.
5. Review coefficients, standard errors, intervals, P-values, R-squared/adjusted R-squared,
   rank/conditioning, row counts and residual diagnostics. Perfect fits suppress misleading
   coefficient inference. Do not describe in-sample fit as predictive validation.
6. Analytical reports summarize computed evidence and assumptions. Opening/downloading
   a browser report is separate from writing a dataset or publishing/database changes.
   Optional statistics.question records the user's analytical question, not an answer.
   Reports separate analysis definition, scope and computed findings from interpretation.
   Critic review must examine source scope, exclusions, grouping, missingness and design
   gaps; truncated evidence is not a successful independent verification. Never claim
   representative sampling, correct units or clinical validity from execution completion.
   Recorded grouped-mean figures show group sizes, not confidence intervals. Correlation
   heatmaps show recorded coefficients with explicit display caps; complete tables remain.
   PDF includes bounded figures; Markdown retains numerical tables/descriptions. Viewing
   charts or the adjacent advisory assessment does not execute or request another review.
7. Reuse this method family before proposing generated code or new dependencies. Unsupported
   categories, study designs, causal identification and unimplemented methods require a
   concrete clarification/limitation, not fabricated tool calls or medical conclusions.

Bounds: 200,000 matching rows, 24 selected numeric fields, 12 predictors, worker CPU/
memory/output limits. Exact full-file processing or explicit failure; no silent sampling.
The optional project statistics dependency profile supplies SciPy/statsmodels. The
fixed minimal Docker dataset-profile worker is a different runtime; this skill currently
uses the existing bounded table-analysis service in the configured project environment.

Initial guidance may include `analysis_starters`: closed descriptive option shapes
for complete numerical candidates, with missing_policy=error. They are advisory, not
executed skills or confirmed scientific designs. Reuse the typed shape for an explicit
request; keep selected grouping labels literal, do not invent marker handling, and do
not silently add regression/outcomes. A profile with filters needs its original query,
not a whole-source starter. The ordinary review/Execute boundary still applies.
