# Runtime write controls and checkpoint 27 demo gate

Recorded 2026-10-18; updated 2026-10-19. **Design history with an implemented 27.7 slice.**
See [current behavior, limitations and acceptance](CHECKPOINT27_RUNTIME_WRITES.md).
This document itself does not enable writes or authorize work. Overwrite remains
a separate follow-up.

Preserve the [checkpoint 27 plan](CHECKPOINT27_PLAN.md),
[ordered delivery plan](POST_CALCULATION_DELIVERY_PLAN.md) and historical
acceptance records. Add 27.7 without renumbering previously recorded slices.

## 27.7 — Runtime write availability

Problem: restarting the launcher whenever normal interactive work needs writes
interrupts planning and testing. Replace that routine interaction with a shared,
backend-enforced runtime control, keeping exact authorization and execution
separate. Do not implement permission solely in browser storage or model context.

### State and transitions

The policy service owns runtime enabled/disabled state, a monotonic policy
revision and an API session identity. It also reports any explicit administrative
restriction. API restart creates a new session, invalidating prior session-bound
authority. Ordinary startup defaults OFF; explicitly configured startup behavior,
including compatibility for --enable-write-tools, must be documented and tested.
Session state is not a remembered browser preference.

Use separate concepts for initial availability and an administrative read-only
ceiling. Do not interpret the current default-disabled setting as an irreversible
ceiling that makes the new switch ineffective. Exact configuration names and
legacy-flag migration need implementation review; do not silently weaken an
explicit deployment restriction.

Settings uses the existing slide-switch style, with a compact header status.
A typed request reads/changes server state and reports the confirmed revision.
Stale updates reject instead of overriding a newer decision. Protect mutations
through the existing local-origin/request protections; no model tool receives a
permission-changing capability. The switch makes no model call.

- OFF → ON permits requests for supported writes; it does not approve a workflow.
- Authorize binds exact plan/review/targets, expiry, policy revision and session.
- Execute rechecks those bindings before dispatch; lower-level write entry points
  must not bypass the same policy. Read-only inspection stays available while OFF.
- ON → OFF blocks subsequent write dispatches. Already dispatched work finishes
  or stops at its supported boundary, retaining validation and partial evidence.
  Do not promise immediate thread/transaction cancellation or rollback.
- Any actual policy transition invalidates pending write authority. OFF → ON
  cannot revive old approval. An idempotent unchanged-state request should not
  unnecessarily revoke authority. Serialize state transitions and dispatch checks
  so the supported operation boundary has a defined meaning.
- Record bounded policy/decision provenance without credentials. Nothing retries
  automatically because availability changed.

### Shared services, CLI and compatibility

Reuse registry effects, exact authorization, execution dispatch and cancellation
services. No new agent, container or MCP server is required. Planner can prepare
write workflows while writes are OFF; preparation is never permission.

Interface and CLI must use the same core policy/authorization contracts. A CLI
targeting the running API uses its session. Standalone CLI behavior needs an
explicit local session/permission contract; an unrelated short-lived process must
not silently grant the API permission or bypass its administrative restriction.
Inventory direct service/MCP/CLI write paths before choosing the integration.

Preserve stored plans, digests and historical evidence. Store runtime bindings in
versioned authorization/execution envelopes rather than changing operation-plan
content. Old evidence remains inspectable; legacy approvals cannot silently
satisfy the new session-bound execution contract. Define migration behavior and
error guidance before implementation.

### Measurable acceptance

1. Read-only inspection succeeds with writes OFF. A direct write request is
   blocked by the backend even if the UI is bypassed.
2. Enable in Settings without restarting; no model call, approval or output is
   created. Exact Authorize → Execute succeeds for a temporary fresh CSV target.
3. Disable after authorization: no later write dispatch uses that approval.
   Re-enable: fresh authorization is required. Restart: previous session authority
   remains unusable, regardless of the configured new startup state.
4. A mid-run disable prevents later write steps; the active operation's supported
   completion/cancellation boundary, validation and partial outputs remain honest.
5. Expired approval, stale revision, changed scope/target and locked policy reject
   clearly. Concurrent transitions cannot revive authority or dispatch twice.
6. Interface/CLI and applicable direct entry points share enforcement. Historical
   views remain readable without new execution. Existing launcher startup modes
   have documented compatibility and tests.
7. Run backend and frontend checks plus browser transitions with temporary
   fixtures. No live database/service mutation is needed for this acceptance.

## Overwrite — separate follow-up, not implied by 27.7

Keep existing fresh-output contracts for checkpoint 27 acceptance and the first
demo. A global switch cannot make currently unsupported replacement safe.
Later local-file replacement needs an explicit typed operation/mode, exact target
and current digest, reviewed replacement scope, and operation-specific backup and
publication behavior. A changed target rejects. Test collisions, failure and
recovery before enabling it. Database replacement requires separate contracts;
file backup is not database rollback. Scope/number that follow-up separately
after demo acceptance, without extending every operation implicitly.

## Remaining checkpoint 27 work and why

Delivery order is **27.7 → 27.3 → remaining 27.4 → 27.5 fixture evaluation → 28.1 → 28.2 → 29 → demo acceptance**.
Numbering preserves history rather than implying the new slice comes last.

| Slice | Purpose | Completion evidence |
| --- | --- | --- |
| 27.7 | Remove routine restarts for supported writes | Policy/session transitions and exact authorization pass the acceptance above |
| 27.3 | Ground optional Critic feedback in actual evidence | Provenance/applicability/limitations are explicit; disabled/failed inference never blocks baseline retention or changes deterministic status |
| Remaining 27.4 | Make actual output understandable | Artifact-linked bounded CSV chart and supported vector preview show correct values/geometry, limits and unavailable cases without model calls or live queries |
| 27.5 | Establish complete, repeatable behavior before unfamiliar data | Spatial, CSV and compatible combined journeys cover planning, review, authorization, execution, checks, results, refresh, retention/reuse and failure/cancel/recovery; measure failures as well as successes |
| 27.6 demo gate | Make rehearsal reproducible and choose suitable data | Accurate executable/scanned/unsupported capability list, setup requirements, prompts, expected results, limitations and operator acceptance instructions |

Use existing fixtures first. Record actual model/version/settings, calls, available
token usage, elapsed time, correctness and interventions; separate fixture-model
tests from actual local-model acceptance. Do not invent success-rate thresholds
or make a broader readiness claim from one passing example. Optional model
enrichment is not a requirement for ordinary successful execution.

The operator can identify candidate real data now. Before rehearsing with it,
check format, size, fields/CRS, rights/privacy constraints and the intended
question against supported contracts. Use fresh outputs. Live databases/services
still require explicit scope-specific permission. Installable-package
implementation follows chosen-data/demo acceptance. Operator revision
(2026-10-19) supersedes the earlier minimum-demo proposal: generated capabilities
(28.1), learning/RL (28.2) and advanced private memory (29) must be implemented
and validated before demo/real-data testing. Fixture-based checkpoint 27
evaluation continues first; no cross-chat permission is added.
Demo preparation does not authorize Git/publication/release actions.

## Later structure — preserve the learning experiment boundary

Keep Planner, Critic, optional helper, registry and deterministic execution; no
separate Builder reasoning agent is required. 28.1 proposes isolated adapter
acquisition and explicit promotion. 28.2 proposes an optional eligible-candidate
selector, potentially a contextual bandit: fixed baseline → shadow suggestions →
held-out comparison → opt-in only if measured benefit justifies it, with rollback.
Hard validation/authority constraints remain gates, not reward trade-offs.

Selection learning does not itself acquire operations, establish domain truth or
train Ollama weights. Start with isolated evaluation data or same-conversation
verified outcomes; no implicit cross-chat pooling. Domain correction/retrieval
remains 29; cross-chat sharing remains 30+ with a fresh decision. These later
experiments remain later numbered deliveries, but their implementation and
validation are now required before demo/real-data testing. This does not claim
that a learned selector improves results or that Ollama weights are trained.
