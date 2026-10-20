# Checkpoint 27.4b — bounded recorded charts and point maps

Implemented slice, 2026-10-19. The later [27.4c Results workspace](CHECKPOINT27_RESULTS_WORKSPACE.md) adds direct View output, result tabs, resizing/expansion, linked selection and explicit verified CSV reads; the snapshot limits below remain in force. Extends [recorded result cards](CHECKPOINT27_RECORDED_RESULTS.md)
without adding a model, package dependency, external tile service or live database
query. Broader map/chart formats and laptop/model evaluation remain unfinished.

## Delivered behavior

Select a completed operation in the current workflow, or choose its Operation result and Map/Chart tab in Outcome. The optional Chart recorded data / Map recorded geometry
disclosure identifies the recorded run, step and source/output path. Drafts and
unexecuted operations have no visualization. Existing chat/plan/run matching
continues to govern which result is shown.

CSV previews support per-row bars and numeric scatter plots. Choose category/X
and value/Y columns; no grouping, aggregation or full-file totals are invented.
The chart uses at most the first 20 stored preview rows and 32 columns. The stored
preview may already be shorter due to backend row/byte limits. It labels plotted,
omitted, preview and recorded row counts. Missing values are omitted; mixed text,
non-finite or out-of-range numeric columns are unavailable. Leading-zero strings
remain identifiers. Numeric chart display is approximate; tables retain the
stored strings. HTML-looking labels render as literal text.

Vector inspection now captures a small point snapshot while it already has the
first inspected layer in memory. The shared service and CLI return the same
snapshot. No second file read is added for visualization. Supported maps require
declared EPSG:4326 or OGC:CRS84 and valid Point geometry. At most the first 32
features are examined; non-points, empty geometry and invalid/out-of-range
coordinates are omitted and counted. Additional layers are not displayed.

The point map is a local longitude/latitude diagram with north indicated. It is
not a distance-preserving projection or a basemap. No tile downloads, reprojection,
attribute upload or live target inspection occurs. Its digest identifies only the
saved geometry snapshot, not the entire source file. Source/output paths and run
identity remain visible. Opening/reloading a view uses the saved snapshot even if
the current file changes; it does not establish current file freshness.

Older vector runs without saved geometry show an unavailable explanation; they
are never silently enriched from current files. A newly executed inspection can
capture geometry. Polygon/line/multipoint maps, arbitrary raster/database maps,
multi-layer selection, interactive map navigation, full-file charts and visualization
exports remain outside this slice. Oversized overall run projections may omit
the preview under the existing 6 KB per-step storage budget.

## Manual acceptance using synthetic fixtures

1. Restart the existing launcher once to load the updated Python inspection
   service: `bash scripts/start_actioncharter.sh`. Refresh the browser. No change
   to model configuration or automatic authority is needed.
2. Open a chat with a successfully executed CSV workflow. Select its inspection,
   aggregation or calculation operation. Expand Chart recorded data in the
   information panel. Existing saved table previews work without reexecution.
3. For the existing sample_orders calculation, select Value = doubled and
   Category = region. Expect five plotted values: 20, 40, 80, 10, 60, with one
   missing value omitted from the six-row snapshot. Switch to Scatter, X axis =
   amount and Y axis = doubled; expect five points. These are per-row values,
   not regional totals. Outcome → choose the operation → Chart exposes the same view.
4. In a new chat request: `Inspect sample_points.geojson. Return feature count,
   fields and CRS. No writes.` Confirm the actual proposal is inspection only.
   Execute this read-only inspection; enabling writes/Authorize is unnecessary.
5. Select Inspect vector dataset → Map recorded geometry. Expect two points near
   Boston, a WGS84 CRS, 2 examined / 2 total features and no skipped features.
   Expand Geometry snapshot identity if needed. A historical run without a
   snapshot correctly cannot show the points.
6. Reload/return to the same chat. The matching snapshot restores without model
   calls or execution. A different chat, new proposal or draft must not inherit
   it. Unsupported CRS/geometry must show a limitation rather than guessed data.

Do not use private/live data for this acceptance. The operator's capability,
learning and private-memory pre-demo gates remain unchanged.

## Automated acceptance

Run `make test`, `make interface-validate` and
`corepack pnpm@10.17.1 --dir interface browser:test:27-visualization`.
Backend tests check known coordinates, bounded sampling, skipped/unsupported
geometry/CRS, digest and snapshot persistence after source deletion. Browser
checks use real temporary CSV/vector execution with fixture model replies,
checking plotted values, omissions, refresh and absence of visualization-induced
model/execution calls. Boundary response fixtures exercise row caps and literal
HTML-looking content. Browser data/profiles remain isolated from normal caches.

Verification recorded: 1,792 backend tests, frontend typecheck/build, eight
visualization browser cases and 12 recorded-calculation regression cases passed.
The eight cases include an actual unsupported projected-CRS inspection and a
legacy read-response fixture without saved geometry. Screenshot inspection checked
narrow-panel control stacking and readable plot labels. Live-model latency/quality
and live database/service acceptance are not established.
