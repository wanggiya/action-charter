# Initial statistical field guidance and readable Summary

Implemented 2026-10-28. This extends existing inspection, not a new autonomous agent
or statistical execution permission. Historical checkpoints and saved evidence remain.

Next slice: [analysis recommendations, agent roles and report evidence](T05_ANALYTICAL_ADVICE_AND_REVIEW.md)
adds Possible next analyses and recorded next-analysis advice; existing behavior below
remains. Reports can retain an optional question with explicit computed findings.

## Operator experience

New completed CSV inspections show **What to explore next** in Outcome → Overview.
Shortlists distinguish candidate measurements, grouping/category fields and identifiers.
Fields with constant values, ambiguous low-cardinality integer codes, missing markers,
mixed data or unavailable cardinality are called out for review. Expand **Field evidence
and limitations** for candidate roles, counts, reasons and cautions.

**Ask Planner about these fields** prepares a question in the current chat. It does
not submit automatically. Sending that advice question uses the recorded evidence,
allows only an explanatory message with plan=null, and preserves the existing plan.
It cannot approve/execute operations, create a replacement workflow or silently select
a regression outcome. The prepared question binds the source hash; advice never
substitutes a different recorded source/hash if the requested evidence is unavailable.
This also holds with inspection-on-send enabled. The submission
message explicitly says the workflow is unchanged, rather than claiming a new proposal.
The model can ask about the user's objective and units, not invent clinical definitions.

Statistics Summary/Regression facts now use full-width label/value rows. Shared legacy
dd width:100% no longer squeezes labels to zero width. At narrow panel widths labels
sit above their values; words remain horizontal. Long paths/hashes can wrap normally.
Statistical page tabs scroll horizontally when the panel is narrow.

## Shared backend and agent responsibilities

- Ordinary CSV inspection collects fixed counters during its existing complete
  hash-verified scan. No second scan, DataFrame, SciPy import, model call or full-file
  statistical fit is needed to produce initial hints. Preliminary preview metadata
  never claims completed guidance.
  Its hints cover the complete source even when another analytical query is filtered;
  comprehensive-profile hints instead describe that profile's recorded matching rows.
- Comprehensive profiling reuses the same role classifier and advice builder. Explicit
  role overrides/codebooks retain their existing meaning. Existing fixed worker results
  can be enriched by the host service; a rebuild is not required merely for advice.
  The isolated worker build manifest includes the shared standard-library module for
  future builds. No worker/network/credential boundary is weakened.
- Planner receives bounded candidate names and aggregate evidence from the matching
  recorded chat/plan/run. Advice-only questions use a small message/null-plan schema
  with no operation schemas. The backend rejects attempted workflow/action changes,
  including from a provider ignoring decoding constraints. Normal processing requests
  retain the normal planning/approval/Execute path.
- Agents can request a fresh read using registered read-only MCP **recommend_table_fields**.
  CLI **geoagent table-guidance PATH --project-root ROOT** uses the same service.
  Terminal **/guidance [RUN_ID]** reads ordinary recorded inspection advice without
  rereading sources; comprehensive terminal Overview also shows candidate shortlists.
- The Planner manifest, operation catalog and table-statistics skill document this
  capability. No new unrestricted library function, generated code or execution role.

## Meaning and bounds

Roles are heuristic candidates, not verified domain knowledge or learned clinical
rules. Numerically encoded IDs/codes are not measurements just because float parsing
succeeds. Interval labels such as age bands stay categories; their midpoints are not
invented. Missing markers remain separate from declared missing values. There is no
automatic removal: potential marker strings are excluded only from the candidate
numeric-role compatibility count, while source values and declared missing counts stay
unchanged. Supplied codebooks keep defined numeric-looking fields categorical. There is no
automatic imputation, field conversion, outcome selection, causal claim or statistics run.

All records are examined under the existing CSV file/time/column budgets. Ordinary
advice retains at most 64 distinct short values per field, with fixed counters for
types/missingness/range. Overflow/long values make cardinality unavailable, not sampled.
Presentation caps explanations at 32 fields and shortlists at 8 per group, shrinking
further if required by the existing inspection response budget. Total/omitted field
counts and limits are explicit. This is a starting shortlist, not an exhaustive ranking
of domain importance. Full profile Columns remains available for other fields.

Saved hints describe the recorded source hash, not current freshness. Old runs without
guidance are not silently rescanned or rewritten. A new read-only inspection records it.
No cross-chat knowledge, model-weight training or new memory sharing was added.

## Manual verification

1. Restart the usual launcher and refresh. Open an existing statistical run →
   Statistics → Summary, then Regression → diagnostics. Check that labels use normal
   horizontal words. Narrow the panel: values should stack below labels when needed.
2. Start a new chat and send:

   ```text
   Inspect test/diabetic_sample_5000.csv. Return row count and column names. No writes.
   ```

   If inspection-on-send is off, click Execute. No write authorization is needed.
3. Open Outcome → Overview. The current sample has 5,000 rows and 50 fields. Look
   for time_in_hospital/num_medications among numerical candidates, age/gender/race
   among category candidates, and encounter_id/patient_nbr among identifiers. Codes,
   missingness and sparse/constant fields should not become confident measurement claims.
4. Click **Ask Planner about these fields**, inspect the prepared question, then Send.
   Confirm an explanatory answer, the same workflow/run and no new execution. The
   agent should ask about objectives before choosing a regression outcome.
5. Refresh/open the saved run. Hints should persist with the recorded source binding.
   In terminal use `/guidance`; for a fresh CLI read use
   `./.venv/bin/geoagent table-guidance test/diabetic_sample_5000.csv --project-root .`.

## Verification scope

Automated fixtures check full-source counters, identifier/code/band handling, missing
markers, constant fields, response bounds, CLI/MCP equivalence, safe paths and agent
workflow preservation (including inspection-on-send). Browser checks cover initial
visibility, question composition, advice without replay, and Summary at wide/narrow
widths. Real 5,000-row inspection established all 50 fields and the expected candidate
families. Browser agent wording uses a model fixture; actual local-model explanation
quality remains a manual check. Ollama had no model loaded during this implementation.

Verification: full suite 2,179 passed before the final supplied-codebook/source-binding
follow-ups; final focused conversation/guidance/calculation suite 95 passed, and the
additional profile/discovery/terminal suite passed. Interface validation and final
isolated browser journey passed with zero page errors, horizontal Summary labels at
wide/narrow widths, hash-bound advice without dispatch and preserved report downloads.
No dependencies installed or real browser profile/cache accessed for this slice.

## Inspection-to-analysis follow-up — 2026-10-28

This implements the next T03/T05 slice from IMPLEMENTATION_TODO. After inspection,
expand **Prepare a descriptive analysis** in the same Overview section. Choose a
numerical field and optional **Group by**, then **Prepare analysis request**. The
composer receives a plain-language request with explicit typed inspect_csv arguments.
You can edit it or simply ask the Planner for analysis directly; this is an optional
shortcut, not a mandatory form. Send proposes one analysis step replacing the ordinary
inspection. Review the actual proposal and press Execute. Preparation/submission never
claims that statistics ran. Initial hints and advice-only questions remain unchanged.

The shared guidance service exposes at most eight starter specs through existing
inspection/MCP/CLI outputs. They use the existing AnalysisOptions/StatisticsSpec shape,
describe, one selected measurement, missing_policy=error and the established defaults:
quartiles, sample variance/SD (ddof=1), no imputation or excluded rows. Optional grouping
uses retained grouping candidates and preserves literal category labels; group labels
that represent missing markers are not silently removed or decoded. Agents can use the
same typed statistical skill without this UI. No new operation, runtime or agent role.

Only complete numeric measurement candidates with no recorded cautions, at least
three observations, values within ±10^12, and at most 200,000 complete source rows
qualify. Constants, identifiers, ambiguous low-cardinality numeric codes and incomplete
numeric measurements are excluded from the shortcut, not from all explicit statistical
analysis. Filtered profiles need an explicit original-query specification; starters do
not reconstruct lost filters. Output budgets can reduce starter/explanation counts.
Old saved guidance without starters still opens. The standard-library-only profiler
module remains compatible with the fixed worker build and does not import SciPy/model
code for hints. No worker image was rebuilt.

The prepared request records the historical source hash as context, not a freshness
guarantee or executable argument. Execution verifies/records its own source; old advice
is not a substitute for inspecting changed inputs. Units, the scientific objective,
analysis unit and a clinically meaningful outcome still need domain judgment. The
shortcut does not select regression designs or causal conclusions.

### Exact real-data validation

1. Restart with `bash scripts/start_actioncharter.sh`. Writes are unnecessary here.
2. In a new chat send `Inspect test/diabetic_sample_5000.csv. Return row count and
   column names. No writes.` Execute if inspection-on-send is off.
3. Outcome → Overview → Prepare a descriptive analysis. Choose **time_in_hospital**
   and **age**. Prepare analysis request. Confirm the composer changed but no run started.
4. Send. Check one inspect_csv step whose analysis.statistics has methods=[describe],
   columns=[time_in_hospital], by=[age] and missing_policy=error. If the model changes
   those selections, correct the proposal before execution. No regression or writes.
5. Execute. Outcome → Statistics → Descriptive must show 5,000 analysis rows,
   zero excluded rows, mean **4.6592**, sample variance **9.647384836967394**, and ten
   expandable age groups. Expand one to see its measurements. These are encounter
   descriptions, not independent-patient inference; the sample is the recorded first
   5,000 rows, not an established representative sample of the full source.
6. Report: verify the same fields, groups, row counts and source hash, then download
   Markdown or PDF. Refresh/reopen through Workflow history: results must persist.
   Terminal `/statistics` reads the matching recorded run; CLI `chat history CHAT_ID`
   followed by `--entry run:RUN_ID --json` reopens its full recorded outcome. CLI
   `chat result --view overview` still targets comprehensive profiles, a distinct path.

Independent read-only verification on the real 5,000-row sample reconciled the whole
mean/variance and every age-group mean with Python's statistics module. Unrelated
temperature/region fixtures validate known means and sample variance, typed contracts,
CLI/MCP equality, and rejection of newly introduced invalid values under error policy.
The isolated browser verifies inspection → chosen fields → one-step model-fixture
proposal → explicit Execute → report → CLI history read, without accessing real browser
cache. Existing PDF, statistical pages, charts and restoration journeys also pass.
Actual Ollama proposal quality for this new request remains manual acceptance; fixture
results do not prove local-model reliability. No dependencies installed or Git/live
database operations performed.

Verification for this follow-up: `make test` **2,182 passed** (13 existing spatial
warnings); `make interface-validate` passed with the existing bundle-size advisory;
the complete isolated analytical browser journey passed with zero page errors.
