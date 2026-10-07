# Frontend walkthrough: vector inspection to PostGIS

Use this focused pass after restarting the current source launcher. This is a browser validation procedure, not a completed acceptance report. Keep checkpoint 23 open until the actual run and recovery checks pass. The broader [dialogue acceptance guide](PLANNER_DIALOGUE_ACCEPTANCE.md) has failure/editing cases and a results template.

## 1. Restart and check the material

In your existing launcher terminal, press Ctrl+C and run:

```bash
bash scripts/start_actioncharter.sh
```

Keep your working model exports. The launcher also reads non-secret database/model settings from the project .env, with terminal overrides taking precedence, and uses host .secrets files. Expect “PostGIS credential file: readable and non-empty” at startup. If an old terminal export points POSTGRES_PASSWORD_FILE at /run/secrets, change that export to the intended host file before restarting. Do not paste the password into chat. Open http://127.0.0.1:5173 and hard refresh. The API port remains 8765.

In Settings select Outline. Buttons, graph nodes and information surfaces should have subtle color near the top/bottom edges, fading to a transparent middle with readable opaque text. The timeline should have a centered connector through each marker, spaced status/labels and thin frames only for selected/running stages. Expand it to compare the full view. Check Solid with white and black text as well; it keeps its existing fill. Record any overlap, clipping or illegible content.

## 2. Prepare a vector-only proposal

Open Planner agent. Leave Skills empty (Automatic), or select Inspect vector dataset. Send:

> Replace the current workflow with only inspection of sample_points.geojson. Return feature count, fields and CRS. No conversion, database loading or writes.

Expect one inspect_vector operation with path data/input/sample_points.geojson. The chat and graph are proposals at this point. Select its block to inspect exact arguments. If the current chat is confusing, New chat keeps the current workflow as context; the explicit replace request above still asks for a one-step proposal.

## 3. Execute the inspection

Click yellow Execute. In the right-side panel, check the exact source and confirm execution. Expect evidence reporting two features and EPSG:4326 for the public sample. Check Outcome, then Execution History; both should identify the same completed attempt. Return to Planner without regenerating the proposal.

Do not continue to the database stage if this inspection fails. Record the error and attempt identity.

## 4. Propose the database workflow before allowing writes

Clear Skills for Automatic, or select Load vector into PostGIS. Use an allowed schema and a fresh table name. The example schema below is the project's default example; replace it if your configured allowed schema differs. The table name is a proposed new target, not evidence that it is absent.

Send:

> Keep the inspection of sample_points.geojson. After it, load that original GeoJSON into PostGIS schema agent_sandbox, fresh table ac23_ui_points_20261006a. Then validate two rows, EPSG:4326 and POINT geometry. Do not overwrite an existing table. Do not publish to GeoServer. Only propose the workflow; do not authorize or execute it.

Expect three operations: inspect_vector → load_vector_to_postgis → validate_postgis_layer. In the inspector verify:

| Operation | Exact scope |
| --- | --- |
| Inspection | path: data/input/sample_points.geojson |
| Load | same source path; your reviewed target_schema and fresh target_table |
| Validation | same schema/table; expected_row_count: 2, expected_srid: 4326, expected_geometry_type: POINT |

Load must require approval, and validation must require validation. If arguments/dependencies are wrong, ask Planner to correct them, or edit them and use Validate and save edits. A model reply is never authority. Missing scope should produce clarification; do not proceed using an unreviewed invented target.

Optional report: select Create workflow report too, or leave selection empty, and send “Add a report after validation for task ac23_ui_postgis_acceptance. Preserve the existing three operations and their exact scope.” Inspect its task_id and ordering. The expected graph then has four operations.

## 5. Review the live database target

Confirm the database connection refers to your intended test database, that the schema is configured as allowed, and that the proposed table is absent. Review this exact target before approving the live write. The normal launcher uses your existing trusted database configuration; chat must not contain credentials.

For the write-enabled stage, stop the launcher and restart in the same terminal with:

```bash
bash scripts/start_actioncharter.sh --enable-write-tools
```

Hard refresh, reopen your saved conversation, and click Open conversation plan. Check that all arguments still match the target you reviewed. The backend may block execution if the connection, allowed schema or write mode is unavailable; record that state instead of treating it as a successful load. Overwrite remains disabled.

## 6. Authorize, then execute

Click orange Authorize. The right-side review should show the exact target and highlight required graph blocks. Record the explicit approval in that panel. Authorization alone must not create the table.

Then click yellow Execute. Confirm the same exact workflow in the right panel. Wait for its actual completion. Read Outcome and the validation evidence: two rows, SRID 4326 and POINT geometry. Inspect the report artifact if you added the report. Planning predictions are not run evidence.

If any operation fails, preserve its attempt identity and error. Do not authorize a different scope or re-execute a load against the now-created table as a recovery shortcut.

## 7. Verify recovery and acceptance

Open Execution History and select the completed attempt. Its target, steps, validation and outcome must match the run. Return to Planner; the current proposal remains available. Refresh and reopen the conversation plan/history without regenerating or re-executing. Historical approval does not authorize a new revision.

Record PASS/FAIL for appearance, inspection, proposal scope, authorization-without-execution, load/validation, optional report and recovery. Attach actual run/evidence identities. Complete the related denied/invalid-edit cases in the broader guide before closing checkpoint 23. Advance only after required cases pass; no live database acceptance is implied by automated tests.

## If Execute returns 409 after authorization

Authorization confirms exact permission; it does not prove database readiness. Read the right-panel error first. Missing/unreadable credentials require correcting the launcher's trusted password-file setup; an absent/outside-allowlist schema requires reviewing the configured allowed existing target; an existing table requires a fresh reviewed name. Connection/loading failures require database reachability/permission diagnosis without exposing secrets. Do not auto-retry an attempt that may have written data; inspect history and actual target state first.

If the reason is still unclear, DevTools → Network → workflow/execute → Response contains the safe error, failure_code and failed_step_id when available. Share that JSON without credentials. The JavaScript call stack and HTTP status alone do not identify the blocker. After a source update restart the write-enabled launcher, hard refresh, reopen the saved plan, and explicitly review/authorize its exact scope again before testing Execute.
