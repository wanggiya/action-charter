> Current scope update: [single-dataset spatial expansion](INSPECTION_ON_SEND_EXPANSION.md)
> adds bounded vector/raster inspections and health revision `bounded-local-v2`.
> The original CSV pilot record below is retained as historical implementation detail.

# Checkpoint 28.2 — explicit bounded CSV inspection on send

Implemented slice, 2026-10-21. This delivers the CSV-first part of the
[inspection-on-send design](INSPECTION_ON_SEND_DESIGN.md), not the whole learning,
large-data, spatial-auto-execution or demo-readiness roadmap.

## Normal interface journey

1. Restart the existing launcher, refresh the page and create a new chat.
2. Open the gear beside Planner agent. Turn **Inspect on send** ON.
   It starts OFF and is remembered across chats/refreshes in this browser.
3. Leave skill selection automatic and Allow writes OFF. Send:

       Inspect sample_orders.csv. Return row count and column names. No writes.

4. The workflow and recorded Outcome appear without Authorize or Execute. Check
   six rows and columns `order_id`, `region`, `amount`, `customer_id`, `unused`.
   The source is `data/input/sample_orders.csv`; no data/output file is created.
5. Reload and reopen the same chat. Results belong to its saved plan/run; reload
   does not submit or execute again. Opening Outcome may be needed to view them.
6. With the mode still ON, ask for inspection plus selecting columns to a fresh
   CSV. Review the complete proposal: nothing, including its inspection prefix,
   runs automatically. Writes retain Allow writes → Authorize → Execute.
7. Turn the mode OFF and submit the first request in a fresh chat. It creates a
   proposal only; use Execute as before.

A network failure may occur after dispatch. **Check last submission · no retry**
reads the durable receipt/run; it never starts or replays a task. Pending receipt
identity survives page refresh in this browser tab. If the process stopped at an
uncertain stage without a run, inspect saved chat/history before deliberately
sending a new request. A missing receipt is not proof that nothing ran.

## Scope and bounds

Only the existing narrow, complete single-file metadata request contract can
qualify, and only `inspect_csv` for a CSV/TSV. Backend eligibility requires one
step, the exact supplied safe input, registered read-only effects and no
approval gate. Extra model operations are rejected through existing bounded
correction, not silently removed. A conservative explicit approval gate is
retained. Ambiguous, compound, spatial, database, remote, installed-adapter and
write requests keep the existing review/Execute path. Chat text cannot enable
writes, approve operations or confer authority through historical context.

This Linux-first slice uses the ordinary stricter table limits: **8 MiB source,
10,000 rows, 100 columns, 4,096-character cells and 64 MiB table memory**. The fixed
worker has a 30-second wall deadline, 10-second CPU soft limit, 2 GiB address-space
limit and no file-output allowance; response is capped at 16 KB. Existing metadata
and preview limits apply, with at most 20 preview rows × 20 columns. Full column
metadata remains separately bounded. These supersede the design's unimplemented
64 MiB source proposal. The table-memory check occurs after pandas allocation;
process limits are an additional ceiling, not a promise of 64 MiB peak process RAM.
This is not massive-data support or a general security sandbox for model code.
Only trusted fixed code runs, with a scrubbed environment and no generated code.

Safe bounded bytes are snapshotted before planning under the explicit submit
mode. Dispatch verifies the same content digest, chat revision, saved plan and
operation contract. The reader parses those verified in-memory bytes; replacing
the source cannot yield a successful stale/mismatched outcome. A changed source
requires a fresh submission. Oversized/invalid data is not automatically retried
or silently sampled as a complete count. Reviewed Execute retains its own reader
limits. Normal conversation/plan/run/evidence metadata is persisted locally;
“read-only” refers to dataset/external-service effects, not absence of app records.

## Architecture and compatibility

- `planner_submission` coordinates the existing conversation, plan storage,
  workflow preparation and durable-run services. New POST `/api/v1/planner/submit`
  explicitly separates submit from receipt reads. Existing conversation reads,
  turns and workflow APIs keep their meanings and do not start automatic work.
- `inspection_policy` provides deterministic eligibility, source/contract binding
  and a cancellable bounded worker launcher. `inspection_worker` invokes the fixed
  pandas reader/preview code. No extra LLM agent, model call for eligibility,
  dependency, container, MCP server or package installation is added.
- Additive `inspection_submissions_v1` records in the existing task SQLite store
  claim submission identity before inference, bind a preassigned run ID before
  dispatch and retain a bounded receipt. Maximum 200 receipts, 2 MB each, within
  the existing overall database limit. No eviction is automatic.
- Duplicate same-payload submissions read their existing receipt/run. Reusing an
  ID for different input rejects. Uncertain interrupted submissions are never
  replayed. Durable runs handle progress/cancellation; for this fixed read worker,
  cancellation also terminates the child. Writes keep existing semantics.
- A chat write transaction covers the last revision check and dispatch. Late
  frontend responses cannot replace a different chat or edited workflow. Lost
  responses can be reconciled from the preassigned run identity. This does not
  claim exactly-once execution under arbitrary filesystem corruption.
- API health exposes `inspection_on_send_revision: bounded-csv-v1`; incompatible
  running APIs are blocked before submission. Restarting the launcher is needed
  to load this code, not to enable writes routinely.
- CLI `planning-submit --request-file FILE --project-root ROOT` accepts the same
  typed `SubmissionRequest` and invokes the same policy/services. A submit request
  contains `action`, a 32-hex `submission_id`, `conversation_id`, explicit
  `inspect_on_send`, and a normal `turn` request. `action: read` needs only the
  submission/chat IDs. Old planning-only commands remain planning-only.

## Validation and limits

Regression coverage exercises exact output values, OFF behavior, historical gates,
changed sources, duplicate/mismatched submissions, cross-chat receipt rejection,
uncertain claims, unwanted PostGIS steps, write-prefix exclusion, timeout and
cancellation cleanup, concurrency, post-dispatch receipt failure and CLI parity.
Browser acceptance uses temporary project fixtures, actual backend services,
a deterministic model fixture and an isolated browser profile. It covers OFF/ON,
automatic skills, reload, complete write proposals and lost-response recovery.
Actual-model acceptance must be reported separately; fixture success does not
establish arbitrary request coverage or small-model reliability.

Remaining 28.2 learning acceptance is separate. See
[non-RL learning direction](LEARNING_WITHOUT_RL.md). Deferred Codex/DeepSeek harness
research remains deferred; no comparison or integration is performed by this slice.

### Recorded verification — 2026-10-21

- `make test`: 1,924 passed. Three additional concurrency/dispatch-reconciliation
  cases were subsequently included in the 20 passing focused submission cases.
- `make interface-validate`: passed typecheck/build; existing large-bundle
  advisory remains.
- Final submission browser journey: six cases passed, including dropped-response
  reconciliation. Existing execution browser journey: four cases passed. Both
  used real temporary backend storage/execution and a fixture model, zero live
  database calls and isolated browser profiles.
- Single real-model acceptance: `qwen3:4b-instruct`, reasoning `none`, JSON-schema
  output, automatic operation selection. One model call, 21,685 prompt bytes,
  180 completion tokens, 31.846 seconds model time and 33.902 seconds end-to-end.
  Correct three-row synthetic CSV metadata, no data writes/approvals, and a
  duplicate submission reused the same run without another model call. Receipt:
  `/tmp/actioncharter-checkpoint28-inspection-submit.json` (local, temporary).
  Reproduce with `scripts/checkpoint28_inspection_submit_evaluation.py --model`
  and an installed model name using the project Python environment.

The real-model check is one narrow acceptance case, not a benchmark, harness
comparison, measured speedup or learning improvement. Frontend result handoff
waits for committed saved-plan state through an effect rather than assuming
that asynchronous plan callbacks have already rendered.

## Operator clarification after manual acceptance

The user confirmed this slice worked and clarified that inspection on send is
intended for **all supported inspection types without writes**, not CSV alone.
[Expansion direction and acceptance](INSPECTION_ON_SEND_EXPANSION.md) record
vector/raster and later compatible multi-inspection support, a general preference
label and shared effect-based eligibility. This is a future requirement; current
runtime remains the CSV-first implementation described above.

UI follow-up: the preference is labeled **Inspect on send**. The description still states the current single-file CSV scope; vector/raster expansion remains unfinished. The composer footer no longer repeats the saved-plan status beside the selected chat.
