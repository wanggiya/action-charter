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
