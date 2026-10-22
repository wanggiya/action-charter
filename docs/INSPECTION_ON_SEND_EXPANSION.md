# Inspection on send across data types

Originally recorded 2026-10-21 as design only. Subsequent operator authorization
implements the single-dataset slice below. The remaining design is preserved. The operator confirmed the CSV slice worked and clarified
that CSV was an example: the intended behavior applies to supported inspection
tasks without dataset or external-service writes, regardless of data format.


## Implemented single-dataset slice

The existing switch now admits explicit one-dataset metadata requests for
CSV/TSV, GeoJSON, GeoPackage, Shapefile and GeoTIFF on Linux. One shared submit
coordinator, durable run engine and CLI service are used. Read-only and approval
flags must match the existing registry; a closed adapter contract is also required.
Health reports `inspection_on_send_revision: bounded-local-v2`.

Inputs bind to their exact bytes before planning and are verified in the worker
before execution. CSV byte hashes remain unchanged. Spatial hashes cover a
canonical filename/hash manifest. The execution binding includes the inspector's
registry schema and adapter version. Snapshot workers and execution workers use
10 CPU seconds, 2 GiB address space, a 30-second wall deadline, scrubbed environment
and cancellation. Spatial execution copies only approved source bytes into a
private temporary directory, removed afterward. These temporary copies and
application evidence are distinct from dataset/external-target mutation.

| Inspector | Automatic scope and bounds |
| --- | --- |
| CSV/TSV | Existing 8 MiB, 10,000 rows, 100 columns and bounded preview |
| Vector | 8 MiB/file, 32 MiB/package, eight layers, 10,000 total features, 100 fields/layer; existing bounded geometry preview |
| Raster | Embedded GeoTIFF, 8 MiB/file, 16 bands and 100 million band-cells; metadata only, no pixel statistics or image preview |

All automatic worker responses are capped at 16 KB. Oversized metadata/preview
responses fail rather than silently claim full results. Spatial adapters reuse
existing inspectors and result schemas; raster summaries show CRS, dimensions,
bands, bounds and transform. Raster pixel visualization remains unfinished.

Shapefiles require lowercase `.shp`, `.shx`, `.dbf`, with optional `.prj`/`.cpg`;
all are hashed. Additional same-stem files and unsafe links reject automatic
eligibility. GeoPackages with present WAL/SHM/journal files reject; use a closed
file. TIFF sidecars/worldfiles and other same-stem companion files are not accepted in this slice. GeoJSON requires
an inline FeatureCollection and rejects linked CRS definitions. Header checks
reject disguised TIFF/SQLite/Shapefile files before GDAL parsing. Network CRS
lookup is disabled; only fixed trusted readers are called, not model code.
This is resource-bounded parser execution, not a general OS security sandbox.

Unsupported snapshots leave a proposal for ordinary review/Execute. If input
changes or a parsing/resource limit fails after dispatch, the recorded run fails;
it is not replayed automatically. The same submission ID still returns its
original receipt/run. Mixed write tasks execute no prefix on send.

### Manual validation

1. Restart `bash scripts/start_actioncharter.sh` and refresh the browser. Keep
   writes OFF. In Planner's gear, turn **Inspect on send** ON.
2. In a new chat send: `Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.`
   Expect a single Inspect vector operation, automatic Outcome, matching source,
   layer count/fields/CRS and the existing geometry snapshot where supported.
3. In another new chat send: `Inspect sample_dem.tif. Return CRS. No writes.`
   Expect one Inspect raster operation and automatic metadata Outcome. This is
   not a raster image viewer. Neither task needs Authorize or Execute.
4. Refresh/reopen the chat: the recorded workflow/result restores without a new
   execution. Turn the switch OFF and submit in a new chat: proposal only.
5. A request that adds conversion/export remains a complete proposal. Writes
   require Allow writes, exact authorization and Execute. Do not use live targets
   for this acceptance exercise.

Automated acceptance uses temporary GeoJSON/GeoPackage/Shapefile/GeoTIFF inputs,
unchanged-source assertions, repeat-ID reconciliation, sidecar-change rejection,
format/link rejection and limits. Browser journeys use the actual backend with
only model completion replaced; installed-model evidence is reported separately.

## Remaining expansion design

## Desired behavior

With inspection-on-send enabled, submitting a clear inspection request should
plan, validate and run the supported inspection, then show its workflow and
recorded results without another Execute click. This includes vector and raster
inspection as well as tables. The long-term criterion is the complete task's
registered effects and inspection contract, not a filename extension or the
presence of the word CSV. Multiple compatible bounded inspections in one task
should eventually follow the same rule; the CSV pilot's single-step grammar is
an initial implementation restriction, not the intended product boundary.

Rename the composer preference to **Inspect on send**, with a brief description
of eligible read-only inspection tasks. Preserve its remembered preference and
the visible send behavior; do not introduce a switch for each format. Existing
OFF mode remains proposal-only. No default change is requested here.

A task containing any file creation/modification, database mutation, publication
or another consequential write stays a complete proposal and retains applicable
Allow writes → Authorize → Execute controls. Do not automatically run its
inspection prefix. Generated reports/exports are not made read-only simply by
calling them inspection. Ordinary saved chat/run/evidence records are application
metadata, and must be distinguished from dataset/external-service writes.

Read-only database/service inspection belongs to the requested general direction
when its explicit target, registered implementation, credentials/access policy,
bounded resource use and actual non-mutation behavior are established. This is
not blanket permission for arbitrary SQL, network requests or unregistered tools.
No live database/service checks are authorized by documenting this direction.
Unknown effects or unsupported inspection contracts keep the review/manual path
with a concrete reason, rather than silently claiming automatic support.

## Structural changes for implementation, later

1. **Generalize eligibility.** Replace the CSV-specific automatic eligibility
   branch with explicit registered inspection contracts: effects, typed source,
   applicable approval gates, resource limits and result/preview shape. A read-only
   label alone is insufficient. The existing registry remains authoritative.
2. **Add inspector adapters.** Reuse existing vector/raster execution and result
   services, extending their bounded-worker integration. Declare per-inspector
   byte/feature/pixel/time limits; do not copy table limits into spatial readers.
   Bind all relevant inputs for multi-file datasets and reject unsupported sidecar,
   external-reference or remote-access behavior. Avoid rereading data in several
   layers when one verified snapshot/handle can serve the operation.
3. **Generalize scope and bindings.** Resolve explicit user intent and typed
   targets without relying on CSV-specific wording. Validate the entire proposed
   inspection-only graph. Preserve source/contract/chat-revision binding, duplicate
   protection, cancellation and no-replay recovery; extend binding to each source
   and operation before allowing multi-inspection tasks.
4. **Reuse interface and CLI.** Keep one submit coordinator and durable-run engine.
   Show normal workflow progress and type-appropriate Outcome tables/maps/metadata.
   Unsupported scope stays visible with a reason. Do not add another LLM agent,
   execution engine, container or separate frontend workflow per file type.

These are moderate extensions of the current policy/adapter interfaces and source
binding, not a platform rewrite. Result rendering, write authorization, existing
saved workflows and the operation registry remain. Storage additions, if needed,
must be versioned and preserve earlier CSV submission receipts and run identities.

## Measurable acceptance

- With mode ON, one send inspects a temporary CSV, vector fixture and raster
  fixture in separate journeys, without Authorize or Execute; deterministic
  metadata matches the fixture oracle and no dataset/external target is mutated.
- Existing table/map/result views display the correct source, count/schema or
  CRS/extent/resolution as supported. Merely drawing nodes is not completion.
- A bounded multi-inspection task executes only its requested supported reads;
  a mixed write task runs no prefix automatically. Conservative approval gates
  remain enforced. Unknown/unbounded operations do not dispatch.
- Same-ID retries, reload and chat restoration start no additional operations;
  changed inputs/contracts, late responses and cross-chat scope are handled safely.
- Oversized, malformed, cancelled and interrupted cases give accurate recorded
  status and do not replay. Multi-file and externally referenced spatial inputs
  have explicit accepted/rejected cases; no silent uncontrolled data access.
- Interface and CLI share policy decisions. Run meaningful backend tests,
  `make test`, `make interface-validate`, isolated browser journeys and separately
  reported installed-model acceptance. Use temporary fixtures, not live services.

## Delivery order and next checkpoint

Finish this expansion within the **28.2 inspection interaction follow-up**; do not
rename it 28.3 or claim completion of learning acceptance. Remaining 28.2 work is
also to evaluate practical non-RL case reuse, typed failure feedback and focused
context-aware retrieval from the [learning direction](LEARNING_WITHOUT_RL.md).
Existing experimental fixed ranking is not proven learning or a trained policy.
RL can remain later; useful learning benefit still requires evidence.

The next numbered checkpoint remains **28.3 visualization expansion**: improve
inspection/processing outputs through connected table, map, chart and check views,
with clear coverage by output type, bounded summaries/paging and responsive
behavior. Confirm requirements and measurable acceptance before choosing a new
rendering/processing dependency. Large-data correctness/resource measurements
must precede claims of scale. Existing charts/maps are not replaced merely to
add another visual style.

Checkpoint 29 retains private source-backed domain knowledge/corrections;
cross-chat sharing stays 30+ and separately authorized. Existing capability,
learning, memory and demo gates are not removed. Codex/DeepSeek harness comparison
and reuse research remains deferred. The remaining design does not imply additional runtime support. No new models,
dependencies, Git actions or live-service changes are part of this slice.

## Verification record — single-dataset delivery

- `make test`: 1,961 passed after enabling loopback sockets for HTTP tests;
  the restricted run had 27 socket-permission failures, not operation failures.
- Final focused inspection checks also cover the additional raster metadata
  vocabulary and `.tiff` filename resolution added after full-suite collection.
- `make interface-validate`: passed; existing large-bundle advisory remains.
- Isolated submit browser journey: eight groups, including CSV and spatial
  automatic outcomes, OFF/mixed-write behavior, restoration and lost-response
  reconciliation. Only model completion is replaced.
- Installed `qwen3:4b-instruct`, temporary vector fixture: one model call,
  21,765 prompt bytes, 36.387 seconds model time; verified feature count/CRS.
- Same model, temporary raster fixture: one call, 21,737 prompt bytes,
  13.614 seconds model time; verified dimensions/band count/CRS.
- Both actual-model checks reused the same run on duplicate submission and
  performed no dataset writes, approvals or live database calls. Reports:
  `/tmp/actioncharter-vector-submit.json` and `/tmp/actioncharter-raster-submit.json`.

These narrow cases establish working examples, not broad model reliability,
large-data scalability, complete checkpoint acceptance or learned domain knowledge.

Same-chat follow-up: explicit filenames are now decoder-bound and independently checked before proposal storage. A stale GeoJSON path cannot be saved as the answer to a new TIFF-only inspection. Browser regression covers GeoJSON → TIFF → CSV in one chat; transcripts and prior runs remain preserved.
