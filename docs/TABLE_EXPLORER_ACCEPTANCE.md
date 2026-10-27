# Column quality and grouped exploration — implemented first slice

Delivered 2026-10-24. This is the first functional slice of the
[full exploratory-analysis task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md), not completion
of its relationship statistics, uncertainty, adjusted model or clinical assignment.

## Profile timeout and refresh recovery — 2026-10-24

A reported 120-second model timeout was followed by a refresh that appeared successful.
Read-only inspection of saved records found a separately saved, zero-model-call profile
and a failed later submission with no run. Refresh restores saved work; it does not
complete a timed-out call. Those records do not prove a context overflow or identify
which exact text/settings reached the model in the failed call.

The complete documented profile now uses deterministic planning through both the
submission endpoint and the older conversation endpoint, with no model call. Explicit
method-selected requests retain their separate planning path. A new health field,
`analytical_planning_revision: table-profile-routing-v2`, lets the frontend block
profile submission to an older running API before dispatch. The prior inspection
contract alone did not establish support for this analytical route.

The frontend reconciles pending submission receipts without retries. Failed receipts
are labelled explicitly: a workflow restored on refresh is saved work, not a successful
retry. Existing proposals/runs remain unchanged. No model-size or timeout tuning is
required for the exact deterministic profile request.

After updating, stop the existing launcher with Ctrl+C, run
`bash scripts/start_actioncharter.sh`, then refresh the browser. Send the complete
profile prompt from the validation steps below. Expect **Exact inspection workflow ·
no model call**. Use Execute only after reviewing the proposal. Inspect a failed
submission with **Check last submission · no retry**; do not infer success from refresh.
Targeted routing/recovery tests and isolated browser old-version/timeout/refresh cases
pass. Final make test: 2,074 passed with 13 existing Rasterio warnings;
make interface-validate passed. No actual model call was needed for these regressions.

## Follow-up schema rejection — investigation pending exact request

A later report rejected an undeclared `columns` field after model correction. The latest
two persisted receipts confirm failure before run creation. The UI now distinguishes
that confirmed state from uncertain transport failures or submissions with recorded runs;
it no longer warns that dispatch may have occurred after confirming no run exists.
The failed prompt itself was not persisted, so the exact text has been requested to
reproduce routing. This message fix does not establish the cause of that model route
or claim to solve arbitrary natural-language planning. Existing reviewed plans remain
preserved. No backend routing changes in this follow-up.

## What changed

Completed CSV inspections now offer Columns and Explore alongside existing Results
pages. Plain CSV inspections can request these reads too; a prior profile is not required.
The workflow remains unchanged. UI controls use the same profile_table service exposed
through MCP and CLI, with typed AnalysisOptions and source/codebook verification.
Planner receives quality/group contracts for relevant requests; conversational model
reliability remains distinct from deterministic tool correctness.

Columns has searchable fields, empty versus declared-missing counts, exact distinct,
once-only and repeated-value metrics, frequent values, optional entire-row duplicate
checks and a selected-key check. Backend composite keys support up to four fields;
the first UI version selects one key field. Missing-key rows are excluded and reported;
a candidate key requires no missing keys and no repeats in a nonempty matching table.
Repeated patient IDs are not automatically duplicate records. Entire-row duplication
compares complete decoded raw rows; missing-token declarations do not collapse them.

Explore selects group/split fields, a distinct-count measure, an optional numeric
summary and one exact-text filter. The backend supports three group fields, four distinct
fields and six AND filters; this first UI has two grouping selectors, one distinct field,
one numeric field and one filter. Numeric summaries include count, mean, sum, min and
max; invalid and missing counts are shown. No type/clinical meaning is inferred from
numeric-looking codes. Empty text is a valid exact filter value when a filter is selected.

Run analysis explicitly scans and verifies the complete eligible source. Changing a
chart/measure only uses calculated groups, with no LLM call. Raw group keys remain
visible, including missing/unknown groups; chart labels use supplied code definitions
where available. Group proportions use all matching rows. Per-group distinct counts
can overlap and must not be summed as the global distinct count.

Interactive results remain while the same Results workspace is open, including tab
changes. Closing/reopening restores the original recorded operation, not a durable
saved exploration. Saving an exploration into a workflow/report is a later addition.
Stop waiting aborts the browser request and blocks stale responses; it does not cancel
an already running backend worker. Reads retain existing time/resource limits. No
changes to write authorization; these tools cannot export, approve or run writes.

## Exact frontend validation

1. Restart with `bash scripts/start_actioncharter.sh`, refresh
   http://127.0.0.1:5173 and use a new chat. Existing originals stay in data/input.
   Keep Inspection on send OFF for this reviewed test.
2. Paste and review, then Execute (no write authorization needed):

   ```text
   Profile diabetic_data.csv using IDS_mapping.csv. Group by age, readmitted. Summarize time_in_hospital. Count distinct patient_nbr. No writes.
   ```

3. Open Outcome and optionally expand it with the existing expand icon.
   Under Columns, search patient_nbr, select it, choose encounter_id for Check duplicate
   key, turn Duplicate entire rows ON, then Run quality checks.
   Expected: 71,518 distinct patients; 54,745 once-only patient values; 16,773 repeated
   patient values; 0 excess duplicate entire rows; encounter_id is a candidate key.
   These checks cover all source rows unless a recorded filter is active.
4. Search weight, select it, enter `?` in Declared missing tokens, then Run quality checks.
   Expect 98,569 declared-missing values. Repeat race (2,273) and payer_code (40,256).
   Empty-cell counts remain separate. Raw values and original files are not changed.
5. Explore: Group by admission_source_id, Split by readmitted, Distinct count field
   patient_nbr, Numeric summary field time_in_hospital. Leave No filter, then Run analysis.
   Expect complete coverage of 101,766 rows; grouped row_count sums to 101,766.
   Distinct patient counts appear per group and may overlap. Inspect numeric validity.
6. Switch Result table/Result chart; choose patient_nbr_distinct as Plot measure.
   Chart changes should not invoke the model or generate a workflow. Code definitions
   appear in chart labels where supplied. Above 100 groups the UI requires table/refinement
   instead of silently dropping groups.
7. Choose readmitted as Filter field and `<30` as Exact filter value; Run analysis.
   Expect 11,357 matching rows. The scope/query panel must show the filter and denominator.
   Change tabs and return: current computed results stay; opening a different run must
   not inherit them. Draft controls and recorded result scope are labelled separately.
8. Try an excessive grouping such as encounter_id with no filter: the group-limit error
   must be visible and previous results preserved. No partial aggregate is shown as success.

## Backend/MCP/CLI use

The existing profile_table MCP tool now advertises typed AnalysisOptions. For example:

```json
{
  "path": "diabetic_data.csv",
  "options": {
    "codebook_path": "IDS_mapping.csv",
    "group_by": ["admission_source_id", "readmitted"],
    "distinct_columns": ["patient_nbr"],
    "numeric_columns": ["time_in_hospital"]
  }
}
```

Quality options are `quality_columns`, `duplicate_rows`, `duplicate_key` and
`missing_values`. They can be supplied to the same tool or inspect_csv.analysis.
CLI: save just the options object in an ordinary local JSON file and use
`.venv/bin/python -m geoagent_harness.cli profile-csv diabetic_data.csv --project-root . --options OPTIONS_FILE`.
CLI entry compatibility is checked in tests; the installed command/module launcher
must follow the project's existing CLI entry instructions.

## Verification and resource bounds

The real-data acceptance script uses temporary copies and independent CSV counters,
not expected values embedded in production code. It verifies quality, grouped patient
counts, original profile facts and normal authorized aggregate export:

```bash
.venv/bin/python scripts/diabetes_analytical_acceptance.py
```

Measured trial: 101,766 rows, 30 age/outcome groups, validated_success; 42 admission-source/outcome groups also matched independent counts and patient sets.
Approximately 12.8 seconds for quality, both groupings and export combined; profile
worker peak RSS approximately 446 MiB in that run. Performance varies; this is not a massive-data benchmark.
Synthetic tests cover repeated/missing keys, raw versus declared missing, zero matches,
high-cardinality frequency recovery, output-name conflicts, explicit limits, source
changes, typed MCP/CLI parity and nonexecuting Planner quality proposals. An isolated
Playwright journey covers model selection, full-source pages/filters, quality checks,
grouped distinct counts, chart/tab changes and existing authorized export with zero page
errors, including an over-budget grouping preserving the previous result.
Final make test: 2,070 passed, 13 existing Rasterio warnings. Final targeted quality/
Planner/retrieval checks: 67 passed; final quality file: 14 passed.
make interface-validate passed; the existing production-bundle size advisory remains.

Exact-check state is bounded to 500,000 charged entries and an estimated 128 MiB, shared
with requested exact distinct sets; grouped distinct sets additionally cap 250,000
entries. Worker outer limits remain 2 GiB address space, CPU/deadline limits and 1 GiB
source. A request may reach a smaller practical limit; no approximation replaces a
failed exact check. Low-cardinality frequency metrics are available within the existing
128-value counters; request explicit quality checks for high-cardinality fields.
Response sizes remain bounded. No temporary dataset files or new dependencies added.

Installed inventory: pandas 3.0.5 and NumPy 1.26.4; SciPy, statsmodels and scikit-learn
were not installed. No statistical package was downloaded. Next coherent delivery is
validated descriptive statistics (including spread/quantiles with declared methods),
then association/uncertainty tools and one adjusted model with diagnostics. No claim of
Tableau parity, model training, clinical validity or the full task being complete.
