# Analytical delivery and real diabetes retest

Implemented 2026-10-24 following operator authorization. This update supersedes
proposal-only status for the delivered scope below. Memory designs remain parked;
checkpoint 29 and the broader clinical assignment are not declared complete.

## Delivered scope

- Settings discovers installed/loaded Ollama models and persists an explicit project
  selection for new API model requests. Active requests retain their starting model.
  Discovery does not download models or test their planning compatibility. Standalone
  CLI model configuration still uses its environment.
- Typed, hash-bound source-table references carry read-only analytical queries and
  codebook bindings. They are not executable authority. Existing validated CSV
  intermediate outputs remain supported; a general lazy dataframe engine is not added.
- Streaming profiles cover the complete file: missing/category/numeric summaries,
  explicit distinct counts, exact filters, bounded pages and reconciled grouped counts.
  Sectioned IDS_mapping.csv supplies labels and mapping coverage without joining or
  duplicating encounters. IDs and age bands receive no invented clinical meaning.
- Explicit streaming aggregate_csv exports full-source count/mean group summaries
  through existing review, write permission, approval, execution and validation.
- Shared services serve workflow, MCP profile_table and CLI profile-csv entry points.
  MCP exposes typed calls; it does not contain the implementation, dataset or memory.
- Results retain existing tabs and styling. Overview shows profiles and definitions;
  Table supports explicit verified reads, filtering and paging; Chart uses all recorded
  groups within its chart budget rather than the first source rows.
- Optional execution assistance reasons over scoped recorded evidence and can request
  one verified profile. It has two model calls and a 45-second overall budget, with
  no write, approval, workflow mutation or automatic retry authority. This is post-run
  assistance, not an autonomous mid-run recovery agent. Revision suggestions go back
  to Planner for normal validation. No additional container or compulsory model chain.

## Exact frontend retest

1. Stop the old launcher with Ctrl+C; from the repository run:

   ```bash
   bash scripts/start_actioncharter.sh
   ```

   Open http://127.0.0.1:5173 and refresh. Keep diabetic_data.csv and IDS_mapping.csv
   in data/input. A nested test/file.csv resolves under data/input/test/file.csv;
   arbitrary project-root test/ access remains disallowed.
2. Settings → Refresh models → choose an installed model → Use selected model.
   Selection persists across chats and launcher restarts. Keep inspection-on-send OFF
   for this analytical test; use Execute after reviewing the proposal.
3. In a new chat paste exactly:

   ```text
   Profile diabetic_data.csv using IDS_mapping.csv. Group by age, readmitted. Summarize time_in_hospital, number_inpatient. Count distinct patient_nbr, encounter_id. No writes.
   ```

   Review the input/codebook nodes and analytical arguments. Click Execute; no
   authorization is required for this read-only workflow. This exact request uses
   deterministic planning; broader natural-language requests still depend on the model.
4. Open Outcome → Overview. Expected for the supplied original file: 101,766 source
   rows, 71,518 distinct patient_nbr, 101,766 distinct encounter_id, 30 age/readmitted
   groups and three codebook sections. Raw readmitted counts: NO 54,864; >30 35,545;
   <30 11,357. Check distributions and group-count reconciliation.
5. Open Analytical table. Choose readmitted as Filter column, enter <30, apply the
   filter: expect 11,357 matches. Next page must show later rows. These actions reread
   and verify the complete source; local page search/sort only affects loaded rows.
   Chart uses all 30 recorded groups. Opening saved results alone does not rerun them.
6. To verify full-file export, send:

   ```text
   Aggregate diabetic_data.csv. Group by age, readmitted. Count encounter_id as encounters. Mean time_in_hospital as mean_stay. Save to data/output/diabetes_raw_groups_20261024_01.csv.
   ```

   Review the aggregate operation and output, turn Allow writes ON, Authorize, then
   Execute. Sending and authorizing alone must create no output. Expect 30 output rows;
   encounters must sum to 101,766. Use a fresh filename if it already exists; this test
   does not authorize overwriting anything. Runtime Allow writes needs no restart.
7. Optional: in Checks open Execution assistance and ask about recorded evidence.
   It may explain or request one scoped profile. It cannot execute suggested changes.
   A timeout must leave workflow and outputs unchanged.

Do not interpret this raw encounter grouping as a clinical cohort, diagnosis,
causal claim or trained predictor. Missing-code policy, exclusions and denominators
must be specified before the substantive health assignment.

## Verification evidence

- Full make test: 2,064 passed, 13 existing Rasterio warnings.
- Final focused analytical/model/planner/path/tabular regressions: 124 passed.
  make interface-validate passed (typecheck and production build); the existing
  large-bundle advisory remains.
- Isolated Playwright journey: Settings selection/persistence, 20,000-row profile,
  codebook, complete-source filter/page/chart and gated aggregate export passed;
  zero page errors. Uses existing project-local browser assets and an isolated profile;
  no installation or shared browser cache access.
- Existing checkpoint-28 execution browser suite: all four cases passed.
- scripts/diabetes_analytical_acceptance.py copies the actual two inputs into a temporary
  project, compares independent CSV counters/sums with profile and exported groups,
  and exercises normal review/authorize/execute/validate. Passed: 101,766 rows,
  71,518 patients, 30 groups, validated_success; approximately 5.6 seconds overall and
  197 MiB peak worker RSS on this laptop. Originals and live services unchanged.
- Actual qwen3:4b-instruct assistance on synthetic numeric values 2 and 4 returned
  count 2, sum 6, mean 3 in two model calls and one verified profile (~10.8 seconds).
  Earlier trials exposed decoder grammar and numeric-selection mistakes; corrected
  contracts and the final passing trial do not establish general model reliability.

Repeat backend real-file acceptance without writing original data:

```bash
.venv/bin/python scripts/diabetes_analytical_acceptance.py
```

## Limits and next work

Profile limits: 1 GiB source, bounded worker time/memory, 16 selected profile columns,
8 numeric columns, 4 explicit distinct sets (250,000 values each), 2,000 groups,
100 rows/page. Category counters stop above 128 distinct values; at most 12 categories
are displayed. No sampled totals are substituted. Normal CSV transforms retain their
existing 8 MiB/10,000-row limits; streaming aggregate is an explicit additional path.
Codebooks are bounded sectioned two-column CSV mappings, not arbitrary metadata joins.
Charts currently cap complete group display at 100 groups. Original source changes
invalidate hash-bound reads. Broader large-file transformations, lazy intermediates,
clinical cohort decisions, automatic execution adaptation and learning/memory work
remain separate follow-ups. Do not claim RL, unrestricted code generation, or parity
with established data-science products.
