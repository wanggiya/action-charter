# Statistics pages, report downloads and covariance matrices

Implemented 2026-10-28 as connected T05/T09 slices. Existing uncommitted work is
preserved; no staging, Git publication or live database/service changes.

## Interface and report behavior

Outcome → Statistics uses page-style Summary, Descriptive, Matrices, Regression and
Report tabs, with keyboard navigation, larger body/table text and the existing result
tab/material styling. It fills the existing Outcome workspace; no additional popup.
Missing-value counts and regression diagnostics are readable tables/facts rather
than raw JSON. Settings appearance selectors now have explicit accessible names.

Select **Report format → Markdown (.md) / PDF (.pdf)** and click **Download report**.
Both formats consume the same recorded Markdown report. PDF is a direct local file
download, not a print dialog, upload, agent call or new backend execution. It includes
embedded fonts, repeated table headers and page numbering. Wide tables retain the
first label column and split the remaining columns into continuation tables; no
statistical rows/columns are sampled or omitted. Values retain report precision.
PDF code/fonts load lazily only when PDF is chosen. Download preparation errors are
shown without clearing the recorded result or changing the workflow.

New numerical results produce structured report tables for source/hash and scope,
descriptive values/percentiles, grouped measures, missing/invalid counts, labeled
matrices, model facts, coefficients/inference, diagnostics, runtime versions and
limitations. Applied exact-text filters are recorded in the report. Markdown remains
the shared canonical report for terminal, CLI/MCP results, page rendering and PDF.
The renderer supports only the report's text/headings/lists/tables; it never executes
HTML, fetches embedded URLs or interprets source text as instructions.

Older outcomes still open with the new page controls and both download choices.
Their original report text is retained; new structured report contents require a new
read-only execution. Historical numerical evidence is not silently rewritten. Downloads
are browser actions, distinct from writing project datasets or reports through workflow
operations; those backend writes retain their normal exact authorization requirements.

## Shared statistical extension

`inspect_csv.analysis.statistics.methods` now also accepts **covariance** with two or
more explicit numeric columns and `ddof` 0/1. The labeled matrix uses all selected
complete matching rows and the same explicit missingness policy as the other methods.
Sample covariance uses n − 1; population covariance uses n. Too few rows for the
denominator reject. A single complete row with population ddof 0 returns a correctly
shaped zero matrix, without claiming useful inferential evidence.

The existing operation registry, Planner argument schema/coverage, MCP table_statistics
and profile_table tools, CLI table-statistics and terminal report all reuse this service.
No new parallel numerical executor is introduced. Named covariance-matrix requests are
distinct from an OLS covariance-estimator choice; cluster covariance alone must never
add a descriptive/matrix method. Decoder constraints omit irrelevant regression fields
for matrix-only proposals. Data contracts and deterministic validation remain authoritative.

## Dependencies and limits

The frontend declares pdfmake 0.2.20 and its TypeScript definitions in package/lock files.
It follows the library's [client-side local-font configuration](https://pdfmake.github.io/docs/0.1/getting-started/client-side/).
No CDN/font fetch occurs at export time. For a fresh checkout, install declared frontend
dependencies with `corepack pnpm@10.17.1 --dir interface install --frozen-lockfile`.
The launcher itself does not install packages; PDF needs no separate browser assets.
Development-only pypdf is declared for independent acceptance inspection of produced
PDFs; it is not required for end-user PDF generation.

The current PDF includes text/tables, not rendered chart figures. It uses bundled
Roboto; universal script coverage/custom font selection is not delivered. Existing
statistical/file/worker/output budgets remain. Browser export is not a general PDF
or document-ingestion capability and does not deliver T11 word clouds/PDF extraction.
Broad causal analysis, categorical modeling and generated analytical Python remain open.

## Manual acceptance

1. Restart the usual launcher after backend/dependency changes, then refresh the UI.
   Open a successful saved run → Outcome → Statistics. Check larger text, page tabs,
   diagnostics and Report. Switch Settings between Outline and Solid fill; active
   tabs, selector and report should match the existing interface, without a white
   default selector or a cyan card around the entire report.
2. Choose Markdown and download; choose PDF and download. Open both files. Confirm
   the same source hash, analyzed/excluded counts, coefficients/P-values and limitations.
   PDF headers should repeat on subsequent pages. No new workflow run should appear.
3. Refresh and reopen that run; its facts and report must remain unchanged.
4. To test the new matrix on the real sample, send in a new chat:

   ```text
   Inspect test/diabetic_sample_5000.csv. Compute descriptive statistics and a
   covariance matrix for time_in_hospital, num_medications and num_lab_procedures.
   Use sample variance/covariance with ddof 1. No writes.
   ```

   Review `analysis.statistics` for describe/covariance and the three numeric fields,
   then Execute if it has not already run. Open Statistics → Matrices and both reports.
   Expect 5,000 matching rows for the current complete sample. The covariance diagonal
   must equal each field's sample variance in Descriptive. Values are associations,
   not evidence of causality. Read-only execution needs no write authorization.

## Remaining ordered work

Finish T03/T04 contract/catalog consolidation and T06 qualified generated-method reuse
in tested slices; do not claim the ownership audit is complete. T09 still needs broader
group comparisons and applicable inference; T10 categorical/predictive/causal work is
not delivered by covariance. T08 common table adapters and T11 document frequencies/
word clouds remain open. Update the consolidated TODO with actual verification evidence.

## Verification record — 2026-10-28

- Full `make test` run: 2,174 passed, 13 existing spatial warnings. Final focused
  statistics/scope suite: 25 passed. The earlier report-escaping test had an incorrect
  header assertion; corrected and superseded by this full passing run.
- `make interface-validate` passed; main/PDF/font chunks retain build size advisories.
  PDF/font bundles are separate lazy chunks, not initial-page imports.
- Isolated browser acceptance passed page navigation, readable text, outline/solid
  styles, styled selector, Markdown/PDF download and saved-run restoration without replay.
  Independent pypdf extraction confirmed a four-page report with measured values and
  limitations; wide nine-column matrix export retained every field and the final value.
  Temporary profile/assets only; no real browser-cache access or report upload.
- The full 5,000-row private sample covariance matched independent pandas covariance;
  its diagonal matched each sample variance. Read-only source, no database/services
  or dataset output writes. No new installed-model quality claim for covariance planning.
