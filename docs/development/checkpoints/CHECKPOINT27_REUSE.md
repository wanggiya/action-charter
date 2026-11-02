# Checkpoint 27.2: focused recipe browsing and Planner adaptation

Extends [automatic retention](CHECKPOINT27_RETENTION.md) and the original
[checkpoint 27 plan](CHECKPOINT27_PLAN.md). This slice implements browsing and
bounded own-chat retrieval/adaptation, not checkpoint 27 as a whole.

## Current direction

[Planner-owned discovery](CHECKPOINT27_DISCOVERY.md) supersedes manual selection as
the normal reuse journey. Search/inspect are bounded read-only capabilities of the
existing Planner; initial matching remains a cheap fallback. Discussion shortcuts
are secondary under More actions, while manual composition remains in Advanced,
renamed Validate composition and open draft. The original slice below is retained
as implementation history, not a requirement to browse before working in chat.

## Two exclusive browser views

Reusable recipes defaults to **Recipe list**: compact rows with short summaries
and a small recorded-success/template label. Selecting a row opens its details;
versions, source runs and hashes belong under **Execution evidence**, not in the
browsing list. Templates and automatically recorded methods remain distinguishable.

**Keywords** replaces the list with keyword buttons only. Choosing a keyword
switches back to Recipe list with that filter visibly applied. **Clear filter**
removes it. Recipe details, search and Advanced authoring are absent from Keywords.
Returning to Keywords preserves the selected keyword for this panel session.
Existing material preferences and outline gradients apply in both views.

The optional **Advanced recipe authoring** disclosure remains in Recipe list.
It retains parameter inspection, manual composition and generalized fixture-tested
recipe preparation. Routine successful-workflow retention requires none of these.

## Retrieval and adaptation

Planner can retrieve up to three relevant methods from this conversation, within
an 8 KB example budget. Matching uses trusted tags/operation metadata rather than
another model or embedding service. **Use in Planner** explicitly selects a method
and prefills the message composer; the user supplies the new task and sends it.
The selection travels in a typed request field, with a clearable “Saved workflow
selected” indicator; no technical hash is inserted in the user message.
It neither generates a plan nor executes automatically on click.

Retrieved examples require current operation contracts, matching source-run/plan
identity and recorded-evidence hashes, successful completion, originating-chat
ownership and the current operation allowlist. The source is checked again after
model generation; changed examples are discarded rather than silently accepted.
Private examples are never retrieved from another conversation. A method hash in
user text cannot bypass scope or contract checks.

With Chat memory ON, relevant own-chat examples can be included automatically.
OFF disables automatic retrieval, while explicit Use in Planner can still include
the chosen own-chat method. The current workflow remains separate explicit context.
The Context sent to Planner disclosure shows the count/status for the last completed
request. No cross-chat memory is introduced.

Examples contain bounded historical operation arguments from the private source,
not old authority, raw outcome rows or transcripts. Credential-related fields and
old target bindings are removed; prior file suffix may describe output format.
The model must adapt to current inputs and requested semantics. CSV mechanical
outputs can be allocated safely; database targets/conversion scope must not be
invented. Existing explicit current-plan context is still supplied separately.

The result is an ordinary editable plan through the same schema/path/dependency/
policy checks. It is not direct replay. New writes require fresh exact authorization.
New data still needs actual execution/validation; past success is not proof of
compatibility or current artifact state. A proposal may use normal operations or
existing generalized templates when those better fit the task.

HTTP `/api/v1/planner/conversation` and existing CLI `planning-conversation-turn --request-file FILE --project-root DIR` use the same coordinator. No extra agent,
container, inference pass, installation or registration is required for retrieval.

## Timeout follow-up and request diagnostics

An offline measurement of the example cleaning request found **31,451 bytes** in
the old system/user prompt, with all operation schemas and repeated instructions.
For the same request, focused schemas, removal of duplicate rules and removal of
schema display titles reduced it to **24,666 bytes**. This measures prompt size,
not model latency or a demonstrated cause of the operator's timeout. History,
current plans and retrieved examples can increase later request sizes.

Automatic CSV requests receive detailed tabular schemas and existing-plan schemas;
explicit skill selections and mixed/unknown domains retain broader detail. The
full supported-operation allowlist and deterministic validation are unchanged.
If needed, the existing one bounded correction receives missing detailed schemas.
Only mechanical CSV target_path is optional in the planning schema: execution
arguments still require the safely allocated, validated path. JSON-schema field
names and constraints are preserved; display-only titles are removed.

Successful request receipts and model-error responses now report stage, bytes,
elapsed seconds, supplied schema count and operation/retrieval counts. The interface
shows those safe metrics, without exposing request contents, credentials or endpoint
values. A generation timeout and a correction timeout are distinguishable. Timeout
preserves the previous conversation/workflow and does not trigger an automatic
model retry or any processing execution. Timeout/reasoning configuration is unchanged.

This does not guarantee a small local model will finish. Actual Ollama latency,
model loading, reasoning and context limits still require laptop evaluation (27.5).
Do not weaken validation or claim context overflow from timeout alone.

## Frontend acceptance

1. Restart the existing launcher after updating backend code and refresh the page.
   Open a chat that has a new successfully executed CSV workflow from 27.1.
2. Open Reusable recipes. Recipe list shows summary rows; keyword buttons are not
   alongside it. Click Keywords: only keywords appear in the body, without the
   recipe list, search, details or Advanced controls.
3. Choose `csv` or `cleaning`: the list returns with the visible keyword filter.
   Clear it to restore other recipes. Select a recorded-success row.
4. Expand Execution evidence → Successful source runs to inspect the original
   outcome if desired. Use in Planner should prefill a method selection without
   starting a model call or an operation.
5. Add a request using another compatible temporary CSV (or repeat with fresh
   outputs), including the desired columns and missing-value strategy. Send once.
   Inspect the new source path, operation order and fresh outputs in the graph.
6. Open Context sent to Planner: verify own-chat method count and request metrics.
   Review and authorize the new exact writes, then Execute and compare actual rows.
   Old outputs/attempts must remain unchanged.
7. A new chat must not retrieve the prior chat's private examples. Chat memory OFF
   excludes automatic examples. Explicit own-chat selection remains possible.
8. If generation times out, keep the previous workflow. Report the stage, byte
   size, elapsed time and schema count from the response; do not retry old writes.

## Verification and remaining work

Temporary-fixture tests cover same-chat retrieval, explicit selection with history
OFF, other-chat exclusion, source tampering, skill restrictions, safe fresh output
allocation, timeout diagnostics and shared CLI adaptation. Browser acceptance uses
real CSV execution with fixture model replies to exercise exclusive views, filtering,
source inspection, adaptation to another CSV and fresh authorization. Actual local
model behavior is unverified. Verified **1,653 backend tests**, frontend
typecheck/build and **35 browser fixture groups**: 7 retention/reuse/navigation,
6 Planner/graph, 6 recipe/cancellation/recovery/restart, 10 private-chat/helper
and 6 full CSV groups. Browser groups reported zero page errors and zero
live-service calls.

Next: optional Critic annotation enrichment, supported outcome charts/maps, measured
laptop/model journeys and prototype/demo preparation. Existing Critic outcome
assessment remains separate; this delivery adds no automatic annotation model call.
No Git/publication or live-service operation is authorized by these instructions.
