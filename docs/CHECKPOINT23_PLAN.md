# Checkpoint 23 — task-centered conversation and governed execution

## Goal and target

Make the normal interface substantially clearer: describe a task, inspect its proposed graph, make an explicit decision, execute the exact permitted scope, then see the outcome. Keep CLI and Advanced available.

Target: a validated demonstration by the end of October 4, 2026 in America/New_York. This is a delivery target, not evidence that the checkpoint is already complete. Ship a smaller verified journey if live-model/integration problems prevent the wider scope.

## Three implementation groups

1. Conversation and graph: one obvious entry point for a new request, visible input/context, readable agent responses and clarification, graph beside it, clear current task and resume behavior. Keep unnecessary technical forms collapsed. Do not advertise generalized durable memory when only checked task history is implemented.
2. Governed continuation: keep one task through intent/planning, review and the existing recipe/run services; remove panel hunting and repeated manual digest handling. Each user decision must bind the exact displayed scope. Read-only work must not require fabricated approval. Write operations still need explicit approval and validated results. A stored plan or reviewed history must never be treated as run authority.
3. Acceptance and demo: complete one reliable local data workflow from request through an actual result. Check denial, visible failure, recovery and artifact identity. Test backend, frontend build, desktop/half-width layout and CLI regression. Prepare README/demo instructions and a short recording for a LinkedIn draft.

Do not add a new lettered checkpoint for every visual tweak. Bundle related corrections into these groups.

## Definition of done for the demonstration

- A viewer can understand what to type and which input is used. Typed input paths and the file picker must agree, or the interface must clearly distinguish them. A missing input must be caught before execution.
- Read-only plans continue without manufacturing an approval record; write approval remains bound to exact scope.
- The graph shows the current proposal and actual run, not a generic fixture.
- The user can find the decision/run continuation without searching Advanced panels.
- A successful run shows a readable result and actual output/evidence.
- A denial remains denied; a failure is clearly distinguished from denial.
- Review/approval/history/recipe digests are checked by the backend, not copied manually by the user.
- Refresh/resume states and limitations are explicit.
- Existing CLI remains usable.

Use a bounded vector conversion or equivalent existing reliable workflow for the first demonstration. Use PostGIS only if its live prerequisites are ready; do not spend the demonstration deadline introducing another backend. Model response time must be measured honestly.

## Deferred scope

Pandas/tabular processing, arbitrary package discovery, general-purpose library function access, 3D operations, packaging for end users and generalized long-term memory remain later checkpoints. They should not delay this interface demonstration.

## LinkedIn readiness

Prepare the post when the demonstration is reproducible and the README explains current capabilities. Publish after acceptance, preferably with a short real screen recording and repository link. Posting on the target date is conditional on the working demonstration; do not substitute untested feature claims for a missed deadline. Describe local governed data workflows and precise current capabilities rather than claiming fully autonomous execution or superiority over other products.
