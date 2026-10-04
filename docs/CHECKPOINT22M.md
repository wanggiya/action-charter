# Checkpoint 22M — explicit vector and raster metadata envelopes

The reviewed-intent Planner bridge now supports exactly one selected read-only capability: inspect_vector or inspect_raster. A shared scope checker is used before planning and during plan storage. One concrete normalized input under data/input is required. Vector outputs are limited to feature count, fields and CRS. Raster outputs are limited to width, height, band count and CRS. Unsupported outputs, additional steps, a different input or different skill are rejected. Conservative human-approval requirements are preserved.

The interface adds Inspection capability in the Plan stage. Changing it discards local generated-plan/continuation state but leaves reviewed intent and immutable disk evidence unchanged. Choose the capability again after recovery: it is a planning choice, not part of the stored Intent. Existing vector plans lacking inspection_skill retain their previous storage compatibility. New Planner requests explicitly embed the selected skill with intent/context provenance.

This uses the existing raster backend; it adds no package or new data processor. The bridge plans and stores, without inspecting data or executing tools. Work approval remains separate.

## Terminal checks

```bash
make test
make interface-validate
test -f data/input/sample_dem.tif && echo "Raster input exists"
```

Restart the launcher with your existing model settings. Execution can remain disabled. If sample_dem.tif is absent from your checkout, use an actual existing raster under data/input and substitute its exact path below.

CLI handoff after reviewing a raster Intent:

```bash
.venv/bin/geoagent plan-reviewed-intent "intent-review.<digest>.json" \
  --allowed-skill inspect_raster --project-root . > /tmp/raster-handoff.json
# Inspect the exact returned plan before storage.
.venv/bin/geoagent save-reviewed-intent-plan /tmp/raster-handoff.json --project-root .
```

## Frontend acceptance

1. Open Context & intent → Start without history.
2. Current request:

   `Inspect data/input/sample_dem.tif and return width, height, band count and CRS only. Read-only raster metadata inspection.`

3. Explicit answers, one per line:

   `Input: data/input/sample_dem.tif. Return width, height, band count and CRS only.`

   `Reading the raster into process memory is allowed. Do not write files, change the raster, load into a database, or upload to external services.`

4. Reason about task. Check the resolved proposal: exact input, the four requested metadata names, no writes. Only confirm it if accurate, then Store reviewed intent.
5. In Plan, set **Inspection capability → Raster — width, height, band count, CRS**. Click Generate inspection plan.
6. Expect exactly one inspect_raster step, arguments containing only path=data/input/sample_dem.tif, validation_required=false. requires_approval=true is allowed and remains a separate requirement.
7. Inspect the graph: raster input and proposed raster inspection, with no history node on this history-free path. Nothing should be labeled executed or validated because planning did not inspect the file.
8. Confirm and Store reviewed plan. Expect Stored · not approved · nothing executed. Continue in Plan reopens the existing separate review flow; no approval or execution is needed for this test.
9. Refresh and reopen this Intent from saved-review recovery. Choose Raster again before generating another plan.
10. Optional rejection check: with this same reviewed raster Intent, choose Vector and click Generate inspection plan. Expect a visible blocked request saying inspect_vector supports only feature count, fields and CRS metadata. No model call, saving or execution should occur. Return to Raster to continue.
11. Regression: reopen your existing vector Intent, select Vector, generate and store its exact metadata plan. Both paths remain available.

Model wording remains a review issue. If the proposal changes the requested metadata names or adds restrictions you did not request, clarify/regenerate rather than approving it. Unsupported capabilities are not silently mapped to another tool.

## Scope after this slice

Checkpoint 22 provides explicit historical context retrieval/review, history-free tasks, Intent clarification and immutable review, bounded vector/raster Planner handoff, plan storage and review recovery. It does not provide generalized memory, durable conversation, arbitrary library functions or write-capable Intent envelopes. Those remain later integration work. CLI and original Plan/Run remain available.
