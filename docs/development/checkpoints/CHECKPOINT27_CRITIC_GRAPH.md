# Checkpoint 27 — advisory Critic branch

Implemented 2026-10-19 as a focused evidence-visibility slice. This does not
complete optional recipe enrichment, laptop evaluation or authorization UX work.

The current recorded workflow shows `Recorded outcome → Critic review · advisory`
as a secondary dashed evidence branch when an assessment was requested. The
branch is a display projection, never a saved plan step, executable dependency,
recipe operation or authorization gate. Existing graph appearance materials apply.

Review states are Waiting, Reviewing, Reviewed, Deferred and Unavailable. A run
with no requested assessment has no Critic node. Execution status and independent
operation validation remain separate: Critic failure cannot turn a successful
execution into a failed execution, or a failed execution into a success.

Selecting the node shows the recorded summary, expandable findings/limitations,
optional unvalidated procedure suggestion and assessment provenance. The panel
identifies the exact run, plan digest, model and evidence digest when recorded.
Opening or refreshing reads records; it neither calls the model again nor runs
operations. Pending recorded reviews reconnect read-only polling after reload.
History can select the matching run and open its Critic branch. Chat/plan changes
and draft edits cannot inherit an unrelated assessment. No new backend agent,
container, assessment retry or authority is introduced.

## Manual acceptance

1. Refresh the running interface. In a new chat send: `Inspect sample_orders.csv.
   Return row count, column names and a small preview. No writes.` Use the
   existing synthetic fixture under `data/input`, not private or live data.
2. Confirm the proposal contains CSV inspection only. Execute the read-only
   workflow; it requires neither enabling writes nor artificial write approval.
3. Close the Outcome panel to inspect the graph. A requested review appears
   below the recorded outcome with a dashed connection. Execution may be
   completed while the review is still Reviewing.
4. Select Critic review. Check the run identity, summary, limitations and
   Assessment provenance. A missing/failed model assessment should say
   Unavailable while execution evidence remains available.
5. Reload or switch away and return to the chat. The matching recorded branch
   should restore without executing again. Execution History → Workflow runs →
   select this run → View Critic review in graph opens the same record.
6. Begin a graph edit. The draft must not claim the original recorded Critic
   assessment. Old runs with no requested assessment correctly show no branch.

Local model availability/latency is not established by fixture browser tests.
Unavailable provenance fields in older records say Not recorded.

## Automated checks

`make test`, `make interface-validate` and
`corepack pnpm@10.17.1 --dir interface browser:test:27-critic`.
Verified: 1,784 backend tests, frontend typecheck/build, seven Critic browser
cases and 17 calculation/write-control regression cases passed.
The seven Critic browser cases use actual temporary CSV execution/storage with fixture
Planner/Critic responses, including held review, model failure, reload/history,
scope changes and non-executable graph projection. Deferred/not-requested states
use read-response fixtures. Browser profiles/data are isolated from normal caches.

Backend tests isolate repository-based legacy policy fixtures from a running
operator API's ledger. Approval authority binds to the project owning approval
storage; a separate registry root cannot supply another project's write session.

## Development hook-update regression

A running Vite session previously retained App's hook slots when the plain
TypeScript `usePlanRun` gained its review-polling effect. This reproduced React's
hook-order warning at slot 211 and broke authorization. The hook itself is
unconditional; the stale hot-update state caused the failure. Production-build
browser tests had not exercised this development-only update path.

Vite now fully reloads when a source `use-*.ts` module changes. Normal component
Fast Refresh remains available. Saved chat/workflow context restores; transient
UI state and unsaved edits may reset. No authorization or execution is restored
automatically. For an already broken tab, hard-refresh once (Ctrl+Shift+R).

`corepack pnpm@10.17.1 --dir interface browser:test:27-hook-refresh` starts an
isolated real Vite server and backend, simulates the older hook gaining the
effect without editing workspace files, checks saved workflow restoration and
records exact authorization. Both development cases pass. It asserts no React console errors, no run starts
and no output files. Models/data/profiles are fixtures; normal browser caches
and the operator's API are not used.
