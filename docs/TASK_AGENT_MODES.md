# Manual task agent modes

Implemented 2026-10-26. This is an opt-in execution-coordination slice, not a claim
of reliable autonomous data science or learned domain knowledge.

## Structure and responsibilities

```text
Conversation settings: choose Single agent or Three agents
                         |
                Task coordinator (same chat only)
                         |
 Single: primary context             Three: separate role contexts
 plan -> work-order self-check        Planner -> Executor preflight -> Critic preflight
                         |                         |
             Typed policy and deterministic validation
                         |
       Read only: Execute / writes: Allow writes -> Authorize -> Execute
                         |
              Existing governed execution services
                         |
        Durable facts, validation evidence and partial failures
                         |
 Single: primary self-review          Three: Critic outcome assessment
                         |
            Saved task report, readable text and evidence JSON
```

The Planner constructs or revises the typed workflow. The Executor role reviews
the work order with an LLM; actual operations remain dispatched by existing fixed
services. The Critic reviews the plan and recorded outcome in three-agent mode.
Single mode assigns these reasoning responsibilities to one primary context;
its final assessment explicitly says self-review, not independent Critic review.
No Builder agent is introduced.

Both modes use the configured shared model sequentially. They do not start a model
or container per agent. Each role keeps at most three short context notes in the
same chat. Three-mode journals are separate, with explicit work-order/evidence
handoffs; single mode uses one journal. This is bounded task continuity, not
cross-chat memory, model training or automatic acquisition of new operations.

## Behavior and limits

- Choose the mode in the conversation gear menu under **Agent mode**. Existing
  chats without a choice retain their previous behavior. No automatic selector yet.
- The selection applies to subsequent planning. A reviewed plan and its run retain
  their captured mode. Switching modes starts fresh role journals; ordinary saved
  chat context remains governed by the chat-memory setting. Active execution blocks
  reconfiguration. Selecting a mode never runs anything or erases the current graph.
- Plan preflight can request a bounded correction. Invalid/unavailable model reviews
  are recorded as unavailable; deterministic checks still control acceptance.
- Existing narrow deterministic inspection paths can avoid model calls entirely.
  Not every inspection invokes all roles.
- Conversation text and model conclusions never authorize writes. Review identity
  binds the explicit owning conversation and captured coordination state. Existing
  expiry, target/source identity, one-attempt write claims and validation still apply.
- Outcome assessment follows execution and can finish slightly later. Reading,
  refreshing or downloading a report does not retry execution or invoke the model.
  A model failure preserves deterministic evidence and is reported as unavailable.
- Reports use aggregate recorded facts, not patient row previews. They describe the
  observed run, not current database freshness or clinical correctness. Existing
  private conversation/model responses remain in the local task store.
- **Download recorded report** saves readable text; **Download evidence JSON** saves
  structured evidence through a user-initiated browser download. These do not grant
  arbitrary backend file-writing authority. The legacy `generate_report` operation
  has separate PostGIS prerequisites and is unnecessary for this task report.

The coordinator allows at most six model calls and 180 seconds per planning turn,
with a 64 KB request ceiling; role reviews have a 15-second timeout and bounded
evidence. These are ceilings, not performance promises. Reports include observed
calls, prompt bytes, elapsed time and provider token counts. Missing token usage
is unknown, not estimated. Metrics cover coordinated calls; optional helper work
outside this coordinator is not included. Operation attempts count workflow step
dispatches, not every internal service/MCP request.

## Frontend validation

1. Restart the existing launcher normally to load the code. Use your established
   `.env`/secrets and PostgreSQL configuration; do not paste credentials into chat.
2. Open a new conversation. Open its gear menu and choose **Three agents**.
   Reload once and verify the selection remains. No execution should occur.
3. Follow [the real diabetes flow](DIABETES_REAL_TEST_FLOW.md) from inspection through
   selection, codebook decoding, groups, fresh PostgreSQL table and export. Keep
   original inputs unchanged. Use fresh output names and a fresh permitted table,
   for example `trial_three_01`. Review the actual proposal before authorizing.
4. Read-only work uses Execute. For writes, enable Allow writes, inspect the exact
   file/database targets, Authorize, then Execute. Authorization alone must not run.
5. In Outcome, expand **Task report**. Check captured mode, operations, deterministic
   validation, Critic findings/limitations and effort. Download text and JSON. If the
   model review is unavailable, it must say so without hiding the execution result.
6. Verify the reference: 5,000 sample encounters; 4,260 distinct patients; 506 repeated
   patients; three mapping fields each 5,000 matched/zero unmatched. The prepared
   database/export flow preserves all 5,000 rows and the expected 17 fields including
   its explicit marker. The separate grouped summary has 30 groups. Compare complete
   values with the documented oracle, not just preview rows. These are fixture facts,
   not hard-coded requirements for other datasets.
7. Start another chat, choose **Single agent**, repeat with distinct targets such as
   `trial_single_01`. Expect equivalent data/validation and **self-review** labels.
   Compare measured effort, findings and errors; do not assume either mode is faster.
8. Reopen each saved chat/run. Its workflow, captured mode and report should return
   without duplicate execution, new authorization or additional model assessment.

The terminal shares these controls through `./actioncharter`: `/mode three`,
`/mode single`, and `/report RUN_ID` (recorded JSON). Noninteractive equivalent:
`geoagent chat mode CHAT_ID three`. A mode change applies to the next planning turn.

## Automated evidence and remaining acceptance

- `make test`: 2,141 tests passed before final report-guard additions; focused mode
  tests cover journals, bounded corrections, preserved plans, own-chat bindings,
  missing token usage and inability to override failed deterministic execution.
- `make interface-validate`: frontend typecheck and production build.
- `node scripts/task_modes_browser_check.mjs`: both modes through real UI settings,
  fixture planning, authorized calculation execution, report and reload persistence.
  Uses an isolated browser profile and existing project-local browser installation.
- `.venv/bin/python scripts/task_modes_acceptance.py`: real 5,000-row sample and
  sectioned codebook, disposable PostgreSQL, both modes and full exported-row oracle.
  Its model is a deterministic fixture: three-mode four calls versus single-mode
  three calls on the authored successful path. Synthetic token usage is not a real
  model benchmark. Sources and live services remain unchanged.

Actual installed-model planning quality, longer tasks, comparative cost/latency,
automatic routing, flexible role assignment, parallel agents, domain learning and
server-scale isolation remain separate work. Complete this real-model comparison
before designing an automatic threshold from token usage alone.

## Inspection planning timeout follow-up — 2026-10-27

The real-model read-only sample request timed out at 120 seconds during Planner
generation with ten supplied operation schemas. This occurred before role reviews;
it does not establish a context overflow or an execution failure. Narrow explicit
read-only CSV analytical inspection now initially supplies only inspect_csv, retaining
its analysis arguments for full-file statistics. Other registered operations remain
available through existing validation/correction; mixed/action requests and existing
non-inspection workflows retain their broader scope. No timeout increase, automatic
retry, model replacement or substitution of a row preview for full-file analysis.

Restart the launcher, refresh, and send the same request in a new Three-agent chat.
Diagnostics should now report one operation schema for that request. Verify actual
analysis arguments and recorded sample results before comparing Single mode. A further
timeout needs model/runtime investigation; reduced prompt overhead is not proof that
the installed model can complete the request. Reopening historical outcomes does not
prove the timed-out submission succeeded; check its owning chat/run and source path.
