# Task/input workspace foundation

This is the first bundled implementation group of the task-centered interface. It does not yet complete seamless execution. Existing Plan/Run and CLI paths remain available.

## Delivered

Task workspace replaces the Context & intent top-bar label and opens a fresh task directly. Context remains an optional stage. Input can be chosen from the existing read-only project catalog, or entered as a filename or explicit data/input-relative path. Input is displayed alongside the request in a pending draft graph after a short typing pause. Draft graph nodes do not claim tool execution, input validity or stored task identity.

The backend walks the selected path through no-follow directory descriptors, checks a regular file before inference and rechecks availability afterward. It rejects resolved model input differing from selection. No dataset content is read by the existence check; file-byte identity and data validity are not established. A selected-input statement is stored with clarification answers for review/recovery, preserving existing Intent envelope compatibility. Legacy requests may omit selection and ask for clarification; the new workspace requires it for submission.

Why ActionCharter is restored. CURRENT_STATUS retains detailed checkpoint history below an explicit marker. Context-pack construction uses the current overview and records the full-file digest. Older status files without the marker retain the previous bounded behavior.

## Terminal validation

Restart the API after applying this ZIP. From the project root:

```bash
make test
make interface-validate
make inspect
bash scripts/start_actioncharter.sh
```

For the CLI with the same model environment already configured:

```bash
.venv/bin/geoagent reason-task-intent   --request "Inspect the selected dataset. Return feature count, fields and CRS only; no writes or database loading."   --selected-input sample_points.geojson   --project-root .
```

It should return a proposal or clarification, not execute. For a missing file, use --selected-input does_not_exist.geojson: exit 2 with selected-input failure before model configuration/inference. Do not use an output target as the selected input.

## Frontend acceptance — exact steps

1. Open http://127.0.0.1:5173 and click **Task workspace**. Task is active without needing Start without history. The graph says Current task and contains only pending request/input/Intent nodes.
2. With no input selected, Send task / answers is disabled. History remains optional under Context; no denial or prior approval is inferred.
3. Choose **sample_points.geojson** from Existing files in data/input. Confirm the selected-input card and graph show data/input/sample_points.geojson. Refresh inputs should keep the selection; it does not grant permission.
4. Enter: `Inspect the selected dataset. Return feature count, fields and CRS only. Reading into process memory is allowed; no writes or database loading.` Send task / answers. Inspect the actual model objective, input, output and constraints. It must name the selected path. Do not confirm an inaccurate proposal.
5. If clarification is needed, answer up to four questions/lines and send again. The selected input is the fifth possible answer, added explicitly by the backend. A resolved proposal for a different path is blocked rather than rewritten.
6. Review and store accurate Intent. Choose Vector metadata in Plan, generate the inspection plan and confirm exactly one inspect_vector step on the selected path. Review/store it and Continue in Plan as before. Execution integration is still a later bundle.
7. Return to Task, change selection or request: the old local Intent/plan must clear and the draft graph update after a short pause. Disk reviews are not deleted. No stale graph is executable.
8. Choose Filename or relative path, enter sample_points.geojson and repeat submission: the stored selected-input statement is canonical data/input/sample_points.geojson. Test a missing filename: an obvious blocked message appears, nothing stored or executed. Test ../outside: also blocked.
9. Refresh the page, reopen a stored Intent review: its exact recorded input is restored in path mode. This is recovery of evidence, not new inference or approval.
10. Check full-width and half-width layout: task pane remains beside/above graph, neither overlays the other. Browser responsiveness and layout are manual acceptance; automated typecheck/build does not prove them.

## Remaining work

Connect this task to supported read-only execution without fabricated approval, integrate write workflows through existing exact-scope services, simplify transitions, and show readable outcomes/attempt history. This bundle is not the final public demonstration. No Jev integration or performance benchmark is included.

## Metadata output wording correction

The capability selector does not overwrite reviewed Intent scope. Equivalent labels such as Feature Count, field names and coordinate reference system are recognized as the supported metadata scope. Complete comma/and-separated enumerations are accepted only when every component is supported. Unknown outputs, summaries with unspecified content, report generation and exports remain blocked before Planner inference. No reviewed record is rewritten.

After applying the correction and restarting the API, reopen the same saved Intent review, choose Vector metadata and click Generate inspection plan again. A new Intent model call is unnecessary for an equivalent existing scope. The Plan stage shows the original reviewed metadata labels; a successful plan also shows the canonical supported metadata. If blocked, read the exact Unsupported requested output labels finding. Unsupported requests require clarification and a new review; do not edit immutable JSON manually.

## Planner response structure correction

A planner_invalid_schema failure means the model returned JSON with invalid plan fields or types. It does not establish that the user's context is wrong. The Planner prompt includes a concrete single-inspection response shape for the exact reviewed path. It sends selected capabilities/datasets and warnings, not the complete checkpoint history.

JSON, schema and policy failures share one correction budget: at most two model calls. The second response is a fresh complete proposal, validated against schema and policy; reviewed input and output scope are rechecked separately. No invalid JSON is patched into approval or execution authority. Transport failures are not automatically retried. A second failure returns up to six safe field findings without rejected model values.

Validation: run make test and make interface-validate. Restart the combined launcher with the same model environment, reopen the existing reviewed Intent, choose Vector metadata and click Generate inspection plan. No new Intent review is needed for unchanged supported scope. On success inspect the exact path, skill and approval flags; nothing has executed. On failure the blocked card must show field findings and One correction attempted. Share those findings instead of repeatedly changing the reviewed request. A retry can take a second full model timeout. Automated fixture tests do not verify local Ollama quality or browser behavior.

## Confirm the running correction code

After extracting this update, stop and restart the combined launcher. Startup must print Planner contract revision: schema-correction-v52. In a second terminal run:

```bash
curl -sS http://127.0.0.1:8765/api/v1/health | python3 -m json.tool
```

The response must include planner_contract_revision: schema-correction-v52 and planner_correction_limit: 1. Absence means the running API has not loaded this update, even if the source files were replaced. Python imports remain in the running process until restart.

A repeated generation can succeed after a malformed response: JSON mode does not enforce WorkflowPlan, and temperature zero does not guarantee every response meets schema. Do not rebuild context to hide a structure failure. The read-only prompt explicitly distinguishes planning from approval; any extra approval requirement still remains in the accepted plan. No flag is silently removed.

Frontend acceptance: reopen the same reviewed Intent, choose Vector metadata and generate once. Expect exactly one inspect_vector step for the reviewed path, or a blocked card with field findings and the correction-attempt indicator. Saving remains separate from execution. Local Ollama behavior must be tested manually.

## Conversation workspace simplification

Only the active stage is visible. Stage switching, historical context, saved reviews, reviewer identity and model diagnostics remain available under expandable controls. Input selection stays visible; source mode and refresh controls are secondary. Clarification answers expand when the model asks questions.

After reviewing an accurate resolved Intent, Confirm understanding and generate plan stores the exact reviewed Intent and requests its plan in sequence. These remain separate backend checks. If planning fails, the stored Intent remains and the Plan stage allows retry; do not repeat the storage operation. The graph is updated only after a validated plan response. Approval and execution are never automatic. Existing Continue in Plan remains a separate transition, so this is an incremental conversation layout, not complete conversational execution or persistent chat memory.

Manual acceptance:
1. Open Task workspace: see input and task composer, without four expanded stage headings. Support controls should be collapsed.
2. Select sample_points.geojson and enter: Inspect the selected dataset. Return feature count, fields and CRS only. Reading into process memory is allowed; no writes or database loading. Click Send task.
3. If questions appear, answer in the expanded clarification section and send answers.
4. For an accurate resolved proposal, choose Vector metadata, check the accuracy confirmation, then click Confirm understanding and generate plan. Expect the reviewed plan beside the panel, without a separate Store Intent click.
5. If the Planner fails, remain on Plan with the stored Intent available; use Generate inspection plan to retry. Nothing approved or executed.
6. Review the plan, check the exact-plan confirmation, Save reviewed plan, then Continue in Plan. Existing approval controls still govern execution.
7. Expand Change stage to return to Task. Changing the input/request must clear downstream local proposals; stored records remain. Reopen saved review under History, saved reviews and settings.
8. Check half/full-width layout and keyboard navigation. Build/typecheck do not prove visual acceptance.

## Text planner agent

A separate Text planner agent entry opens a planning-context composer beside the workflow graph. Generate plan calls the same capability-scoped Planner service, shows the validated result immediately and automatically stores its exact proposal through /api/v1/plans/save-generated. Storage rechecks registry, policy, digest and immutable-file identity using the existing storage service. It explicitly returns human_review_performed=false; neither human review nor approval is fabricated. Unknown extra authority fields and changed digests are rejected. Identical storage can be retried without another model call.

Default selected capability is inspect_vector, visible under Available tools; other implemented capabilities may be explicitly selected. This entry bypasses Intent/context review and sends the user's planning context directly, not an automatic retrieval of historical memory. It does not execute datasets. Changing the context or tools clears local plans and downstream approval/recipe state. Disk proposals remain in Saved plans.

Acceptance:
1. Run make test and make interface-validate, then restart the launcher.
2. Click Text planner agent. Enter: Create exactly one inspect_vector step for data/input/sample_points.geojson. Return feature count, fields and CRS. No writes or database loading. Plan only.
3. Click Generate plan once. Expect a validated single-step graph next to the composer and Plan saved automatically. No Save/Intent review clicks are required.
4. Expand Steps and technical details to inspect exact path/flags and the stored filename. Check Saved plans through the existing Plan workspace or graph source selector.
5. Change context: old local plan and approval state must clear. The saved file remains.
6. For a storage error, the generated graph remains and Retry saving this plan retries storage only. A model/schema/policy failure shows no saved success.
7. Close/reopen the panel and check half/full-width layouts. Unsaved drafts clear on page refresh; this is not persistent conversation memory.

One-click generation plus proposal storage is implemented; approval/run integration remains through existing panels, not automatic.

## Searchable skills and consistent controls

Text planner agent now uses the shared header-button style. Its skill selector is an expandable searchable dropdown with a bounded scrolling list, keyboard-focusable selection buttons, selected tags and a Done button; Escape closes it. Search matches readable names and internal IDs. No matches is explicit, and the existing twenty-skill request limit is enforced. Backend IDs and permissions are unchanged. Planner graph action titles use the same presentation names. No unverified library brand is added to a skill label.

Validate with make interface-validate, then restart/reload. Open Text planner agent, expand Skills, search PostGIS and inspect_vector, select/remove a skill, close with Done or Escape and check tags. An empty selection disables Generate plan. Restore Inspect vector dataset and generate the earlier read-only sample inspection. Expect that readable name in the graph and automatic storage; the policy node should identify the saved proposal rather than claim no durable evidence. Check scrolling in a half-width window and keyboard Tab navigation. Layout/interaction require manual acceptance.

Executable graph editing is still subsequent work: this update does not bind draft block changes to authoritative plans or add new PostGIS export capabilities.

## Compact titles and contextual suggestions

The Text planner accepts ordinary task language; exact capability IDs remain optional and supported. It reuses the existing Plan keyword recommendation score in a shared helper. Up to five suggestions appear while typing; adding a suggestion requires a click and does not infer authority. Selected suggestions are disabled to prevent duplicate IDs.

Generated graph headings use the readable action name for one step, or Proposed workflow with step count. Task request and Plan workflow nodes have short subtitles. Selecting an action opens its full purpose, internal skill ID, arguments and requirements in the right inspector; selecting intake shows the full original request. Full text remains in stored Planner results. The top navigation is unchanged in this bundle; its redesign requires a separate proposed layout. Executable graph editing remains upcoming work.

Acceptance: run make interface-validate, reload, and enter this natural-language planning context:

Inspect data/input/sample_points.geojson and show its feature count, field names and coordinate reference system. Do not change any data.

Expect skill suggestions including Inspect vector dataset. Keep only that capability selected, Generate plan, and confirm a compact graph heading and Task request node. Select the action to read purpose and arguments on the right. Select intake to read the full request. Automatic storage still grants no approval or execution. Try typing a PostGIS inspection request without generating: recommendations should change; no skill should be automatically added. Manual browser and local-model acceptance are still required.

## Context composer, inspector and input shorthand

Removed the Context-to-graph header caption and enlarged the context textarea. Text planner no longer inherits the layout rule hiding the inspector. Wide screens show context, graph and inspector columns; medium screens place the inspector below the graph; narrow screens stack them. Task history starts collapsed, with bounded scrolling when expanded. The upper navigation remains unchanged. Proposed subsequent navigation: Plan, Edit workflow, Run and Results; saved records/templates/history/settings under Advanced, plus a compact active-workflow title.

An optional Input file field accepts sample_points.geojson or data/input/sample_points.geojson. Backend request validation canonicalizes bare filenames under data/input, rejects traversal/non-normalized paths and deduplicates after normalization. Normalized paths are supplied to the Planner; the convention is also explained when the input is mentioned only in prose. This is planning-path normalization, not content inspection or proof that a model obeyed every instruction. Runtime adapters still check access/validation before operations. Automatic storage does not approve execution.

Acceptance: run make test and make interface-validate; restart/reload. Open Text planner agent, enter sample_points.geojson in Input file and type Inspect the selected dataset and return feature count, fields and CRS only. No data changes. Keep vector inspection selected, generate and verify the actual arguments use data/input/sample_points.geojson. Select the action: its parameters must be visible in the inspector without closing Text planner. Task history should be collapsed. Repeat with the full normalized path. Try ../outside.geojson: request validation must reject it before planning. Compare full/half-width layout; on smaller windows the inspector is below the graph. The larger context box and missing caption are visual acceptance checks.

Executable graph add/delete/connect/parameter editing remains outstanding. This bundle fixes discoverability and input conventions, not the execution editor.

## Composer and navigation follow-up (2026-10-05)

Supersedes the optional Input file field and proposed navigation described above. Planner agent is the default entry; Technical Plan is under Advanced. History, Saved records and Settings are direct header controls. History opens execution attempts, Saved records opens saved-plan controls, and Settings expands the existing API model configuration/recovery section.

Describe files in the borderless Planning context surface. Bare input filenames in proposed path arguments normalize under data/input before backend policy checks and hashing. Normalized relative paths remain supported. Absolute, traversal, repeated-separator, dot-component, backslash and control-character paths are rejected by backend policy. These checks do not inspect dataset bytes or grant access; runtime adapters retain their checks. Context text cannot approve or execute work.

The generated proposal survives view switches and execution-history browsing. Returning to Planner restores its graph, including saved-proposal evidence, without a model call. Context or skill changes still invalidate downstream local state. Refresh is not session persistence; stored plans remain recoverable.

Acceptance after restarting/reloading:
1. Confirm Planner agent opens by default with no Input file field. Enter: Inspect sample_points.geojson and return feature count, fields and CRS only. No data changes.
2. Generate once and inspect the exact arguments: path must be data/input/sample_points.geojson. Check the save status and inspector.
3. Open History, Flow graph, Settings and Saved records, then return to Planner agent. The same proposal and saved evidence must remain; no regeneration is required.
4. Check full/half-width layout, textarea focus and scrolling. The writing surface must occupy available left-panel space without a box border.
5. Change context or selected skills: downstream local proposal/approval state must clear. Stored records remain.

Run make test and make interface-validate. Automated tests cover path safety; typecheck/build do not establish browser layout or live-model quality. Executable graph editing remains later work, with canvas-scoped shortcuts and backend validation before approval/run.

Local validation: make test passed (1,374 tests); make interface-validate passed (TypeScript and production build). HTTP fixture tests required permission to bind loopback sockets outside the sandbox. git diff --check passed. Browser layout and live-model acceptance remain unverified.

## Navigation, operation edits and current-plan Execute (2026-10-05)

This supersedes the earlier History/Settings/Saved records aliases. There is one primary Planner agent entry. Execution History replaces the old Run navigation; Outcome shows the current result, not the attempts inventory. Saved records opens a dedicated browser of saved plans and recipes, including loading, empty and failure states. Header controls share the established style. Technical Plan and the legacy Task workspace remain under Advanced.

Settings is a separate panel. Check API model configuration reads the running API process. A configured endpoint with MODEL_NAME missing blocks inference. Run ollama list where Ollama is installed, set the exact installed MODEL_NAME in the terminal launching ActionCharter, stop/restart that launcher, and recheck. The panel supplies a shell-quoted launch command for the entered name; it neither changes environment variables nor tests connectivity. Existing MODEL_BASE_URL is retained.

Current-plan block actions appear above the canvas. Dragging affects presentation positions only. Right-click or Shift+A opens a searchable supported-operation menu. Delete applies only with canvas focus, and the final operation cannot be deleted. Edit parameters opens the selected operation's inspector fields. Added/deleted/changed operations remain local drafts. Validate and save edits calls the backend for schema, registry, dispatcher, policy and governed input/output path checks, then stores a new digest-bound proposal. Old approval artifacts remain immutable; local approval/recipe continuation state is cleared. Execute blocks unvalidated drafts. Dependency rewiring is not implemented here; the existing plan-to-recipe mapping is sequential.

Execute opens one exact-scope review for the current saved plan. The backend independently reloads the plan and deterministically derives the recipe and required gates. The review includes typed arguments, affected paths/tables, validation requirements and write availability. Confirmation binds its digest. Required approval is an explicit checkbox plus approver/reason; the same disclosed decision writes the necessary exact plan/recipe approval artifacts with a 30-minute expiry. Each gate is independently verified before dispatch through the existing recipe execution service. Previous denial remains recorded; a new approval requires a fresh explicit decision. Read-only vector/raster inspection runs through trusted adapters without creating fictional approval records. Conservative Planner-added inspection gates are retained.

Supported recipe dispatch operations are inspect_vector, inspect_raster, convert_vector, convert_raster, load_vector_to_postgis, validate_postgis_layer and generate_report, subject to existing argument/policy/validation constraints. Direct workflows containing only read-only operations currently support vector/raster inspection. Unsupported operations fail closed. Runtime services still enforce access, overwrite and write-enable settings. Context text never authorizes execution.

Read-only inspection attempts are persisted separately under inspection-runs, including failed attempts, and displayed alongside the existing governed recipe attempts in Execution History. Outcome shows inspection metadata or the current validated recipe result/evidence. Inspection history reports recorded metadata, not fresh byte verification or a Critic release. Interrupted inspection records can remain labelled running; generalized recovery is not added.

Manual acceptance after restarting the API and reloading:
1. Confirm one Planner entry and consistent Execute/Saved records/Settings button styles. Generate the earlier sample inspection.
2. Open Saved records: the generated plan should be listed. Open it without a model call. Check empty/error states against an empty/unavailable API.
3. Open Execution History, then Outcome: history lists attempts; Outcome reports no execution until an operation actually ran. Return to Planner without regeneration.
4. Click Execute, inspect the exact sample path, confirm inspection and Execute. Expect metadata in Outcome and a recorded inspection attempt in Execution History. No dataset writes or approval fabrication.
5. Select an operation, Edit parameters, change its path to an unsafe value and Validate and save edits. It must block. Restore a safe input, validate, and review the newly stored proposal. Old authority must not apply.
6. Right-click/Shift+A, search and add an operation; fill its parameters in the inspector. Delete a selected operation with canvas focus. Delete while typing in an inspector field must not remove a block. Drag nodes and check both orientations/window widths.
7. For a supported conversion in a disposable local project, launch with write tools enabled, review exact input/output and required validation, provide approver/reason and confirm once. Execute should return validated output/evidence using the existing executor. Do not use live PostGIS/GeoServer data for this acceptance.

Automated validation includes real vector conversion and output verification in a temporary project, inspection without fabricated approval, exact-review rejection, missing approval, disabled writes, conservative gates, preserved denial, typed edit rejection, safe paths, failed-attempt persistence and loopback origin checks. Browser interactions and live Ollama remain operator acceptance.

Local follow-up validation: make test passed (1,391 tests), including the full offline suite and temporary vector conversion. make interface-validate passed. No live PostGIS/GeoServer operations were run. Browser acceptance and actual MODEL_NAME configuration remain with the operator.

## Repeatable acceptance process

Use [interface acceptance](INTERFACE_ACCEPTANCE.md) for the full current-interface pass and ongoing bug/fix/retest loop. make interface-acceptance prepares a fresh source snapshot without starting services, calling a model or executing workflows. Live-model and deterministic-proposal cases are recorded separately. Local preparation/isolation/proxy checks and the full offline suite passed (1,398 tests), along with make interface-validate and diff checks. A prepared session begins with every browser case NOT_RUN; this is test preparation, not operator acceptance.

## Authorize, Execute and right-side review

Supersedes the earlier combined approval/execute checkbox in the current-plan interface. Orange Authorize with an exclamation icon highlights required operations and opens exact scope on the right. Approver/reason and the explicit Authorize click record exact 30-minute plan/recipe decisions, without running tools. Yellow Play/Execute independently verifies recorded authority before dispatch. Direct read-only inspection requires the explicit Execute click but no redundant inspection checkbox. The backend retains the prior explicit combined API contract for compatibility; the current interface uses separate authorize/execute routes.

Execution History, workflow review and Outcome now occupy a right-side workspace column beside the graph. On narrow screens the panel stacks; it never overlays the graph. Settings has a gear icon. Current plans remain in browser state. Scope edits invalidate local authorization, and changed/expired artifact authority is rejected server-side.

Retest in a newly prepared acceptance snapshot: check the gear and button colors/icons; run a read-only plan from the right-side review without a checkbox; use a conservative-gate or conversion proposal to check orange highlighting, Authorize without any output/run, then Execute; inspect History on the right. The guide now defaults acceptance sessions to ports 5173/8765. Stop an older launcher before reusing these ports.

Local validation for separate authorization: make test passed (1,402 tests), including authorization without execution, reuse without duplicate decisions, changed scope rejection and expiry rechecks. make interface-validate and git diff --check passed. The operator reported the prior main flow working; the latest layout and authorization interaction still require a fresh browser retest. No live PostGIS/GeoServer data was modified.

## Settings appearance controls

Settings → Appearance selects Solid fill or Outline with transparent fill. Solid text can be Black or White; Outline uses the action color for text, icon and border and retains the stored filled-text preference for switching back. The preview updates alongside header, planning and review action controls. The preference is validated and stored under a versioned browser-local key; malformed/blocked storage falls back without blocking the workspace. Graph blocks, evidence cards and navigation rail retain their structural presentation. Appearance changes do not invalidate plans or approvals. White-text fills use darker shades to maintain readable contrast.

Frontend acceptance on the normal bash launcher: open Settings, try all three combinations, inspect header/Generate plan/Authorize/Execute controls and focus/disabled states, close and reopen Settings, then reload. The preference should survive on the same browser origin. Continue planning or reopen a saved proposal to confirm styling does not clear it. No model call or execution is needed for these checks. Add/delete/move/connect/disconnect improvements remain the following work item.

Appearance validation: make test passed (1,402 tests), make interface-validate passed, and git diff --check passed. Preference loading was checked with saved/default, malformed, unknown and unavailable storage. Enabled filled-button palettes with both text colors meet at least 4.5:1 contrast in the checked color pairs. Actual browser switching/persistence/layout acceptance remains to be checked.

## Appearance coverage and active navigation

Execution History and Outcome now expose their selected state and share the thick navigation outline. Saved records, Settings and Advanced use cyan. Settings labels the preference Interface style, since solid/outline now extends to Graph to view, timeline stages, graph blocks/minimap and inspector/right-side information sections. Filled Black/White text applies to those surfaces; nested labels/previews are adjusted for readable contrast. Outline makes their fills transparent while preserving category/status colors. Authorization-required and authorized node outlines still take precedence. No plan or execution contract changes.

Retest on the normal bash launcher after reloading: select History and Outcome, inspect the three cyan utility buttons, then compare Solid Black, Solid White and Outline across selector/timeline/graph/inspector. Select several nodes and check pending/failed/complete labels and orange/green authorization emphasis. Appearance changes must preserve proposal state. Block action behavior is unchanged in this slice.

Appearance-coverage validation: make test passed (1,402 tests), make interface-validate passed and git diff --check passed. Added filled-surface palette pairs meet at least 4.5:1 contrast with their selected text color. Actual navigation outlines, filled graph/timeline/information surfaces and responsive layout still require the operator frontend check.

## Timeline material refinement

Outline is the initial material for the new preference version. Existing filled-text choice is retained from the previous version; explicit choices made afterward still persist. Evidence-backed status labels now inherit the selected filled foreground explicitly. Governed/Draft badges participate in the material setting, preserving their existing meaning.

Timeline events no longer have enclosing card borders or fills. Outline stage text is unboxed; filled mode fills only the stage label, leaving complete/approved/pending status text separate and unfilled. Selected or running stages outline both labels. Increased spacing separates the timeline track from the graph and its text. Running emphasis uses available execution progress; it does not infer a run from a pending proposal. Animation remains future work.

Retest after a hard reload: expect Outline initially, switch to Filled Black/White and read Evidence-backed status and Governed, then inspect the timeline. Click different stages and confirm only the active stage frames both labels; ordinary statuses remain unfilled. Return to Outline and confirm the plain stage labels and visible track. No operation or authority behavior changes.

Timeline refinement validation: make test passed (1,402 tests), make interface-validate passed, and git diff --check passed. Outline default, previous-version text-color migration, later explicit choices and malformed/blocked storage were checked against the frontend preference loader. Browser timeline spacing, label frames and status readability remain operator acceptance.

## Lower-left controls, translucent material and operation wiring

Zoom/fit/orientation controls and the legend now default to the lower-left of the canvas. They remain draggable within bounds; the legend has bounded horizontal scrolling when space is limited. All CSS-controlled scroll areas use the thin timeline track/thumb theme. Outline has a 50% translucent fill for controls, graph blocks, information surfaces and Governed, while content remains opaque. Timeline ordinary text remains unboxed as requested earlier.

The always-visible toolbar exposes Add, Delete, Move, Connect, Disconnect and Parameters. Operation editing is enabled for the current generated/restored plan; recorded graph projections remain view-only until the plan is opened through Saved records. Add/right-click/Shift+A uses the supported-operation menu. Delete removes the operation and its connections, renumbers references and does not implicitly bridge dependencies across the deleted operation. Move toggles local layout dragging; layout does not confer authority. Connect/Disconnect opens completion-order dependency controls in the inspector; matching data-port dragging also connects operations. Duplicate, self and cyclic edges are prevented locally. Edited graph/parameters are visibly marked as an unvalidated draft and cannot be authorized/run until backend validation and immutable proposal storage succeed.

PlanStep now optionally carries depends_on. Omitted/null dependencies serialize as before, preserving old plan digests; absent fields map to the original sequential recipe. Explicit dependencies become recipe DAG prerequisites. Policy checks known references, duplicates, self/cycles and mandatory inspection/load/validation/report ancestry. Execution review presents actual topological order and dependencies; governed dispatch uses that graph. File parameters remain explicit; this adds neither arbitrary functions nor parallel execution. Changed graph scope invalidates local authorization and cannot reuse an old digest-bound decision.

Validation: make test passed (1,412 tests), including a golden legacy digest, graph cycle/reference rejection, dependency-ordered real fixture inspection, changed-graph approval rejection, mandatory ancestry and frontend deletion/renumber/cycle helpers. make interface-validate and diff checks passed. No live PostGIS/GeoServer data was modified. Backend modules changed, so restart the normal bash launcher before the browser test.

Frontend retest: generate/open a vector inspection; check lower-left tools/legend and unified scrollbars; inspect Outline translucency; Add another inspection and set its path; move blocks; disconnect/reconnect their dependency via inspector and ports; reject a reverse cycle; validate/save; review and Execute the read-only DAG. Check Delete only with canvas focus and preservation of layout through validation/view changes. Gesture/layout acceptance remains with the operator.

## Hue-matched material and Blueprint-style pin interaction

Outline now derives its half-transparent fill from the element's accent hue, retaining opaque content. Execute/Authorize/utility controls, Governed, graph/status categories and authorization outlines keep their corresponding tint. Darkening the tint preserves text readability. Add is labelled plainly; its keyboard shortcut remains available without button text.

The current operation editor adapts [Epic's documented pin gestures](https://dev.epicgames.com/documentation/en-us/unreal-engine/connecting-nodes-in-unreal-engine): pin dragging, Alt-click breaking, Ctrl-drag link transfer and pin context menus. It also supports dragging from either pin direction, compatible-target feedback, pin-hover wire emphasis, right-button canvas pan, operation context menus and dropping a pin onto empty space to add/connect a supported operation. Ctrl transfers are atomic: a bad/cyclic transfer leaves the original graph untouched. Menu-created operations still require valid arguments and backend validation.

This is interaction adaptation for the registered-operation DAG, not the Unreal Blueprint language. Automatic type casts, arbitrary nodes, engine variables, loops, macros, undo/redo and grouped/marquee editing are not added here. Cycle, typed arguments, required ancestry, exact scope and approval gates remain enforced. Backend code is unchanged by this refinement.

Retest the gestures listed in the acceptance guide, especially input/output rewiring, invalid-drop cancellation, right-click versus right-drag and creation at the release location. Visual/pointer acceptance remains with the operator.

Validation for the pin refinement: make test passed (1,412 tests), make interface-validate and git diff --check passed. Incoming/outgoing break, link transfer and atomic cyclic-transfer rejection are covered by the frontend helper regression. Tint/foreground pairs were checked against the canvas background for at least 4.5:1 contrast. The full test run exposed CURRENT_STATUS crossing its 128,000-byte limit; the current overview was compacted to restore context construction, preserving the historical section byte-for-byte and keeping the limit unchanged. Browser gestures and visual acceptance still require retest.

## Conversational Planner and compact workspace

Planner agent now uses a backend dialogue coordinator around the existing reasoning-only manifest, shared model client and registry. A turn returns a clarification/explanation or a complete workflow revision. Typed argument, path, DAG and policy checks run before persistence/display. Existing gates for unchanged operations cannot silently disappear. No conversation endpoint calls approval or execution. The CLI and Advanced one-shot planner contracts are retained.

Completed turns and their latest proposal persist under ignored planner-conversations. The latest 20 chats are selectable; a refresh offers explicit Open conversation plan rather than replacing an already open graph. Model/validation failures retain the preceding completed transcript/proposal and the unsent composer text. A proposal-storage failure preserves the workspace; its completed conversation turn remains recoverable. Each chat is capped at 50 turns and 2 MB; model context includes its initial request, latest 12 messages and current plan, with older omissions declared. This is bounded conversation context, not unlimited agent memory. Restart/model failure may leave the last attempted turn unrecorded.

Optimistic conversation revisions and an active-turn guard reject competing turns; browser checks before/after proposal storage prevent delayed replies from overwriting changed plans or pending manual edits. Unvalidated graph edits and busy workflow actions block sending. Proposal storage precedes current-plan replacement. Authorize and Execute remain separate and exact-scope; new revisions clear local authority state.

The toolbar defaults to Add and Block tools, with validation/discard actions visible when needed. The timeline defaults compact and expands on request. Outline content is near-white over existing tinted translucent fills. Node and wire updates are animation-frame bounded and repeated pin-target validation is cached within a drag. These changes need browser acceptance; no frame-rate or smoothness threshold is claimed.

Regression coverage includes clarification, additions/removals, refresh recovery, invalid paths, one correction, stale/duplicate turns, approval-gate retention, bounded history, safe storage and history inventory. Use [Planner dialogue acceptance](PLANNER_DIALOGUE_ACCEPTANCE.md) before closing checkpoint 23. Live PostGIS loading and checkpoint advancement remain pending operator acceptance.

Dialogue validation: make test passed (1,427 tests), including the conversation HTTP/origin guard and common credential redaction; make interface-validate and git diff --check passed. HTTP fixtures required loopback socket permission outside the sandbox. Browser/live-model acceptance and the exact-scope PostGIS run remain NOT_RUN for this change. No live database or GeoServer data was modified.

## Optional conversation skills and conversion clarification

A searchable Skills picker below Send permits empty selection (automatic) and retains selected chips after submission. Explicit selections constrain additions; existing workflow skills remain available and load_vector_to_postgis adds mandatory inspect_vector/validate_postgis_layer dependencies. Selection conveys no execution authority. User messages persist per-turn selection; assistant messages persist workflow skill snapshots, from which the UI displays additions/removals. Saved chats restore their last submitted selection. Legacy entries without metadata are labeled rather than reconstructed.

The dialogue prompt now identifies convert_vector's exact required path/target_path arguments, optional layer names and .gpkg output suffix; no PostGIS schema is needed for local GeoPackage conversion. A missing output path should elicit one focused question with a proposed filename. This guides the model; browser/live-model behavior still needs acceptance.

[Full staged frontend acceptance](PLANNER_DIALOGUE_ACCEPTANCE.md) and its 27-case results template cover automatic/selected conversations, metadata, graph edits, recovery/failure, real local inspection/conversion, and separately reviewed PostGIS loading/validation/reporting. Output-to-input substitution remains unsupported: the database lane loads the original public GeoJSON. All manual cases begin NOT_RUN.

Optional-skills validation: make test passed (1,432 tests), make interface-validate and git diff --check passed. New regressions cover selection constraints with retained operations, automatic mode, per-turn snapshots/recovery, required conversion arguments, mandatory load dependencies and legacy transcripts. Browser/live-model and live database stages remain NOT_RUN.

## Outline edges and timeline alignment

Outline now fades hue-matched tint inward from the top/bottom edges, leaving its center clear and text opaque. Solid material is unchanged. The compact timeline has aligned status/marker/track rows, a quieter one-pixel connector, more readable labels with full-title tooltips and restrained selected/running frames. Unselected timeline stages remain unboxed. Compact height increases from 96 to 112 pixels to avoid clipping labels; expanded mode remains available. Browser appearance acceptance is pending.

Outline/timeline validation: make test passed (1,432 tests), make interface-validate and git diff --check passed. Browser appearance and the focused PostGIS walkthrough remain pending; no live PostGIS/GeoServer data was changed.

## Authorization review typography, layout dragging and failure diagnosis

Execution/authorization review has a dedicated sans-serif input/textarea style, left-aligned operation headings, two-column parameter rows, separate dependency/gate lines and visible status/error paragraphs. Status updates scroll into view. The review can be closed while a request runs; this changes the view, not the running operation. Selecting a review step reveals its graph block.

Live-plan layout dragging and the Move toggle remain available during review/authorization/execution; parameter/topology edits stay governed and blocked while execution is busy. Review fitting does not interrupt an active node/wire drag. Layout positions do not alter plan/recipe digests or approval scope.

Approved execution failures still return 409 when execution cannot complete. The API now maps trusted cause-chain messages to secret-free credential, allowed-schema, missing-schema, existing-table, connection/load and evidence-persistence diagnostics, with a failed step where available. Driver text, SQL, credentials and dynamic database values are never copied into these diagnostics. The frontend displays the reason and recovery guidance. This improves diagnosis; the reported browser failure's specific cause remains unconfirmed without its response body. Live PostGIS was not accessed or modified.

Authorization/failure validation: make test passed (1,439 tests), make interface-validate and git diff --check passed. Tests exercise actual exact authorization and governed dispatch through a fake PostGIS adapter, proving missing-schema conflicts expose the failed step without database access, and check six diagnostic categories against secret-bearing nested driver errors. Browser review/dragging and the actual reported 409 still require confirmation.

## Local .env and host secrets

The reported PostGIS step_2 conflict is now identified: the host launcher did not read .env and inherited the MCP container default /run/secrets/postgis_password rather than the existing .secrets host file. A data-only helper loads allowlisted database/model/scope settings, honors terminal overrides, translates container service defaults for host use, and resolves relative secret-file paths from the project root. Container secret defaults become local .secrets paths when not explicitly overridden by terminal exports. The backend still reads passwords from files; contents are never imported into environment variables, logged or sent to the browser.

The helper executes no dotenv shell commands, imports neither raw passwords nor authority/operational-root settings, and preserves explicit isolated acceptance endpoint/missing-secret overrides. Writes remain a --enable-write-tools decision and overwrite remains disabled. Local verification confirmed a configured database/model, loopback host and readable non-empty host PostGIS secret without exposing its contents. No database connection/load or live data mutation was performed. Restart the launcher to replace the old API process before retrying the exact reviewed workflow.

Host configuration validation: make test passed (1,444 tests), make interface-validate, bash syntax and git diff --check passed. Tests cover host path/address defaults, dotenv-versus-terminal precedence, data-only parsing without command execution, excluded passwords/authority/root settings, missing dotenv and isolated acceptance overrides. Live database connectivity and frontend load remain pending operator validation.

## Information alignment and toolbar baseline

Outcome and authorization review now share a label/value grid: labels align left, values and gate/status text align to a common right edge, with wrapping for long paths and stacked rows on narrow screens. Panel typography and heading spacing are consistent. Authorize/Execute controls align right. Outcome validation JSON is available in expandable details; evidence/report paths use labeled rows. Block action buttons share one icon/text baseline and height, including Add.

The operator reports the .env/host-secret run worked; this is operator-reported success, not a new agent database run. Alignment and block-action browser retests remain pending. Snakemake remains an Advanced governed export path; it is not among the seven supported executable graph operations. Adding a Snakemake execution/export graph block requires a typed backend capability, graph/compiler/policy integration and scope-bound approval/evidence handling. It must not be represented as an executable block before those contracts exist.

Alignment validation: make test passed (1,444 tests), make interface-validate and git diff --check passed. Browser alignment acceptance remains pending; existing run evidence can be reopened to check appearance without repeating the PostGIS load.

## Pinned Add panel and local typing state

The Add operation menu is a separate component with local search state, so keystrokes no longer rerender the workflow App. The entire panel shell uses a 94% opaque charcoal background in both materials; its header/search and top-right × stay outside the independently scrolling result list. Escape closes it, and searches with no supported match show an explanatory state, including the current Snakemake export boundary.

Authorization inputs likewise hold local typing state, syncing drafts on blur/submission rather than every keystroke. Exact backend authorization checks remain unchanged. Status messages no longer initiate animated scrolling while busy; successful authorization emphasizes 30 minutes in larger bold text. Outcome cards/rows occupy full content width to align values to their padded right border; headings and summary text align right. Browser smoothness and visual acceptance still require a direct retest.

Pinned-picker/form validation: make test passed (1,444 tests), make interface-validate and git diff --check passed. Local component state and scroll structure are implemented; direct browser typing/scrolling/authorization appearance checks remain pending. No database load or Snakemake export was performed by the agent.

## Main-workflow Snakemake export and verification (2026-10-07)

The prior Advanced-only capability gap is now addressed by two registered interface-coordinator operations: export_snakemake_workflow and verify_snakemake_export. Add exposes both and automatically appends verification after export; it preserves a typed source plan filename/digest and adds completion dependencies. Conversational Planner receives the saved source reference and may append the same pair, preserving the original operations. Normal recipe dispatch remains its existing allowlist; terminal export orchestration does not turn into arbitrary recipe execution.

Backend validation checks exact source operations/effective dependencies, required gates and terminal export→verification topology. Review requires a validated-success source recipe attempt with independently verified historical authority and result/evidence identities. The source run/evidence and approval identity enter the exact review digest. A fresh plan approval authorizes current package creation; no new source recipe-execution approval is minted. Execute reuses recorded source results, generates or retains the exact immutable package and verifies canonical contents, hashes and source configuration. It never calls the source executor or runs Snakemake. Tampered/mismatched packages, symlinks, missing completion and expired export approval fail closed. Export attempts persist in current-plan history, with truthful reused/exported/verified statuses and no claimed source reexecution.

[Frontend instructions and acceptance](WORKFLOW_SNAKEMAKE_BLOCKS.md) cover the Add and Planner paths without Advanced. This implementation is for exporting a completed governed source; a new source must run successfully before export review. It does not add Snakemake engine execution or live output revalidation. Remaining checkpoint browser/live-model/material/edit/recovery checks are still required.

Main-workflow Snakemake validation: make test passed (1,459 tests), make interface-validate and git diff --check passed. Fifteen new tests cover real temporary conversion→export/verification, source-executor non-invocation, no renewed recipe approvals, immutable package reuse, missing/tampered completion, source scope/dependency/gate checks, write mode, expiry, symlinks, saved-reference conversation generation, legacy dependency materialization and exact approval/review binding. Browser/live-model Add/Planner acceptance remains pending. No live database data was modified and no Snakemake process was run.

## Drag preview, information grid and featured Snakemake

Layout movement now uses a transient compositor transform and direct connected-path/label previews, with one integer-position state commit on release. Cancel restores presentation; graph/view/orientation changes clear pending previews. Shared curve geometry keeps preview and rendered wires consistent. This removes whole-App React updates from normal node-drag frames; browser performance still needs observation. Inspector detail/evidence facts now share a left-label/right-value grid, preserving hashes and boolean casing. Snakemake options are pinned ahead of the independently scrolling operation list, with yellow export and orange verification styling; workflow blocks retain authorization/failure highlights.

[Checkpoint review and remaining gates](CHECKPOINT23_REVIEW.md) provides the combined change summary and acceptance requirements before any requested commit/push. No commit/push has been performed.

Drag follow-up: automatic fit now runs on graph identity/orientation changes, rather than every bounds change, so dropping a moved node preserves zoom/scroll. Escape, graph switches, orientation changes and incoming Planner revisions restore/cancel active presentation previews before changing the graph.

Drag/information/priority validation: make test passed (1,460 tests), including actual frontend drag coordinate/wire/cancellation helper execution. make interface-validate and git diff --check passed. Source config, secrets, conversations, attempts and Snakemake packages remain ignored. Browser dragging/viewport retention and final export/recovery acceptance remain pending; no commit or push was performed.

## Clarified paired layout and production-browser regression

Headings, descriptions, step labels and input labels stay left. Operation names, parameter values and authorization/validation status occupy the right side of full-width paired rows. After/status share a row, and Authorize/Execute share one action row. Execute has type=button and cannot resubmit the approval form. Successful authorization keeps the action row visible. File/identifier casing is preserved. The legacy dd max-width:58% cap was the measured reason values stopped short; shared grid rows now use the whole assigned column. Earlier all-right narrative changes were reversed.

Snakemake choices lead the scrolling result list; only search and × remain pinned. Camera/sizer transitions were removed because they desynchronized drag coordinates from painted scale. Edited-plan projections have stable IDs and memoization; SVG glow is suppressed during drag and Escape cancels even with the button focused. Settings descriptions reflect the actual tinted-edge material.

The production Chromium regression passes nine groups: Add/search/scroll, pointer/drop viewport retention, draft stability, vertical/cancel behavior, mixed card geometry and same-line actions, three materials, Outcome facts, narrow layout and refresh/history recovery. It uses explicit mock APIs, blocks external requests and makes zero live GIS calls. Geometry checks verify right edges within 1.5 pixels, rather than just checking text-align. make test passed (1,460 tests), make interface-validate and diff checks passed. Browser evidence and repeatable setup are documented in CHECKPOINT23_BROWSER_CHECK.md. Live-model/database acceptance stays separate from these deterministic checks; the operator reported the host-configured workflow working.

## Publication audit

The operator authorized commit/push, PR merge with --merge and feature-branch deletion. The proposed branch and staged files were checked against actual local secret values and common encoded variants without displaying those values. No matches, private keys, detected access tokens, archives or runtime/config outputs were found. Explicit staging includes checkpoint source, tests, documentation and acceptance templates only; .env, .secrets, generated GIS/package/evidence records and temporary browser dependencies/results remain excluded. Staged review also caught and corrected an accidental documentation overwrite before publication.

CI portability follow-up: the Python runner installs dependencies globally rather than under repository .venv. Acceptance fixtures now wrap the active sys.executable instead of linking an assumed developer venv, retaining the same isolated snapshot checks. No application startup requirement, authority guard or test coverage was relaxed.
