# Checkpoint 28 — final engineering acceptance

Recorded 2026-10-22. The agreed checkpoint-28 engineering implementation and
acceptance are complete, with the experimental/scale limitations below. A useful
learning benefit and broader demo readiness are not established. This record does not grant execution,
database, Git or publication authority. Historical checkpoint documents remain.

## Delivered structure

    Conversation / CLI submit-inspection
      -> durable submission receipt
      -> exact supported request: typed proposal, no model call
         broader request: existing bounded Planner / correction
      -> policy + source / contract / chat revision binding
      -> existing durable coordinator and operation dispatch
      -> per-step evidence -> graph / Outcome / Execution History

    CLI discover-dataset / MCP discover_dataset
      -> shared discovery service -> same resource-bounded reader

No additional agent, model, daemon, Docker image or unrestricted function loader.
Planner handles interpretation/composition; Critic provides advisory assessment;
backend services enforce source identity, dependencies, budgets and authority.
Discovery source access and CLI/MCP service logic are shared, rather than copied
into another execution engine. Legacy inspectors retain old result contracts.

## Accepted scope and limits

| Area | Behavior and acceptance evidence |
| --- | --- |
| Exact proposals | Closed explicit Inspect grammar with compatible metadata fields, normalized local paths, skill-selection constraints and zero model configuration/calls. Preserve trusted and existing stricter approval/validation gates. Explicit method selections retain Planner. No guessing unknown fields or transforming data. |
| Inspect on send OFF | Prepare a typed proposal; no source content probe, workflow execution or approval. Normal UI sends still get a durable receipt. |
| Inspect on send ON | Probe then execute eligible reads through normal policy/review/dispatch. One receipt/run per submission ID; rereading/retrying that receipt cannot replay. An explicit new send can request a fresh inspection of the same file. |
| Multiple sources | 1–4 distinct explicit local sources, <=1 GiB aggregate package size, serial execution in the existing coordinator. Per-reader budgets remain; maximum full-scan wall allocation is 4 x 120 s, not unlimited processing. Probe phase <=4 x 30 s. No parallel scheduler is added. |
| Failure/cancellation | Preflight failure never executes a valid prefix; completed probe counts remain recorded. Later changed-source failure/cancellation retains completed steps, marks the failed/cancelled step and skips queued work. No automatic retry/resume or authority reuse. |
| Recovery | Durable record/receipt reconciliation; interrupted partial metadata stays unverified. History/restoration never regenerates or executes a workflow. No hardware power-loss guarantee. |
| Inventory | Existing bounds remain: 200 submission receipts and durable runs per project, 50 turns per chat. No silent eviction or automatic replay; deliberate archiving is needed at capacity. |
| Formats | UTF-8 CSV/TSV, bounded GeoJSON, closed GPKG/SHP packages and self-contained TIFF. TSV defaults to tab. Driver counts/extents may be cached or unavailable; hashes do not establish domain correctness. |
| Scale | CSV and TIFF synthetic measurements at 16/64 MiB; >8 MiB GPKG/SHP worker cases at 40,000 features. 1 GiB is a configured guard, not proven arbitrary real-data scale. Transformations and full CSV exploration remain 8 MiB/10,000 rows. |
| Raster information | Bounded readable/expandable technical metadata, compared with gdalinfo on temporary fixtures. No automatic statistics/histogram scan or complete gdalinfo parity. Opacity endpoints/readout and mouse/keyboard checks; the earlier reported fault is not reproduced. |
| Results | Existing table/chart/map tabs, source-verified bounded spatial reads, exact pixels, typed conversational display and recorded-fact explanations. Full geometry/pixel display limits remain separate from discovery. |
| CLI/MCP | discover-dataset and MCP discover_dataset share the same service and worker. submit-inspection shares receipt/review/durable-run behavior; --execute permits supported reads only. Legacy inspect-vector/raster commands and inspect_vector_dataset preserve compatibility/custom-root behavior; no silent result-shape migration. New MCP discovery requires the configured project data/input root. |
| Writes | Allow writes -> exact Authorize -> Execute; overwrite is separate. None of these settings are inferred from transcript/model/memory text. Temporary CSV execution journeys pass; live PostGIS/GeoServer validation is not claimed. |
| Experience reuse | Existing own-chat, current-contract successful-method retrieval and optional check-outcome recommendations; bounded failure counts, changed-contract exclusion, corrupt-store fallback and reset are tested. No model-weight training or demonstrated general learning benefit. |

Automatic request examples:

    Inspect sample_orders.csv. Return row count and column names. No writes.
    Inspect sample_dem.tif. Return dimensions, bands and CRS. No writes.
    Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.

Mixed formats may share only compatible requested metadata fields. More than four
sources, processing, unknown metadata or ambiguous wording retains Planner and
explicit Execute as appropriate; the backend never trims a workflow to execute
its read prefix. The legacy direct conversation endpoint retains its model path;
the new exact route is in explicit submission, used by normal UI sends and CLI.
Current submission contract: inspection-batch-v5. Planner contract remains
inspection-source-v2. Restart launcher and refresh after updating.

## Evaluated experience reuse, without RL

The fixed paired trial used qwen3:4b-instruct, six tasks, two repetitions and both
recommendation states: 24 attempts. Existing successful-method retrieval is part
of both baselines; the ON/OFF difference is optional outcome recommendations,
not a clean ablation of every kind of memory. Synthetic seed workflows were
executed and checked; changed-input tasks used fresh outputs and authority.

Original result: OFF 10/12 and ON 10/12 correct; 14 model calls and two corrections
per side; no extra read steps. Model/processing totals were 602.127 s OFF and
601.687 s ON. Both sides failed the vector case twice with conflicting workflow/
result-view output. Nothing was executed for rejected plans. Original report:
/tmp/actioncharter-checkpoint28-closeout-paired-model.json. Its failures are retained.

This did not meet the predeclared representative-benefit threshold. Keep
recommendations optional and OFF; do not call fixed scoring RL or claim learned
improvement. Failure-feedback safety is checked with deterministic fixtures;
this model trial does not establish improved recovery from arbitrary failures,
schema/units-aware domain recall or cross-chat learning. The broader pre-demo
learning/private-knowledge gate is not cleared by engineering closeout.

The observed vector conflict led to a focused response-schema change: explicit
Inspect/Replace workflow requests no longer receive competing recorded-view
schemas merely because an older run exists. Actual display/explanation requests
keep their view path. A separate targeted four-attempt vector retest is recorded
below; do not merge results across code versions into a fresh 24/24 trial.

## Manual acceptance

1. Restart `bash scripts/start_actioncharter.sh`; refresh localhost:5173. No
   write-enablement launch flag is needed for these inspections. Check that the
   normal preference is still remembered across chats.
2. With Inspect on send OFF, send the first exact CSV example above. Expect an
   inspection graph and "Exact inspection workflow · no model call"; no new run.
   Execute should run the permitted read without Authorize or Allow writes.
3. Turn Inspect on send ON, start a new chat and send the mixed CSV/TIFF example.
   Expect one run with two operations. Outcome's Operation result selector should
   switch between CSV counts/columns and raster characteristics/technical details.
4. Refresh and reopen the named run in Execution History. Both results/run ID
   persist; no model call, new workflow or execution is needed to view them.
5. For a new CSV write proposal, ask Planner to preserve the CSV inspection and
   calculate doubled = amount * 2, preserving all original columns/missing values,
   saving to a fresh CSV under data/output. Confirm the graph contains the actual
   calculation/formula and new output path. Allow writes, Authorize, then Execute.
   Check new values against original amounts; do not infer authorization from chat.
6. For a sufficiently long inspection, cancel through Workflow runs in Execution
   History. Completed evidence remains; incomplete verification must not appear
   completed. Review targets before deliberately retrying any write workflow.

CLI parity (no model needed for these exact requests):

    .venv/bin/geoagent discover-dataset sample_dem.tif --project-root .
    .venv/bin/geoagent submit-inspection "Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes." --project-root .

Add --execute to the second command only when you intend to run its permitted
reads. The response records conversation/submission/run identities. For deliberate
continuation use the returned conversation ID/revision; for receipt reconciliation
reuse the original submission ID and exact original request/revision. Do not
generate a new ID merely to retry an uncertain dispatch.

## Verification and next checkpoint

Final verification:

- `make test`: **2,045 passed**, 13 Rasterio library warnings, 200.79 seconds.
  After final relative-root/stricter-gate coverage, **53 focused exact-inspection,
  result-view and MCP checks passed**. The early failed run exposed task-message
  provenance (fixed) and restricted loopback sockets; it is not counted as passing.
- `make interface-validate`: passed; existing ~758 KB bundle advisory remains.
- Final isolated browser checks: **15 submission/batch + 10 spatial + 4 execution
  + 6 Planner/recipe/graph groups**, all passed, no page errors or live-service
  calls. Model completions are fixtures in these browser journeys. Graph testing
  found and fixed React selection removing the active drag class; one state
  transition at start/end now preserves frame-based movement. Grouped disabled
  action buttons retain the shared outline material.
- Original paired local-model trial: 20/24 correct (10/12 per side). Separate
  corrected vector retest: **4/4**, one call per task, no corrections. OFF: two
  calls / 33.373 s total; ON: two calls / 30.496 s. This is not a new full 24-case
  result and does not establish ranking benefit. Failed and targeted reports remain
  separate; default stays OFF.
- Exact temporary TIFF submission: **zero model calls**, correct metadata and
  same run on duplicate submission, 1.359 s total on this machine. Configured model
  was not called. `/tmp/actioncharter-checkpoint28-exact-submit.json`. One example
  is not an all-file latency or competitor benchmark.
- Fixture paired harness: all 24 attempts passed. Negative feedback/contract
  mismatch/corruption/isolation/reset checks are deterministic tests, not proof
  of arbitrary model recovery. Live PostGIS/GeoServer data was not modified.
- Historical CURRENT_STATUS suffix and its byte bound are preserved;
  `git diff --check` passed. No stage/commit/push/merge/release, dependency download
  or shared browser-cache change. Existing user changes/untracked manual Git note
  are preserved. WORK_RESUME retains the recovery handoff.

Raw temporary reports are disposable; these metrics and limitations survive in
this document if /tmp is lost. Full-file statistics, streaming large GeoJSON,
general model reliability and learning benefit are not silently marked delivered.

Next numbered checkpoint is 29: private source-backed domain definitions/methods,
bounded retrieval, applicability, corrections/supersession and provenance. Start
within one conversation, using synthetic acceptance fixtures. Cross-chat/project
sharing stays 30+ and separately decided. Broad realistic-data/demo and packaging
preparation do not imply learning/private-memory gates are already satisfied.
Model-weight RL, unrestricted code generation/MCP creation, full-file statistical
analysis, broader real-data scale and hardened multi-user/desktop packaging remain
explicit future work. No Git/publication action is performed by this record.
