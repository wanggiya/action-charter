# Real diabetes sample — frontend acceptance flow

2026-10-29: the **full supplied file is the real acceptance target**. The sample-scale
flow below remains a preliminary/reference journey. Follow the new
[readiness and full-data acceptance](READINESS_ASSESSMENT_AND_FULL_DATA_TEST.md) before
claiming full-data completion. Report now combines existing evidence; actual-model
planning, domain review and full-scale preparation/database transfer remain unverified.

## Inspection to descriptive analysis — 2026-10-28

Follow the [six exact steps and known answers](INITIAL_FIELD_GUIDANCE.md#exact-real-data-validation)
to inspect the sample, prepare time_in_hospital grouped by age, Execute and examine
the recorded report. This exercises general shared field guidance/statistics rather
than a dataset-specific operation. Expect 5,000 rows, ten age groups, mean 4.6592 and
sample variance 9.647384836967394; do not mix this sample with the full source.

## Age-by-gender cross-tab — 2026-10-27

The ordinary executed CSV inspection Outcome previously used a flat grouped list;
the cross-tab was only wired into the separate analytical-session Groups view.
Both now reuse the same two-field renderer. In ordinary Outcome the old Explore
tab is labeled **Groups**; existing internal view identifiers remain compatible.

1. Restart the launcher and refresh to load the new frontend. Open the completed
   inspection run for `data/input/test/diabetic_sample_5000.csv`; do not rerun writes.
2. Open **Outcome**. If multiple operations exist, select **Inspect CSV table** in
   **Operation result**. A saved proposal without an executed inspection has no result;
   execute the read-only inspection first, or reopen its actual completed run.
3. Select **Groups**. Set **Rows (vertical)** to `age` and **Columns (horizontal)**
   to `gender`. Optional distinct/numeric summaries and filters are under **Additional
   measures and filters**. Clear the filter unless testing a deliberately filtered population.
4. Click **Run analysis**. This is a source-verified full-file read, not an LLM request
   or a new workflow execution; write authorization is unnecessary. The source must
   remain available and match the recorded identity.
5. In **Result table**, expect age bands down the left, observed gender categories
   across the top, counts in cells and a grand total of **5,000** for this unfiltered
   sample. Categories absent from the source are not invented.
6. **Cell values** switches count / row percentage / column percentage / overall
   percentage. **Swap rows and columns** changes orientation. These presentation
   changes do not rescan the source. **Detailed measures** retains other computed
   numeric/distinct summaries; **Result chart** remains available.

For changed fields, apply the calculation before expecting the result title to change:
the title describes the displayed data, not the draft controls. Group chart supports
record counts or percentages with a visible all-matching/within-row denominator and
0–100% percentage axis. **Chart size** offers Compact, Comfortable (default) and Large;
the default uses the available width rather than the previous narrow chart. Additional numeric/distinct
chart measures remain selectable separately; those are not automatically percentages.

For two-field groups, **Chart → 3D columns** puts the first/second grouping fields on
the base and count/percentage on the height axis. Rotation/elevation sliders and Reset
adjust the view without a new read. Click or keyboard-activate a column for exact
values/denominator; background/Escape dismisses details. Height is a third visual axis,
not a third input feature. The cross-table/2D view remains the exact comparison path;
perspective may obscure columns. No new plotting dependency or model call is required.

Execution-state follow-up: disabled header Execute now provides its reason in its
tooltip/accessible description and graph status. Reloading a saved proposal does not
create an Outcome; the browser explicitly checks restore-before-execution. Historical
views remain read-only. This does not establish that every timeout/recovery case is solved.

For the analytical-session Outcome, use **Groups**, the same row/column selections,
then **Apply grouping**. Historical snapshots do not permit new source calculations;
return to the current workflow/session when a fresh grouping is required.

Browser acceptance uses temporary copies of the real sample/codebook, reconciles every
displayed age/gender count against all 5,000 source rows, and verifies totals/percentages.
A separate 20,000-row fixture checks equal gender splits, axis swapping and no new
analysis calls for display changes. Model proposals are fixtures; actual backend reads
and browser rendering are exercised. No live database calls or original-file mutations.

Prepared 2026-10-26 against the files actually present under `data/input/test`.
This is a structural/descriptive data-engineering test, not a clinical cohort,
population estimate, trained model or evidence of autonomous domain learning.

## Files and independently established reference

| File | Observed role | Rows / columns |
| --- | --- | --- |
| `data/input/test/diabetic_sample_5000.csv` | Bounded preparation acceptance source | 5,000 / 50 |
| `data/input/test/diabetic_data.csv` | Full source for comparison and provenance | 101,766 / 50 |
| `data/input/test/IDS_mapping.csv` | Three sectioned ID → description mappings | admission type 8; discharge disposition 30; admission source 25 codes |

The sample matches the **first 5,000 rows** of the full file, including multiplicity.
It is not a verified random/representative sample. Do not extrapolate its rates or
missingness to the complete source. In particular payer_code is `?` in every sample
row, versus 40,256 rows in the full source. This affects which analyses are meaningful.

Reference identities (recompute if files change):

- Sample SHA-256: `55b57c6c552e7b20f40c9dbd1dea98e706e5f214e879fe92407794fcd4e2d01b`.
- Codebook SHA-256: `f1bb82b471cb34649352597572c9b1fb00bd27f77b9f5a22a03dc3eb1039749e`.
- Full-file SHA-256: `0689e7ec031237dc63031b938805c48377748761a3b26acab621567afa24df97`.

| Sample fact | Expected result | Meaning / denominator |
| --- | ---: | --- |
| Encounters | 5,000 | Raw sample rows; no exclusions |
| Distinct encounter IDs | 5,000 | No duplicate keys or empty encounter IDs |
| Duplicate entire rows | 0 | All 50 original fields |
| Distinct patients | 4,260 | Patient identity differs from encounter identity |
| Patients occurring once | 3,754 | Counts people, not encounters |
| Patients occurring more than once | 506 | Not 740 patients; 740 is excess encounter occurrences |
| Recorded readmitted `<30` | 555 / 11.10% | All 5,000 encounters |
| Recorded readmitted `>30` | 1,967 / 39.34% | All 5,000 encounters |
| Recorded readmitted `NO` | 2,478 / 49.56% | All 5,000 encounters |
| time_in_hospital sum / mean | 23,296 / 4.6592 | All 5,000 values |
| time_in_hospital min / median / max | 1 / 4 / 14 | Age bands and IDs must not receive these numeric interpretations |
| Raw `?` in weight | 4,873 / 97.46% | Candidate/declared missing token, not an empty CSV cell |
| Raw `?` in payer_code | 5,000 / 100% | No observed payer variation in this sample |
| Raw `?` in medical_specialty | 1,519 / 30.38% | Preserve until an explicit preparation policy changes it |
| Raw `?` in race | 101 / 2.02% | Do not infer a demographic category |
| Mapping coverage, each of the three ID fields | 5,000 matched / 0 unmatched | According to the supplied codebook, not independently established clinical semantics |

Raw diagnosis `?` counts: diag_1 = 5; diag_2 = 36; diag_3 = 169. No inference about
clinical coding equivalence, chronology or causal relationships is made.

Two small cross-tab checks:

- age `[0-10)` × gender: Female 25; Male 19; row total 44. Female row percentage
  = 56.82%; Female overall percentage = 0.50% of 5,000 encounters.
- age `[0-10)` × readmitted: `<30` 1; `>30` 4; `NO` 39; row total 44.
- All age/readmitted groups: 30 observed groups, whose counts sum to 5,000.

For comparison, full-source recorded counts are `<30` 11,357; `>30` 35,545; `NO`
54,864; distinct patients 71,518; mean time_in_hospital ≈ 4.395986871843248.
These differences are expected; mixing full-source and sample results is a test failure.

## Start and preflight

1. Restart the existing launcher, then refresh `http://127.0.0.1:5173`:

   ```sh
   bash scripts/start_actioncharter.sh
   ```

   Leave that terminal running. Frontend uses 5173 and API 8765 by default. The runtime
   Allow writes switch controls availability; a startup write flag does not substitute
   for exact authorization. If an older launcher requires `--enable-write-tools`, use
   it only for this deliberate write test and still review/authorize the workflow.
2. In Settings, confirm an installed serving model is selected. Start a new chat for
   this test; use same-chat memory if desired. Leave capability acquisition and method
   experiments OFF so this acceptance isolates supported operations. Do not resubmit
   merely because a model request timed out; inspect the receipt and saved workflow.
3. Use the exact sample path below. Do not let the agent silently substitute the full
   file or generate a new sample. Full-file preparation exceeds current transform limits.
4. Database stages require an existing allowed **test** schema and working launcher
   credential-file configuration. Examples use `agent_sandbox`; substitute your allowed
   test schema consistently. If it does not exist, stop and arrange an explicit separate
   administrator action. Discovery/import does not create schemas or silently use public.

## A — read-only inspection and cross-tabs

Paste:

```text
Profile data/input/test/diabetic_sample_5000.csv using data/input/test/IDS_mapping.csv. Group by age, readmitted. Summarize time_in_hospital. Count distinct encounter_id, patient_nbr. No writes.
```

If this prepares a read-only workflow, click Execute; no write authorization is needed.
If recorded analysis is already returned, inspect that result rather than executing again.
Check source path, 5,000 rows, patient count, numeric summaries, recorded readmission
counts and codebook coverage against the reference above. A preview is not the population.

In Outcome choose Columns / the relevant field to review observed type and role. For
missingness distinguish the raw `?` token from empty cells and declared missing values.
For richer quality checks the later inspection step explicitly requests encounter-key
and whole-row duplicate checks plus a `?` policy; do not count unrequested checks as done.

Where the interactive dataset Groups view is available, choose age and gender, apply
then select count/row/column/overall percentages and swap axes. Compare the small cells
above. If this request opens the recorded inspection Results layout instead, use its
Explore grouping controls, or ask for comprehensive exploration to open the dataset
workspace; do not mistake a preview table for a complete grouping.

Optional terminal parity with the same running API/chat:

```text
/columns age
/columns age gender
/crosstab row
/crosstab total
```

The two-field command calculates a source-bound grouping; `/crosstab` only changes
presentation. Terminal interactive dataset commands require a saved comprehensive
profile. A legacy inspection-only record is not silently upgraded to one.

## B — inspect a database destination (read-only)

Before planning writes, ask in the same chat:

```text
List ordinary PostgreSQL tables in schema agent_sandbox. Prepare the read-only workflow; do not write anything.
```

Execute the read-only proposal. A missing schema/connection error is a configuration
finding, not evidence that imported tables exist. Pick a fresh name, for example
`diabetes_sample_trial_01`. If it or a proposed output already exists, choose a new suffix
before authorization; never drop/replace existing data to make the test pass.

## C — prepare local transformations, then append database operations

Paste the following. **Review the plan but do not execute it yet** if you intend to
include the database stages in the same workflow.

```text
Prepare a workflow for data/input/test/diabetic_sample_5000.csv using data/input/test/IDS_mapping.csv.
First inspect readiness: check encounter_id uniqueness and whole-row duplicates, count distinct patient_nbr, summarize time_in_hospital, and report ? as missing in race, weight, payer_code and medical_specialty.
Select only encounter_id, patient_nbr, age, gender, race, time_in_hospital, readmitted, admission_type_id, discharge_disposition_id, admission_source_id, weight, payer_code and medical_specialty.
Use decode_csv_codes to append labels for admission_type_id, discharge_disposition_id and admission_source_id from the supplied sectioned codebook. Unknown codes must fail. Preserve original codes and all encounters.
Aggregate the decoded table by age and readmitted, counting encounter_id as encounters and averaging time_in_hospital as mean_stay.
Use fresh CSV outputs. Do not impute, drop rows, change clinical labels, or execute anything yet.
```

Expected graph: inspection → selection → decoding → grouping. Inspect each block:
selection reads the original input; decoding references the validated selected CSV;
grouping references the decoded records. The mapping file is sectioned: an ordinary
`join_csv` directly against IDS_mapping.csv is **not** an equivalent plan.

Do not let the readiness `?` policy silently change the saved CSV. This preparation
preserves those raw strings; labeling and selecting columns are the only transformations.
Codebook labels such as literal `NULL` remain supplied descriptions, not CSV nulls.

Append database steps in a second message **before executing the preparation**:

```text
Keep these planned inspection, selection, decoding and aggregation steps. Append importing the decoded encounter table, not the grouped summary, into a fresh PostgreSQL table agent_sandbox.diabetes_sample_trial_01.
Preserve identifiers, age bands, codes and labels as text. Map only time_in_hospital to bigint. Set encounter_id as the primary key. Treat only empty CSV cells as null; preserve literal ? strings.
Include an explicit new NOT NULL boolean soft_delete_marker named is_deleted, default false.
Then export the validated imported table, including all selected fields, the three labels and is_deleted, to data/output/diabetes_sample_trial_01_roundtrip.csv.
Use the validated decoded CSV step as the import source and the validated import step as the export source. Do not execute or authorize anything yet.
```

Expected final graph and data references:

```text
Original sample ──→ Inspect readiness
       │
       └──→ Select 13 fields ──→ Decode 3 supplied mappings ──→ Aggregate groups
                                      │
                                      └──→ Import fresh PostgreSQL table ──→ Export CSV
```

Completion prerequisites can be sequential; the import's **data source** must still be
individual decoded records, not the aggregation output. No need to type file hashes or
JSON bindings. The backend binds the configured connection identity and validated
ancestor outputs. If the Planner asks a concrete schema/mapping question, answer it;
if it returns invalid schema or a timeout, capture diagnostics without repeating writes.

## D — one explicit review, authorization and execution

1. Enable Allow writes. Click Authorize and review the panel beside the graph.
2. Confirm original sample/codebook paths; fresh CSV targets; target schema/table;
   column types; text IDs; primary key; explicit deletion marker; export columns/path.
3. Record authorization. **No preparation CSV or database table should be created
   by this click alone.** Do not infer authority from the conversation wording.
4. Click Execute once. Wait for the recorded terminal status and inspect each step.
   Model summaries do not establish success; every writer needs passing validation.

Expected acceptance:

| Stage | Requirement | Expected output |
| --- | --- | --- |
| Readiness | Encounter grain and named missingness policy | 5,000 distinct encounters, 4,260 patients, no duplicate entire rows |
| Selection | No row loss or ID coercion | 5,000 rows / 13 columns |
| Decode | Three unique supplied mappings, no unknown codes | 5,000 rows / 16 columns; each mapping 5,000 matched / 0 unmatched |
| Aggregate | Complete sample, correct denominator | 30 groups; encounter counts sum to 5,000; mean_stay agrees with original rows |
| Import | Fresh table, exact schema/source | 5,000 rows / 17 columns; unique encounter primary key; all is_deleted=false |
| Export | Correct source table and create-only target | 5,000 records; all 17 projected values reconcile with decoded data + false marker |

Click Decode in the graph/information section: Codebook mapping coverage should show
three fields, each with 5,000 mapped and 0 unmapped. Full paths and order remain
expandable. Bounded previews may contain fewer rows to preserve metadata; row counts,
mapping coverage and validation remain visible. Current Outcome does not present a
standalone polished readiness-report page; use recorded inspection/quality evidence.

Inspect the imported table through a **new read-only** workflow after the writer run
has completed. Restore earlier versions through Workflow history to compare, without
executing them again. Reopening history must not copy old authorization or replay writes.

## E — optional marker and recovery test

This optional stage is for the chosen test table only, with a new explicit approval.
Inspect the imported table, choose two distinct encounter IDs from its recorded preview,
and ask to mark exactly those two records deleted. Use encounter_id, not patient_nbr.
Review exact keys/count, marker and snapshot; Authorize → Execute. Total rows stay 5,000;
exactly two records become marked. Ordinary inspection/export includes marked records.

Inspect again before preparing restore. Restore those two keys with a fresh snapshot
and new authorization. Row count stays 5,000 and marked count returns to zero. For this
small temporary test, table-content hash returns to the pre-delete identity; that does
not revive old approval, because each approved DB step has a one-attempt claim.

Expected rejection tests: stale snapshot, already attempted authorization, existing
output/table name, unknown code, invalid numeric mapping, or mismatched keys/count.
On any failure inspect failed_step_id, committed earlier outputs and recovery guidance.
Do not retry the entire writer workflow automatically. Source changes need new inspection;
soft-delete/restore recovery must not rename an existing target to a nonexistent table.

## Automated checks already provided

- `scripts/diabetes_reference.py`: independent Python CSV/Counter/Decimal oracle,
  all original-field row hashes for provenance, no platform analytical functions.
- `scripts/diabetes_test_flow.py`: explicit six-operation reference workflow. This
  tests adapter correctness; it is not a claim that a model generated that workflow.
- `scripts/diabetes_workflow_acceptance.py`: uses original data read-only, temporary
  copies/output/evidence and a newly created disposable PostgreSQL container; normal
  exact authorization precedes execution. Compares every projected row/value, all
  three supplied labels, grouped means/counts, primary key and independent SQL counts.
- `scripts/diabetes_preparation_browser_check.mjs`: real sample/codebook, actual API,
  graph, authorization, CSV processing and history restoration; only the model reply
  is a fixture. No live database calls. Verifies visible mapping coverage after reload.
- Unit tests cover unknown-code policy, preserved raw values, literal labels, invalid
  paths/collisions, intermediate identity, tampered labels and saved-preview budgets.

Developer reproduction from the project root (data files are not downloaded):

```sh
.venv/bin/python scripts/diabetes_reference.py --report /tmp/diabetes-reference-01.json
.venv/bin/python scripts/diabetes_workflow_acceptance.py --report /tmp/diabetes-roundtrip-01.json
node scripts/diabetes_preparation_browser_check.mjs
```

Report files are create-only; choose a fresh name for a new check. Docker acceptance
uses the existing local postgres:17 image and removes only its UUID-owned container.
Raw row-level CSV outputs and throwaway secrets remain in the temporary project and
are deleted after validation. Reports contain aggregate facts/hashes, not patient IDs.
Do not stage original datasets, runtime outputs, credentials or private reports.

## What to record during your real-model frontend run

Record model name, each exact request, current source identity, generated operation
sequence, prompt bytes/elapsed time, correction/timeout findings, manual clarifications,
actual row/coverage/group results, write targets and per-step validation. Use this
reference to distinguish planning failure, display failure, unsupported operation,
configuration failure and numerical mismatch. The actual installed model has not been
certified by the deterministic proposal/browser fixture; this remains your next acceptance.

Do not claim broader readiness from this sample: maximum-scale transforms, clinical
cohort definitions, patient-dependent uncertainty, adjusted models, prediction/leakage
controls and reusable domain learning remain the documented later tasks. A plausible
model explanation or successful database load is not evidence of those capabilities.

## Verification recorded for this delivery

- `make test`: **2,130 passed**, 13 existing raster fixture warnings. The three new
  independent-reference fixture tests were added after suite collection and passed
  separately; the final focused data/SQL regression selection passed 45 tests.
- `make interface-validate`: passed; existing bundle-size warning remains.
- Real sample/disposable PostgreSQL acceptance: passed for all 5,000 projected rows,
  30 groups, three mappings and 17 exported columns, with no model call or live-service
  connection. Original sample and mapping hashes were unchanged after the run.
- Real-data preparation browser acceptance: passed actual authorization/execution,
  visible 5,000/0 mapping coverage for each field, recorded validation and reload/history
  restoration without a second execution; no page errors or database calls.
- Prompt-size regression checks passed after keeping unrelated codebook schemas out
  of focused requests and removing a duplicated deferred-ID list from calculation prompts.

These checks validate supported services and presentation with an operator-authored or
fixture proposal. They do not certify the installed Ollama model's natural-language
planning; record that separate frontend run using the exact requests above.
