# Proposed 28.2 follow-up — bounded inspection on send

Status: original design, 2026-10-21. The bounded Linux CSV-first slice is now
implemented; see [delivery and acceptance](CHECKPOINT28_2_INSPECTION_SUBMIT.md).
The original proposal below is retained; its proposed 64 MiB source limit was
not adopted. Other slices and defaults remain subject to acceptance.
The user confirmed the latest inspection-only regression test worked. That is
manual acceptance of the existing proposal/Execute journey, not this new flow.

## Purpose and existing behavior

Today, sending a message asks Planner for a validated proposal. An ordinary
read-only inspection then needs a separate Execute click. Write workflows retain
Allow writes → Authorize → Execute. A narrow single-file metadata-request check
now rejects unrelated operations before saving a conversational proposal.

For an unambiguous bounded local inspection, combine submission and execution
without removing the recorded workflow. The graph becomes both an explanation
of the operation and a place to inspect its actual result. Broader workflows
still benefit from review before execution. This reduces interaction overhead;
it does not establish better model reasoning, learning or industry parity.

## Intended interaction

The composer will visibly say **Send and inspect eligible local files** when the
mode is enabled. Provide a simple preference to return to proposal-only sending;
keep it independent of Chat memory, capability acquisition and recommendations.
The final default requires acceptance of the first bounded slice. Do not silently
activate it during a software upgrade. The existing Enter/Shift+Enter behavior
stays consistent: the submit action, whether keyboard or button, has one policy.

1. Submit an inspection request. Show Planning, then Checking scope, then
   Inspecting if eligible; never display a result before execution finishes.
2. Show the validated workflow and source while execution runs. On completion,
   attach recorded metadata/preview and show it in the existing Outcome views.
3. Ambiguous requests ask for a concrete missing input. Schema/policy failures
   retain the existing single correction budget and preserve the prior workflow.
4. A valid proposal outside automatic scope stays a proposal. Explain why it
   needs Execute or authorization; do not run just its read-only prefix.
5. Writes retain Allow writes → Authorize → Execute. The agent may prepare a
   write plan and explain the next action, but cannot enable or approve writes.

Opening a chat, restoring a plan, refreshing, graph edits, changing preferences
or receiving a delayed response must never submit a new run. Historical results
remain labelled with the plan/source/run they actually describe.

## Backend eligibility and bounds

Eligibility is a backend decision about both the submitted request and the
validated complete proposal, never an LLM field or the word “safe.” Sending is
an explicit bounded inspection action only when the visible mode is enabled.
Context, saved messages and model output do not confer execution authority.

First implementation scope: one registered `inspect_csv` step for one explicitly
supplied local CSV/TSV under the permitted project input scope, with no approval
requirement or historical conservative approval gate. The complete request must
fit the narrow metadata-only contract. No compound/follow-up workflow is silently
replaced by a small inspection. General read-only SQL, remote sources, installed
adapters, generated capabilities, report creation, workflow export and every
dataset write are excluded. Unknown effects fail closed. Existing selected-skill
restrictions continue to apply. CSV success is followed by separate acceptance
for vector/raster inspectors; they are not automatically included because their
contracts say “read.”

Proposed initial limits, to verify before enabling: 64 MiB source size, 30 seconds
inspection wall time and at most 20 preview rows × 20 preview columns, with
existing stricter text/response bounds retained. Enforce byte/time limits inside
the actual reader/worker, not just a preflight stat. Large/wide inputs receive an
explicit bounded refusal or a reviewed execution option, never an unbounded
fallback or a misleading complete count. These numbers are proposed product
limits, not claims about the present inspector. Use the existing no-follow safe
path rules and recheck source identity at dispatch. A changed source invalidates
the prepared scope; ask for a fresh send rather than silently inspecting a
replacement. Do not read credentials or unrelated project files.

“Read-only” here means no dataset or external-service mutation. Normal local
conversation, execution and evidence records are still persisted. This distinction
must appear in the implementation contract and tests.

## Structural changes and responsibilities

| Area | Planned change and responsibility |
|---|---|
| `TextPlanner.tsx` and conversation client | Label submit behavior, send the explicit mode and submission identity, show progress and safe failures; disable duplicate sends while in flight. |
| `interface_api/conversation.py` | Keep proposal generation/one repair; return the exact validated chat revision and plan identity. Do not add execution to ordinary conversation reads/restores. |
| Shared execution-intent policy service | New small deterministic component evaluates request, mode, registered effects, source, gates and limits; returns eligible or a stable refusal reason. Reusable by interface and CLI. |
| `interface_api/workflow.py` and `workflow_runs.py` | Reuse preparation, final scope checks and durable execution. Add an explicit submit-and-inspect orchestration action that binds the submission to the validated proposal and starts only eligible runs. No new dispatcher or bypass. |
| Durable state | Add a versioned submission-to-chat/revision/plan/run binding and outcome state so a lost response can be reconciled. Reuse the project-local store; preserve old records. |
| `App.tsx`, graph and Outcome | Consume the returned run identity; show existing operation progress/results without an additional Execute click. Prevent late responses from replacing another chat's view. |
| CLI | Expose the same explicit inspection-on-submit choice and backend policy. Existing planning-only commands keep their meaning. |

Planner interprets the request and produces typed arguments. Deterministic
services decide eligibility, enforce bounds and execute. Critic remains advisory
on recorded evidence; it is not required to authorize or delay a basic inspection.
No additional LLM agent, model call for eligibility, container, MCP server or
library-function execution surface is planned. Acquisition and optional outcome
ranking remain separate; this work neither trains a model nor completes their
pre-demo acceptance gates.

Proposed flow:

    visible submit intent + request
      → existing Planner → typed/schema/scope validation
      → deterministic eligibility + source/contract/budget checks
      → exact submission binding → existing durable execution
      → recorded result → graph + Outcome

    ineligible valid proposal → existing review/Execute or write gates
    invalid/ambiguous proposal → correction/question, no execution

The orchestration action must not leave a race between a saved plan changing and
execution starting. Bind chat revision, plan digest, operation contract, source
identity and submission ID; revalidate at dispatch. Same-ID retries return the
existing state/run, while reuse with a different payload is rejected. Concurrent
submissions, cancellation, chat switching and startup recovery must be tested.
If a crash leaves dispatch uncertain, expose reconciliation/manual recovery;
never automatically repeat a run or claim exactly-once filesystem execution.

## Dependency-ordered implementation and acceptance

1. **Backend policy and inspection budgets.** Implement typed decisions and limits
   against temporary fixtures. Acceptance: the supported one-file CSV inspection
   qualifies; writes, DB/network reads, unknown adapters, multiple steps, extra
   approval gates, unsafe/changed sources and exceeded budgets do not dispatch.
   Compound “inspect then write” requests remain complete proposals.
2. **Submission orchestration and durable binding.** Reuse current execution
   services. Acceptance: one submission produces one observable run; duplicate
   requests return its identity; mismatched/revised scope rejects; simulated
   failure between save/start is recoverable without automatic rerun. Restore,
   refresh and chat reads start zero runs. Cancellation uses existing semantics.
3. **Composer, graph, Outcome and CLI integration.** Acceptance: with mode enabled,
   one send yields the expected CSV count/columns and recorded source without
   Execute; disabled mode preserves proposal-only sending. Writes still require
   all existing gates. Errors preserve prior results with their provenance;
   delayed results cannot cross chats. CLI and interface agree on eligibility.
4. **Complete regression and local-model acceptance.** Run `make test` and
   `make interface-validate`, then browser journeys using temporary data/profiles.
   Exercise automatic skill selection, adversarial extra PostGIS/report replies,
   failed correction, double submission, reload and source changes. Repeat the
   ordinary CSV journey with the user's installed model and report timing/failures
   separately from fixture results. Only then consider the initial default and
   separate bounded vector/raster acceptance.

Update delivery/status documents with measured results after implementation.
Do not claim these proposed cases already pass. No Git/publication, dependency
installation or live database/service mutation is required for this design.

## Product value and subsequent checkpoints

This path aims to make routine inspection faster while retaining typed operations,
source provenance, editable graphs, durable outcomes and controlled writes.
A stronger model or open-source reasoning framework can replace/improve the
Planner but does not substitute for these contracts or verified outcomes. No
specific third-party framework integration is decided here.

Keep this inside the current 28.2 interaction/reliability follow-up. It does not
renumber or complete 28.2 learning evaluation, 28.3 visualization expansion,
29 private domain knowledge or later cross-chat work. The existing pre-demo
gates and packaging-after-data/demo-acceptance order remain in force.
