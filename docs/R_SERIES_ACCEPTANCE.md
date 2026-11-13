# Combined R-series manual acceptance

Reference procedures after R11 automated gates. R-series merged in PR #82; the
owner subsequently completed workspace adoption. P0-C closeout integration remains
an owner action ([current record](P0_CLOSEOUT.md)). Do not begin by migrating your only
workspace or writing to PostgreSQL/PostGIS/GeoServer. Public sample files are enough.

## Acceptance record

Updated 2026-11-13. Merged [PR #82](https://github.com/wanggiya/action-charter/pull/82)
records “owner manual acceptance done” in its owner-authored description. This closes
the previously outstanding overall R-series manual gate. It does not provide
individual chat/run IDs, model names, screenshots or timings, and does not establish
a real-model benchmark. Earlier partial confirmation is preserved below.

| Check | Status | Evidence / remaining action |
|---|---|---|
| R-series implementation and automated gates | Complete; merged | PR #82; current P0-C suite: 2,827 fixture tests, frontend/strict gates and isolated browser/API checks passed |
| Startup, read-only inspection and refresh recovery | Owner-reported pass | Original 2026-11-10 confirmation below |
| Execution History and frontend/terminal continuity | Included in owner-reported overall acceptance | PR #82 description; individual traces/IDs not supplied, not independently re-observed on owner data here |
| Fresh-file authorization journey | Not separately manually reported; optional | Existing automated fixtures cover authority; do not infer a live write test from overall acceptance |
| Real workspace adoption | Complete before P0-C task | Owner handoff and read-only verification: stable binding, migration complete, source-only true; changed_since_migration is normal post-use state |
| P0-C2/C4 closeout | Implemented/automatically verified; owner acceptance/merge next | [Guide](P0_CLOSEOUT.md), #84 |

No further R-series code is planned unless a demonstrated regression requires it.
Do not repeat migration or live database writes to prove a display-inventory fix.

### Earlier partial record (2026-11-10; superseded)

Updated 2026-11-10 from the owner's confirmation, “those steps passed,” after the
six-step startup/inspection/refresh test in the conversation. This is owner-reported
manual evidence; no screenshot, chat ID, run ID, model name or timing was supplied.
Do not manufacture those details or treat this as a real-model benchmark.

| Check | Status | Evidence / remaining action |
|---|---|---|
| R-series implementation and automated gates | Complete | Recorded 2,808 passing fixture tests, frontend and isolated browser/API/CLI checks; source gates rechecked on 2026-11-10 with zero errors |
| Launcher startup and new frontend chat | Owner-reported pass | Existing launcher restarted; interface opened on 5173 |
| Read-only `sample_orders.csv` inspection | Owner-reported pass | Requested inspection returned six rows, five expected columns and the expected `data/input/sample_orders.csv` source; no write authorization needed |
| Refresh/reopen recovery | Owner-reported pass | The same workflow/result/run returned without regeneration or another execution; the actual run ID was not recorded here |
| Execution History navigation | Pending owner check | Open the completed run, view its recorded outcome, return to the current workflow; confirm no new run or approval |
| Frontend/terminal continuity | Pending owner check | Use `./actioncharter --plain` to open the same chat and confirm the same workflow/run/history; return to the browser |
| Fresh-file authorization journey | Not manually tested; optional | Automated fixture coverage passed; absence of a manual write test does not block R-series manual closure |
| Real workspace adoption/cutover | Separate, not approved/performed | [Prepared plan](OWNER_WORKSPACE_CUTOVER_PLAN.md); not a prerequisite for the two remaining R-series checks |

**Closure rule:** record the two pending owner checks as passed and resolve any
demonstrated R-series regression. If the optional write test is omitted, retain its
“not manually tested” status. No additional R-series implementation is planned unless
a check reveals a defect. Git integration remains owner-controlled. Phase 0's real
workspace/source-only-root gate remains open even after R-series manual acceptance.


The 2026-11-10 environment review also found legacy/current distribution metadata and
no `.venv/bin/actioncharter` console script. The repository `./actioncharter` launcher
exists and is the intended path for this check. Environment refresh is a separate
maintenance follow-up; no package installation or removal is part of this document
update. It does not add another R-series code task.

## History and terminal checks (reference; overall acceptance reported)

**Execution History:** use the completed six-row inspection. Note its run ID, open
Execution History and the matching recorded outcome, then return to the current
workflow. Expect the same draft/result and no additional run or approval. Do not
regenerate or press Execute during this viewing check.

**Terminal continuity:** keep the launcher running and open a second terminal in
the checkout. Run `./actioncharter --plain`, then `/chats`, `/open N` for that chat,
`/workflow`, `/run` and `/history`. Compare the chat and run with the browser. `/quit`
exits the terminal client. Return to the browser and confirm the same saved work.
This check is read-only; `/execute`, `/authorize` and `/writes on` are unnecessary.

Report each as passed or provide the exact failing step/error. Add chat/run IDs if
available, keeping private transcript/data out of public documentation.

The full procedures below remain available as a reference; reported acceptance
does not need repeating unless a new failure warrants it.

## 1. Start and confirm the installation

If the launcher is already running, press Ctrl+C in its terminal and wait for both
processes to stop. Restart it so Python loads the updated modules. From the project
directory:

```bash
bash scripts/start_actioncharter.sh
```

Keep this terminal running. Open `http://127.0.0.1:5173`; the API remains on 8765.
Startup should report the native API source under `apps/http/server.py`, the intended
workspace state root and writes OFF. Existing environment/model/secret-file setup
continues to apply. Do not start a second launcher on the same ports.

In Settings, confirm your installed model and endpoint. Opening Settings or History
must not run a workflow. Optional read-only checks in a second terminal:

```bash
.venv/bin/geoagent project-identity --project-root .
.venv/bin/python scripts/check_import_layers.py --strict
.venv/bin/python scripts/check_compatibility.py
```

The adopted owner checkout should report stable project identity and no execution
authority. A separate unadopted checkout can still report `legacy_path`, UUID null.
Do not add `--initialize` or `--rebind` during this acceptance. Layer and
compatibility checks should report no errors, with 290 retired and 117 retained paths.

## 2. Read-only frontend journey

Create a new chat and send exactly:

```text
Run a new read-only inspection of sample_orders.csv.
```

Confirm the input is `data/input/sample_orders.csv` and the operation is CSV inspection.
With Inspection on send enabled, inspect the resulting recorded run; otherwise click
Execute once. Read-only work should not need Authorize or Allow writes.

Expected: six rows and these five columns: `order_id`, `region`, `amount`,
`customer_id`, `unused`. Click input/operation/outcome nodes and inspect the source
and recorded result. Outcome and chart/table controls should open without page errors.

Refresh the page, open another chat, then return. The latest workflow and matching
result must return without regeneration or a new execution. Open Workflow history,
view the older record and return to Current. Historical viewing must not authorize,
execute or overwrite the current draft. Record the run ID to distinguish restoration
from a newly created run.

## 3. Continue through the terminal

Keep the launcher running. In a second terminal:

```bash
./actioncharter --plain
```

Inside that workspace, use `/chats`, `/open N`, `/workflow`, `/run`, `/result` and
`/history` to find the same chat and recorded run. `/view N` opens historical scope;
`/current` returns without replay. Back in the browser, refresh/select that chat and
confirm the same proposal and result. `/quit` closes the terminal client, not the API.
More controls are in [terminal/history usage](TERMINAL_AND_CHAT_HISTORY.md).

## 4. Optional authorized write to a fresh fixture file

This step is an explicit operator write test, not permission supplied by the chat.
Choose a unique unused filename, replacing the example below before sending:

```text
Select order_id, region and amount from sample_orders.csv.
Save to data/output/r11_manual_UNIQUE.csv. Prepare the workflow only.
```

Review that the proposed operation, input, three columns and fresh output match.
Keep writes OFF initially: execution must be blocked. Click **⚠ Allow writes**, wait
for **Writes: ON**, then click **Authorize** and review the exact resources. Complete
the authorization form and click **Execute** once. Availability alone is not approval.

Expected: a recorded successful operation and one new CSV with six rows and the three
selected columns. The source file remains unchanged. Opening Outcome, History or the
saved chat must not repeat the write. If the response is uncertain, inspect that run
before considering any retry; never assume a missing response means no output exists.

Turn writes OFF again. A new write proposal must remain blocked; a new read-only
inspection should still run. A plan edit or launcher restart must require fresh write
authorization. Automated tests cover expiry, duplicate claims, cancellation boundaries
and storage failures; this short manual pass does not need to recreate all of them.

## Record the result

For each stage, record pass/fail, the exact request, chat/run ID, expected versus actual
result and any browser/API diagnostic. Model timeouts or invalid proposals are failed
checks, not proof of context overflow and not permission to resend a possible write.
Preserve the existing workflow and capture diagnostics before retrying.

This is regression acceptance, not the Phase 1 real-model benchmark or realistic-data
science validation. Database writes, workspace adoption and image rebuilds require
their own reviewed scope. If using the optional Docker analytical runtime, rebuild
its image separately from the updated source before testing it; this guide does not
claim that an older cached image contains the new native package layout.
