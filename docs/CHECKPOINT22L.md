# Checkpoint 22L — new tasks without historical context

Historical task context is now optional for Intent reasoning. Context & intent offers **Start without history**. That explicit choice opens Task directly, without history selection, retrieval or context review. The Intent request contains an explicit null review filename; the returned intent contains null context filename/digest and no historical citations. No fake history artifact is created.

Resolved Intent still requires human review before planning. The same bounded inspection envelope, immutable intent/plan storage and separate work-approval rules apply. A history-free reviewed intent can be recovered after refresh. Its plan graph omits the unused reviewed-history node and edge. Historical reviews retain their existing source freshness checks.

## Terminal validation

```bash
make test
make interface-validate
```

Restart the launcher with your existing model settings. Execution can remain disabled.

CLI equivalent, without --review-filename:

```bash
.venv/bin/geoagent reason-task-intent \
  --request "Inspect data/input/sample_points.geojson and return feature count, fields and CRS only. Read-only." \
  --clarification "Input: data/input/sample_points.geojson. Return feature count, fields and CRS only." \
  --clarification "Reading the file into process memory is allowed. Do not write files, change data, load into a database, or upload to external services." \
  --project-root . > /tmp/fresh-intent.json
.venv/bin/geoagent inspect-intent-proposal /tmp/fresh-intent.json --project-root .
```

Expected: review_filename=null, context_sha256=null, cited_sequences=[], no execution or approval inferred. If the model asks a genuinely unanswered question, answer it before reviewing. A valid resolved proposal is not a guarantee that its meaning matches your request: read it.

## Exact frontend validation

1. Open Context & intent. In Historical context, click **Start without history**. Do not select a history or type `denied`.
2. Task expands. Context heading says **Not used**; the notice says no historical context will be sent.
3. Current request:

   `Inspect data/input/sample_points.geojson and return feature count, fields and CRS only. Read-only inspection.`

4. Explicit answers, one per line:

   `Input: data/input/sample_points.geojson. Return feature count, fields and CRS only.`

   `Reading the file into process memory is allowed. Do not write files, change data, load into a database, or upload to external services.`

5. Click Reason about task. Verify the exact input, metadata-only outputs and no persistent writes/database loading. If resolved and accurate, check the confirmation and Store reviewed intent.
6. Generate inspection plan. It must contain one inspect_vector step with the exact file and validation_required=false. An additional requires_approval=true requirement remains valid and must not be bypassed.
7. Inspect the graph. It should contain request, selected input, Intent, Planner and proposed inspection, but **no Reviewed history node**.
8. Confirm and Store reviewed plan. Expect Stored · not approved · nothing executed. Continue in Plan opens the existing saved-plan flow, not execution.
9. Refresh the browser. Open recovery → Load saved reviews → reopen this Intent review. Request, answers and proposal should return, with Context still Not used and Plan available. Recovery makes no model call.
10. Optional regression: reopen your older history-based Intent review. Context should show Reviewed, not Not used; its history source is still checked. Do not change old history records merely for testing stale rejection.

Changing context selection/query switches back to explicit historical review and clears downstream local state. Choosing Start without history replaces current drafts; stored evidence remains on disk. This slice removes historical-context prerequisites for new tasks, not intent/plan review or separate execution approval.

## Scope

Only the vector metadata Intent→Planner envelope is supported. The original Plan/Run paths keep their existing broader capabilities. Durable chat, automatic context retrieval and broader Intent capabilities remain next work.
