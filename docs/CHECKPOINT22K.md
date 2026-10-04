# Checkpoint 22K — one current stage in Context & intent

The checked context/Intent/Planner services now have a clearer interface journey: Context, Task, Plan, Continue. Only one stage is expanded. Earlier stage headings and navigation remain available for inspection. Successful context review advances to Task, successful intent review advances to Plan, and successful plan storage advances to Continue. Reopening a saved context or intent lands at the appropriate next stage and collapses the recovery list.

This removes simultaneous open forms, not required review decisions. No extra approval gate, API route or execution authority was added. Storage, rechecking, exact approval requirements and CLI behavior remain unchanged. The current-state summary distinguishes retrieved, proposed, reviewed and stored evidence. Stored artifacts no longer retain misleading “not reviewed” or “planned only” labels.

Scrolling to a new stage affects only the context panel; it does not move the surrounding page or graph. Request errors bring the panel's feedback into view and leave the current stage unchanged. Context/request edits invalidate local downstream proposals and return to the relevant stage. Disk evidence is not deleted. Closing/reopening retains the active stage and drafts; page refresh still requires reopening saved evidence.

## Terminal validation

```bash
make test
make interface-validate
```

Restart your existing launcher after applying the cumulative ZIP. Backend services have not changed in this slice. No execution enablement is required.

## Frontend acceptance — quick recovery route

1. Open Context & intent. Expand Resume a saved context or intent review → Load saved reviews.
2. Reopen your available metadata Intent review. Expect the recovery list to collapse and stage 3, Generate and review plan, to expand. Context and Task headings remain visible but their forms are collapsed.
3. Use the Task navigation button or stage 2 heading. Verify the restored request/answers and that the proposal says **Intent reviewed · no work approved**. Merely viewing does not invalidate it.
4. Return to Plan. Generate inspection plan, inspect its graph/details, confirm it and Store reviewed plan.
5. Expect stage 4, Continue with stored plan, to expand automatically. It prominently states **Stored · not approved · nothing executed**. The Plan heading says Stored.
6. Click Review plan and graph. Stage 3 opens and its result says **Plan stored · nothing approved or executed**, without another storage checkbox. Return to Continue using its navigation button.
7. Click Continue in Plan to reopen the existing saved-plan and separate approval review flow. This does not record a decision or execute anything.
8. Close/reopen Context & intent; its state stays available. Refresh the browser; saved evidence can be recovered through the recovery list again.

## Full fresh route

If testing new reviews, use the earlier denied history and exact metadata request from docs/CHECKPOINT22I.md. Retrieve context and confirm it; successful Store context review must advance to Task. Reason about task, inspect the resolved proposal, and confirm it; successful Store reviewed intent must advance to Plan. Clarification-required or blocked requests must not advance.

After a reviewed intent, return to Task and edit an answer. Expect local intent/plan/stored-plan continuation state to clear; Plan and Continue become unavailable until fresh reasoning/review. The previously stored artifact remains in Saved plans. Changing the selected history/query returns to Context and also clears downstream local state.

Check both a full-width and half-width window. Navigation should remain legible and only one stage body should be expanded. The graph remains alongside the panel on wide screens, below it on narrow screens. Manual browser behavior remains an acceptance check; automated validation here is typecheck, production build and unchanged backend regressions.

## Remaining scope

Intent still requires explicitly reviewed history and supports only vector metadata inspection. Fresh tasks without prior history, broader capability envelopes, durable conversation and a unified run journey remain future work. This is interface navigation polish, not completion of the full agent product.
