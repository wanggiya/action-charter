# Terminal workspace and chat workflow history — 2026-10-25

This completes the persistent terminal/history slice alongside the delivered interactive
[Outcome tables, groups, charts and percentages](COMPREHENSIVE_INSPECTION_DELIVERY.md).
It is not a claim of Codex feature parity or completion of the statistical-health task.

## Start and use the terminal

Keep the existing launcher/API running. From the checkout, start a second terminal:

```bash
./actioncharter
```

No Python command, new package download, shell-profile edit or shared browser cache is
needed. The executable selects this checkout's environment/source. A normal package
installation also provides the `actioncharter` console entry point on its environment's
PATH. This turn does not install a global executable. The backend remains the running
API on port 8765; its frontend can remain on 5173, and no browser page must be open.
Use `--api-url http://127.0.0.1:PORT` for another local API. No remote/proxy/redirect use.

Default on a POSIX TTY is a full-screen standard-library curses workspace: chat list,
conversation/result area, editable prompt, working status and scrolling. It makes no
new model selection and uses the running API's settings and project. Small/limited
terminals can use the persistent scrolling prompt:

```bash
./actioncharter --plain
./actioncharter --chat YOUR_32_CHARACTER_CHAT_ID
```

Normal messages continue the selected chat. Bounded explicit exploration may calculate
read-only findings; proposals do not execute automatically. Completed analytical messages
show their Overview immediately, rather than only saying that the message was sent.
Partial/failed evidence remains visible through the chat/history; a successful submission
is not itself proof of successful calculations or execution.

Useful commands (type inside the workspace):

```text
/chats                    list numbered chats
/open 1                   select a chat without copying its ID
/new                      start separate work
/refresh                  reload after frontend changes
/workflow                 current proposed operations and parameters
/result                   current recorded analytical overview or last run summary
/columns time_in_hospital recorded field statistics
/table                    recorded bounded rows
/chart age                terminal distribution from saved source counts
/groups age               explicit new age-only grouping
/groups age readmitted    explicit new combined grouping
/tablefields age readmitted  explicit selected-column read
/checks                   source hash/runtime/verification information
/history                  numbered workflow/analysis/view/run records
/view 1                   read a historical item
/current                  return to current chat without changing its draft
/continue 1               restore the selected version as a NEW draft revision
/receipt SUBMISSION_ID    check an uncertain chat submission, never resend it
/help                     full guide
/quit                     exit
```

F2 opens chats, F3 history, F4 Outcome. PgUp/PgDn scrolls output. Arrow/Home/End and
Backspace/Delete edit the current one-line prompt. Ctrl+D exits; Ctrl+C clears its draft.
Plain mode supports the same slash commands. This is a lightweight workspace, not a
shell, arbitrary Python console, full terminal code editor or streaming model-token UI.
No private terminal transcript is written outside existing project state.

### Explicit governed execution

Terminal operator controls use the same backend validation/review/authorization/run
services as the frontend. They are not tools that model text can invoke:

```text
/review                   inspect exact operations, arguments and affected targets
/execute                  explicitly start the reviewed current workflow
/run                      read its progress/outcomes; never restart it
/run RUN_ID               inspect a recorded run owned by this chat
/cancel                   request cancellation of that attempt
/writes                   show write availability
/writes on                explicitly enable availability; not approval
/authorize YOUR_NAME REASON  explicitly authorize the exact required operations
/execute                  explicitly dispatch after approval, when writes are allowed
```

Read-only workflows need explicit Execute, without an unnecessary approval record.
Writes still require allowed availability and exact authorization. Backend read-only
locks, changed sources/reviews, expired/mismatched approvals and one-active-run checks
remain authoritative. Availability changes affect the running API session, as the
frontend switch does. They do not grant a blanket permit. Natural-language messages
about authorization remain planning context, not these explicit operator commands.

Authorization is not carried between chats, historical records, restored drafts or
terminal restarts. A changed chat revision requires refresh before dispatch. An uncertain
start response blocks another terminal dispatch until the recent matching run is inspected;
there is no automatic retry, write repeat or resume. Quitting during a request can leave
server-side work running; recovery IDs or an execution warning are printed on exit.
Cancellation retains the backend's existing operation-boundary behavior.

## Historical workflow records

Each chat now has **Workflow history** in Planner. It lists:

- Workflow proposals at recorded chat revisions, including parameters/dependencies.
- Analytical sessions, including saved full-field profiles and scope.
- Explicit interactive table/group queries and their recorded results.
- Existing durable execution attempts whose conversation ID matches this chat.

Opening an item displays a labelled historical graph and, where available, the recorded
Outcome. Archived analytical grouping/table controls cannot start a new calculation. Execution
records use the existing hash-bound run explorer; explicit new artifact analysis remains
separate from opening a saved result. Chart/table
presentation within saved evidence remains usable. Execute/Authorize and graph editing
are unavailable in that historical scope. Current plan, unsent composer draft and execution state are not replaced by opening it. Return to current workflow
restores the previous graph. Async history responses are scoped to the selected chat.

**Continue from this version** is separate. It validates the selected proposal against
current installed contracts and restores proposal/analysis as a new revision of this chat,
retaining the transcript. A selected table/group view is restored atomically as well.
Historical calculations remain old evidence, not a new scan. New reads verify source
hashes, and any execution goes through normal fresh review/authority checks. Continuing
from a run is unavailable: choose a workflow version instead; run recovery remains separate.

Scriptable equivalents remain available:

```bash
.venv/bin/python -m geoagent_harness.cli chat history "$CHAT_ID"
.venv/bin/python -m geoagent_harness.cli chat history "$CHAT_ID" --entry "$ENTRY_ID" --json
```

### Storage and boundaries

```text
Frontend + terminal + scriptable CLI
                 |
         same loopback API
         / chat / analysis view / governed runs
                 |
      shared conversation coordinator
      current state + immutable snapshot references
                 |
   project planner-workspace/tasks.sqlite3
   - existing current chats/memories
   - chat_history_v1: owner, revision, time, kind, content references
   - chat_history_blobs_v1: content-addressed plan/analysis/view payloads
                 |
   linked durable workflow-state/interface-runs
                 |
   recorded graphs, outcomes, percentages and terminal views
```

Snapshots are written in the same SQLite transaction as the corresponding chat or view
update. Shared content is stored once, not copied for each revision. Hashes are checked
on read; entries are explicitly owned by one chat. Physical blob deduplication is not
cross-chat memory or retrieval. No model summarizer, knowledge agent, RL or new worker
container is added. The existing bounded database/storage contracts still apply.

At most 128 distinct history items per chat are indexed. Database size remains bounded
at 64 MB by the existing service; exhaustion fails explicitly rather than silently losing
history. Automatic export/pruning is not implemented. Run indexing examines the existing
bounded recent run-file inventory; legacy unlinked runs remain in Execution History,
not guessed into a chat. Existing run reconciliation may mark interrupted attempts;
it never restarts them. Snapshot reads may index the recoverable current baseline.

Earlier overwritten proposals/analyses were not previously versioned. This work preserves
future revisions and the recoverable baseline; it cannot reconstruct missing history.
Existing original data, plans, transcripts and run files are retained. No Git changes,
release publication or live PostGIS/GeoServer mutation is part of this work.

## Combined manual acceptance

1. Restart `bash scripts/start_actioncharter.sh`, refresh the browser, and open
   `./actioncharter` in another terminal. Start with read-only tests, writes OFF.
2. In the terminal use `/chats`, then `/open NUMBER` for your diabetes analysis chat.
   `/result`, `/columns time_in_hospital` and `/groups age readmitted` should show
   source-scoped facts and percentages. In the browser, reopen the Groups tab to load
   that saved selection. Counts/bases should agree.
3. Change grouping in the browser (age alone, then age/readmitted), then reopen terminal
   `/result groups`. Inspect the same saved result. No model call merely to view it.
4. In both interfaces open history, then an older grouped result. It should remain the
   older grouping after later edits; opening it must not scan or execute. In the frontend
   Execute is disabled; historical Apply grouping/Load selected columns are disabled.
5. Return to current. Check that your unsent frontend draft and current workflow remain.
   Continue from a saved workflow version deliberately; expect a new chat revision and
   no transferred approval. Send a new message in the frontend and inspect it in terminal.
6. In a separate new terminal chat, send `Inspect sample_orders.csv. Return row count
   and column names. No writes.` Use `/review`, then `/execute`. Inspect `/run` and
   `/history`; open that execution in frontend history. This reads the public sample.
7. Try `/view NUMBER`, then send a message or `/execute`: the terminal must reject action
   in historical mode until `/current` or deliberate `/continue`. A stale chat revision
   must fail safely rather than overwrite frontend work.
8. For write testing, use temporary fixture outputs only. Review exact targets first.
   Neither plain text nor opening history may enable writes, authorize or execute.

Automated verification includes isolated frontend↔CLI journeys, recorded percentages,
read-only historical Outcomes, restoration followed by a frontend message, digest/scope
rejection, fresh-revision/authority checks and a real PTY running `./actioncharter`.
The PTY executes only a read-only sample workflow in a disposable fixture API project;
write authorization payloads and uncertain dispatches are covered with test doubles.
Original diabetes data and live services are not changed.

Final verification for this delivery: `make test` passed **2,108 tests** with 13 existing
Rasterio warnings. Frontend typecheck/production build passed with the existing bundle
size warning. The combined browser acceptance passed with no page errors, including
historical grouped outcomes, workflow restoration followed by a frontend message and
CLI continuity. A real PTY ran the standalone entry through new chat, proposal, exact
review, explicit read-only Execute, run history/outcome, historical view and return/quit.
The focused history/task suite also passed after allowing its local fixture sockets.
