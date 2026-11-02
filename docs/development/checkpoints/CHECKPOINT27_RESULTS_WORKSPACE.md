# Checkpoint 27.4c — recorded Results workspace

Implemented slice, 2026-10-19. Builds on [27.4b visualizations](CHECKPOINT27_VISUALIZATION.md).
Uses familiar data-explorer patterns: one selected operation, separate result
tabs, a searchable table and an expandable visualization surface. This does not
establish Snowflake, Tableau or Databricks feature parity.

For the current chart/geometry/layout extension, see [27.4d](CHECKPOINT27_ANALYSIS_AND_LAYOUT.md). Earlier bounds below describe the initial 27.4c delivery.

## Interaction

Outcome opens Current outcome as a Results workspace. Completed operations in
the information panel offer **View output**: CSV results open Table and vector
inspection opens Map. The operation selector changes the recorded step while
retaining the chosen tab. Overview, Table, Map, Chart and Checks are visible;
only the selected view renders. Missing/unsupported views explain their boundary.
Proposals and drafts cannot inherit execution results or a View output action.

The views use connected page tabs rather than standalone buttons. The active tab
joins a single content surface with a view title and operation/status context;
the existing blue edge gradient remains. Left/Right arrows switch tabs, Home/End
select the first/last tab, and Tab moves into the active page. Table, chart and
map preferences remain intact when switching pages for the same operation.

The divider on Results' left edge resizes it with pointer drag or left/right
arrow keys. Width is saved separately from inspector width. It works at tablet/
laptop widths above 760 CSS pixels, including the previous 1,050-pixel failure
range. The divider remains outside the scrolling body. Expand results fills the
workspace; Restore graph beside results preserves graph state and position.
Narrow screens use full-width Results; Close outcome returns to the graph.

Table provides literal-text search, natural ascending/descending sorting, column
visibility, selected rows and 25-row paging over the loaded preview. Counts state
loaded versus recorded rows. Search/sort operate on loaded rows only, never on
an implied complete dataset. Identifiers retain their stored strings; missing
values remain distinct. Table/chart selection links by snapshot row index. Vector
Table lists saved point coordinates, not unrecorded feature attributes; selection
links to the point map. Table preferences, chart axes/type and map camera persist while switching tabs for the same operation. Switching operation resets selection, view preferences and loaded data; preferences are not durably saved across closing/reloading the workspace.

Map supports point selection/identification, wheel/button zoom, drag pan and Fit
extent. It remains the same offline WGS84 first-layer/32-feature snapshot contract:
no basemap, automatic projection, polygons/lines, raster data or database queries.
Chart retains per-row bar/scatter views of the first 20 loaded rows; a selected
table row outside those rows is explicitly reported. No full-file aggregation is
implied. Overview shows operation/dataflow and metadata; Checks separates recorded
deterministic validation from the existing run-level advisory Critic assessment.

## Explicit verified CSV reads

Opening Results and switching views use saved snapshots. **Load verified CSV**
explicitly reads the recorded CSV artifact only after matching run, plan, optional
conversation and completed step. The backend derives path/hash from that record;
the client cannot supply a file path. It rejects changed/missing files, unsafe
links, malformed identities and mismatched scope. Failures preserve the saved
snapshot. Loaded rows are transient UI state, not memory sent to the model.

Reads reuse the bounded tabular service: 8 MiB, 10,000 rows, 100 source columns and
64 MiB dataframe memory. The returned preview is further capped at 1,000 rows,
32 columns, 160 characters per cell and 128 KB of row JSON, with truncation flags.
CSV inspection preserves the recorded delimiter; it does not infer parsing from
the filename. Table search/paging remains limited to returned rows. Recheck CSV
artifact repeats a read/hash check; Use saved snapshot discards the larger preview.
Preview I/O occurs outside the execution-progress lock so it cannot hold up run
progress or cooperative cancellation. Scope changes ignore delayed UI responses.

The same typed API/CLI service uses POST `/api/v1/workflow/runs` or
`geoagent workflow-runs --project-root PATH --request-file request.json`:

```json
{
  "action": "preview",
  "run_id": "<exact recorded run ID>",
  "confirmed_plan_sha256": "<exact recorded plan digest>",
  "step_id": "step_2"
}
```

Placeholders must be replaced with actual recorded identities. An optional
conversation_id adds the same conversation check used by the interface. No write
availability, approval, execution, recovery, model request or registry change is
performed. Older synchronous inspection/export history can display saved snapshots
but is not silently promoted into this durable-run preview capability.

## Manual validation with synthetic fixtures

1. Restart the existing launcher once with `bash scripts/start_actioncharter.sh`
   to load the preview API, then refresh the browser. No dependency installation
   or model configuration change is required.
2. Restore a completed CSV workflow. Select its operation → View output. Confirm
   Table opens, row counts are explicit, search/sort/columns work, and selecting
   a row highlights its corresponding chart mark when it is within the chart sample.
3. Choose Load verified CSV. Confirm the hash-at-read badge and larger preview.
   This is available with Writes OFF and must not authorize/execute anything.
   Use saved snapshot returns to the original record. On larger synthetic fixtures,
   use Next/Previous page and check the loaded-row/truncation limits.
4. At a browser width around 1,000 CSS pixels, drag the left divider and try its
   arrow keys. Scroll the results body; the divider should remain reachable.
   Expand, then restore the graph. Its workflow and manual block positions remain.
5. Restore a newly executed sample_points.geojson inspection → View output.
   Map opens directly with two known points. Select a coordinate-table row and
   return to Map; select the other point and return to Table. Try zoom, pan and
   Fit extent. Old runs without geometry explain why no map is available.
6. Checks exposes independent validation and separate advisory Critic findings.
   A CSV's Map tab explains that it has no geometry. A new chat/draft must not
   inherit another workflow's results. Reopening snapshots must not trigger reads
   or execution; verified file reads occur only through the explicit action.

## Verification and remaining work

`make test`, `make interface-validate` and
`corepack pnpm@10.17.1 --dir interface browser:test:27-results`.
Tests use actual temporary CSV/vector execution and fixture model responses.
Coverage includes resizing/expansion, linked selections, changed-file refusal,
literal HTML-like data, bounds, CLI parity, original delimiters, unsafe links,
malformed records, scope mismatches and delayed responses after a chat change.
Browser profiles remain separate from normal browser caches. The page-tab follow-up
reruns the Results journey, including Left/Right and Home/End keyboard navigation,
and checks page headings and the single active tab focus target.

Full-data query/aggregation/filter pushdown, line/histogram charts, durable view
configurations, visualization export, broader geometry/CRS/layer support, raster
previews and live-model/laptop evaluation remain open. 27.4d now adds persistent collision-aware layout, return-lane edges and the
warning Allow writes toolbar control; arbitrary obstacle routing remains future work. Capability acquisition/learning/private-memory pre-demo gates are unchanged.

Recorded verification: 1,804 backend tests, frontend typecheck/build and 63 browser
cases passed: Results 10, visualization 8, calculations 12, CSV 6, retention 7,
Planner 6, installed adapters 5 and intercepted authorization/layout 9. Fixtures
and screenshots were isolated; these checks do not establish live-model quality
or live-service acceptance.
