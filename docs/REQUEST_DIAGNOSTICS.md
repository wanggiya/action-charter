# Durable request diagnostics — 2026-10-29

## Problem and delivered behavior

Failed first submissions previously retained only a fixed “Submission stopped”
finding. Detailed error/usage diagnostics sent to the browser could be lost on refresh;
a new chat could fail without entering the saved-chat list. This prevented a reliable
retrospective diagnosis. Old missing metrics cannot be reconstructed.
Advisory review requests for revision now have their own `planner_review_needs_revision`
error category rather than being incorrectly labelled deterministic operation policy.

A content-free telemetry service now records submission and model-call intervals in
the existing project-local `planner-workspace/tasks.sqlite3`, table
`request_diagnostics_v1`. Records start before model dispatch and finish on success
or failure. Context variables bind chat/submission and role/phase; nested different
chats remain separate. Background workflow workers with chat identity have their own
interval and record actual workflow status separately from request completion.
Failed first chats remain discoverable, using the existing task title when present
or “Unfinished request · diagnostics available” when no chat content was saved.
Their prompt is not copied into telemetry. SharedModelClient captures
actual calls; custom clients that bypass it have no fabricated call/token measurements.
The existing model configuration diagnostics module remains separate.

Recorded fields:

- Chat/submission/call identities, parent identity, timestamps, status, role and phase.
- Model identifier, effective request timeout, output token cap, format/reasoning mode.
- Prompt-message and response-schema bytes (not a token estimate); reported input and
  output tokens; finish reason. Missing usage remains null/unknown, including timeouts.
- Duration, API-process CPU seconds, start/end and sampled peak API RSS, minimum sampled
  system available memory. Samples every 0.5 seconds, no full sample series retained.
- Safe failure code and numeric diagnostic fields, never raw exception text. Transport,
  model structure, planner policy and process interruption remain distinguishable.
- Submission dispatch/run identity and workflow status when known. Completing a model
  call/request does not prove a valid plan, successful operation or approval.

Worker-process, Ollama-model RAM and GPU/VRAM readings currently remain **unknown**.
API RSS is process-wide, including concurrent work; sampled peaks are not exact peaks
or isolated per-chat allocation. System available RAM is machine-wide. CPU seconds
also include concurrent work. No extra provider polling or model call collects metrics.
These observations cannot establish an OOM or context overflow by themselves.

Records exclude prompts, dataset rows, model response bodies, endpoints, credentials,
source paths and schema content. Exports still contain technical IDs and model names.
Retention keeps up to 600 finished intervals and their calls, plus at most 6,000
finished calls; active records are retained separately. Reads return at most 100 recent
records for the requested chat, with totals explicitly scoped to those records.
The existing 64 MB SQLite storage ceiling still applies. If collection storage fails,
execution is not retried, approved or changed; the parent record marks incomplete
collection when it can still be saved. Exports are manual local downloads.

Where process-owner checks are available, a started record owned by an exited/replaced
process is presented as interrupted on read. Unknown ownership is not assumed dead. An alive process with unfinished work remains started: a read does not assume a
crash or replay anything. Historical approvals/context/model text never grant authority.

## Access and manual validation

1. Restart the existing launcher with `bash scripts/start_actioncharter.sh`, refresh
   port 5173 and use the normal configured local model.
2. In a new chat send: “Inspect records.json. Describe numeric x by region. No writes.”
   Use the supplied flat JSON fixture under data/input, or a known available CSV.
3. Open **Request diagnostics** in the Planner panel. Expand the submission and model
   call. Inspect model, phase, elapsed time, timeout, token cap, request/schema bytes,
   reported tokens and sampled memory. Opening/refreshing this panel never retries.
4. **Export diagnostics JSON**, reopen it and verify it contains metrics and identifiers,
   not your request text/data rows/model reply/credentials. Token counts are unknown if
   the provider did not return them; RAM should not be labelled as model allocation.
5. Refresh the page and reopen the panel. Records persist. For a failed request inspect
   the exact error code; changing authorization cannot repair malformed model output.
   Earlier failures have no retroactive diagnostics. Use a newly recorded attempt.
6. Switch chats: only that chat's records appear. A failed first request can be reopened
   from the saved-chat selector under its existing task title or generic diagnostics title.
7. Terminal workspace: `/diagnostics`. CLI equivalent:

   ```bash
   .venv/bin/python -m geoagent_harness.cli chat diagnostics CHAT_ID --json
   ```

   Both use POST `/api/v1/planner/diagnostics` with a validated conversation identity.
   Export/display are read-only metadata operations; no model/source scan/data execution.

## Planning reliability and measured reproduction

Existing focused inspection planning and single targeted schema correction remain in
use. No unvalidated proposal, fixed fallback workflow or silent sample is accepted.
No automatic timeout retry was added. Review calls previously had a hard 15-second
cap despite measured local model calls of 35–53 seconds. Advisory review now has a
60-second cap, further bounded by the configured model timeout and the unchanged
180-second/six-call coordinator budget. It adds no attempts or execution authority;
phase timings/failures are visible instead of silently treated as successful reviews.

`planner_diagnostics_evaluation.py` submits the full-file inspection question from the
previous manual instructions against qwen3.5:9b in a temporary project, reasoning none,
120-second timeout, 1,536-token output cap. It proposes only; no operations execute.
The measured run returned one inspect_csv proposal: 12,871 message bytes, 4,891 schema
bytes, 2,835 input / 252 output tokens, 52.872-second model call. Observed Python RSS
was about 202 MiB; minimum sampled system available RAM about 5.0 GiB. Ollama memory
was not measured. Original missing failure details remain unknown, and this successful
reproduction does not certify every future request or identify the old failure.
These measurements are evidence for debugging, not a controlled performance benchmark.

## Checks

Regression coverage includes durable timeout with exactly one call, unknown tokens,
invalid transport response versus later schema rejection, privacy exclusions, nested
chat isolation, bounded retention, storage failure, interrupted owners, phase tagging,
existing configuration diagnostics and role authority/budgets. Isolated browser tests
exercise JSON export/CLI parity, a real backend fixture timeout, recovery after refresh
and zero execution replay. No live database, browser profile or model settings are
changed by these tests. Complete data/JSON/PDF journeys remain in
[FULL_DATA_WORKFLOW_ACCEPTANCE](FULL_DATA_WORKFLOW_ACCEPTANCE.md).


The subsequent Single-mode full-file selection experiment with the 60-second review
cap failed after bounded policy correction (no database connections). Its planner
correction returned in 34.869 seconds; total effort was 175.547 seconds. Therefore
this allowance is not claimed to solve role-mode reliability or complete F5. The prior
15-second review failures and the new experiment remain evidence of an open gate.
A failed request must be inspected by category/phase rather than assumed to be RAM,
context length, or missing user authorization.

Verification: `make test` passed **2,237 tests** with 13 existing spatial warnings;
interface validation passed with the existing bundle warning. Browser/CLI/PTY tests
passed with zero page errors, including failed-request recovery/export after refresh.
Subsequent targeted API/privacy/budget/configuration checks cover the final safe error
classification and missing-resource behavior. No live databases, personal browser
profiles, model installation/configuration or Git mutation were used.

Final telemetry/conversation inventory regressions: **53 passed**. The final browser
journey also confirms failed chats remain in the bounded recent selector; meaningful
existing task titles are preserved and empty failed chats get a diagnostics label.


## Inspection timeout and panel follow-up — 2026-10-30

An actual failed generation was retained: 22,605 message bytes / 5,985 schema bytes,
120.0765-second timeout, qwen3.5:9b, 1,024 output-token cap and no explicit reasoning
setting. API sampled peak RSS was 220,831,744 bytes (~211 MiB); minimum sampled system
available RAM was 3,745,951,744 bytes (~3.49 GiB). Ollama/model/GPU memory was not
measured, so these observations neither establish nor rule out model-side pressure.
They do not justify requiring users to close every Chrome tab.

The wording “numerical statistics” was not recognized by the analytical-scope test,
and simple inspections without the older quality keywords could stay on the larger
general instruction profile. Numeric-summary wording now preserves typed analysis
arguments, and eligible single-inspector requests use the existing focused profile,
including metadata-only requests. This changes supplied instructions/schema scope,
not deterministic validation, execution authority, or stored workflow semantics.
Model defaults are not silently changed. Existing explicit reasoning settings remain
operator-controlled; diagnostics now display the sent effort or “Provider default”.

The diagnostics disclosure was positioned before a long error block in a fixed-height
panel with hidden overflow. Failures now have **View request diagnostics** directly
inside the error message. It opens the disclosure and scrolls to it. Diagnostics and
error details have bounded scrolling; the Planner panel can scroll rather than clip
its controls. Existing local JSON export and no-retry behavior are preserved.

After updating, stop the old launcher and restart normally, refresh port 5173, then
repeat the inspection. If it fails, click View request diagnostics and export before
retrying. For a compatible installed model, an explicit comparison can be launched as
`MODEL_REASONING_EFFORT=none bash scripts/start_actioncharter.sh`; this is an optional
operator setting, not a claimed universal timeout cure. Do not run two launchers.


Measured comparison after the routing fix, on the same installed qwen3.5:9b,
12,829 message bytes / 4,891 schema bytes and 1,024-token output cap:

| Explicit reasoning setting | Result | Model interval | Reported tokens |
| --- | --- | --- | --- |
| Unset/provider default | Timeout, no execution | 120.1398 s | Unknown |
| none | One inspect_csv proposal, no execution | 38.5694 s | 2,827 input / 230 output |

Runs were sequential on a shared local runtime, not an isolated performance benchmark.
The result supports an explicit-none comparison for this task, not a claim that the
provider's internal thinking state was observed, every timeout is solved, or Chrome
must be closed. No launcher settings or model defaults were changed automatically.

2026-10-30 verification: `make test` **2,244 passed** (13 existing spatial warnings);
`make interface-validate` passed with the existing bundle-size warning. Isolated
browser/API/CLI/PTY journey passed with zero page errors, including the failure-message
diagnostics shortcut, export and refresh without replay. No live database changes,
secret/environment-file edits, Git actions or model-setting changes were performed.

## Project reasoning settings and analytical report contracts — 2026-10-30

Settings → Model service now has **Reasoning effort** and **Use reasoning setting**.
Choices: launcher/environment, provider default, none, low, medium, high. The selection
is saved in the project SQLite database with optimistic revision checks. New requests
use it without restarting the launcher; in-flight API/conversation requests keep their
starting snapshot. Backend conversation entry points also apply the project preference;
background requests inherit the starting model context and record independent telemetry.
The shared client sends the selected value. This does not grant execution authority,
change installed models/endpoints/secrets or automatically retry failed requests.
Supported effort levels still vary by provider/model; no silent fallback is added.

The failure “generate_report is missing required arguments: task_id” occurred after
model output, before dispatch. Analytical readiness/statistical reports are derived
from recorded inspection evidence and displayed in Outcome → Report, with local
Markdown/PDF export. The separately registered legacy generate_report operation is
an evidence-file step whose existing policy requires prior PostGIS validation. It is
not a primitive for constructing a CSV quality report. Adding PostGIS steps merely
to satisfy that legacy path would be wrong.

Ordinary table report requests now focus on inspect_csv, keep typed analysis fields,
explain derived report availability, and exclude the legacy evidence operation from
structured decoding. Backend coverage also rejects an unrequested evidence step if
a client bypasses structured decoding; one existing correction can repair the proposal.
No invalid/unrequested step is silently executed, removed from an approved workflow,
or excused by write permission. Existing report steps are preserved in revisions.
Explicit legacy evidence-file requests bind a missing task_id from trusted current
conversation/task identity before review. Prior validation and exact write approval
requirements remain unchanged; binding is not approval or report execution.
Generic policy error guidance no longer asks users to supply internal approval flags.

Manual check after updating/restarting the API once:

1. Start normally: `bash scripts/start_actioncharter.sh`.
2. Settings → Model service → Reasoning effort → **None · no thinking** →
   **Use reasoning setting**. Close/reopen Settings and confirm it persists. No further
   restart or environment prefix is needed for this selection.
3. New chat: “Inspect test/diabetic_data.csv. Return row count, column names and
   numerical statistics for time_in_hospital. Provide a data-quality report. Use the
   complete file. No writes.”
4. The proposal should contain inspection/typed analysis, not generate_report or
   unrelated PostGIS nodes. Inspect diagnostics: reasoning none; recorded phases and
   any bounded correction are visible. Do not authorize extra writes to fix a plan.
5. Execute the read-only plan if inspection-on-send is off, then open Outcome → Report.
   Reopen saved results and export Markdown/PDF without workflow replay.

Actual-model report-request check returned one inspect_csv proposal, no data execution,
after one bounded correction: generation 66.7773 s (2,888 input/237 output tokens),
correction 37.1815 s (3,499 input/194 output tokens). Model qwen3.5:9b, reasoning none,
1,024-token output cap, temporary full-source copy. This demonstrates that case, not
one-shot or universal model reliability. The isolated browser test also exercises an
incorrect extra report step repaired to read-only inspection and live Settings persistence.

Final reasoning/report verification: `make test` **2,248 passed**, 13 existing spatial
warnings (525.55 s); interface validation and isolated browser/API/CLI/PTY passed.
The browser verifies persisted Settings reasoning and automatic repair of an incorrect
extra report step to read-only inspection, with no execution replay. Decoder regression
coverage confirms unrelated calculation allowlists remain compatible. Source data,
live databases, environment/secrets files and Git staging/publication were untouched.

## Execution and outcome-review distinction (2026-11-02)

Diagnostic phases now end `executor / execution` at operation completion; standalone
post-run model calls are `critic / outcome_review`. Workflow-processing records link
to the durable run and separately expose workflow status and review status/error/budget.
The latter contains only status metadata, never review prose or findings. Model-call
records also carry the run ID, actual timeout, timing and usage. Processing elapsed time
includes review; the durable run's timestamps remain the source for execution duration.

A completed inspection followed by a model timeout therefore remains completed, with
Critic review unavailable. A genuinely failed execution remains failed regardless of
review. Invalid review output is unavailable, not successful execution verification.
No diagnostic read or timeout-setting change retries a review or an operation.
Historical records are not rewritten: the UI explains that old `executor / workflow`
labels can include post-run review. Consult the linked workflow status.

Settings → Model service → **Critic outcome review timeout** saves the standalone
review cap per project (integer 5–180 seconds; unchanged default 15). It takes effect
for future requests, without launcher restart; active request settings remain pinned.
The actual call can be shorter if the model request timeout or effort budget is lower;
Request diagnostics records the actual call cap. This setting does not change planning
timeouts or coordinated Single/Three task-report budgets. It does not approve work.
The existing standalone review response cap remains 1,024 tokens.

API clients can POST `/api/v1/models/review-timeout` with `seconds` and
`expected_revision`; stale settings return 409 and foreign origins are rejected.
The model catalog includes `review_timeout` with seconds/revision/source. No model
call or execution occurs when saving settings. Storage uses the same planning SQLite
helper, including the opt-in P0-2 workspace foundation.

Manual validation after loading the updated code:

1. Restart the usual launcher once and refresh the browser.
2. Open Settings → Model service; confirm the Critic outcome-review timeout. Optionally
   choose 30 or 60 seconds, Save review timeout, close/reopen Settings and verify it.
   A larger budget is not a guarantee that the local model will finish.
3. In a new chat inspect sample_orders.csv without writes, then Execute only if the
   read-only inspection has not already run on send.
4. Open Outcome and Request diagnostics. The workflow's completed/failed status and
   Critic's status must be separate. New standalone review calls say critic/outcome_review;
   a timeout shows the call cap and leaves the successful inspection result available.
5. Refresh/reopen history: no new workflow attempt or review call should be created.
   Changing the timeout does not revisit an already cached unavailable review.

Tests use mocked HTTP/model responses and temporary output files. They cover review
success/caching, timeout, malformed output, genuine operation failure, no execution
replay, status-only telemetry, bounded/revision-checked configuration and request pinning.
The browser journey verifies settings persistence and existing read-only execution/history.
No live model or database acceptance is implied by these fixture checks.

Final verification for this slice: **2,275 backend tests passed**, 13 existing spatial
warnings, 531.45 seconds. Interface validation passed. The isolated browser/API/CLI/PTY
journey passed with zero page errors; settings persistence was exercised against the
real temporary API, and the exact review-timeout rendering used a labelled diagnostic
response fixture. Backend tests used mocked model HTTP to exercise actual worker/review
status separation. No live-model quality/latency or live database acceptance was run.

## Read-only inspection wording (2026-11-02)

The request `Run a new read-only inspection of sample_orders.csv` previously missed
both the exact metadata parser and the narrow inspector schema recognizer. It entered
general table planning with 12 operation schemas; the recorded failed submission had
no workflow run. The model returned an unsupported field after one correction. That
failure is a planning/schema failure, not an executor/Critic timeout or evidence of RAM
exhaustion. The exact unexpected property was not retained in private diagnostics.

A shared normalization now recognizes the explicit `run/perform [a] [new] read-only
inspection of` lead-in (optionally `please`). All consumers still match the entire
metadata request: plan construction, narrow schema selection and input-path binding
use the same text. Additional transformations, instructions or unsupported metadata
remain outside this closed route; they are not stripped. Existing safe path checks,
format-specific fields, allowlists, batch limits and duplicate-submission protection
remain authoritative. This is not general natural-language understanding.

Original user text stays unchanged in persisted chat/provenance. For this exact request,
the normal submission path creates a typed inspect_csv proposal without a planning
model call. Inspection-on-send OFF still means proposal only; ON permits only the
existing eligible read-only scope. Critic review is separate and may call a model after
execution; zero planning-model calls does not promise zero model calls overall.

Validation: restart the usual launcher once, refresh, and submit the exact sentence
above in a new chat. Expect one Inspect CSV operation for data/input/sample_orders.csv,
not a 12-schema planner request. With inspection-on-send disabled, click Execute after
reviewing the proposal; otherwise inspect the recorded outcome. Reopening a submission
must not create another run. Existing failed receipts remain historical and are not
silently retried. No write authorization or storage change is needed.

Temporary-fixture tests cover enabled/disabled send policy, source identity, CSV/vector/
raster recognition, unsafe paths, unavailable operations, additional-clause rejection
and duplicate receipt reuse. The isolated browser journey uses the user's actual wording
and reads the saved state back through CLI to assert deterministic_inspection and zero
planning calls. This proves the route, not general small-model planning reliability.

Final wording-fix verification: **2,287 tests passed**, 13 existing spatial warnings,
538.25 seconds. Interface validation and the isolated fixture browser/API/CLI/PTY
journey passed with zero page errors. The browser submitted the user's unchanged
sentence and verified deterministic_inspection, one inspect_csv source and zero planning
model calls via saved chat state. No live dataset, database or model execution was used.
