> Follow-up: [vector-first spatial views](CHECKPOINT28_3_SPATIAL_VIEWS.md) now
> implement explicit verified layers/reprojection and bounded raster image/pixel reads.
> The initial CSV-focused delivery below is retained; broader gates remain open.

# Checkpoint 28.3 — typed exploration and Planner result views

Implemented first coherent slice, 2026-10-21. Builds on existing Results tabs,
ten chart types, recorded geometry, hash-verified preview/aggregation and durable
run scope. This is not full checkpoint completion, large-data support, a new
learning system or a claim of Tableau/Codex performance parity.

## Delivered structure

    recorded step + exact chat/run/plan identity
        → shared verified artifact reader
        → typed filter/sort/page + column profiles + optional aggregation
        → Results Table / Chart

    recorded geometry snapshot → existing Map + displayed extent/type summary

    latest user display request + recorded field metadata
        → Planner result_view specification
        → deterministic scope/field validation
        → same Results/query services, without a replacement workflow

No new agent, model training, container, MCP server, plotting dependency or
execution engine is added. Existing workflow/authorization formats remain valid.
Planner's manifest describes the result-view role; backend services own computed
values. New models live in `interface_api/exploration_contracts.py`, queries in
`result_exploration.py`; old preview and new exploration share `recorded_frame`.

## Tables, profiles and identity

**Explore complete CSV** is the primary read action. The older Load verified CSV
preview remains under **Preview options** to avoid two competing primary controls.
Explore complete CSV explicitly reads the recorded artifact. The new
`workflow-runs` action `explore` requires matching chat, run, plan and completed
step. Path/hash are derived from the recorded outcome; clients cannot supply
arbitrary paths. Changed, missing or unsafe files reject. Old saved snapshots
remain available. No operation dispatch, approval, export or source mutation
occurs. Normal opening/tab switching uses snapshots unless it is applying a
fresh explicit Planner view request.

Queries support up to five AND-combined typed predicates, one stable sort,
selected columns and bounded offset/limit. Operators: eq/ne/gt/ge/lt/le, literal
case-sensitive contains, is_missing/not_missing. Ordinary comparisons exclude
missing cells. Only empty CSV fields are missing; literal NA/NULL stay strings.
Text sorting is lexical; numeric sorting is explicit, rejects mixed/non-finite
values and uses the supported ±1e15 display range. Missing values sort last.
Original identifiers such as `001` are not rewritten.

Filtering, sorting and aggregation use the complete bounded artifact, including
rows beyond the old preview. Page row IDs retain original zero-based source
positions, so table/chart selections cannot silently switch records after sort.
Byte-limited pages return the actual next offset, avoiding skipped rows. Limits
remain 8 MiB/10,000 rows/100 source columns and bounded pandas memory; returned
pages have 25/50/100 requested rows, at most 32 columns, 160 characters/cell and
128 KB row JSON. This rereads the bounded file for each request; it is not a
streaming, cached, distributed or arbitrarily large query engine.

Column profiles cover the complete verified source before filtering: storage is
string, observed numeric compatibility/text/empty, missing count, distinct count
and bounded numeric min/max. Numeric-looking identifiers are not inferred to be
measures or units. The interface shows the key profile fields in an expandable
panel. UI controls edit one filter; Planner/CLI may supply up to five. Editing
that first filter explicitly replaces a multi-filter list, with a notice.

## Charts and maps

Existing manual chart controls retain all ten types. When an explored table is
active, **Analyze verified CSV** computes count/sum/mean/min/max over all matching
rows, not just the current page. The result identifies original and matching row
counts and complete-filtered scope. Null numeric values are excluded; all-null
numeric groups remain null; missing categories form a separate group. Counts
count rows. The existing 100-group limit and finite/range checks apply. Views
without a complete analysis remain labelled as sampled rows. Grouped marks do
not pretend to identify individual source rows. Changing controls requires a
fresh analysis before a new full-summary claim is shown.

Map adds an expandable WGS84 displayed-geometry extent and geometry-type counts.
It reuses existing point/line/polygon-with-hole rendering and table selection.
Extent refers to the displayed snapshot, not an implied full dataset. This slice
does not filter a map using CSV filters, join unrelated table rows to geometry,
add basemaps, reproject data, render raster pixels or query a live database.

## Agent capability and bounds

Planner receives only current-chat/current-plan recorded result identity and
bounded field metadata, not dataset rows. It may return `result_view` with
plan=null. The coordinator validates known run/plan/step, supported view and
existing fields and preserves the workflow. Mixed view+workflow/capability/recipe
actions reject through the existing one-correction budget. A genuine missing
semantic-input question remains available. The frontend reads the matching run
and applies the specification through the same query services.

Clear show/plot/display requests for an existing table/chart/map use a focused
view schema instead of unrelated operation schemas. Addresses and field enums
are constrained to the recorded context. For a request without filter/sort/field
selection, query parameters are omitted from the model schema: grouping by a
field means all categories, not a request for a category value. Stale summaries
of the prior inspection do not satisfy a chart request. This is a bounded display
route, not a general proof of natural-language intent or analytical correctness.

Automatic grouped view proposals support bar/column/line/area/pie/donut with
count/sum/mean/min/max. Other manual chart types remain available but are not
claimed as typed agent proposals in this slice. Map proposals use existing
recorded geometry, not arbitrary file reads. Returned view advice is not execution
authority. Numeric explanations in later chat turns are not automatically
grounded in query values; broader explanation/tool-observation integration remains
future work rather than permitting invented totals.

View requests are consumed once. Closing/reopening, restoring a chat or reading
conversation history does not replay a query or workflow. A new explicit display
request can recheck the same source. Late responses cannot populate another
chat/result scope. Query results are transient UI state; opening Results later
returns to recorded snapshots. A file hash verifies identity at read time, not
permanent freshness.

## Interface acceptance with the supplied sample

Restart the existing launcher and refresh the browser to load this code. No write
flag is needed. Inspect `sample_orders.csv` in Planner; either the existing ON
CSV-inspection mode or the normal Execute path can produce the recorded result.

1. Outcome → Table → **Explore complete CSV**. Expect six source/matching rows.
   Expand Column profiles: amount has one missing value; region has one missing.
2. Expand **Filter and sort complete CSV**. Choose amount / ge / Number / 20;
   sort amount as Number descending. Apply: expect three rows with amounts
   40, 30, 20 and preserved IDs 004, 006, 002.
3. Chart: Category region, Value amount, Aggregation sum → **Analyze verified CSV**.
   Matching-row totals are south 40, Missing 30 and north 20; scope is three of
   six source rows, even if a smaller page is shown.
4. Return to Planner and send:

       Show total amount by region as a bar chart.

   Expect an unfiltered result view with north 35, south 40 and Missing 30.
   No filter was requested, so the earlier UI filter is not silently inherited.
   The saved workflow and execution-run count remain unchanged; writes stay OFF.
5. Close/reopen Outcome: no new workflow/query is started. Repeating the explicit
   chat request may reverify its artifact once. A real changed-source rejection
   is covered using temporary automated fixtures; do not alter your working data
   just to test this behavior.
6. Existing vector results → Map → **Displayed geometry extent and types**.
   Check displayed boundaries and attributes. Numbers describe the shown sample;
   this does not auto-enable vector inspection on send.

The existing CLI `workflow-runs --request-file FILE --project-root ROOT` accepts
`action: explore`, the same exact scope fields, optional `query`, and optional
`analysis`. Existing `preview` requests keep their behavior. No user-written SQL
or Python is evaluated. API health identifies `result_exploration_revision` as
`typed-views-v1`.

## Acceptance and remaining work

The delivery exercises full-artifact queries beyond 1,000 rows, byte-bound paging,
row identity, profile/missing-value semantics, filtered aggregation, invalid scope,
changed files, CLI parity and bounded Planner correction. Browser journeys use
actual backend services and temporary data with fixture model replies; installed
model acceptance is recorded separately below.

Remaining 28.3 work includes broader typed chart requests/explanations, richer
spatial/raster exploration, large-data resource measurements and an independently
validated scaling strategy. 28.2 format-independent inspection expansion and
learning acceptance remain open; 29 private knowledge and 30+ cross-chat gates
are unchanged. Deferred external-harness research stays deferred. No Git,
publication or live database action is implied.

### Recorded verification — 2026-10-21

- `make test`: **1,950 passed**. An earlier full run exposed a prompt-size
  regression; the instruction/context budget was fixed without loosening the
  existing threshold, and the final full suite passed.
- `make interface-validate`: typecheck and production build passed. The existing
  bundle-size advisory remains; no new runtime dependency was installed.
- Final result-exploration browser journey: six cases, including queries beyond
  the preview, complete filtered sums, Planner views, one-shot reopening/repeated
  requests and changed-file rejection. Existing Results regression: seventeen
  cases covering all chart types, geometry/table links, resizing and restoration.
  Both use real temporary backend data/storage, fixture model replies and an
  isolated browser profile; no live database/service call is made.
- Installed-model acceptance uses `qwen3:4b-instruct`, JSON schema, reasoning none,
  1,024 max output tokens. Final synthetic result-view request passed with one
  model call, 6,711 prompt bytes, 191 completion tokens, 12.774 seconds model time
  and 14.288 seconds including fixture setup/execution/query. Backend verified
  North=30 and South=5; workflow unchanged, zero extra workflow runs/approvals or
  dataset writes. Report: `/tmp/actioncharter-checkpoint28-result-view.json`.
  Reproduce through `scripts/checkpoint28_result_view_evaluation.py` with the
  project Python environment and an installed `--model`.

Initial local-model trials produced a stale inspection summary or an unnecessary
category question instead of a usable chart request. They remain in the local
`...result-view-initial.json`, `...result-view-missing-view.json` and
`...result-view-unrequested-filter.json` reports. Focused view context/schema,
recorded-address binding, latest-message emphasis, bounded missing-view correction
and omitting unrequested query parameters addressed this narrow case. The final
single pass is not a general reliability, speedup, learning or harness-comparison
claim. Group/field interpretation outside the supported contract can still fail.
