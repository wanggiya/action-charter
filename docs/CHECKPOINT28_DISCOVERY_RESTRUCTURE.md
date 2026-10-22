# Checkpoint 28 — characteristics-first discovery and structural consolidation

Recorded 2026-10-22. This revises delivery priorities without deleting historical
checkpoint plans. No Git/publication or live-service changes are authorized.

Final update: [checkpoint-28 engineering acceptance](CHECKPOINT28_CLOSEOUT.md)
supersedes earlier open-stage statuses in this historical delivery record. Exact
zero-model submissions, bounded batches and shared CLI/MCP discovery are accepted;
submission revision is inspection-batch-v5. Experimental reuse has no established
benefit and remains OFF; checkpoint-29 private knowledge and broader pre-demo
learning/scale limitations remain separate. Preserve the original model failures.

## Baseline and delivered work before this revision

Inspection on send supports one explicit local CSV/vector/raster metadata task.
The automatic reader snapshots/hashes before dispatch, with an 8 MiB per-file
bound and format-specific limits. CSV inspection materializes a bounded pandas
frame. Spatial displays, typed recorded-result requests, model-free factual
explanations, latest-source binding and directly accessible named run history
have been implemented and tested. These are bounded working features, not
massive-data support, proven learning benefit or completed checkpoint 28.

The local 1.4 GB development footprint is mostly Python/frontend dependencies and
isolated test browsers. Source complexity still matters: App/API/CLI coordination
and overlapping record/reader paths need incremental consolidation.

## Revised user target

Describe a task or select a dataset; see useful characteristics promptly, then
receive completed evidence without managing separate metadata/hash modes.
Keep existing inspection-on-send preference. Do not add mandatory agents, Docker
containers, technical controls or extra approval for permitted reads. Writes
retain review, exact authorization and Execute. Context never grants authority.

1. Quick characteristics are provisional and explicitly marked.
2. Full cryptographic hashing and requested scans run with bounded memory,
   persisted progress, cancellation and no automatic replay after interruption.
3. Completed facts identify metadata/sample/full-scan scope. A digest identifies
   content; it does not prove domain correctness or authenticity.
4. Changed sources must not yield a falsely verified result. Exact immutable
   capture and ordinary observed file-change detection are distinct guarantees.
5. Prefer statistical summaries and bounded visual samples to rendering all data.

## Shared structure and agent responsibilities

    Interface / CLI / MCP
        -> application services
        -> discovery facts + source identity
        -> focused context -> one Planner reasoning/correction loop
        -> typed policy -> durable execution -> local or optional MCP adapter
        -> recorded evidence -> Outcome / History / advisory Critic
        -> optional evaluated experience retrieval

Planner interprets intent and selects compatible registered operations. Readers
establish facts; Critic interprets recorded evidence and applicability. Deterministic
services own budgets, checks, identity, persistence and authority. The optional
method helper is not a new container or mandatory call. Existing legacy Builder
commands are not required by the Planner-owned capability pilot.

Do not rewrite all services at once. Extract shared readers first, consolidate
callers, then reduce oversized coordination modules as behaviors acquire tests.
Preserve old plan digests and record readability; extend versioned result contracts
rather than relabel historical evidence. Docker remains an optional execution
adapter; the normal launcher still runs frontend/API on the host.

## Dependency-ordered delivery

1. **Streaming CSV discovery slice:** one shared safe reader for automatic
   inspection and existing CSV inspector entry points. Probe bounded header/sample
   before full scan; publish provisional metadata during a durable run; stream full
   row/missing counts and SHA-256 without pandas materialization. Preserve existing
   small-table processing/complete exploration limits and communicate the difference.
2. **Spatial discovery:** metadata-first TIFF and closed vector-package adapters;
   metadata availability/cost is driver-dependent. Do not load all geometry/pixels
   merely to inspect a large source. Bind required sidecars. Preserve read-only
   driver isolation and source consistency; measure accepted sizes before advertising.
3. **Agent/context consolidation:** feed scoped facts to Planner; narrowly explicit
   inspection may bypass inference through the same validated record path. Broader
   tasks still require reasoning. No extra hidden correction loops or permissions.
4. **Coverage:** bounded multi-inspection, interface/CLI/MCP parity, changed/malformed/
   oversized/cancelled/interrupted cases, named historical outcomes and migration checks.
5. **Learning acceptance:** compare outcome-informed applicable-case/failure retrieval
   against fixed baseline using the same small model and held-out tasks. Report
   correctness, interventions, calls, latency and resource cost. Keep optional/OFF
   by default; no Ollama-weight training, authority expansion or silent write retry.
6. **Checkpoint closeout:** one accurate acceptance matrix, limitations and manual
   journeys; checkpoint 28 remains open until its required gates pass.

## Later private domain knowledge — checkpoint 29

Source-backed units, valid ranges, missing-value conventions, applicability and
procedures; preserve versions, corrections, expiry and provenance. Model-generated
entries are candidates, not verified facts. Routine bookkeeping is automatic;
ambiguous assumptions remain unconfirmed. Same-conversation scope first;
cross-chat sharing stays checkpoint 30+ and needs a fresh decision.

## Revised remaining work — operator agreement, 2026-10-22

Documentation only in this update. The spatial delivery below remains accepted;
the following items are planned, not implemented or newly verified. This order
supersedes the earlier remaining-stage order without deleting checkpoint history.

1. **Opacity and inspection information.** Reproduce the reported raster-opacity
   endpoint problem before assigning a cause. Fix endpoint dragging so 0% hides
   the image, 100% shows valid pixels fully, NoData stays transparent and controls
   remain usable. Expand readable Overview and technical details toward gdalinfo
   metadata coverage: driver, dimensions, CRS, extent, affine transform, resolution,
   per-band types/NoData, block sizes, compression, color interpretation, units,
   scale/offset, overview sizes and available metadata. Missing values must be
   labeled unavailable. Acceptance: endpoint/drag browser regression and independent
   metadata comparisons on temporary raster fixtures. Statistics/histograms that
   require scans remain explicit bounded reads with progress/cancellation; hashes
   do not establish pixel statistics or data quality. No full gdalinfo parity claim.
2. **Faster exact inspections.** Route narrowly recognized supported local
   inspection requests through existing typed validation, source binding, durable
   runs and no-replay services, with zero model calls. Keep Planner for ambiguous,
   mixed and processing requests. Acceptance: counted zero calls for eligible
   cases; negative cases cannot silently broaden scope or run an inspection prefix
   of a write workflow. Inspect on send remains optional; writes retain Allow writes
   -> Authorize -> Execute.
3. **Bounded multiple-dataset inspection.** Extend the existing coordinator with
   explicit input/step/resource bounds, separate results, progress and cancellation.
   Acceptance: multi-input fixtures, mixed success/failure and interruption retain
   correct per-step evidence; no automatic replay or repeated writes. Do not add
   a second execution engine.
4. **Shared-service consistency.** Migrate remaining spatial CLI/MCP inspection
   paths to shared readers with compatibility checks. Consolidate duplicated
   coordination incrementally. Acceptance: equivalent results and rejection rules
   across entry points, old records readable, no weakened contracts/authority.
5. **Evaluate learning without RL.** Compare relevant successful-method and failure
   retrieval OFF/ON with the same small model, fixed baseline and held-out tasks.
   Record correctness, corrections/interventions, calls, latency and resource cost.
   Keep optional/OFF until evidence supports enabling it; report no benefit or
   regressions honestly. Retrieval does not train Ollama weights or confer authority.
6. **Checkpoint-28 closeout.** Complete CSV/vector/raster and combined journeys,
   direct permitted reads, authorized writes, cancellation/interruption and history.
   Use temporary fixtures, backend/frontend checks and isolated browser journeys.
   Publish an accurate acceptance matrix and limitations, then prepare manual Git
   guidance in conversation. No Git/publication action is authorized by this plan.

Structure: frontend owns presentation and controls; Planner interprets requests;
Critic assesses recorded outcomes and proposes evidence-backed lessons;
deterministic backend services enforce contracts, budgets, storage and authority.
No additional mandatory agent, daemon, container or broad rewrite is planned.

Next numbered checkpoint remains **29: private domain knowledge**, following
the [knowledge design](DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md). Evaluated learning
and private knowledge acceptance precede the broader realistic-data/demo stage
requested by the operator. Synthetic fixtures remain necessary beforehand. This
does not promise model-weight RL before demo or authorize cross-chat sharing.

## Acceptance for the first slice

- Inspect a CSV larger than 8 MiB and 10,000 rows with exact parsed row count and
  independent SHA-256 oracle; quoted multiline records and literal NA are handled.
- Metadata is visible while verification is pending, never labeled completed then.
- Memory is bounded independently of total source size; no full-file byte/frame load.
- No-follow regular-file checks, parse/time/size/output bounds, source-change
  detection, cancellation and durable no-replay behavior remain enforced.
- Same shared inspector behind automatic inspection and existing CLI/MCP service.
- Existing transformations and complete exploration retain their stated small-data
  limits; inspection capability is not falsely generalized to processing.
- Run backend/frontend/browser checks with temporary fixtures and isolated profiles.

## Implementation record

The baseline above is delivered. The revised stages above are targets. Append
actual implementation, measurements and remaining limits below as work completes.


### Delivered first slice — 2026-10-22

- New discovery/source.py owns the existing no-follow access checks, re-exported
  under the old tabular names. discovery/csv.py owns probing and streamed parsing/
  hashing. No pandas frame or whole-file byte string is needed for inspection.
- A CSV probe reads at most 256 KiB / 20 complete records and publishes at most
  the requested 20 preview rows, 20 columns and 4 KiB of preview text. Header bounds
  remain 100 columns / 1024 UTF-8 bytes; fields remain bounded to 4096 characters.
  Logical records have a 1 Mi-character cap, including quoted multiline records.
- Existing inspect_csv service, CLI and MCP entry points share the reader. The
  automatic path probes before planning, supplies only source/column characteristics
  to Planner, records preliminary discovery separately from workflow execution in
  the submission receipt, and binds stat identity through dispatch. Planner still generates
  the proposal; deterministic zero-model inspection routing is NOT delivered yet.
- Interface workers stream preliminary metadata over a bounded inherited pipe.
  The existing observer persists it under a running step; the current Outcome opens
  during verification. Exact rows/missing counts and raw-file SHA-256 are published
  only after complete UTF-8 parsing and identity/change checks. Failed/cancelled
  records do not become verified; the UI labels their verification incomplete.
- Reader cap: 1 GiB, 120-second wall/read deadline, 90-second CPU budget in the
  interface worker. Worker address-space cap remains 2 GiB; reply/progress 16 KiB.
  This is a configured ceiling, not demonstrated 1 GiB production capacity.
- UTF-8/BOM and explicit comma/tab delimiter are supported. Encoding inference,
  numeric type inference and arbitrary delimited formats are not implemented.
- Exact count/hash share a sequential full scan; metadata probing is a small
  earlier read. Identity checks use opened-file/path stat information, not an
  immutable filesystem snapshot or proof against an adversarial concurrent writer.
  A SHA-256 identifies observed content, not correctness/authenticity. Later writes
  still use their own normal exact review, bounded readers and authorization.
- The final inspection result schema permits the larger count; transformation
  artifact schemas retain their 10,000-row maximum. Historical records remain
  readable; contract-bound reuse can correctly mark an old inspection contract
  changed until fresh evidence exists. No stored reviews/approvals are rewritten.
- CSV transformations and complete result filtering/chart summaries retain 8 MiB /
  10,000-row budgets; the UI hides unsupported complete-exploration controls for
  larger inspected inputs. Sample tables/charts remain bounded and labeled.
- The health contract for submission is now streaming-csv-v3. Restart the API and
  refresh the frontend after updating. No new dependency, agent or container.

Synthetic resource measurements: /tmp/actioncharter-discovery-measurements.json,
produced by scripts/checkpoint28_discovery_evaluation.py. About 16 MiB / 16,693
rows and 64 MiB / 66,774 rows matched independently computed hashes and expected
counts. Observed worker peak RSS was approximately 189 MiB in both cases; elapsed
probe+scan times were 1.08 s and 0.35 s respectively (warm/cold/import/cache effects
make these unsuitable as a size-speed trend). This is not an end-to-end model,
whole-platform, competitor or real-data performance claim.

The initial browser acceptance has 13 groups, including a controlled pause after
provisional metadata for a >8 MiB / 12,000-row CSV, sample access while pending,
exact completed count/hash, disabled unsupported complete exploration and reload
without replay. Its model reply is a fixture; real-model acceptance is separate.
Spatial discovery, multi-inspection, inference bypass, adaptive learning and the
checkpoint closeout remain open; checkpoint 29 private knowledge is still future.

Manual validation:

1. Restart with bash scripts/start_actioncharter.sh and refresh the browser.
2. Keep Inspect on send ON. Put a UTF-8 CSV under data/input, then send:
   Inspect your_file.csv. Return row count and column names. No writes.
3. When scanning is long enough to observe, Outcome first shows characteristics
   with verification pending; a very fast scan can finish before a UI poll.
4. Completion shows exact parsed row count, column names and recorded SHA-256.
   Table is a bounded sample. Larger files do not show Explore complete CSV.
5. Reopen the named run in Execution History, then refresh: the run ID remains
   the same and no operation is repeated. Existing spatial journeys still work.
6. CLI uses the same reader: geoagent inspect-csv your_file.csv --project-root .
   No write-enablement flag or authorization is required for these inspections.


Actual-model acceptance: /tmp/actioncharter-streaming-csv-model.json passed with
qwen3:4b-instruct, one call, 22,282 prompt bytes, 28.6 seconds model time / 29.7
seconds total for the small temporary CSV. Duplicate submission returned the same
run. No approvals, dataset writes or live database calls. This confirms integration,
not reduced end-to-end model latency or learning. The model-free route is still a
later stage; reader speed must not be confused with full conversational latency.


Final verification: make test **2,002 passed** in 190.85 seconds, with five
expected Rasterio fixture georeference warnings. make interface-validate passed
(typecheck/build; existing bundle-size advisory). All **13** browser groups passed
against the shared backend and temporary data, with only model completion and a
controlled progress pause supplied by fixtures. The separate installed-model
acceptance above passed. History remains compatible, the historical status suffix
is unchanged, and no dependency install, Git mutation, publication, browser-cache
change or live-service data modification was performed.

### Delivered spatial slice — 2026-10-22

- `discovery/spatial.py` reads metadata for self-contained TIFF, closed GPKG and
  lowercase SHP/SHX/DBF packages (optional PRJ/CPG). GDAL sees private aliases to
  opened regular no-follow files. It does not copy the whole input, load a geometry
  frame, read raster arrays or create an external overview/statistics file.
- GPKG must have no WAL/SHM/journal companions and use rollback-mode headers;
  active or persistent WAL-mode sources require a separately prepared closed copy.
  Extra same-stem SHP/TIFF companions reject. Driver availability/count cost varies:
  counts/extents are available metadata, possibly cached/stale, or explicitly
  unavailable. No expensive count/bounds scan is forced. Hashing is not geometry,
  pixel, cached-statistics, domain or authenticity validation.
- Guards: 1 GiB per closed package, 120 s discover wall deadline, 90 s worker CPU,
  2 GiB address space, 128 raster bands, 8 vector layers, at most 100 displayed
  fields/layer with bounded names and a truncated-field indicator. One metadata
  event is capped at 16 KB; final output is also bounded. Directory enumeration
  stops at 10,000 entries. Probes use the existing 30 s wall / 10 s CPU guards.
- A provisional event precedes streamed component SHA-256 and the existing
  manifest-digest scheme. Open-file and reopened path/member stat checks bind
  source identity; these checks are not immutable snapshot guarantees. A changed,
  replaced, malformed, oversized, cancelled or timed-out source cannot produce
  completed verification. Small inputs can finish before the first UI poll.
- Automatic and reviewed interface inspections use this reader. `discover-dataset`
  exposes the same bounded worker in CLI. Existing legacy `inspect-vector`,
  `inspect-raster` and their MCP tools retain their old contracts/limits; their
  migration is not claimed delivered. CSV CLI/MCP already share the streaming
  reader. GeoJSON remains on the old 8 MiB bounded snapshot reader; safe streaming
  JSON/geometry discovery is not implemented.
- Typed registry results accept old spatial outputs and the new versioned metadata
  result. No old plan, approval or evidence is rewritten. Contract-bound reusable
  records can become ineligible after the contract changes. The submission revision
  is now `spatial-discovery-v4`, superseding this guide's earlier CSV-only revision.
- Outcome Overview distinguishes preliminary, completed and interrupted evidence;
  other tabs keep a compact status. Existing small-source verified layers and
  raster images/pixels still work, including conversational settings from metadata
  without an old geometry preview. Large source discovery does not expand the
  viewer's 8 MiB/file, 10,000 features/layer, 100 fields, 16 bands / 100 million band
  cells or processing limits. The UI explains when Map is unavailable.
- Existing durable run writes fsync the record and its containing directory.
  A stale running record without a held execution lease becomes interrupted when
  read after restart; provisional evidence stays unverified, queued work skips,
  and nothing restarts automatically. Tests simulate lost-process records; actual
  power-loss/filesystem/hardware fault tolerance has not been established.

Measured resource acceptance: `scripts/checkpoint28_discovery_evaluation.py
--spatial --output /tmp/actioncharter-spatial-discovery-measurements.json` generated
temporary uncompressed TIFFs of 16,789,870 and 67,133,806 bytes. Independent hashes
and dimensions matched. Probe+scan took 1.856 / 0.606 seconds; reported worker peak
RSS was 208,476 / 210,432 KiB. Warm/cold cache/import effects prevent deriving a
size-speed trend. Separate worker tests accepted >8 MiB GPKG/SHP packages with
40,000 features and independently matched component/manifest hashes. These are
synthetic cases, not all-format 1 GiB or real-world performance acceptance.

Installed-model TIFF acceptance:
`/tmp/actioncharter-raster-discovery-acceptance.json`, qwen3:4b-instruct, one call,
22,274 prompt bytes, 44.621 s model time / 46.827 s total. Dimensions/bands/CRS
matched; duplicate submission returned the same run. No dataset writes,
approvals or live DB calls. The restricted first attempt could not reach Ollama;
the permitted local endpoint run passed. This remains a narrow example, not a
general reliability, speedup or learned-knowledge claim.

Spatial verification: `make test` passed **2,017 tests** in 317.64 s, with five
expected Rasterio fixture warnings. After the metadata-only conversational vector
context correction, **41 focused spatial/result tests** passed, including the new
regression. `make interface-validate` passed (existing ~754 KB bundle advisory).
Final browser acceptance passed **14 submit groups + 8 spatial-view groups**, using
the actual backend and temporary data, with fixture model completions. It covers
large TIFF progress, existing maps/layers/exact pixels, reload/no replay, and
changed-source rejection. The restart test preserves provisional metadata as
interrupted without re-executing. Historical status text and byte budget are
preserved; `git diff --check` passed. No Git mutation or live-service changes.

The current conversational path still waits for Planner before starting the full
durable inspection; preliminary source facts are supplied to Planner first.
Reader speed does not remove model latency. The next narrow deterministic route
is intended to address exact inspection requests without another agent.

Manual frontend validation for this slice:

1. Restart `bash scripts/start_actioncharter.sh`; refresh `http://127.0.0.1:5173`.
   These read-only inspections need no `--enable-write-tools` flag.
2. In Conversation settings turn **Inspect on send** ON. Send:
   `Inspect sample_dem.tif. Return dimensions, bands, CRS and NoData. No writes.`
3. Outcome → Overview should show raster characteristics and completed package
   SHA-256 evidence. Expand Recorded metadata for the component manifest/digest.
   A small TIFF may complete too quickly to show pending status.
4. Outcome → Map → Load verified raster should retain the existing small-file
   image, render controls and exact source-pixel inspection. No workflow write.
5. Put your own closed GPKG or lowercase SHP package under `data/input`, then send
   `Inspect your_file.gpkg. Return available feature counts, fields and CRS. No writes.`
   Substitute the SHP name when appropriate. Check layer names, declared CRS,
   fields and count basis. Unavailable counts must not become zero.
6. For a TIFF/GPKG/SHP above 8 MiB, check metadata/hash completion in Overview;
   Map must explain its separate limit. Do not expect full geometry/pixel display.
7. Reopen the named run in Execution History and refresh. Its run ID and recorded
   facts should stay the same, with no new run or approval. Use `discover-dataset`
   for the same CLI service, for example:
   `.venv/bin/geoagent discover-dataset sample_dem.tif --project-root .`

Recovery/handoff: [context/WORK_RESUME.md](../context/WORK_RESUME.md) records what is
verified and the next ordered stages. Checkpoint 28 is still open: narrow inference
bypass, bounded multi-inspection, remaining entry-point parity, evaluated experience
retrieval and consolidated acceptance precede closeout. Knowledge 29 and cross-chat
30+ remain deferred; this slice adds no RL or new agent/container.

### Raster information and opacity follow-up — 2026-10-22

Added `raster-details-v1` as optional typed `technical_details` in spatial results;
old outputs remain valid and old records are not backfilled or reread. The same
worker reads TIFF headers/tags and saves compression, tiled/strip layout,
interleave, CRS WKT, band blocks/color interpretation/descriptions/units/scale/
offset and exact first-band overview dimensions. No pixel arrays, statistics or
histograms are requested. Stored statistics tags can be stale and are labeled
stored-only; a file hash does not verify their scientific correctness.

Bounds: technical details <=5,500 serialized bytes, up to 16 band detail records,
16 overview levels with first-band exact dimensions, 2,048 WKT characters,
1,500 bytes total selected metadata tags, <=12 tags per selected namespace/band,
80-character tag keys / 200-character values and bounded descriptions. Only
default and IMAGE_STRUCTURE dataset namespaces plus default band tags are read;
other metadata domains, color tables, full masks/GCPs and gdalinfo option parity
are not delivered. Truncation is explicit; count/types still cover the accepted
128-band metadata limit. Existing worker/output/source guards remain. Runtime
does not require or invoke gdalinfo; its installed CLI is an optional test oracle.

Overview shows readable basics and collapsed technical/per-band/tag sections.
Expanding them reads the recorded result without a backend call. Missing metadata
is labeled Not recorded; older results explain that fresh inspection is required
for extra details. Do not silently reconstruct missing historical metadata.

Opacity endpoint diagnosis: pre-change browser tests reached 0/100% and recovered
from zero using mouse dragging and keyboard Home/End/arrows. The user's original
symptom is not reproduced or declared fixed; clarification was requested. Added
stable native-slider sizing/focus, visible endpoint labels, bounded values and a
percentage output. Endpoint changes affect the raster image only, not controls or
the source dataset. Existing NoData alpha remains part of the verified PNG.

Manual validation:

1. Restart the existing launcher, refresh and turn Inspect on send ON.
2. Send `Inspect sample_dem.tif. Return dimensions, bands, CRS and NoData. No writes.`
3. In Outcome -> Overview, expand Raster technical details, CRS WKT, metadata
   tags and Band 1. Check extent/resolution/type/NoData, storage and band metadata.
   The sample may have no units/overviews; use a TIFF that records them to see those
   values. A saved older run may legitimately lack the new details.
4. In Map, Load verified raster. Drag Opacity to both ends and back; try keyboard
   Home, End and arrows. The percentage should match the image (0% hides it).
   Controls stay visible and adjusting opacity must not create a new run/read.
5. Reopen the saved run through Execution History; metadata should remain recorded.
   Technical expansion must not compute statistics or require write enablement.

Next: resolve any concrete reproducible opacity finding, then the agreed narrow
zero-model inspection route, bounded multi-inspection, CLI/MCP parity and evaluated
experience reuse. Full-file statistics/histograms need a separately implemented
explicit bounded read before being advertised; they are not added by this slice.

Final verification for this follow-up:

- `make test`: **2,021 passed**, 184.80 s; 12 Rasterio library warnings (fixture
  georeferencing and pending is_tiled deprecation). The last Unicode WKT budget
  regression was added after collection; the final **19-test** discovery run
  includes it and passed after the final budget hardening.
- `make interface-validate`: passed; existing ~758 KB bundle advisory remains.
- Actual-backend isolated browser checks: **10 spatial-view + 14 submit groups**
  passed, fixture model completions only, no page errors or live-service calls.
  The pre-change slider endpoint check also passed, so the original issue cannot
  honestly be declared reproduced/resolved.
- Independent installed `gdalinfo -json` oracle matched known temporary TIFF
  dimensions, affine transform, block shape, compression, scale/offset/unit and
  exact overview sizes. A stored-statistics fixture remained stored-only;
  pixel/statistics APIs were forbidden in the metadata-only reader test.
- Metadata-heavy 128-band and Unicode fixtures retain bounded replies and explicit
  truncation. Old-record compatibility and historical status suffix are preserved;
  `git diff --check` passed. No Git mutation, dependency download, shared browser
  cache change or live-service modification. Resume details are in WORK_RESUME.
