# Full-data preparation, database round trip and reports

Updated 2026-10-29. Delivery of F1–F4 continues T03/T04/T05/T13; F5 model
reliability is a separate gate. Earlier checkpoints remain historical records.

## Delivered structure

```text
Planner / existing role coordination
  -> registered typed operation schemas + relevant skill instructions
  -> proposed streaming strategy bound before review, never after approval
  -> normal exact-scope write authorization
  -> shared bounded preparation / PostgreSQL services
  -> deterministic validation + durable evidence
  -> source-linked analytical and technical documents
  -> interface / terminal / CLI / MCP read the same saved records
```

No new permanent agent, general Python/SQL executor, dependency installation or
permission inferred from chat was added. MCP exposes the contracts; the shared
backend implements them. Skills explain composition and interpretation. Existing
Single/Three modes remain available; advisory model reviews do not determine
execution permission or override actual validation.

* **F1:** `streaming=true` on select/filter/missing/decode/export CSV operations;
  streaming aggregation accepts validated CSV-producing ancestors. Shared readers
  preserve textual identifiers, full hashes, bounded previews and source identity.
  Row-local transforms reuse existing typed semantics. Bounds: 200,000 input/output
  rows, 1 GiB input-reader bound, 64 MiB output, existing reader time/state bounds. Output is checked
  before create-only publication; cancellation/collisions do not publish partials.
  New proposals automatically select this qualified strategy for CSV/TSV sources
  over 8 MiB and qualified descendants, unless explicitly false. Smaller files with
  too many rows still need explicit streaming selection; discovery is not row counting.
  Joins/calculated columns retain 10,000-row/8 MiB dataframe limits.
* **F2:** read-only `validate_postgres_import` checks every mapped value, key,
  cast and nullability against the exact source and connection identity. Per-column
  `null_values` overrides the legacy global policy; an empty list preserves every
  token. Proposed DDL is generated from typed declarations. This preflight does not
  connect to the database, establish target availability or authorize execution.
  Import repeats mapping validation before opening its write transaction.
* **F3:** existing create-only bulk import, actual-schema inspection and
  snapshot-bound export use their normal authority and transaction checks. Import
  receipts now include mapping digest and executed typed CREATE statement. A later
  failure never proves an earlier committed write rolled back; inspect receipts
  and targets before any deliberate retry. No automatic write retry.
* **F4:** saved workflow reports combine source-bound readiness/statistical findings
  with actual column types, nullability, keys, counts, digests, executed CREATE,
  mapping parameters and recovery limitations. Proposed DDL is labelled separately.
  No source scan/model call occurs on report read. Documents are bounded to 256 KB
  each with explicit omission notices; original step evidence remains available.
  Defaults, foreign keys, non-key indexes and grants are not a complete database
  backup. Outcome → Report includes Workflow technical handoff and Markdown/PDF
  download; CLI `chat report RUN_ID --kind technical|analytical|json`, terminal
  `/report RUN_ID` and MCP `workflow_report` reuse the same records. Existing
  readiness reports remain available. Local downloads do not grant tool authority.

## Manual frontend validation

Use a test database/schema you control, not a production target. Automated acceptance
below uses a new disposable PostgreSQL container and never your configured database.
A manually executed database workflow writes to the configured target: review its
identity carefully and use a fresh table name. Do not retry a failed write blindly.

1. Restart the existing launcher after the update:

   ```bash
   bash scripts/start_actioncharter.sh
   ```

   Open `http://127.0.0.1:5173`. API remains on 8765. Settings must show the intended
   installed model and endpoint. Files should be `data/input/test/diabetic_data.csv`
   and `data/input/test/IDS_mapping.csv`. Bare filenames are under data/input; use
   `test/…` for this subfolder. Use a new chat and automatic skill selection.

2. Submit this initial read-only request:

   > Inspect test/diabetic_data.csv, the complete source, using test/IDS_mapping.csv
   > for the three admission/discharge code definitions. Return full-file row and
   > field counts, distinct patient_nbr, encounter_id key and full-row duplicate
   > checks. Describe time_in_hospital numerically. Treat age as categorical bands
   > and identifiers as text. Treat ? as missing only in race, weight, payer_code
   > and medical_specialty. Compare age with readmitted using complete counts and
   > percentages. Do not sample or write files.

   If Inspection on send is off, press Execute. Read-only operations need no write
   authorization. Expected: **101,766 rows, 50 fields, 71,518 distinct patients**,
   encounter key with no duplicate records, **30 age/readmitted groups**, mean stay
   **4.395986871843248**. Missing `?`: race **2,273**, weight **98,569**, payer_code
   **40,256**, medical_specialty **49,949**. Check denominators and source hash,
   not just the preview. Columns/Groups/Chart/Checks/Report must refer to this run.

3. Ask for preparation, keeping scope explicit:

   > Keep the inspection. Prepare a full-file streaming CSV selecting encounter_id,
   > patient_nbr, age, gender, race, time_in_hospital, readmitted, admission_type_id,
   > discharge_disposition_id, admission_source_id, weight, payer_code and
   > medical_specialty. Preserve every row and textual identifier. Decode the three
   > admission/discharge fields using test/IDS_mapping.csv into additional label
   > columns without replacing original codes. Then aggregate encounter counts
   > and mean time_in_hospital by age and readmitted. Use fresh outputs. Prepare
   > only; do not sample or execute.

   Inspect graph/parameters before execution: selection → decoding → aggregation;
   use `source_step` for validated CSV artifacts, never the metadata inspection.
   Streaming must be true for full-source preparation. Allow writes in the runtime
   control, then Authorize the exact workflow, then Execute. Authorization alone
   must create nothing. Decoded output: **101,766 rows and 16 columns**; grouped
   output: **30 rows**, counts sum to 101,766. Inspect history before retrying.

4. On a controlled test target, request the mapping/preflight and fresh-table
   import plus export. Give a fresh allowed schema/table (for example
   `agent_sandbox.diabetes_trial_20261029_a`) and explicitly say it is a test target.
   Ask for text identifiers, encounter_id NOT NULL primary key, repeated patient_nbr
   allowed, bigint time_in_hospital, all other selected/decoded columns text, and
   `?`/empty as SQL NULL only in the four declared fields. Request a separate
   read-only `validate_postgres_import` before import and retain its evidence.
   Ask for an optional `is_deleted` false boolean marker and a fresh CSV export.
   Connection/source digests should be bound from trusted configuration/evidence,
   not invented or typed from a model response.

   Review source, mapping, key/null policy, exact target and effects. Allow writes,
   Authorize the changed exact workflow, Execute once. **17 actual columns** with
   marker, **101,766 rows**, **71,518 patients**, zero marked records; encounter_id
   key and observed types must match. Compare SQL NULL totals with step 2. No
   overwrite, delete or existing-table maintenance is needed for this test.
   Model output that omits an operation or asks a genuine target ambiguity is not
   evidence of execution: inspect the graph before approving.

5. Open Outcome → Report. Expand **Workflow technical handoff**. Check actual
   table/column metadata and executed CREATE separately from proposed DDL. Download
   Markdown and PDF; both should contain readable tables, correct source identity,
   counts and limitations. Reopen the run in history and repeat report access:
   no new operation should start, no target should change, and approvals must not
   become reusable for edited workflows.

## JSON and PDF checks

JSON support here is tabular **flat record arrays**, JSONL and NDJSON. Nested data is
not silently flattened. This does not claim generic JSON transformation support.
Use existing `examples/table_formats` fixtures; copy a fixture to data/input if needed.
Ask: "Inspect records.json. Describe numeric x grouped by region. No writes."
Repeat with records.jsonl. Expect four rows, overall x mean 1.5, sample variance
5/3, group A mean 0.5 and B mean 2.5. Compare source/rows/types, view the recorded
figure and export its report. Automated acceptance also covers XLSX.

PDF support tested here is **report export**, including readable multi-page statistics
and matrices. PDF document ingestion/OCR/text extraction is not delivered by this
slice. Do not submit a source PDF expecting it to become a table automatically.

## Reproducible isolated checks

```bash
make test
make interface-validate
node scripts/analytical_workflow_browser_check.mjs
.venv/bin/python scripts/diabetes_workflow_acceptance.py \
  --full-preparation --csv data/input/test/diabetic_data.csv
```

The last command requires the existing PostgreSQL 17 image/Docker daemon, creates a
new uniquely named tmpfs database with temporary credentials, verifies every projected
record against an independent CSV reference, then removes the container. It never
connects to configured/live services. Originals remain hash-checked and unchanged.
No row-level health data or secrets are written to repository acceptance documents.

Real-model comparisons use `scripts/full_data_agent_evaluation.py` with `--source`,
`--columns` and `--mode single|three`. They execute one full-file selection in a
throwaway project through normal approval, not the complete seven-step database plan.
Single successful planning/execution does not certify advisory reviews, latency or
all future model outputs. Test the staged frontend journey before Git preparation.

## Recorded implementation evidence

- Final `make test`: **2,230 passed**, 13 existing spatial warnings (275.45 s).
  `make interface-validate` passed with the existing bundle-size warning. The final
  terminal-history report fix passed 18 focused tests; strategy/discovery checks
  passed 27. `git diff --check` passed. No Git staging or publication occurred.

- Full-source **saved-run** acceptance passed in disposable PostgreSQL 17: 101,766
  source/export records, 71,518 distinct patients, 30 grouped records, 16 decoded
  fields and 17 database fields including the marker. Every projected exported
  value reconciled; actual types/key/null totals and technical CREATE/mapping receipts
  matched. Originals were unchanged. This used a typed fixture proposal, no model
  planning, and no live services. The final check took 125.405 seconds while other
  checks were running; this is not a performance benchmark.
- Isolated browser/real API/CLI/terminal journey passed, including technical-handoff
  PDF download, saved report CLI parity, JSON/JSONL/XLSX statistics, multi-page PDF
  tables/matrices, history and recovery. Zero browser page errors. Browser profiles
  and generated files were temporary; no personal browser cache was used.
- Actual installed `qwen3.5:9b`, reasoning none, same full-file selection task:

  | Mode | Planner | Full-source output | Advisory reviews | Total observed time |
  | --- | --- | --- | --- | --- |
  | Single | 1 successful planning call, 3,564 input / 188 output tokens | 101,766 rows matched | executor preflight and final self-review unavailable at 15-second budgets | 97.461 s |
  | Three | 1 successful planning call, 3,565 input / 189 output tokens | 101,766 rows matched | executor/critic preflight and final Critic unavailable at 15-second budgets | 96.662 s |

  These executions had zero database connections and used temporary full-file copies.
  Failed-review token usage was unavailable; no complete token totals are claimed.
  Calls were sequential, with different cold/warm/resource conditions, so elapsed
  times do not demonstrate one mode is faster. Advisory failure was explicitly
  retained; deterministic checks still passed. The evaluation script reports partial
  acceptance when reviews are unavailable. F5 remains open for review-budget/model
  reliability and complete staged user/model composition of the database workflow.

First validation exposed a missing ancestor handoff to the read-only mapping check;
it was fixed before the successful full-source run. Extending acceptance to durable
reports then exposed a test-harness identity assumption and insufficient schema-preview
retention; both were corrected and the complete saved-run path rerun in a fresh
throwaway database. A failed test never triggered an automatic production write retry.
