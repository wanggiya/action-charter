# Checkpoint 27.2 follow-up: Planner-owned recipe discovery

Implemented after the [initial reuse slice](CHECKPOINT27_REUSE.md). Normal users
stay in Planner chat. The recipe browser is an optional reference, not a required
composition step. This does not complete all of checkpoint 27.

## Normal journey and roles

Describe the new task in Planner. The existing Planner role may search method
summaries/keywords, inspect promising definitions and adapt them, or use ordinary
registered operations when nothing fits. It asks only for genuine missing scope.
The result remains an editable proposal, with fresh review/authorization for writes.

The backend provides read-only discovery and deterministic schema/path/contract/
dependency/authority checks. It does not make the semantic reuse decision for the
model. No separate Builder, subagent, new container, library installation or broad
MCP execution interface is added. Historical success never grants new authority.

When a source is used, the reply identifies **Adapted from: …**. This is either
backend-expanded template composition or the Planner's reported adaptation from
an inspected/supplied source, not independent proof of generalized applicability.
Unknown/uninspected source claims reject through the bounded correction path.
Actual results still need execution and independent validation.

## Bounded discovery protocol

Planner can return a typed `recipe_discovery` request in the existing Reply JSON:

- `search`: query descriptive catalog metadata; at most five matches / 5 KB.
- `inspect`: exactly one `recipe_id` or eligible own-chat `method_id`; at most 8 KB.

The coordinator supplies a read-only result in the same conversation with the
model. No processing operation is dispatched. This JSON protocol uses the existing
OpenAI-compatible runtime, without requiring provider-native tool calling.

At most **two discovery exchanges** are allowed per user turn. They share the
existing 64 KB prompt budget. Including the final response and the existing one
schema/policy correction, a turn makes at most **four Planner model calls**.
Ordinary plans and the inexpensive initial shortlist need no discovery exchange.
Discovery is optional, not a forced extra model pass for every request. Calls run
sequentially; configured per-call timeouts/reasoning settings are unchanged.

A no-match result permits ordinary planning. Repeated discovery beyond its budget,
invalid mixed discovery/execution proposals or changed inspected definitions fail
without replacing the saved workflow. Model timeout is never automatically retried.
Metrics distinguish generation, after-discovery and correction-after-discovery.
Context sent to Planner reports discovery rounds and reported reuse sources.
Actual small-model latency/reliability remains laptop acceptance, not fixture proof.

## Visibility contract

Library-wide discovery covers built-in and explicitly registered catalog methods.
It does not pool private successful-run records or chat memory across conversations.
Catalog inspection exposes operation structure and current parameter requirements.
For registered definitions, descriptive text is generated from trusted operation
names rather than copying potentially private author text. Private fixed values,
paths and data literals become `current_binding_required` placeholders; original
fixtures and their rows are never sent to discovery.

A definition is available for direct automatic recipe composition only when its
arguments are declared parameter/step references, nulls or trusted schema enums.
Otherwise Planner must propose ordinary operations with current user bindings;
structural inspection is not permission to use concealed literals. This conservative
rule may exclude safe but non-enumerated constants from direct automatic composition.
Manual Advanced composition retains its existing explicit review path.

Own-chat success examples still require matching source-run/plan/evidence hashes,
current contracts, the current allowlist and permitted history scope. Chat memory
OFF excludes automatic private-method discovery, except an explicitly selected
own-chat reference. No other chat's bindings/evidence, credentials or old approval
enter the model through search or inspection. A guessed method ID cannot bypass
these rules. Inspected definitions/evidence are checked again before saving a plan.
Cross-chat memory remains deferred to checkpoint 30 or later with a fresh decision.

## Recipe browser

Recipe list and Keywords remain exclusive reference views. The normal list has no
Create workflow action. Select a summary to inspect applicability/evidence.
Optional discussion shortcuts are secondary under **More actions**; ordinary reuse
requires none of these clicks.

Manual parameter binding stays in **Advanced parameter inspector**. A queued
manual composition is under **Advanced composition**. Its action is named
**Validate composition and open draft**, including single-template composition.
It produces a validated proposal, never authorization or execution. **Advanced
recipe authoring** retains optional fixture-based generalization/registration.

## API/CLI parity

The existing POST `/api/v1/reusable-recipes` accepts `search` and `inspect`, using
`query`, `recipe_id` or `method_id` and an explicit originating `conversation_id`
where private examples are requested. Requests without chat scope expose catalog
metadata only. These are shared services used by the Planner coordinator and the
existing `reusable-recipes --request-file FILE --project-root DIR` CLI.

Conversational adaptation still uses the shared `/api/v1/planner/conversation` /
`planning-conversation-turn --request-file FILE --project-root DIR` coordinator.
No request JSON or manual registration is necessary in normal frontend use.

## Manual acceptance

1. Restart the existing launcher after the backend update and refresh the frontend.
2. Stay in a chat with an eligible successful CSV method. Send an ordinary request
   to clean a compatible temporary CSV, specifying columns and missing-value
   strategy and asking for fresh outputs. Do not select a recipe first.
3. Planner may use its supplied shortlist, search/inspect as needed, or propose
   ordinary operations. Check the new input, semantics and fresh targets. If reuse
   is reported, its source should appear in the message/receipt. Never treat that
   claim as evidence that the new data has already been processed.
4. Review, authorize exact writes and Execute. Compare actual rows and validation
   findings. Earlier outputs must remain unchanged.
5. Use a new chat to confirm that private prior-run examples are not inherited;
   built-in/sanitized catalog structures can still be discovered.
6. Browse Recipe list/Keywords as reference. Manual composition controls should
   require opening Advanced and should say Validate composition and open draft.
7. On timeout, retain the previous plan and report stage/bytes/elapsed time/schema
   count. Do not rerun old writes as a workaround. Discovery adds bounded possible
   inference time; local-model evaluation remains a required later checkpoint slice.

## Verification and remaining checkpoint work

Temporary-fixture regressions cover search/inspect/final-plan turns, no-match fallback,
private-literal redaction, own-chat/history/allowlist scope, request bounds, invalid
reuse claims, changed inspected contracts, timeout preservation and API/CLI parity.
Production-browser fixtures exercise ordinary-chat discovery/adaptation followed by
fresh authorization and real CSV execution, plus reference navigation and Advanced
compatibility. Model replies are fixtures; no live database/service is called.
Verified: `make test` — 1,663 passed; `make interface-validate` — typecheck/build passed; 35 browser fixture cases passed across CSV, private chats, Planner/graph, cancellation/recovery and recipe discovery/reuse. No live model was evaluated.

Remaining checkpoint 27: optional Critic annotation enrichment, bounded CSV charts/
geospatial previews, actual laptop/model evaluation, installation/demo examples
and prototype packaging/release preparation. No Git operation or publication is
performed by this delivery.
