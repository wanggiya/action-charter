# Checkpoint 22H — context and Intent interface vertical slice

## Summary

New Context & intent button opens a nonmodal panel beside the graph on wide screens, above it below 1050px. The regular inspector is hidden while this panel occupies the workspace; closing restores the previous layout and exposes graph details. The panel supports explicit selected-history retrieval, displayed-excerpt review, Intent reasoning with explicit answers, semantic confirmation of resolved Intent, immutable review storage and exact inspect_vector Planner handoff. No manual digest typing: API responses retain checked digests for explicit review clicks. No work approval is inferred.

The generated graph shows current request, reviewed history, selected input, Intent Agent, Planner, plan review and pending inspection capability. It does not claim dataset inspection or execution. Graph to view includes Reviewed intent · unsaved plan. Closing/reopening the panel keeps component drafts; refreshing clears drafts and unsaved graph. Stored context/intent reviews remain on disk. There is no automatic task association, saved-plan bridge, execution or durable chat transcript in this slice. Existing CLI and original Plan/Run flows stay available. Close the panel before using the original flow. Exit draft graph mode before opening it.

Edits to history selection/query invalidate context and downstream intent/plan. Request/answer edits invalidate intent review and plan. Controls are disabled during pending actions; model calls may take time. Error banners state Request blocked, never imply an execution failure. Upstream changes clear the generated intent graph. API schemas reject authority flags and bounded response reading remains enforced. A resolved model proposal can still be semantically wrong: inspect actual inputs/outputs/constraints before checking confirmation. Unresolved intent cannot be stored. The backend rechecks sources and exact plan scope; conservative Planner approval requirements remain visible.

## Terminal validation

```bash
make test
make interface-validate
```

Stop an old launcher with Ctrl+C, then restart in a terminal with these model settings:

```bash
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_NAME=qwen3:4b-instruct
export MODEL_TIMEOUT_SECONDS=300
export MODEL_MAX_TOKENS=4096
bash scripts/start_actioncharter.sh
```

Open http://127.0.0.1:5173. No write-tools flag required. No backend implementation changes in this ZIP; API routes require the cumulative 22G source.

## Frontend acceptance flow

1. Click Context & intent in the top bar. Confirm the reasoning-only notice and visible graph beside it (wide screen) or below it (narrow screen).
2. Choose only task-63f0cd2f3f3f42ffa42e16a381822d32 in the history list. Enter denied in Search selected histories. Click Retrieve context. Expect the recorded denial excerpt, Retrieved · not reviewed, no model call.
3. Read the excerpt and source details. Check I reviewed these excerpts as history, not approval. Click Store context review. Expect Context reviewed · no work approved. This adds a new immutable review record, not a new task event or approval.
4. Current request: Inspect the selected dataset and return metadata only. Earlier denial is historical context, never approval.
5. Explicit answers, one per line:

```text
Input: data/input/sample_points.geojson. Return feature count, fields and CRS.
Reading the file into process memory is allowed. Do not write files, change data, load into a database, or upload to external services. Do not add other restrictions.
```

6. Click Reason about task. Expect objective, concrete input, requested outputs and constraints. If Clarification needed appears, add genuinely required answers and reason again. Do not store inaccurate invented restrictions. A single corrective inference may happen when explicit answers exist and the first proposal is unresolved.
7. For a correct resolved proposal, check The displayed intent accurately matches my request, then Store reviewed intent. Expect Intent reviewed · no work approved. Audit digests/filenames are available under collapsed details.
8. Click Generate inspection plan. Expect Planned only · nothing executed and the generated graph beside the panel. There should be one pending inspect_vector capability for the selected input. An approval requirement, if returned, is preserved and clearly reported. Plan details shows true/false flags. It is not saved or executed by this button.
9. Close the panel and select Reviewed intent · unsaved plan in Graph to view. Click graph nodes to inspect the standard information section. Reopen Context & intent; the current drafts/results remain. Existing Plan/Run controls are not automatically populated with this new handoff yet.
10. Edit one explicit answer. The downstream intent review/plan should clear, and the old generated graph should no longer be selected. Reason again before reviewing a new scope. Change the history/query and confirm context review also clears. No old confirmation should be reused.
11. Test 1920x1080, around 960px width, and a narrow phone-sized viewport. The panel must not cover the graph as an overlay; it scrolls within its area. On narrow screens it appears above the graph. Closing should restore the normal layout. Source/code strings wrap instead of extending into the graph.

Expected disk records: reviewed-contexts/ and reviewed-intents/, both ignored. No new plans/, approvals/ or recipe-runs/ records from this panel. Inspect with git status --short --untracked-files=all -- reviewed-contexts/ reviewed-intents/ (no output). Existing denied task remains denied.

## Limits and next

This is a first context/intent surface, not the final conversational agent interface. No persistent chat, automatic context selection, multi-tool handoff, saved-plan bridge or execution here. Next: rechecked saved review recovery and bridge the new plan into the existing governed plan/recipe flow without requiring manual CLI work. Then simplify the user journey while retaining exact approval and evidence checks in details.

22H local validation: frontend TypeScript typecheck and production build passed. Frontend response schema accepted a valid Intent envelope and rejected true plan_created/approval_inferred/execution_performed/tools_called flags. Live browser interaction/layout acceptance remains with the operator. Backend unchanged from the tested 22G baseline.

## UI correction v39

Context & intent now matches the existing header secondary-button treatment (height, padding, colors, border, active state, keyboard focus). Retrieval still requires explicit selection and a nonempty query; typing denied does not select any task. The panel now displays selected count, visibly highlights checked history cards, and gives a precise prerequisite beside Retrieve context. Loading and inventory errors remain visible independently of query edits. Failed inventory loading can be retried with Refresh histories. No automatic selection or authority changes.

After applying v39, run make interface-validate, reload the page and open Context & intent. Confirm histories load, tick the checkbox for task-63f0cd2f3f3f42ffa42e16a381822d32 and see 1 of 5 histories selected. Enter denied; expect Ready to search the selected histories and an enabled Retrieve context button. Untick the checkbox and expect the select-history instruction plus disabled retrieval. If Histories unavailable appears, restart the updated backend and click Refresh histories; the error should remain visible while typing. Type checking and production build passed locally; browser acceptance remains to be checked.
