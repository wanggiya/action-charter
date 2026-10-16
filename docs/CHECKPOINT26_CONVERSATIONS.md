# Checkpoint 26.1 revision — one conversation, one task

The operator replaced the earlier multiple-task/shared-chat design with a simpler model: **each conversation is one task with private memory**. Changing from vector data to CSV within that chat preserves its transcript and current proposal; it does not require creating or selecting another task.

## Current behavior

- No New task title, task selector or cross-chat task linking. Normal New chat and saved-conversation navigation remain.
- A conversation's task identity is automatically its conversation ID. Its memory consists of the full persisted transcript, bounded recent excerpts and latest validated workflow.
- Memory stays within that conversation. A new chat starts with an empty transcript and no inherited plan or authority. Opening an older chat returns that chat's own state; it does not merge memories.
- Include recent chat messages OFF excludes previous messages from the model while preserving the transcript and current typed workflow. Saved chat history shows bounded excerpts; Context sent to Planner separates next-request choices from the last completed request.
- A subject change retains context. An explicit request to replace the workflow can propose CSV work instead of the previous spatial workflow. Ambiguous addition/replacement requests should prompt clarification.
- Validated/saved edits to this conversation’s own graph automatically update its remembered workflow without a model call. A different externally opened graph can be explicitly bound using Use current workflow in this conversation, after graph validation. Binding supplies planning context only. Switching chats clears workspace authorization and blocks transitions during pending edits/execution.

This is transcript/plan memory, not semantic summaries, indexed core facts, automatic corrections or automatic method extraction. An OFF-by-default [method-memory prototype](METHOD_MEMORY_PROTOTYPE.md) separately supports explicit selected-source method proposals and reviewed/unvalidated saves. Indexed summaries/corrections remain future single-conversation work. No cross-conversation memory service, sharing controls, vector index or background curator has been added.

## Storage and compatibility

`planner-workspace/tasks.sqlite3` stores conversation and private memory snapshots in one transaction. The `memories` table is keyed by conversation ID; the former `tasks` table remains untouched as historical records. Legacy JSON and old conversation snapshots remain readable. Adoption uses only the selected conversation's own messages and stored plan snapshot, never the former shared task's live history or current plan. Legacy JSON bytes stay unchanged after adoption.

Old `create_task` / `select_task` requests fail with an explanation. Explicit binding requires this conversation's own identity. Existing direct Planner turn callers may omit the new identity/revision fields; conversation revision checks still apply. Modern clients supply both. No operation is executed by memory read/save/bind.

Prototype bounds remain 128 records per table, 2 MB per record, 64 MB database and 100 messages per conversation. These are storage guards, not a measured laptop capacity claim. Full transcript archival, export/deletion and longer-conversation summarization are future work. Back up the SQLite store consistently or stop the launcher before copying it. Runtime memory is ignored by Git/container builds.

## CLI

```bash
.venv/bin/python -m geoagent_harness.cli planning-conversation-read CHAT_ID --project-root .
.venv/bin/python -m geoagent_harness.cli planning-tasks --project-root .
```

The legacy-named planning-tasks command lists persisted private conversation metadata only; it does not share context. `planning-conversation-bind-plan --help` describes binding a typed PlannerResult. The old planning-task-bind-plan alias requires task ID equal to conversation ID. Separate-task create/select commands are removed.

## Frontend acceptance

1. Restart the normal launcher and refresh. Planner should have New chat and the previous-message switch, with no task creation/selection controls.
2. Send: `Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.`
3. In the SAME chat, send: `Now replace the workflow with inspection of sample_orders.csv. Return row count and column names. No writes.`
4. Confirm the CSV proposal appears, both exchanges remain visible, and Saved chat history retains earlier vector context. No new chat/task is created by changing topics.
5. Refresh: the same conversation, its transcript and latest saved plan should recover without generation or execution.
6. Click New chat: memory starts empty and the previous workflow/authorization is cleared. Open the earlier saved conversation to return to its own history.

## Cross-conversation memory — deferred until checkpoint 30 or later

The operator deferred sharing for several checkpoints; [the dependency order](DEFERRED_CROSS_CHAT_MEMORY.md) reserves a fresh decision gate at checkpoint 30 or later. No sharing work is authorized in 26–29. Keep memory private by default. If the operator later chooses project-level reuse, share only explicitly selected preferences, decisions or reviewed methods with source/freshness links. Do not automatically pool transcripts: that can import irrelevant assumptions, private details and outdated data references. A relevance-filtered, explicit sharing mechanism is preferable to universal memory. This recommendation has not been implemented.

## Checks

Backend fixtures cover topic changes, private new chats, disabled linking, legacy/shared-record preservation, stale revisions, atomic rollback, independent conversations, redaction and CLI/HTTP controls. The private browser journey exercises same-chat vector→CSV planning, empty new-chat memory, reopening, explicit authority and real validated fixture CSV output. Model replies are fixtures; backend services are actual. Live-model responsiveness remains operator acceptance.

Identical generated workflow definitions can reuse the immutable saved artifact without modifying its bytes or importing its older request into a chat. New wording/model metadata stays in that conversation. The API marks reused definitions and whether exact result metadata was already stored. Reviewed-plan storage retains its strict full-result comparison. Reuse grants no approval/execution.

Validation: `make test` passed **1,530 tests**; `make interface-validate` passed. Four private-conversation browser groups passed, and the six-group existing CSV journey passed with an added check that validated graph edits update conversation memory. Browser models were fixtures; storage, policy, authorization and pandas validation were actual backend services. No live-service calls or page errors occurred.

## Chat context clarity

The switch is **Chat memory**. OFF excludes old messages, including the separate opening-message excerpt, while retaining the current workflow; it does not erase history. **Saved chat history** belongs only to this chat and is not generated knowledge or a collection of conversations. Saving messages does not require Authorize/Execute.

**Context sent to Planner** shows latest-message/current-workflow inclusion and the next request's history choice. Its last-completed-request receipt shows the actual history flag, included/omitted recent-message counts, opening-message inclusion and workflow inclusion. Changing the switch does not rewrite that prior receipt. Older records explicitly show unavailable fields rather than inferred values. Project guidance and registered-operation contracts remain separate from chat history.

Chat presentation: saved-history excerpts use role-labelled user/Planner bubbles; the saved-chat picker shows its summary in the selector. Disclosure headings override generic workbench top margins. Storage and authority are unchanged.

Workspace spacing: Chat history & context collapses as one group, with bounded scrolling when expanded. The message-area separator supports dragging and Up/Down arrow keys. The duplicate title below the chat selector is removed. The optional method-memory prototype is a separate explicit action; it does not run when viewing history or expanding these controls.

## Simple chat interaction follow-up

The normal interface now has only Chat memory for previous-message inclusion, remembered across chats in this browser. The method-generation/source/review/selection UI is removed; automatic notes are deferred, while the experimental API/CLI and saved records remain intact. Selecting a chat restores its own latest validated workflow directly from its snapshot, reusing or recreating a validated proposal artifact without model regeneration. No workflow/bookmark from another chat is selected, and no approval/execution is restored. Unsaved/manual graph work is protected during asynchronous recovery. The simple test sequence is in docs/METHOD_MEMORY_PROTOTYPE.md. Verified: 1,552 tests, frontend validation and seven private browser groups, including missing-artifact recovery without model regeneration.

## Workflow-only helper follow-up

Automatic method notes now has a separate OFF-by-default Settings opt-in: validated workflow structure → cached machine-generated/unvalidated notes → later own-scope Planner advice, behind an independent typed module. No manual source/review/selection UI is reintroduced. Chat memory still controls recent messages; chat restoration is model-free. Note failures preserve workflows. See METHOD_MEMORY_HELPER_DESIGN.md for acceptance/bounds and remaining evidence/lifecycle work; checkpoint 26 is not declared complete.

Helper follow-up verification: 1,570 tests, frontend validation and ten private browser groups passed with fixture models; local-model quality/performance remains operator acceptance.


### Schema-repair deferral regression

A null-plan reply asking permission to repair its own schema is not a successful clarification. The coordinator recognizes this bounded English deferral pattern and uses the existing single correction attempt. A repeated deferral reports failure and leaves the stored transcript/revision/workflow unchanged. Real missing-input questions remain valid; this guard does not guarantee semantic completeness of every model reply or detect every language/paraphrase. Restart the launcher, open the affected chat and resend the CSV inspection request. Expect a validated inspect_csv graph or an explicit failure, never authorization/execution.
