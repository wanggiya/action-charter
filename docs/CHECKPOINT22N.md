# Checkpoint 22N — integration acceptance

Added a 12-case integration matrix joining reviewed Intent to the real trusted registry, immutable plan storage, approval preparation, recorded decisions, independent decision verification, recipe compilation and immutable recipe storage. It covers vector/raster × fresh/history-backed tasks × approved/denied/no-approval-required plans. Model proposals are fixtures; no live Ollama, database or data-tool execution is claimed by these tests.

Approved plans compile to exact matching recipe steps; recipe storage itself grants no approval or execution. Denied plans cannot compile. Plans requiring no approval do not receive invented approval records. Existing direct recipe execution is tested elsewhere; this slice does not add an execution route or bypass an authority gate.

Saved-plan continuation now displays the reviewed task objective in the request field instead of the embedded Planner provenance JSON. This is a display transformation only. The saved PlannerResult, original structured request, plan digest and intent/context provenance remain unchanged. Ordinary plain-text Planner requests keep their original display.

## Terminal validation

```bash
make test
make interface-validate
.venv/bin/pytest -q tests/test_checkpoint22_integration.py
```

Expect all 12 integration cases to pass. They use temporary storage and do not modify real plans, approvals, recipes or datasets.

## Frontend check

1. Restart the launcher and open Context & intent.
2. Reopen your saved vector or raster Intent review. Select the matching Inspection capability in Plan; generation after recovery remains intentional.
3. Generate a fresh exact plan, inspect its step, confirm it, then Store reviewed plan.
4. Click Continue in Plan. Expect a readable task objective, not a long JSON string containing instruction, exact_arguments or reviewed_intent_untrusted.
5. Check the saved plan's step/path and approval scope. They must still match the plan you reviewed.
6. If requires_approval=false, expect No approval-required steps. Do not force an approval. The legacy approved-plan recipe compiler requires recorded approval and is not the no-approval inspection run path. Checkpoint 23 must provide a clear task-centered continuation rather than pretending an approval exists.
7. If requires_approval=true and you want to test denial, record Denied and verify the recorded decision. Expect execution blocked; do not execute. Approval evidence is append-only.
8. Close/reopen the saved plan. The readable objective and exact step remain; denied authority must remain denied.
9. Reopen a conventional older plain-text saved plan. Its request should display as before.

This is integration validation and a continuation display fix. Live model quality and actual frontend behavior remain local acceptance checks. The remaining Checkpoint 22O is documentation/commit closeout, not another capability expansion.
