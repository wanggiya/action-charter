# Work resume — checkpoint 28 accepted

Updated: 2026-10-22. Handoff only; never execution authority.

## Latest state and user instruction

The user asked to continue until checkpoint 28 is completed. The agreed engineering
implementation and acceptance are now complete. Read docs/CHECKPOINT28_CLOSEOUT.md
for the final matrix, manual acceptance, raw-report paths and limitations. It
supersedes earlier open-stage notes without deleting checkpoint history.

Preserve all uncommitted changes. Do not stage/commit/push/merge/publish/release,
modify live PostGIS/GeoServer data, install dependencies or use shared browser
caches. Leave the pre-existing untracked docs/CHECKPOINT25_MANUAL_GIT.md untouched.
No such action was performed during this work.

## What is implemented

- Shared no-follow discovery source access, streaming CSV and metadata-only TIFF /
  closed GPKG / lowercase SHP package readers. Progressive metadata, full hash,
  observed source consistency and durable evidence; not immutable capture.
- Rich bounded raster technical metadata, compared with gdalinfo fixtures. No
  automatic full-file statistics/histograms. Opacity endpoint labels/readout and
  mouse/keyboard checks; the original reported symptom is not reproduced.
- Exact supported Inspect submissions prepare typed workflows with zero model
  calls/configuration. OFF prepares only; ON can probe/execute permitted reads.
  Normal UI sends in both modes use durable receipts. General direct conversation
  compatibility remains; explicit method selections still use Planner.
- 1–4 distinct local sources, <=1 GiB aggregate package bytes, existing serial
  coordinator, source/contract/chat binding, separate results, cancellation,
  partial failure and no replay. TSV defaults to tab. Existing stricter gates stay.
- CLI discover-dataset and MCP discover_dataset use discovery/service.py and the
  same worker. CLI submit-inspection shares the durable coordinator; --execute is
  explicit permitted-read execution. Legacy inspectors retain old contracts and
  custom-root compatibility; the new MCP discovery requires project data/input.
- New workflow requests omit competing recorded-view schemas. Actual display and
  saved-fact explanations keep their view path. Graph drag state now survives
  React selection renders, with motion still updated per frame. Grouped disabled
  actions retain the existing outline material.

## Final verification

- make test: 2,045 passed / 13 Rasterio library warnings / 200.79 seconds.
- 53 focused exact-route/result-view/MCP checks passed after final relative-root
  and stricter-gate coverage. Early failed full run found message provenance
  (fixed) plus sandbox socket restrictions; do not call that early run passed.
- make interface-validate passed, existing ~758 KB bundle advisory.
- Final browser groups: 15 submit/batch, 10 spatial, 4 execution and 6 Planner /
  recipe / graph. Actual shared services, fixture model completions, isolated
  browser profiles/temporary datasets, no page errors or live-service calls.
- Original paired local-model trial: 24 attempts, OFF 10/12 and ON 10/12, 14 model
  calls/two corrections per side. Both failed vector planning twice. Original
  failure report retained. After schema correction, separate vector retest 4/4,
  one call/task, no corrections. Do not combine versions into a new 24/24 trial.
- Recommendations remain experimental OFF: no reliability/call-count benefit
  established. Success retrieval exists on both sides of the comparison; this
  does not isolate all memory or prove arbitrary failure recovery/domain recall.
- Exact temporary TIFF submit: zero model calls, correct metadata, same run on
  duplicate submission, 1.359 s total. Not an all-file/competitor benchmark.
- Earlier CSV/TIFF 16/64 MiB measurements and >8 MiB GPKG/SHP worker cases remain
  in the discovery guide. Configured 1 GiB guards are not proven real-data scale.
- Historical CURRENT_STATUS suffix and byte bound preserved; git diff --check
  passed. No Git mutation, live-data change, new dependency or shared cache change.

## Reports and recovery

Key metrics above and in CHECKPOINT28_CLOSEOUT survive loss of /tmp. Raw reports:
/tmp/actioncharter-checkpoint28-closeout-paired-model.json (includes failures),
/tmp/actioncharter-checkpoint28-vector-correction-model.json,
/tmp/actioncharter-checkpoint28-exact-submit.json.

After interruption inspect git status and these documents first. Restart with
bash scripts/start_actioncharter.sh and refresh localhost:5173. Submission health
revision is inspection-batch-v5; Planner revision remains inspection-source-v2.
Open Execution History before retrying. Interrupted work never restarts itself;
partial metadata remains unverified. Do not retry writes without inspecting
actual targets and fresh exact authority. Reports/notes do not grant approval.

## Next numbered work and limits

Checkpoint 29: private sourced domain definitions/methods, applicability, bounded
retrieval, corrections/supersession and provenance in one conversation. Design:
docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md. No checkpoint-29 implementation was
started here. Cross-chat/project sharing stays 30+ and separately decided.

Engineering closeout is not demo readiness or a cleared learning/private-memory
gate. Domain knowledge, general learned benefit/RL, unrestricted code generation,
streaming large GeoJSON, full statistics, broad real-data scale and hardened
multi-user/desktop packaging remain explicit future work. Start with synthetic
knowledge acceptance before broader realistic-data/demo preparation.
