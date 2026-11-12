# Recorded inspection quality reports

Phase 0 bug fix, [issue #81](https://github.com/wanggiya/action-charter/issues/81).
This extends existing table inspection/reporting; it does not add an agent, execution
permission, statistical model or a new public operation schema.

## What changed and why

A completed owner diabetes run recorded 101,766 rows and 50 columns, but its plan
contained only `inspect_csv` with a source path. Missing counts and types existed;
no analytical profile, duplicates or statistics were requested. The report generator
ignored metadata-only evidence, and the interface assumed every CSV run contained a
readiness report. Consequently a successful inspection had an incomplete download.
The observed run was read for diagnosis only; no original run/report was rewritten.

New ordinary inspections collect basic quality during the same complete reader pass:

- Missingness for every column, storage types, candidate analytical roles.
- Distinct nonmissing values, values occurring exactly once, repeated values, and
  excess occurrences. These describe values, not automatically patients or entities.
- Whole-row duplicate patterns and excess duplicate rows, using SHA-256 of complete
  typed native records. The theoretical possibility of a hash collision is stated.
- Count, mean, minimum, maximum and sample standard deviation for finite numerical/
  count candidates. IDs, code fields and ordered interval labels are excluded from
  automatic measurement summaries. Roles require domain review.
- Observed candidate missing-marker strings with their counts. They remain real values
  unless the analysis explicitly declares them missing. No imputation occurs.

CSV values remain strings. Metadata missingness means empty CSV cells; native JSON/
XLSX nulls and empty text remain separate. The profile analytical view excludes empty
cells and explicitly declared tokens; its missing policy is printed. Incompatible
numeric values, including undeclared marker strings, are excluded from numerical
summaries and counted as non-numeric. Only finite values within ±10^15 qualify.
Standard deviation uses n−1 and is unavailable for fewer than two numeric values.

Basic profiles cover the complete inspected table, **before analytical filters**.
Existing filtered analyses retain their own matching-row denominators. A filename
suggesting a sample does not establish population provenance or permit extrapolation.

## Limits and compatibility

Shared distinct/duplicate counters retain at most 500,000 entries and an estimated
64 MiB including dictionary overhead. Exceeding either bound clears the affected
counter and marks its result unavailable; the scan, missing counts and numerical
summaries continue. No partial count is shown as a complete-file result. Exact
value counts and hash-based duplicate counts are distinguished in the report.

Ordinary worker outcomes remain within the existing 16 KB budget; explicit analytical
outcomes retain their existing 128 KB budget. Profile display fields can be omitted
with an explicit omission count, and advisory field guidance can be shortened.
Existing file, reader, worker-time and preview limits remain applicable. This fix
adds computation to the existing scan; it does not imply unlimited profiling.

The additive output `basic_profile` has schema version `basic-table-profile-v1`,
source path/hash, complete row count, missing-token policy and counter limits.
Compact field/numeric arrays declare their positional columns in `field_columns`
and `numeric_columns`; they contain aggregates, not raw rows. The renderer accepts
only a matching source/hash/row count. Missing/omitted values are not zero.

Older runs expose the source, missingness, types and limited cardinality advice they
actually recorded. Unperformed duplicate/numerical checks say not calculated. Existing
files and approvals retain their hashes. Opening/downloading reports never scans a
source, calls a model, executes a workflow or grants authority. A fresh inspection is
required for newly computed facts; refreshing an old report cannot create them.

Regression coefficients, P-values, confidence intervals, prediction error, precision
and causality are **not generic inspection metrics**. They appear only when a suitable
explicit analysis was actually executed. Existing Statistics/readiness reports retain
calculated methods; basic coverage explicitly states what it does not calculate.

## Shared implementation

Trusted readers feed `data/tabular/inspection.py`; `basic_profile.py` shares bounded
counters and pure report projection. Existing numerical compatibility guidance supplies
candidate roles and streaming moments. No arbitrary generated Python is executed.

Workflow handoff composes recorded basic facts with existing readiness/statistical
reports. New readiness downloads include the basic appendix when it fits; otherwise
an explicit omission points to the workflow Analytical report. Interface Report uses
that shared report for metadata-only runs and refreshes when run status changes,
including when Report was opened before execution finished. CLI `chat report RUN_ID --kind analytical`,
terminal `/report RUN_ID`, MCP `workflow_report`, and HTTP workflow report actions
reuse the same handoff. The existing report operation also uses this handoff when
persisting a new evidence report; downloads do not silently persist replacement files.

## Owner validation

1. Stop your existing launcher and restart with your usual configuration:
   `bash scripts/start_actioncharter.sh`. Open `http://127.0.0.1:5173`.
   These read-only inspections/downloads need no write enablement or authorization.
2. Open a **new chat** and send `Inspect sample_orders.csv. No writes.` If inspection
   on send is off, click Execute. Wait for the recorded run to complete.
3. Open Outcome → Report. Expect **Recorded inspection quality**, source/hash,
   six rows/five columns for the supplied fixture, missingness, distinct/repeated
   values, whole-row duplicates and numerical summaries. Mean/minimum/maximum are
   for numerical candidates; identifier fields are not treated as measurements.
4. Select Markdown and download, then PDF and download. Both contain those findings.
   Downloading must not create a new execution or authorization request.
5. Start a fresh read-only inspection of `test/diabetic_data.csv` (adjust only the
   relative folder if your file lives elsewhere under `data/input`). Confirm the
   source and 101,766 rows/50 columns for the original file. Compare an actual numeric
   field such as `time_in_hospital`, candidate missing markers, distinct `patient_nbr`
   and `encounter_id`, and the whole-row duplicate check. Age bands remain categories.
   A sample file must show its own source and row count, never the full-file count.
6. Reopen the earlier metadata-only run in Execution History → Outcome → Report.
   It now shows recorded missingness/types and labels unperformed checks. It must not
   suddenly claim newly computed duplicates, means or P-values. Refresh/reopen should
   preserve the same run ID. Existing downloaded files are historical and unchanged.
7. Optionally use the terminal `/report RUN_ID` or CLI analytical report for the same
   run. Remove/rename a **temporary fixture** after inspection if testing no-rescan
   behavior; the saved report should still open. Do not remove your real source data.

## Verification

Final focused backend checks passed: 75 inspection/readiness/source/compatibility
checks, plus the final 10 report checks including redaction and durable MCP parity.
Frontend typecheck/build passed; existing bundle-size warning remains. Strict source
and compatibility gates pass: 614 modules / 497 native, 290 retired / 117 public
boundaries retained, zero dependency debt/errors. The new module belongs to data
inspection/reporting, not transport or agent orchestration.

A temporary **synthetic** 101,766-row/50-column fixture retained all 50 profiles,
101,766 distinct encounters, 50,883 distinct repeated entities and zero excess whole
row duplicates. Direct shared-reader time was 7.47 seconds, compact outcome 15,286
bytes, process peak RSS 57,448 KiB in this run. This is a basic scan check, not a
real-model or comparative performance benchmark. No real source data was executed.

`make test`: **2,816 passed**, 13 existing spatial warnings, 785.18 seconds. The full
suite collected the initial eight new report cases; the final focused 10-case run
also covers subsequent redaction and durable MCP cases. Final frontend validation
passed; isolated stable-identity/relocated-state browser/API/CLI/PTY journey passed
with zero page errors. This includes exact CLI/Markdown equality, both download
formats, restored histories and report refresh on run-status changes. The browser
uses project-local dependencies and a fresh temporary profile, not the owner's
browser profile/cache. Documentation links and whitespace checks passed.

These are fixture/fake-model results. No new real-model, real owner-data execution
or live PostgreSQL/PostGIS test is claimed. Owner real-file report acceptance remains
the manual steps above. Issue #81 remains available for that acceptance record.
