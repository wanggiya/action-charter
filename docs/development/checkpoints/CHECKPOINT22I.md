# Checkpoint 22I — reviewed-intent plan storage bridge

The Context & intent panel now offers explicit plan confirmation, Store reviewed plan, and Continue in Plan. Saving rechecks the immutable reviewed intent, current context sources, exact input, supported skill, validation flag and confirmed plan digest. It calls the existing immutable plan store. The generated Planner request embeds the exact reviewed-intent filename and intent/context digests, preserving provenance in the stored artifact.

Storage does not call a model, approve work or execute tools. Additional approval requirements remain unchanged. Continue in Plan reopens the artifact through the existing saved-plan inventory and prepares review scope, without recording a decision. Read-only plans may display No approval-required steps; conservative plans still require a separate decision. No automatic association with the old denied task is made.

## Validate

Run `make test` and `make interface-validate`. Stop the launcher once with Ctrl+C and restart with your existing model settings using `bash scripts/start_actioncharter.sh`. Execution authority can remain disabled.

1. Open Context & intent. Select the denied history, retrieve `denied`, review the excerpts and store the context review.
2. Request: `Inspect the selected dataset and return metadata only. Earlier denial is historical context, never approval.`
3. Explicit answers, one per line:
   - `Input: data/input/sample_points.geojson. Return feature count, fields and CRS.`
   - `Reading the file into process memory is allowed. Do not write files, change data, load into a database, or upload to external services. Do not add other restrictions.`
4. Reason about task. Check the displayed input, outputs and constraints, confirm their accuracy, then Store reviewed intent.
5. Generate inspection plan. Check the graph and Plan details: exactly one inspect_vector step, correct path, validation_required false. requires_approval true is allowed and must remain visible.
6. The Store reviewed plan button stays disabled until its separate confirmation checkbox is checked. Check it, then store. Expect **Stored · not approved · nothing executed**.
7. Click Continue in Plan. The context panel closes and the existing Plan panel opens with the exact saved plan and approval scope. No decision is recorded by this click.
8. Close and reopen the original Plan panel or refresh the page and select this artifact in Saved plans. It remains on disk. Do not approve or execute merely to test storage.
9. Repeating storage with identical bytes is idempotent. Editing upstream context/request clears the local downstream proposal; stored artifacts remain immutable.

Existing handoffs from older versions lack provenance fields and the plan digest. Generate a fresh plan with this version before saving. Saved-review recovery without repeating reasoning remains future work. This slice supports only vector metadata inspection, not PostGIS or conversion via Intent.

## CLI equivalent

After human review of the generated handoff JSON:

```bash
.venv/bin/geoagent plan-reviewed-intent "intent-review.<digest>.json" \
  --allowed-skill inspect_vector --project-root . > /tmp/reviewed-handoff.json
# Read the exact plan before storing it.
.venv/bin/geoagent save-reviewed-intent-plan /tmp/reviewed-handoff.json --project-root .
```

The same service validates storage for CLI and API. It does not prove model provenance or grant execution authority.
