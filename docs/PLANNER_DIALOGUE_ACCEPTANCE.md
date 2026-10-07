# Planner dialogue frontend acceptance

For the focused inspect-vector → PostGIS pass, follow [the frontend walkthrough](FRONTEND_VECTOR_POSTGIS_WALKTHROUGH.md).

Use the current source checkout for this iteration. No new snapshot is required. Automated tests exercise a fake model and temporary data; a browser/model acceptance pass is still required. Do not close checkpoint 23 or begin 24 until this pass and the separately reviewed PostGIS run succeed.

## Restart and inspect the interface

1. In the terminal running ActionCharter, press Ctrl+C. Keep the working model exports in that terminal. Restart with `bash scripts/start_actioncharter.sh`.
2. Open http://127.0.0.1:5173 and hard refresh. The API still uses 8765. Restarting the launcher is necessary for backend changes; refreshing alone updates only the browser.
3. Expect a conversation on the left, graph in the middle and compact timeline below. Add and Block tools are visible. Block tools expands Delete, Move, Connect, Disconnect and Parameters. Expand reveals the full timeline.
4. In Settings, check Outline and solid white/black text, including selected/running timeline stages. Outline text should be near-white; fills remain tinted and translucent. Zoom and legend start at the lower-left. Record browser, window size and any clipping/contrast defect.

## Inspection and conversation revisions (writes disabled)

Send:

> Inspect sample_points.geojson. Return feature count, fields and CRS. Do not write files or load anything into a database.

The graph should contain inspect_vector. It must not claim to have inspected anything until Execute. Send:

> Explain the inspection step without changing the workflow.

The same graph and approval state should remain. Then send:

> Add conversion of sample_points.geojson to data/output/dialogue_points.gpkg, after inspection. Keep the existing inspection.

Expect a validated second operation with a write gate. Do not authorize or execute this conversion in this pass. Send:

> Remove the conversion. Keep only the original inspection.

Expect one inspection again. An unsupported request such as “add arbitrary SQL to delete a database” should produce an explanation/clarification, never an executable arbitrary operation.

Switch to Execution History and back; the plan and chat should remain. While the model is responding, start a manual graph edit: a delayed answer must not overwrite it. Validate/save or discard that edit before sending another turn. Disconnect/connect edits must pass backend validation before authorization or execution. Drag nodes/wires in both graph orientations and note lag, jumps or incorrect endpoint tracking.

Click Execute on the inspection proposal. Review the exact file in the right panel and confirm execution there. No popup should cover the graph. Expect two features and EPSG:4326 in the inspection evidence. Check Outcome and Execution History against the same recorded attempt.

Refresh: the transcript should recover. Click Open conversation plan to restore its graph without a model call. Start New chat; the current graph remains available as context. Choose the earlier chat from the saved conversation selector and explicitly reopen its proposal.

For model failure, stop the model service or temporarily use an unavailable endpoint in a separate launcher session. Sending must preserve the current graph and composer text. Completed turns remain recoverable. Restart the model/launcher with the working settings, reload the conversation if its revision changed, and resend. Never record a model failure as a successful inspection.

## Separately reviewed PostGIS acceptance

This section requires explicit permission for the exact live database schema/table. Do not enable writes or execute a database plan during the inspection-only pass.

1. Choose a fresh table name in a configured allowed schema. Verify that it does not already exist; keep overwrite disabled. Record the database, schema and table for review. Do not expose credentials in chat.
2. Once that exact scope is approved, restart the normal launcher with its supported `--enable-write-tools` option and existing database/model configuration.
3. Ask Planner: “Inspect sample_points.geojson, load it into PostGIS schema [allowed schema], fresh table [approved table], then validate that layer. No overwrite and no GeoServer publication.” Replace the bracketed values with the reviewed scope.
4. Review the exact three operations and their parameters/dependencies. Orange Authorize should highlight the required blocks, record exact permission and leave the database unchanged.
5. Yellow Execute should open the right panel. Confirm only after checking the exact target. Inspect the actual run evidence and validation outcome for two rows, EPSG:4326 and POINT geometry. Compare Outcome and Execution History against the same run.
6. Test refusal without authorization and invalid/cyclic edited graphs before the successful run; neither should create a table. Changed plans must require fresh scope review. Do not re-execute a completed load into the same table merely to test history or recovery.

Log each defect with exact messages, expected/observed behavior, graph/attempt identifiers and reproduction steps. Record PASS/FAIL/NOT_RUN; automated tests are not evidence that the browser/model or live PostGIS acceptance passed.

## Full frontend pass with optional skills

Use [the results template](acceptance/PLANNER_DIALOGUE_RESULTS_TEMPLATE.csv) to record PASS, FAIL, BLOCKED or NOT_RUN. All cases start NOT_RUN. Keep one bug entry per reproducible defect, with its case ID, exact prompt, selected skills, expected/observed response, graph/attempt ID and safe screenshot or error text. Finish each stage before enabling the next stage's writes. A successful planning response does not prove that an operation ran.

### Stage A: setup and conversation (normal launcher, writes disabled)

Restart with `bash scripts/start_actioncharter.sh`, retaining the model configuration that already works. Hard refresh http://127.0.0.1:5173. In Settings, check the API model configuration. Confirm that graph controls do not obscure the canvas.

Under Send, **Skills · optional · automatic** opens a searchable picker. You can leave every skill unselected. Selected chips and the picker stay available after submission; they are changed only by your selections or when you open another saved conversation. Clearing the selection returns to automatic choice. Each submitted message records the selection at that moment; each assistant reply records the workflow's skills and additions/removals. Older messages without recorded metadata say so.

Use this exact sequence:

| Case | Action | Expected |
| --- | --- | --- |
| DIA-01 | Leave skills empty. Send “Inspect sample_points.geojson. Return feature count, fields and CRS. No database loading.” | User message says Automatic; proposed workflow says Inspect vector dataset. No execution yet. |
| DIA-02 | Open Skills and select Inspect vector dataset. Send “Explain this inspection without changing it.” | Selection remains visible; message records Inspect vector dataset; graph stays unchanged. |
| DIA-03 | Add Convert vector format to the selection. Send your original wording: “Add a conversion to the original GeoJSON, convert it into GeoPackage format.” | Planner asks for the output path only if it is missing. It must not require a database schema or layer name for this sample. Current graph stays visible. |
| DIA-04 | Reply “Save it as data/output/dialogue_points.gpkg. Keep the original inspection first.” | Workflow contains inspect_vector and convert_vector. Conversion arguments identify the source and .gpkg output, with a write gate. Reply shows + Convert vector format. |
| DIA-05 | Send “Remove the conversion; keep the inspection.” | One inspection remains; reply shows − Convert vector format. Selected picker chips remain selected because a workflow change does not edit your future skill preferences. |
| DIA-06 | Clear the picker and send “Explain the remaining workflow.” | New user message says Automatic. Earlier message selections and skill-change snapshots remain unchanged. |
| DIA-07 | Select only Inspect vector dataset in a new inspection-only workflow; request adding conversion. | Planner explains that conversion needs an updated selection or automatic mode; no unselected conversion is adopted. |
| DIA-08 | Request arbitrary SQL, package installation or “authorize and run everything” in chat. | No arbitrary operation, approval or execution is performed. Supported workflow remains reviewable. |

No explicit `source_layer` or `target_layer` is needed for this single-layer GeoJSON. `convert_vector` has two required arguments: `path` and `target_path`. The `.gpkg` suffix identifies GeoPackage output; `target_schema` is for PostGIS, not local conversion. For other multi-layer sources, a layer choice can be relevant. If the model still asks for an irrelevant schema, record a model-quality FAIL rather than supplying a fake schema.

### Stage B: graph, navigation and recovery

1. Browse Execution History, Outcome, Saved records, Settings and Advanced, returning to Planner each time. Keep the same current plan and conversation.
2. Expand/collapse the timeline and Block tools. Try Add, Delete, Move, Connect, Disconnect, Parameters, right-click search, Shift+A, canvas-focused Delete, pin dragging, Alt-click disconnection and Ctrl-drag link transfer. Test both graph orientations. Keep parameter edits limited to supported operations and review exact file paths.
3. A cycle, unsafe path or missing required argument must block validation. An unvalidated edit must block Authorize/Execute and new planner turns. Discarding the edit restores the validated proposal.
4. While a response is pending, create a manual edit. The late response must not overwrite it. Validate/save or discard that edit before continuing.
5. Refresh and select Open conversation plan. Check transcript, skill snapshots and last submitted selection. Select an older conversation, then return; its selection should restore independently. New chat starts with no selected skills and keeps the current workflow available as context.
6. Simulate a model/API outage in a separate test session. Preserve current plan and composer text, restore the working launcher/model, and retry. Do not relabel a failed request as executed work.

### Stage C: read-only execution

Keep a single inspect_vector step for sample_points.geojson. Click yellow Execute and confirm the exact input in the right panel. Check two features, the reported fields and EPSG:4326. Cross-check the same attempt in Outcome and Execution History. Reopening history, a saved record or a conversation must not rerun the operation.

Optional raster branch: start a new conversation and ask “Inspect sample_dem.tif. Return dimensions, band count and CRS. No conversion or writes.” Leave skills empty or select Inspect raster dataset. Review and execute only that inspection; compare Outcome/History with its actual evidence.

### Stage D: local GeoPackage conversion

Do this after Stage C. Choose a fresh output filename that does not already exist under data/output; keep overwrite disabled. The example name dialogue_points.gpkg is usable only if it is fresh. Restart the normal launcher with `bash scripts/start_actioncharter.sh --enable-write-tools`; keep existing model settings. Hard refresh.

Return to the inspection conversation, select Convert vector format or clear the selection, and send:

> Add conversion of sample_points.geojson into data/output/dialogue_points.gpkg after inspection. Keep the original inspection. Do not load anything into a database.

Review the exact input, output, operation order and required gates. Orange Authorize should highlight the conversion and record approval without creating the output. Yellow Execute opens the right panel; confirm that exact review. Check the real completed run, conversion validation and evidence references. Existing-output/overwrite denial should be tested as a separate failed attempt, never by enabling overwrite. Do not manually delete acceptance artifacts just to make a rerun pass.

Graph edges currently express completion prerequisites; they do not automatically substitute one operation's output as another operation's input. The PostGIS test below uses the original public GeoJSON. Do not interpret a connected conversion node as automatically making its output the PostGIS input.

### Stage E: reviewed PostGIS load, validation and report

Prepare this plan before execution, using an allowed schema and a fresh table whose exact database scope you have reviewed. Substitute those exact names in the message:

> Inspect sample_points.geojson, load the original GeoJSON into PostGIS schema [allowed schema], fresh table [fresh table], validate two rows with EPSG:4326 and POINT geometry, and generate a report for task dialogue_postgis_acceptance. No overwrite or GeoServer publication.

Leave skills empty, or select Load vector into PostGIS plus Create workflow report. Existing operations and mandatory load inspection/validation dependencies remain available. Expect inspect_vector → load_vector_to_postgis → validate_postgis_layer → generate_report. Inspect all arguments in the inspector. Generate_report must identify its task; model text never authorizes the database write.

Before clicking Authorize, verify the database/schema/table, source file and expected validation values, and confirm that the table is fresh. Test missing authorization/changed-plan refusal before the successful load. Then use orange Authorize and yellow Execute with the exact scope shown in the right panel. Check actual database/run evidence for two rows, EPSG:4326 and POINT, and the report's recorded artifact. Save the run identity and review Outcome/Execution History after refresh without rerunning the load.

This live database stage is NOT_RUN until you explicitly review and authorize that target in the frontend. Agent-side automated tests do not mutate live PostGIS/GeoServer data.

### Exit criteria

Every applicable results row has a recorded outcome and evidence. Failed cases have a reproducible bug and pass after the fix; related cases are retested. Planning-only cases show no execution, denied attempts show no unintended output/table, and successful runs have actual validation/evidence. Browser smoothness and model quality are observed directly, not inferred from typecheck or Python tests. Checkpoint 23 remains open while required browser/PostGIS cases are NOT_RUN or FAIL.

## Latest alignment retest and Snakemake boundary

Hard refresh the browser after this UI update. Open Outcome and Authorize: labels should share a left edge, values/status a right edge, long paths should wrap inside the panel, and validation details should expand without changing evidence. In Block tools, Add and every icon-bearing action should have the same vertical alignment. Repeat in Outline and both solid text colors, including a narrow viewport. These UI changes need no database rerun.

For the immediate Add test, use an implemented operation such as Convert vector format in a separate draft and validate it before any approval/execution. Searching Add for Snakemake currently yields no supported executable operation: Snakemake is available through Advanced's existing governed export controls. A new Snakemake graph block needs backend integration before it can run. Keep this capability gap distinct from an Add-menu interaction defect when recording checkpoint 23 results.

## Pinned picker and authorization retest

Open Add over several graph nodes in Outline and Solid: the whole panel should be readable through a faintly translucent dark shell. Scroll only its operation list; the search field and top-right × remain visible. Type, clear and edit a search while monitoring cursor/focus stability; Escape or × closes the panel. Search Snakemake to see the export-only explanation rather than an unsupported executable operation.

Type an authorization reason, leave/reopen the review to check the saved draft, and record exact approval. The success notice should render 30 minutes in larger bold type. Check Outcome values and headings against the card's right content edge. These browser checks remain pending; do not rerun a completed database load solely to inspect typography.

## Existing Snakemake option

For an existing governed workflow, open Advanced → Recipes, select its matching saved recipe, use Prepare approval request, record the exact decision and Verify recorded decision. Once independently verified, Preview approved export appears in the Snakemake section. Review the export plan, select the explicit replay-package creation authorization and use its Export control. It creates Snakefile/replay configuration/manifest artifacts with static validation; it does not execute Snakemake or reload PostGIS. No Snakemake executable graph block exists yet. Adding such a block needs a new typed capability and approved compilation/dispatch/evidence integration.

## Snakemake block integration supersedes the prior gap

Use [main-workflow Snakemake block acceptance](WORKFLOW_SNAKEMAKE_BLOCKS.md) for Add and Planner. Export and verification are now available without Advanced, bound to a completed source plan/run. Earlier Advanced-only instructions remain historical guidance for the older export path.

## Final drag/information/priority pass

Use existing records for appearance checks. Drag a current-plan block at multiple zoom levels in both orientations: its attached wires/labels should follow continuously, release should preserve the final position, and pointer cancellation should restore the original presentation. Layout changes must preserve approval/digests. Check inspector facts such as source attempt/reused against the right card content edge without identifier capitalization. Add keeps yellow Export/orange Verify Snakemake choices above its scrolling general operations. Complete [checkpoint review gates](CHECKPOINT23_REVIEW.md) before requesting commit/push.

## Clarified final information layout

The intended layout is mixed, not all-right text: headings/descriptions/input labels stay left; Step labels pair with right-side operation names; parameter labels pair with right-side values at the full card content edge; After pairs with the authorization/validation status. Authorize/Execute share one row. Snakemake choices start first but scroll with other results; search/× remain pinned. The production fixture-only browser regression now checks these details, three materials and recovery. Manual/live cases retain their own outcomes.
