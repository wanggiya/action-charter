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
