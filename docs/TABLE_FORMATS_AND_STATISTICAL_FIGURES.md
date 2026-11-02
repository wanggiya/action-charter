# Statistical figures and table-format adapters

2026-10-29. T05 report/assessment presentation plus T08 common table-reader slice.
The user has not yet manually accepted the preceding or current slices; automated
acceptance does not substitute for that validation. Existing checkpoint history remains.

## What changed

Statistics Descriptive now shows a grouped-mean figure for the selected measurement,
with analyzed/matching group sizes on selection. Means retain original units and a
zero baseline, including negative values. No confidence intervals are implied. Matrices
adds coefficient heatmaps with selected coefficient, unadjusted P-value and common
complete-case count. Unavailable values are gray, not zero. Click a mark or focus it and
press Enter/Space; Escape or leaving the figure clears the detail. These are projections
of recorded aggregates, never new source reads or fits.

Report renders the same bounded figures; PDF embeds generated local SVG figures and
captions, with no network assets or chart uploads. Markdown retains the complete
numerical tables and descriptions rather than broken image links. Reports show at most
four grouped measurement figures, 24 groups/figure and 12 fields/heatmap; captions state
omissions and complete tables remain unchanged. These plots do not supply missing
raw-data histograms, scatterplots or uncertainty estimates. Existing statistical figures
can render for old compatible snapshots without rewriting them.

Statistics also has a collapsed Agent assessment section using the existing Critic/
self-review component. It separates model interpretation from computation, displays
waiting/unavailable states, and reads recorded assessment only. Opening it does not
start another review/model call or execution. No new agent or role routing.

## Reader support and limits

The stable workflow operation remains `inspect_csv`, including its legacy readable
name in some surfaces. The catalog advertises supported_source_formats and the same
operation's typed analytical options. Existing CSV-only transforms remain CSV-only;
this release does not pretend they can join/write XLSX or JSON directly.

| Format | Delivered reader policy | Limits or exclusions |
| --- | --- | --- |
| CSV/TSV | Existing streamed, verified reader and typed transforms | Existing independent metadata/analysis/write limits retained |
| XLSX | Read-only selected worksheet, literal text header, explicit header_row or cell_range | Ambiguous workbook needs sheet; formula/error cells, macro members and external-link packages reject; no cached-formula substitution |
| JSON | Flat record array; optional explicit top-level records_key | No automatic GeoJSON handling or nested-cell flattening; empty array cannot establish schema |
| JSON Lines / NDJSON | One flat object per nonempty UTF-8 line | Blank lines skipped; malformed/oversized records reject |

New readers: 16 MiB original file, 200,000 rows, 100 bounded fields, 4,096 characters/
analytical cell; existing CPU/memory/output budgets also apply. XLSX archive metadata
is checked before loading: <=2,000 members, <=64 MiB total expanded and <=32 MiB per
member. XML protection uses declared defusedxml; openpyxl does not execute formulas.
Plain JSON arrays decode incrementally; JSON Lines streams records. Explicit object
wrappers use a bounded 16 MiB in-memory decode; this is not an unlimited streaming
wrapper implementation. XLSX uses read-only iteration; shared-string handling still
has the declared archive/process memory bounds.

XLSX source_options.cell_range uses an explicit A1:C100 rectangle with the first row
as header. It cannot be combined with a nondefault header_row; reversed, oversized and
out-of-Excel ranges reject. Selected range/worksheet enter query identity and report
scope; a range's rows are not claimed as the complete workbook. Without a range,
over-budget worksheet dimensions reject. Understated worksheet dimensions are reset
before iteration so they cannot silently truncate the selected table.

The first JSON object defines ordered column names. Missing later keys become null;
new later keys, duplicate keys and nested object/array cells reject rather than discard
or silently flatten data. JSON booleans, text identifiers and numeric types remain
visible in native preview/type metadata. Workbook dates become ISO text. Numeric
Excel display formats do not turn a number into a leading-zero text identifier.

The existing analytical accumulator uses a **string analytical view**, preserving
IDs stored as text. It treats null and empty string as missing. Metadata retains
separate null and empty-string counts and exposes this policy in warnings; this is
not full native pandas nullable-type preservation or arbitrary spreadsheet semantics.
Statistics still requires explicit numeric fields and missing policy. Bounds fail
explicitly; there is no implicit sample or permanent CSV conversion artifact.

Safe no-follow paths and before/after file/path identities protect reads. Original
file SHA-256, source selection and query enter result references; no converted CSV hash
substitutes for workbook/JSON identity. Recorded view changes inherit worksheet/record
selection. Changing it requires a fresh reviewed inspection; a matching byte hash alone
does not make two worksheets the same dataset. Source changes reject fresh views.

## Agent, MCP and CLI access

- The Planner receives source selection schemas/policies only for relevant record-source
  requests or an existing record-source workflow; ordinary CSV prompt budgets stay small.
  Its statistical skill documents supported readers, prerequisites and exclusions.
  Existing source-existence checks recognize the new suffixes. Explicit selector
  annotations/simple worksheet names, typed statistical arguments and a closed simple
  descriptive command bind their supplied values in decoding and backend validation.
  This is not general natural-language constraint extraction. Fully specified, single-
  source descriptive requests produce a typed proposal; missing/ambiguous inputs and
  richer study designs retain clarification. No reader selection is guessed or patched
  into a model reply after generation. Providers ignoring decoding constraints are
  independently checked before a proposal is saved.
  For this bound descriptive path, the visible confirmation comes from validated
  source/field/group/selector arguments. Original model prose is retained as unverified
  diagnostic text; it cannot misstate the normal confirmation or grant authority.
- MCP profile_table accepts AnalysisOptions, including source_options. table_statistics,
  linear_regression and recommend_table_fields also accept typed source_options.
- CLI inspect-table PATH --options JSON uses the same bounded service. Existing
  table-statistics/table-guidance accept --source-options JSON. No Python code is evaluated.
- Frontend graph, Execute, Outcome statistics, grouping and durable history reuse the
  same operation/run path. New formats require Execute even with inspection-on-send ON;
  sending never probes these new formats or chooses a sheet automatically.
- Analytical folder exploration/comprehensive Docker profile remains its existing
  CSV-focused protocol. The new adapters use the shared table-analysis worker, not
  arbitrary Python or a rebuilt Docker image. Request the file explicitly in Planner;
  do not claim universal folder-agent or all-format transform support.

Dependency profile: `.venv/bin/python -m pip install --no-cache-dir -e '.[table-formats]'`
in the launcher environment. dev includes the reader dependencies. This slice installed
openpyxl 3.1.5, defusedxml 0.7.1 and et-xmlfile 2.0.0 without pip/browser cache access.
No install occurs automatically during execution. Missing runtime produces an error.

## Combined manual acceptance

1. Copy synthetic fixtures from examples/table_formats into data/input (choose new
   names rather than overwriting your files). Restart the existing launcher. Writes
   are not needed for these inspection/analysis tests.
2. In a new chat, inspect the copied JSON file. Send should create a proposal; Execute
   records four rows and preserves record_id="001". Check Overview source/type warnings.
3. Ask for descriptive statistics for x grouped by region, missing_policy=error, replacing
   the inspection with one analysis step. Review the selected fields, then Execute.
4. Statistics → Descriptive: mean x=1.5, sample variance=5/3; group A mean=0.5 (2 rows),
   group B mean=2.5 (2 rows). Click a bar, check its count/value and clear with Escape.
5. Ask to replace the analysis with Pearson correlation of x/y. Execute, then Matrices:
   coefficient approximately 0.982707629824, four complete rows. Click its heatmap cell;
   it must agree with the table. No causal claim or established independence.
6. Report → PDF: expect figures/captions plus all report tables. Markdown retains
   the numerical report. Expand Agent assessment: completed review or explicit
   unavailable state, clearly separate from computations. Opening it must not add a run.
7. Repeat with the equivalent JSON Lines file and your chosen XLSX worksheet, specifying
   the sheet and actual column names. An ambiguous workbook must ask for sheet selection;
   formula cells must fail explicitly. Do not use a private production spreadsheet first.
8. Reopen Workflow history/terminal history. Source/query/results must agree without
   rerunning. For workbook groups/columns, verify that changing the view retains the sheet.

CLI example after copying the fixture as data/input/format_records.json:

```bash
.venv/bin/geoagent inspect-table format_records.json --project-root . --options '{"statistics":{"columns":["x"],"by":["region"],"missing_policy":"error"}}'
```

Terminal `/statistics` still reads the stored numerical report; it does not become a
GUI heatmap. CLI/MCP numerical evidence and original source bindings match the frontend.

## Verification and next formats

Equivalent CSV/XLSX/JSON/JSONL/NDJSON fixtures independently reconcile complete means,
variance, grouped results and original hashes. Tests cover selection persistence,
unsafe paths/mutation, formula rejection, duplicate/nested/new JSON keys, null/empty
semantics, CLI/MCP equality, CSV-only write rejection and no inspection-on-send dispatch.
The isolated browser verifies real API/worker execution for JSON/JSONL/XLSX, recorded
bar/heatmap selection, advisory assessment, PDF figures and historical/terminal recovery.
Fixture model replies do not prove actual-model format selection quality.

Actual installed qwen3.5:9b (reasoning_effort=none) acceptance exposed omissions and
historical-source/field carryover. The generic source/selector/field bindings above
addressed those findings without dataset-specific rules. Final XLSX/Data/x-by-region
and JSON Lines/x-by-region proposals passed in one call each (~60 and ~62 seconds),
with correct original sources/fields and independently checked mean 1.5 across four
synthetic rows. The model's free prose still referenced historical fields/formats;
the validated confirmation added afterward is independently unit-tested. These two
cases do not establish general model reliability or good scientific interpretation.
The proposals were explicitly evaluated by read-only analysis, not workflow-dispatched.
Reproduce with `.venv/bin/python scripts/statistical_planner_evaluation.py --formats-only`.
Earlier failures are retained as limitations/evidence, not counted as successful runs.

Final verification: `make test` **2,204 passed**, with 13 existing spatial warnings.
Focused selector/field/receipt checks and `make interface-validate` passed; the latter
retains its existing bundle-size advisory. The complete isolated browser journey passed
with zero page errors, including three new-format executions, interactive means and
heatmap values, PDF figures, assessment/history and existing terminal continuity.
Visual screenshots confirmed that generic result SVG CSS no longer recolors these
figures' backgrounds and data cells. Final report field-cap captions were typechecked/
built afterward; full numerical tables remain unchanged. No user manual acceptance,
live database changes, Docker rebuild or Git/publication action is claimed.

After this slice: Parquet is the next table candidate for larger columnar data, with
explicit pyarrow/schema/row-group budgets. TXT/Markdown, PDF text and DOCX belong to
the document extraction/frequency/word-cloud path (T11). ODS/Feather are lower-priority
table candidates. Ordinary images and point clouds remain T12. None is delivered by
listing it here. Export formats/transform compatibility require their own authorized
write contracts; new readable suffixes do not grant those capabilities.
