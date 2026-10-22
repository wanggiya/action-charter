# Checkpoint 28.3 — vector-first spatial exploration

Implemented 2026-10-21 as an extension of existing Outcome tabs. This records
bounded working functionality, not product parity, massive-data support or
completion of the capability/learning/private-knowledge pre-demo gates.

## Structure and authority

    completed spatial inspection + chat/run/plan identity + source hash
        → explicit shared workflow-runs spatial_view read
        → bounded worker verifies a private snapshot
        → vector layer sample / raster PNG / exact source-pixel values
        → existing Outcome Map / Table / Chart

No new agent, container, MCP server or plotting dependency. The same service is
available through interface and `workflow-runs --request-file ... --project-root ...`.
Requests cannot choose source paths, expressions, SQL or code. Source and digest
come from the recorded completed inspector, and exact chat/plan/step checks
precede the read. This read does not dispatch workflow operations, approve writes,
create output datasets or change execution authority.

Inspection-on-send results already bind their spatial source manifests. New
ordinary read-only Execute inspections also retain such bindings when the source
fits the existing closed snapshot contract. Unsupported normal-Execute inputs
keep their original inspector behavior and saved metadata without claiming a
verified-view binding. Older results without a binding keep their saved snapshots;
a new inspection is required for explicit verified exploration.

The worker reuses the Linux CPU/address-space/wall/file limits and no-follow
source reader. See [spatial source restrictions](INSPECTION_ON_SEND_EXPANSION.md).
One spatial-view worker at a time per API process prevents parallel display reads
from multiplying memory pressure; additional requests get an explicit busy error,
not an automatic retry. Input snapshots are private temporary copies, cleaned up
after reading. This is bounded trusted-parser execution, not a general OS sandbox.

## Vector first

- Existing saved WGS84 snapshots remain available without source reads.
- **Load verified vector** verifies the recorded source package and reads the
  explicitly selected layer. Layer changes alone do not read the file.
- Vector sources with a declared CRS can be reprojected to EPSG:4326 for display.
  Source CRS, display CRS and reprojection status are shown; source data is unchanged.
  Missing/unsupported CRS or failed transformation does not become invented geometry.
- Up to eight source layers, 10,000 features per selected layer, 100 fields/layer
  under the snapshot byte limits. Display is a sample: first 256 features, at most
  8,192 vertices, 256 KB geometry, 12 attributes and 160 characters/value.
- Points, multipoints, lines, polygons and holes retain the existing SVG geometry
  renderer. Invalid/oversized geometries are omitted, never silently simplified.
- Hide/show, pointer-anchored wheel zoom, drag pan, fit extent, fit selected feature
  and clear selection. Attributes render as text, not HTML.
- Selected features link to the displayed geometry attribute Table; Chart can use
  the same sampled attributes. Its first-20-row/sample limits remain explicit.
  No full-dataset chart totals are implied by a map sample.

The longitude/latitude diagram is not a distance-accurate projected GIS map. There
is no basemap, tile loading, multi-layer overlay, editing or spatial filtering.
The layer selector displays one source layer at a time.

## Raster image and data viewing

**Load verified raster** produces an RGBA PNG, at most 256 × 256 pixels, preserving
source aspect ratio. It uses nearest-neighbor resampling; it is a preview, not a
replacement file or a full-resolution tiled viewer.

- Grayscale, continuous cyan-to-orange ramp, RGB band combinations and explicit
  categorical colors. Categorical mode allows at most 32 classes in the sample;
  it does not infer that numeric measurements are categories.
- Selected bands, preview min/max or 2–98 percentile stretch, local display opacity,
  pan/zoom and fit. Band/render changes require Apply; opacity/navigation do not
  trigger reads. NoData/non-finite values are transparent.
- Ranges and categorical legends describe preview pixels only. No complete raster
  statistics, histogram, analytical raster processing or auto-inferred scientific
  units are claimed. NoData in any selected RGB band makes that preview pixel transparent.
- Clicking the displayed image maps to a source row/column and explicitly reads
  the original pixel, returning selected-band values or NoData and the source CRS
  pixel-center coordinates. The source pixel read is distinct from resampled
  preview values. It is hash-verified again.
- Source CRS, bounds, affine transform, dimensions and bands are inspectable.
  The image follows the source pixel grid, including rotated transforms; it is
  not reprojected or overlaid on the vector longitude/latitude view.

## Panel layout

Planner, graph and Outcome/review now occupy distinct desktop grid columns when
open together. This fixes the graph/saved-plan selector covering the chat selector.
Resize limits account for the other visible dock. Expanded Results hides the other
panes; at narrower widths the active result takes priority and closing it restores
the conversation/graph. This changes presentation, not saved workflow scope.

## Persistence and failure behavior

Loaded views and selection survive Table/Map/Chart switches while that result
workspace remains mounted; switching tabs does not read or execute again. Closing
or refreshing the workspace restores durable inspection evidence, not a persisted
raster image cache. A fresh explicit load is needed for its image/larger vector
sample. Do not label earlier ephemeral previews as freshly verified after restore.

Changed, missing or unsafe inputs reject a new display read and clear the current
verified display. The saved inspection metadata/geometry remains. View failures
are read errors, not failed workflow execution; they neither rerun operations nor
consume/reuse write approval. Leaving a result ignores late UI responses; the
bounded worker can finish its read but has no workflow execution authority.
Planner can open the current run's Map view for recorded vector/raster results;
this does not automatically load additional pixels/layers or execute processing.
Numeric/domain explanations beyond backend-computed evidence remain unfinished.

## Exact frontend validation

1. Restart the existing launcher and refresh `http://127.0.0.1:5173`. Keep writes
   OFF. Turn Planner gear → **Inspect on send** ON.
2. New chat: `Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.`
   In Outcome → Map, click **Load verified vector**. Pan/zoom, select a feature,
   use Fit selected feature, then Table. The corresponding row/attributes should
   remain selected. Return to Map: no new read or execution.
3. To check boundaries, copy the invented `examples/visualization/boundaries.geojson`
   into `data/input` under a fresh name, then inspect that name in a new chat.
   Check polygon holes, line/point visibility, Hide/Show and sample labels. A
   closed multi-layer GeoPackage additionally exercises layer selection and Apply.
4. New chat: `Inspect sample_dem.tif. Return dimensions, bands, bounds and CRS. No writes.`
   Outcome → Map → **Load verified raster**. Try continuous color, select a band,
   Apply, adjust opacity, pan/zoom and fit. For a real multiband source, choose RGB
   and its Red/Green/Blue bands. Click a pixel: source row/column, coordinates and
   exact values should appear. NoData is transparent, not displayed as zero.
5. Navigate Overview → Map. The loaded preview stays without a read. Close or
   refresh: recorded metadata restores; load the preview explicitly again.
6. For a temporary copied source only, change it after inspection and request a
   new load: expect a read error and cleared verified image, not stale fresh data.
   Do not mutate live data for acceptance. Neither view needs Authorize/Allow writes.

## Verification and remaining gates

`tests/test_spatial_views.py` uses known projected coordinates, multi-layer
GeoPackages, RGB values, NoData, dimension limits, changed sources, scope mismatch,
legacy missing bindings, concurrency and CLI parity. The isolated browser script
`scripts/checkpoint28_spatial_views_browser_check.mjs` uses the actual backend and
temporary files; only model completion is replaced. Existing results and submit
journeys provide regression coverage. Installed-model inspection evidence remains
in the inspection expansion guide; it is not an actual-model visualization study.

`scripts/checkpoint28_spatial_view_evaluation.py` measures sequential synthetic
100/1,000/10,000-point sources and 256/1,024/2,048-square raster sources. It records
source/response size, end-to-end display time and Linux worker peak RSS. It does
not include model inference or whole-platform memory and establishes no general
large-data or competitor comparison. Exact results are reported after execution.

Remaining: broader typed Planner layer/render controls, evidence-grounded domain
explanations, full-resolution/tiled raster and richer GIS layering/filtering.
Learning/private-memory acceptance remains separate; no RL or cross-chat sharing
is added by visualization. Packaging and representative demo follow the roadmap gates.

### Measured resource profile

One sequential synthetic profile after the 256-feature display expansion:

| Source | Display | Wall seconds | Worker peak RSS (KiB) |
| --- | --- | --- | --- |
| 100 points | 100 features | 0.4307 | 205020 |
| 1,000 points | 256 features | 0.4778 | 206044 |
| 10,000 points | 256 features | 0.6856 | 210652 |
| 256 × 256 raster | 256 × 256 | 0.4000 | 221584 |
| 1,024 × 1,024 raster | 256 × 256 | 0.3561 | 222608 |
| 2,048 × 2,048 raster | 256 × 256 | 0.3504 | 225604 |

Report: `/tmp/actioncharter-spatial-view-measurements.json`. Vector response sizes
were about 14–35 KB and raster responses about 2.6–3.7 KB for these compressible
fixtures. Different geometry complexity, imagery and machine load can cost more.
This is not a benchmark of arbitrary datasets or a reason to remove resource limits.

Browser acceptance: six new spatial groups and 17 existing Results groups passed,
including the distinct-column regression at 1,600 and 1,100 CSS pixels. No browser
page errors or live-service calls occurred; model replies were fixture-controlled.

### Final regression verification

- `make test`: **1,976 passed**, 161.96 seconds. Five expected Rasterio warnings
  concern PNG previews/one unreferenced synthetic fixture, not failed checks.
- `make interface-validate`: typecheck and production build passed. Existing
  Vite large-chunk advisory remains; no new dependency was installed.
- Spatial browser: **six groups passed**, including distinct panel columns.
- Existing Results browser: **17 groups passed**.
- Inspection submission browser: **eight groups passed**.
- `git diff --check`, context-file size and historical checkpoint preservation
  checks passed. No Git staging/commit/push, live-service mutation or release.

Earlier intermediate regressions were resolved before these final runs: an old
missing-map message assertion was preserved, worker fixed-error replies are now
propagated as read errors, and the combined Planner/Outcome grid collision has a
browser non-overlap regression. No failing check was removed to claim completion.

## Conversational views, recorded explanations and same-chat follow-up

A real saved submission exposed the source bug: the latest TIFF request produced
`inspect_raster` with the previous GeoJSON path. Execution correctly refused it,
but skill-only scope checks had allowed that proposal to be saved. Explicit
single-file inspection now binds the latest normalized filename in the decoder
schema and checks it again before storage. A wrong historical path receives one
bounded correction; repeated mismatch preserves the previous validated workflow
and performs no new execution. Existing historical records are not rewritten.
Browser acceptance covers GeoJSON → TIFF → CSV in one chat, including automatic
Outcome handoff and preservation of the conversation identity.

Planner `result_view` now optionally includes typed spatial settings: an existing
vector layer or existing raster bands, render and stretch. Scope, inspector kind,
layer and bands are validated against recorded metadata. The user request triggers
one bounded verified display read, not processing execution. Tab changes do not
repeat that read, and unsupported layers/bands are rejected. Exact pixel requests
remain in the viewer, not model-selected arbitrary coordinates.

Examples after the corresponding completed inspection:

- `Show boundaries layer on the map.` (requires that actual layer name.)
- `Display band 1 as a color ramp.`
- `Explain the current result dimensions and band count.`
- For CSV: `Explain the current result row count.`

Explanations select keys from a bounded projection of saved inspection facts.
Backend formatting supplies the actual numbers and scope; the model's free-form
explanation text is not promoted to verified evidence. Available facts include
recorded counts, dimensions, bands, CRS, bounds, NoData encodings, saved geometry
sample counts and bounded deterministic validation status/check names when present.
An encoding such as -9999 is not a missing-pixel count. Explanations do not reread
files, compute new statistics, claim freshness or infer domain meanings/units.
Display acknowledgments are likewise backend-formatted and do not invent totals.

Typed display proposals and explanation selections use the existing result-view
contract, current-chat recorded run and shared view services; no new agent or
memory sharing. These are narrow grounded factual explanations, not unrestricted
scientific interpretation, causal analysis or the checkpoint-29 knowledge layer.

### Recorded-fact fast path and small-model schema refinement

Exact factual requests such as `Explain the current result row count.` or
`Explain the current result dimensions and band count.` now use a closed
recorded-evidence route: zero model calls, zero source reads, the same scope
validation and conversation storage. The UI marks the reply as recorded evidence;
its context receipt reports zero messages/prompt bytes sent to a model. Generic
recorded-result summaries also use this route when their facts are available.
Other questions still use Planner and must not be interpreted as established
domain knowledge. Fact selections and display settings remain non-authoritative.

An installed-model diagnostic originally put `band_1` in the vector `layer`
field and repeated it during correction. Raster-only view schemas now omit vector
layer/pixel fields and require integer `bands` plus `render`. A focused local-model
raster case passed in one call after this refinement. This is a narrow measured
improvement, not general model reliability or learning/RL.

### Installed-model follow-up evidence

The final temporary `qwen3:4b-instruct` sequence passed: vector inspection →
raster inspection in the same chat → typed color-ramp display → recorded dimensions
and band-count explanation. Four model calls covered the first three requests;
the raster proposal needed one correction for an unsupported reuse citation.
The factual answer selected width/height/band_count with **zero model calls**.
The whole sequence took 97.623 seconds on this run, created exactly two inspection
runs, reused the first run on duplicate submission, and made no dataset writes or
approvals. This establishes one bounded acceptance case, not broad reliability.

Reports: `/tmp/actioncharter-same-chat-acceptance.json` (passed),
`/tmp/actioncharter-raster-view-fixed.json` (one-call raster display, 14.196 model
seconds). Failed intermediate reports are preserved at
`/tmp/actioncharter-same-chat-acceptance-initial.json`,
`/tmp/actioncharter-raster-view-diagnostic.json`, and
`/tmp/actioncharter-recorded-explanation.json`. The last records why simple factual
questions no longer depend on model-generated prose: the model supplied an
unsupported elevation interpretation and then asked for confirmation of already
recorded metadata. Fixed factual formatting and no-inference routing prevent
those statements from becoming verified answers for the supported exact questions.

### Final same-chat/dialogue regression result

`make test`: **1,983 passed** in 167.73 seconds (five expected Rasterio fixture/PNG
georeference warnings). Frontend typecheck/build passed with the existing bundle
size advisory. Browser acceptance: **nine** inspection-submission groups including
same-chat switching, **eight** spatial groups including conversational controls
and factual answers, and **six** complete-CSV exploration groups. All used the
shared backend, isolated browser profiles and temporary data, with no live database
changes. The final installed-model sequence and earlier diagnostics are recorded
above. Git actions/publication were not performed.

For operator regression, keep one chat open and send, separately:

1. `Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.`
2. `Inspect sample_dem.tif. Return dimensions, bands, bounds and CRS. No writes.`
3. `Display band 1 as a color ramp.`
4. `Explain the current result dimensions and band count.`
5. `Inspect sample_orders.csv. Return row count and column names. No writes.`

The active workflow/Outcome follows the latest inspection. The display request
loads verified pixels without a new processing run; the exact factual question
shows a recorded-evidence receipt without a model call/source read. Earlier
messages and execution records remain preserved; this is not automatic multi-step
inspection or cross-chat memory sharing.


### Final CSV transition and loaded-version regression

The reported final-step error was a deterministic table-format rejection. The
saved chat retained its TIFF inspector; failed generation did not replace it.
The exact rejected model response is not stored, so its path/operation pairing
cannot be established retrospectively. The current source-binding implementation
rejects a historical TIFF path before accepting a new explicit CSV inspection.
A regression deliberately supplies that wrong path and verifies one correction,
then the correct CSV outcome. Repeated rejection continues to preserve prior state.

The earlier actual-model sequence ended after raster display/explanation; only
the fixture browser test covered the return to CSV. The actual-model script now
also sends the final CSV request, verifies its source and three-row metadata,
and checks exactly three processing runs with no dataset outputs or approvals.
`/tmp/actioncharter-same-chat-csv-acceptance.json`: **passed**, qwen3:4b-instruct,
six model calls, 184.0 seconds, temporary synthetic data. Two calls were bounded
corrections of unsupported reuse claims; the factual explanation used no model.
This run did not reproduce the reported format rejection and is not a broad
reliability or performance claim.

The loaded Planner contract is now `inspection-source-v2`, rather than reusing
`capability-pilot-v1` for both old and corrected implementations. Updated clients
reject an old API before posting a turn/submission and give launcher restart
instructions. Python API changes require stopping/restarting the launcher;
refreshing Vite alone cannot reload that process. Format errors now identify the
step, operation, expected extensions and received extension without exposing
file contents. Existing source/path checks and authorization remain unchanged.

Retest: stop the existing launcher with Ctrl+C, run
`bash scripts/start_actioncharter.sh`, confirm startup reports
`Planner contract revision: inspection-source-v2`, refresh the browser, reopen
the same chat and send step 5 above. With Inspect on send ON, expect one completed
CSV inspector, source `data/input/sample_orders.csv`, and CSV row/column metadata;
no Authorize action or write-enablement flag is needed. Earlier raster runs and
messages should remain available. If rejection remains, capture the exact sent
message and the new operation-specific error. Do not edit saved plan records.


Verification for this follow-up: `make test` **1,985 passed** in 177.07 seconds
(five expected Rasterio georeference warnings); `make interface-validate` passed
with the existing bundle-size advisory. All **ten** inspection-submission browser
groups passed, including an injected old-contract response that blocks before a
Planner turn/submission POST. No live database changes, Git mutations, dependency
installations or shared browser-cache changes were performed.


### Saved inspection history visibility — 2026-10-22

The workflow-run management link was below the older current-plan inspection
inventory. New chat-submitted inspections use durable workflow-run records, so
that older inventory alone cannot show the complete relevant history. Execution
History now places those saved workflow runs first, labeled with source filenames,
operation names, timestamps and run IDs. Loading/listing and opening records use
the existing read-only workflow-runs API. Its compact inventory now includes
up to 20 normalized local source paths per run, while full arguments and outcomes
remain omitted until an explicit read. Cancellation/recovery remain available
at the top of this section. Existing legacy inventories remain accessible below.

To reopen a TIFF: click **Execution History**, find **sample_dem.tif** under
**Saved workflow runs**, then click its **View outcome** button. The existing
Outcome tabs show the historical record. The graph and active CSV plan remain
unchanged. Clicking the top **Outcome** navigation button returns to the current
workflow result. Viewing saved metadata does not read the source again; explicitly
loading a spatial view still performs the usual hash-verified bounded source read.
No model call or execution is triggered by opening a saved result.


Verification: `make test` **1,986 passed** in 176.99 seconds (five expected
Rasterio fixture georeference warnings); `make interface-validate` passed with
the existing bundle-size advisory. **Twelve** isolated inspection/history browser
groups passed. The new journey reopens a same-chat TIFF after CSV, checks its
source/run identity, returns to the current CSV outcome and opens run management,
with no new processing run or Planner turn. Inventory tests confirm source-label
bounds and continued omission of full arguments/results. Fixtures only; no live
services, browser-cache changes, dependency installations or Git actions.
