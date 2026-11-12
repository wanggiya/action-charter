# Current implementation status

[Full-data delivery; F5 partial](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md); [resume](WORK_RESUME.md). [Goals](../docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md).

Updated: 2026-11-11

Phase 0 bug [#81](https://github.com/wanggiya/action-charter/issues/81):
[recorded inspection quality reports](../docs/INSPECTION_QUALITY_REPORTS.md) now render
legacy metadata facts and explicitly unperformed checks. New table scans collect
bounded basic distinct/repeated-value and whole-row duplicate counts plus numerical
candidate summaries. Shared report/MD/PDF paths reuse saved evidence, without a new
model call, download-time scan, authority or historical rewrite. Verification: make test 2,816 passed (785.18 s, 13 existing spatial warnings), final
10 focused report checks, frontend build/typecheck, strict source/compatibility
checks and isolated stable-ID browser/API/CLI/terminal passed. Owner real-file
report acceptance remains pending; no new real-owner-data execution or model
benchmark claimed.

R-series closeout: implementation and automated gates are complete. The owner has
reported startup, read-only `sample_orders.csv` inspection (six rows/five columns,
expected source, no write authorization) and refresh/reopen restoration passed.
[Acceptance record](../docs/R_SERIES_ACCEPTANCE.md#acceptance-record): two required
owner checks remain, Execution History navigation and frontend/terminal continuity.
Fresh-file authorization is optional and not manually tested. No new R-series code
is planned unless a demonstrated regression requires a fix. Owner IDs/model/timings
were not supplied; this report does not establish a real-model benchmark. Source/
compatibility gates rechecked on 2026-11-10, zero errors. Local environment metadata
has both legacy/current distributions and no installed `actioncharter` console script;
the repository launcher exists. Environment refresh remains a separate follow-up,
not another R-series coding gate. No installs or runtime changes in this doc update.
Real workspace cutover remains separately unapproved/unperformed; Phase 0 stays open.

P0-2b [owner cutover preparation](../docs/OWNER_WORKSPACE_CUTOVER_PLAN.md), tracked
under #79, is ready for review; actual cutover is NOT authorized by this preparation.
Read-only inventory: 44 runtime roots, 2,129 regular files / 27,742,154 bytes (26.46
MiB), six blocking dependency links in three old acceptance sessions. No other links,
hardlinks, special or unreadable entries found. Three SQLite stores passed immutable
read-only quick checks with no sidecars; eight existing locks were not held. No
launcher-port listeners or matching Compose-label containers were observed. This is
a point-in-time observation, not certification that every external writer stopped.
Existing migration preview correctly blocks links. Proposed private state/backup
parents are on the same filesystem with about 35.34 GiB free; reserve/recheck 256 MiB
for this snapshot. No reference to the three session IDs appeared in the 740 regular
runtime files outside those sessions. Plan preserves whole sessions separately, with
links intact, after an independently verified backup. Synthetic structural rehearsal
passed blocked/clean previews, link preservation, stable ID, copy/verify/archive and
prelaunch rollback. No real record copy, source/config/identity change, live DB/service
change, Git action or secret modification. Metadata/root-setting key presence and a bounded
runtime-byte ID screen examined; credential files untouched and values/content not
disclosed. Application code/tests unchanged;
R11 implementation gates below remain the preceding evidence. Two manual interface
checks and actual backup/cutover remain pending, as recorded above; Phase 0 is not complete.

R11 [compatibility retirement](../docs/R11_COMPATIBILITY.md), [#80](https://github.com/wanggiya/action-charter/issues/80),
implementation and required automated gates complete. Retired 290 obsolete
adapters and migrated maintained callers/launchers to native owners. The project has
613 modules: 496 native implementation modules and 117 supported public/schema/
SDK boundaries (60 package roots, 57 aliases). Historical R6 inventory, 94-schema,
original CLI/HTTP/MCP fixtures, registry IDs and generated SDK bytes remain unchanged.
Strict graph: 3,016 imports, zero upward/dynamic debt. The partition/caller gate rejects
unclassified or restored adapters and hidden implementation under old public roots.
Analytical worker packaging now copies native standard-library CSV/profile code;
its actual build context passed an isolated Python check without building an image.
Reserved candidate SDK overlays remain separate from native implementation packages.
Final `make test`: **2,808 passed (859.92 s; 13 existing spatial warnings)**.
Focused final group: 87 passed; frontend passed (5.44 s build; existing bundle warning);
stable-ID relocated browser/API/CLI/terminal journey passed, zero page errors, one
explicitly authorized temporary write. No new agent, data operation, UI or authority.
The literal historical zero-shim target is not claimed: required compatibility is
explicit supported API. [Combined manual acceptance](../docs/R_SERIES_ACCEPTANCE.md)
has partial owner confirmation; only history navigation and terminal continuity remain
required. R-series implementation/automated gates are complete
with the documented supported-compatibility boundary. Owner real cutover remains separate; Phase 0
is not complete. No Git, secret or live-service changes. Fixtures, not new live-model
or live-database evidence.

P0-2b [stable project identity](../docs/PROJECT_IDENTITY.md), [#79](https://github.com/wanggiya/action-charter/issues/79),
local implementation and required automated checks are complete. Explicit offline adoption binds
one UUID to source/state filesystem objects; legacy projects retain path ownership.
Verified same-filesystem source moves and verified state cutovers preserve identity,
canonical evidence/claims and historical references. Copies, substituted state, active leases
and stale approvals fail closed. Installed CLI supports explicit projects from another
working directory. No owner migration, Git mutation, agent/UI/dependency or new authority.
Cross-filesystem source transfers and host/container mapping provisioning remain future
work. Owner real backup/cutover remains separate; R11 completion is recorded above. Phase 0
is not complete. Current manual acceptance progress is recorded above. These identity
checks are temporary fixtures only; no new live-model/live-DB evidence.
Verified: 25 new identity cases, existing focused group 208 and final identity/CLI/
container group 37 (overlapping checks). Final `make test`: **2,796 passed (816.47 s;
13 existing spatial warnings)**. Frontend typecheck/build passed (4.59 s build,
existing bundle warning); relocated legacy and stable-ID browser/API/CLI/terminal
journeys each passed with zero page errors and one authorized temporary write.
Strict graph: 903 modules / 3,305 imports, zero upward/dynamic debt. Real checkout
status remains `legacy_path`, with no identity/config/audit files created.

R12 [action context and execution services](../docs/EXECUTION_CONTEXT.md),
[issue #78](https://github.com/wanggiya/action-charter/issues/78), implementation and required automated checks are complete;
owner manual acceptance/Git review remain pending. Frozen owner/run/budget contracts and local policy/clock/credential/queue
ports serve 70 explicit task entrypoints, HTTP dispatch, all 27 MCP ingress callbacks
and ordinary CLI callbacks. MCP tool schemas remain unchanged.
Nested/queued work retains context; exact domain approval remains mandatory. A separate
SQLite action ledger records processing/mutation actor/run lineage and references
without changing existing canonical records. Pure lookups use bounded transient query
telemetry; request threads inherit their server's explicitly composed service profile. Explicit event keys survive failure/restart and block repeat dispatch;
HTTP POST supports an optional Idempotency-Key header, which grants no authority.
Local broker issues nothing; cancellation retains existing safe boundaries. MCP audit
uses the existing writable trace mount; proposal-only CLI works with read-only roots.
35 new contracts pass; MCP/container/context group passed 116 and MCP/security 106;
recovery/parity 97. Final `make test`: **2,771 passed (793.66 s; 13 existing spatial
warnings)**. Frontend passed (4.36 s build; existing warning). Final relocated fixture
browser/API/CLI/terminal passed, zero page errors and one authorized temporary CSV
write. Strict graph: 902 modules / 3,288 imports, zero upward/dynamic debt; 407 adapters.
Both checkout audit locations remain absent after tests.
No new agent, operation, UI or server autonomy. Evidence is temporary fixtures only.
P0-5b [specialized ledger contracts](../docs/LEDGER_CONTRACTS.md), #77, remains complete:
2,736 tests (750.12 s), frontend/strict gate and isolated fixture journey passed.
[R9/R10](../docs/LEDGER_CONTRACTS.md#r9-and-r10-reconciliation) reuse delivered P0-3/P0-6.
Owner manual validation remains deferred until all R-series work is complete. P0-2b
identity follow-up is recorded above; owner real cutover and final R11 remain open; Phase 0 is not complete.
Earlier task evidence below is retained for traceability.

R8 [HTTP routers](../docs/HTTP_ROUTER_STRUCTURE.md),
[issue #76](https://github.com/wanggiya/action-charter/issues/76), is complete for implementation and
required automated checks. Composition is 172 lines, transport 84,
dispatch 103, error mapping 133 and largest router 198. The 21 GET branches/50 POST
paths, 16 request schemas, 24 original coordinator ASTs and 104 captured responses
retain their contracts. Six task-action owners hold the existing coordinators; inline
cache/reference coordination stays with execution. Public aliases, shared state and
selected-model/authority/exception boundaries remain. Focused API: 146 passed; boundary:
76 passed (ten new). Final `make test`: **2,709 passed (713.38 s; 13 existing spatial warnings)**. Frontend passed (6.06 s build,
existing warning); isolated relocated fixture browser/API/CLI/terminal passed with
zero page errors and one authorized temporary write. Strict graph:
893 modules / 3,209 imports, zero upward/dynamic debt; 407 audited adapters, 61 package roots.
No new agent/operation/UI/dependency/authority. Owner manual acceptance is explicitly
DEFERRED until the R series is complete; automated gates still run per task. Git review,
P0-2b/R12 and final R11 remain open; P0-5b completion is recorded above; Phase 0 is not complete. These are fixture
checks, not new real-model/live-database acceptance.

R7 [CLI command modules](../docs/CLI_COMMAND_STRUCTURE.md),
[issue #75](https://github.com/wanggiya/action-charter/issues/75), is complete for
implementation and required automated checks; owner manual acceptance/Git review
remain pending. Composition is 142 lines,
registration 290, largest command module 783. All 150 top-level commands, 165 help
screens and 110 original function ASTs match the pre-edit baseline. Eight small
registrars move intact; public app/module/installed entrypoints and named callbacks
remain. Existing tests are unchanged. Focused checks: 47 passed; existing CLI/Builder/
workspace/action checks: 227 passed; frontend validation passed (5.09 s build, existing
warning). Final `make test`: **2,693 passed (730.42 s; 13 existing spatial warnings)**. Relocated fixture browser/API/CLI/terminal
journey passes with zero page errors and one authorized temporary write. Strict gate passes: 862 modules / 3,091 imports, zero upward/dynamic debt;
400 audited compatibility adapters including 61 package roots. Installed CLI sample
inspection returns six rows/five columns. No new feature, agent, dependency, execution
engine, authority or UI change. Owner manual acceptance/Git integration remain pending;
At R7 completion, R8/R11/R12 and P0-2b/P0-5b were still open; current progress is recorded above. Phase 0 is not complete.

R6 [native ownership and layer moves](../docs/R6_COMPLETION_AND_ACCEPTANCE.md),
[issue #74](https://github.com/wanggiya/action-charter/issues/74), is complete for
implementation and required automated gates; owner manual acceptance and Git review
remain pending. Existing shared policy/ledger/contracts now have
core/platform owners; calculations and fixed workers stay in data/workspaces; model
roles, acquisition, analytical dialogue and replay coordination stay above them.
Native packages follow the declared layers. At R6 completion historical imports retained 391 audited
compatibility adapters, including 61 package roots; lower native imports of adapters
still fail the layer rule. Strict gate passes: **826 modules / 3,037 import occurrences,
zero upward dependencies and zero dynamic-import debt**. All 94 sampled schema exports
match; 1,918 of 1,921 original top-level definitions differ only by imports, with three
intentional routing/source-path changes. Existing test assertion ASTs are unchanged.
Frontend validation (4.28 s build, existing warning), Compose validation and final
relocated fixture browser/API/CLI/terminal journey pass: zero page errors and one
authorized temporary write. Earlier mock/public-port/recipe-namespace regressions were
repaired; all 35 diagnostic failures pass in replay. Final `make test`: **2,688 passed (728.54 s; 13 existing spatial warnings)**.
These are temporary fixture checks, not new real-model/live-database acceptance.
Manual validation is prepared after R6; R7 is ready to use the native owners directly.
No new agent/operation/UI/dependency, authority, secret or live-service change. R7/R8,
R11/R12 and P0-2b/P0-5b remain separate; Phase 0 is still open. Earlier R6a/evidence/
registry slices and their validation remain in their linked guides and CHANGELOG.

Earlier consolidation foundations remain implemented; their detailed slice evidence
is retained in the linked guides and CHANGELOG. R6 above supersedes their intermediate
dependency counts and remaining-ownership notes.

| Task | Delivered foundation | Full-suite evidence at that slice |
|---|---|---|
| R1 | [Explicit static dependency gate](../docs/IMPORT_LAYERS.md); no runtime authority | 2,501 passed, 722.32 s |
| R2 | [One platform configuration](../docs/PLATFORM_CONFIGURATION.md); immutable layout, lazy views and existing request precedence | 2,529 passed, 678.41 s |
| R3 | [Shared metadata/plan contracts](../docs/STORAGE_REPOSITORIES.md#r3-transaction-and-plan-contracts); unchanged transactions, identity and serialized plans | 2,555 passed, 708.70 s |
| R4 | [Shared bounded reader/worker and contracts](../docs/DATA_ACCESS_BOUNDARY.md); runtime authority/concurrency remains with actions | 2,581 passed, 735.04 s |
| R5 | [Shared task composition/lazy CLI delegation](../docs/TASK_ACTIONS.md#r5-shared-composition-and-evidence-boundaries); 213 imports through 146 service exports | 2,607 passed, 668.71 s |

Earlier R6 [controls/contracts](../docs/SHARED_EXECUTION_PRIMITIVES.md),
[evidence/storage](../docs/SHARED_CRITIC_EVIDENCE.md) and
[registry/metadata](../docs/TRUSTED_REGISTRY_BOUNDARY.md) preserve their separate test
records. Native ownership does not deliver stable project IDs/real cutover (P0-2b),
specialized append-only/concurrency contracts (P0-5b), entrypoint splits or server seams.
Fixture browser/frontend checks at these stages do not establish model quality or live
DB acceptance. Owner manual write acceptance remains pending.

Task-local metadata follow-ups use the active workflow source or ask when absent/ambiguous. Shared inspector format checks reject mismatches in plans, edits, saved workflows and recipes before reader dispatch. [Behavior/validation](../docs/INSPECTION_SOURCE_COMPATIBILITY.md).

Clarification responses now carry complete frontend diagnostics; older no-model clarification chats/receipts are completed on read without storage edits/replay. Equivalent explicit read-only `do/run/perform … on/of` wording uses shared metadata routing. Verified: 2,327 backend tests, interface validation and isolated fixture browser/API/CLI/PTY passed.

Explicit “Run a new read-only inspection of …” wording now uses the same closed metadata route as “Inspect …”; original text, full-request validation and inspection-on-send policy are preserved. Broader requests still use planning.

Diagnostics distinguish completed execution from unavailable standalone Critic review. Settings now expose its unchanged 15-second default as an explicit bounded future-request preference; planning and coordinated-report budgets are separate. Historical records remain intact with legacy-label guidance. [Validation](../docs/REQUEST_DIAGNOSTICS.md#execution-and-outcome-review-distinction-2026-11-02).

Phase 0 P0-2 implementation is complete: [workspace storage](../docs/WORKSPACE_STORAGE.md) covers internal runtime-store families through shared services and CLI defaults. Explicit roots, logical references, hashes, host-local ownership and session revocation remain enforced. Offline preview/copy/verification/cutover, optional legacy archival and guarded rollback are available; new SQLite WAL records also block rollback. Verified: **2,388 tests passed** (13 existing spatial warnings, 666.49 s), frontend validation, Compose config, shell syntax and relocated fixture browser/API/CLI/PTY (zero page errors). Disposable cutover proved a source-only root and restored chat/run identity. No real project records/configuration moved; owner checkout migration and manual acceptance remain explicit owner actions. These are fixture checks, not live-model/database claims. Phase 0 overall remains in progress.

P0-3 [shared PostGIS lifecycle](../docs/POSTGIS_LIFECYCLE.md), [issue #60](https://github.com/wanggiya/action-charter/issues/60), is complete. Existing facades share decision checks, fixed transactions, independent readers and seven immutable package stores. Detached snapshots bind stored bytes/names and returned metadata. Workspace-bound one-attempt claims and append-only journals distinguish rollback from uncertain commit. Public schemas, canonical hashes and CLI arguments remain compatible. Verified: **2,419 tests passed** (13 existing spatial warnings, 672.35 s), 193 focused checks, frontend/Compose validation and relocated fixture browser/API/CLI/PTY (zero page errors). These are fixture results; no live database/model acceptance or production-readiness claim. No new UI/MCP mutation entry point or real-record/Git changes; the issue was created with explicit owner authorization.

P0-4 [shared task actions](../docs/TASK_ACTIONS.md), [issue #61](https://github.com/wanggiya/action-charter/issues/61), is complete. Connected chat/submission, workflow review/authorization, durable execution and result services now have shared owners; API, CLI, chat and existing MCP entry points retain their contracts. Compatibility aliases share locks/context; actions load without the HTTP server, and the fixed spatial orchestrator calls shared operation actions directly. Verified: **2,447 tests passed** (13 existing spatial warnings, 688.52 s), frontend validation and relocated fixture browser/API/CLI/PTY (zero page errors). Transport parity covers default/relocated roots, identical reviews, one CLI execution and API/chat/MCP outcome reopening. No new operation/agent/UI, real-record migration, live DB/model acceptance or Git mutation. P0-5 repository work follows below; legacy Advanced/assurance, settings relocation and full router restructuring are separate.

P0-5 [storage repositories](../docs/STORAGE_REPOSITORIES.md), [issue #62](https://github.com/wanggiya/action-charter/issues/62), is complete. Closed metadata transactions and SQLite/file adapters serve operational chat/history/submission/settings/view/diagnostic clients, durable runs and saved-plan access. Formats, IDs, hashes, raw legacy compatibility, revision checks and authority remain; reads use coherent snapshots. Verified: **2,480 tests passed** (13 existing spatial warnings, 732.26 s), 33 new repository cases (4.10 s), 215 focused checks (80.01 s), frontend validation and relocated fixture browser/API/CLI/PTY (zero page errors). These are fixture results, not live DB/model acceptance. No new remote backend, dependency, agent/UI, live migration or Git mutation. Specialized authority/evidence/ranking stores, legacy JSON writing and local leases retain their existing implementations. P0-6 frontend work follows below; Phase 0 overall remains in progress.

P0-6 [frontend workspaces](../docs/FRONTEND_WORKSPACES.md), [issue #63](https://github.com/wanggiya/action-charter/issues/63), is complete. App is now composition over workspace controllers/views, a provider-owned shared state store, local transient state, pure projections and unconditional effects. Existing layout, navigation, storage keys and backend authority remain. Current chat identity is explicit for run lookup; coupled UI transitions batch. Verified: **2,483 tests passed** (13 existing spatial warnings, 938.96 s), type/build and nine focused checks; relocated browser/API/CLI/PTY, graph/Planner, write-policy/authorization and development hook-refresh journeys passed with zero page errors. Browser evidence uses fixture models and temporary data, not live DB/model acceptance. Owner subsequently reported the manual frontend smoke checks passed. No new dependency, agent, operation, visual redesign or Guided mode. Phase 0 overall is unfinished.

P0-7 [active roadmap](PRODUCT_ROADMAP.md), [issue #64](https://github.com/wanggiya/action-charter/issues/64), is complete. Current phases/dependencies and retained T01–T15 requirements are separate from the complete [historical roadmap](../docs/development/ROADMAP_HISTORY.md). Memory/learning alternatives and unresolved decisions remain discoverable, not newly implemented. Snapshot link rebasing reconstructs all 113,332 original bytes and SHA-256; the active roadmap was 14,788 bytes at delivery and retains its 64,000-byte maintenance target. Verified: 545 local links/151 fragments, 12 context checks (1.02 s), and **2,483 tests passed** (13 existing spatial warnings, 682.93 s). The current context-pack builder does not load the roadmap; no prompt, agent, data or runtime behavior changes, so frontend/browser checks were not repeated for that documentation-only task. A pre-existing historical document-content anomaly is recorded in the history index, not repaired there. R1 above now tracks the remaining Phase 0 gates; do not automatically start Phase 1.

[28 accepted](../docs/development/checkpoints/CHECKPOINT28_CLOSEOUT.md): exact inspections, batches, discovery; [resume](WORK_RESUME.md).

Checkpoint 26 [closeout](../docs/development/checkpoints/CHECKPOINT26_CLOSEOUT.md) and 27 [acceptance](../docs/development/checkpoints/CHECKPOINT27_EVALUATION.md) preserve delivered reuse, results, charts/geometry, runtime writes and persistent graph layout. Acceptance limited; packaging after demo; cross-chat 30+.

[28.1 bounded pilot](../docs/development/checkpoints/CHECKPOINT28_1.md): per-chat default-OFF acquisition, Planner-owned closed text definitions, resource-bounded synthetic/held-out checks, advisory Critic, explicit exact-digest install and normal authorized CSV execution. No arbitrary Python/dependency installation. Fixture/model pilot passes; broader reliability unproven. Learning benefit/RL, large-data visualization and 29 private knowledge remain pre-demo limits.

[28.3 spatial](../docs/development/checkpoints/CHECKPOINT28_3_SPATIAL_VIEWS.md): spatial views, facts, named saved-run outcomes; broader gates open.

## Product boundary

ActionCharter is a local single-operator alpha for governed spatial and tabular workflows. Models propose and assess; typed services, deterministic policy, exact operator decisions, runtime validation and durable evidence establish permission and results. Conversation/context text, historical decisions, discovered library names and package installation never authorize execution. CLI coverage remains broader than the default workflow graph. This is not a packaged desktop application or a hardened multi-user service.

## Checkpoint 25 — contracts, discovery and installed adapters

The shared catalog describes the 25 implemented builtin operations and installed adapters: stable IDs/readable names, typed parameters/results, input/output contracts, completion dependencies, runtime requirements, effects, gates and preview/validation contracts. Existing skill bytes, workflow formats and historical digests remain compatible. Planner/graph support 18 main operations plus installed CSV adapters; other catalog entries retain their existing service/CLI paths. Settings Operations & libraries and CLI use the same services. Operation names and capability metadata refresh after installation.

Discovery automatically inventories installed Python distributions and statically parses declared .py/.pyi files for functions, classes, methods and properties. It does not import/evaluate candidate modules, decorators, defaults or annotations. Private declarations are optional, controlled by the existing sliding ON/OFF switch. Settings uses shared surface colors; scan inventories and installed adapter records persist in the same project across restarts, without reinstalling or granting execution authority. Native symbols, dynamic/inherited/reexported functions, missing editable manifests and scan limits are reported as incomplete; this is not proof of every runtime library export. Scans cap source bytes/files/time/candidates and preview text; immutable project-local snapshots support paginated search. Candidates are non-executable and never become dispatcher entries from a model name or scan result.

A small tested JSON package installs ext_order_identity through a fixed pandas CSV projection adapter. Tests use temporary fixtures; installation repeats tests, creates a digest-verified metadata record, and neither installs dependencies nor approves/runs a workflow. Proposals and runtime bind the exact installed package hash; writes use the same exact authorization, create-only outputs, independent verification and lineage as builtins. Arbitrary code/entrypoints, unknown adapters, invalid signatures/contracts, changed records, conflicts and unsafe links reject. The existing Builder candidate/test/promotion lifecycle remains separate. General Python-code adapter loading, marketplaces, package upgrades/uninstallation and native-symbol enumeration remain outside this delivery.

Operator follow-up: Settings lists persisted verified scan inventories with expandable library/function groups; review, selected-operation and outcome cards show dataflow arrows. Examples have a function-based index while historical paths remain intact. Later checkpoint 26/27 sections supersede the original agent-history and outcome-preview proposals.

See [checkpoint 25 guide](../docs/development/checkpoints/CHECKPOINT25.md) for contracts, bounds, package authoring, CLI parity and operator acceptance. Checkpoint 26 now includes the recipe/recovery slice below; checkpoint 27 retains laptop/PC prototype preparation. No Git/publication or live-data action is implied.

## Planner and execution

Checkpoint 26.1 revision: each conversation is one automatic task with private transcript/plan memory. Domain changes retain the same chat context; new chats start separately. Task creation/selection and cross-chat linking are removed. Local SQLite saves conversation/memory atomically; legacy JSON and former shared-task records remain preserved. Verified: 1,530 tests, frontend validation, four private-chat and six CSV browser groups. No extra model/dependency/background agent is added. Indexed core facts, summaries, corrections, methods and remaining orchestration are unfinished. See [current acceptance](../docs/development/checkpoints/CHECKPOINT26_CONVERSATIONS.md).

Planner agent is the primary entry beside the editable workflow graph. Optional skills constrain additions; automatic selection includes registered supported operations, retaining mandatory load dependencies. Typed plans normalize bare filenames under data/input and reject unsafe scope. JSON/schema/policy failures receive one bounded correction with the rejected candidate and safe specific findings. A closed legacy plan-only response is also validated through the same policy. Requests, titles and context remain descriptive, never execution authority.

Chat controls now say Saved chat history and Chat memory; OFF preserves the workflow/transcript. Context sent to Planner separates next-request settings from actual completed-request inclusion counts. Cross-chat memory is deferred to checkpoint 30 or later, with no sharing work in 26–29; see docs/DEFERRED_CROSS_CHAT_MEMORY.md.

Full conversation transcripts persist; recent excerpts cap at 6 KB and full prompts at 64 KB. Previous-message inclusion is optional; current typed workflow remains explicit. Model errors distinguish timeout, HTTP rejection/configuration and validation failure. Optional MODEL_REASONING_EFFORT supports compatible Ollama thinking control, without establishing live-model response time or quality. Startup loads source lists and restores remembered existing saved scope, protecting open plans/edits and making no model call, new save, approval or execution.

Orange Authorize reviews affected operations/resources and records exact plan/recipe decisions for 30 minutes. Yellow Execute independently rechecks scope and authority. Read-only vector/raster/CSV inspection requires no invented write approval. Supported writes use the shared recipe runner and output verification. Optional typed dependencies preserve old digests when absent and compile DAGs in reviewed topological order; references, duplicates, cycles and required ancestry are validated. Scheduling remains sequential. Context & intent/legacy planner integration is narrower than the main saved-workflow path.

## Spatial and tabular behavior

Registered vector/raster inspection/conversion, PostGIS workflows and bounded GeoServer service/CLI paths remain. The operator reported the checkpoint 23 PostGIS flow working historically; no new live-service check is implied. The host launcher reads allowlisted .env settings and resolves host .secrets file paths, preserving terminal overrides and explicit write flags. Default ports remain frontend 5173 and API 8765; startup neither installs dependencies nor approves work.

Checkpoint 24 adds inspect/read CSV/TSV, column selection, row filtering, missing handling, cardinality-checked joins, grouped numeric aggregation and export. A flat GeoJSON-attribute bridge explicitly drops geometry/CRS after inspecting the same source. The first CSV transform reads the original path: inspection returns metadata, not a table artifact. Later transforms bind completed validated ancestor CSV hashes. UTF-8 comma/tab reads preserve string identifiers and only empty fields are missing. Files/rows/columns/cells/memory/previews are bounded. Every transform creates a fresh CSV with exact authorization and source/output SHA/count/column checks; replacement and arbitrary pandas expressions are prohibited. Failures identify stopped steps and observed partial output hashes, with no automatic retry. The operator confirmed expected six-input-row regional totals (North 30/2, South 40/1, Unknown 30/1).

## Workspace and graph

Saved-plan selection restores exact current scope, clearing stale presentation/review state without new authority. Equivalent bare/relative source references share one displayed input resource without changing stored arguments/digests. Blue input nodes differ from cyan tools; long labels remain contained and full paths are available in the inspector. History, review and Outcome dock beside the graph. Desktop Planner/information widths can be dragged; per-operation outcomes and saved-plan/recipe/run source groups collapse independently. Matching recorded workflows show a read-only outcome block; edits/different scope cannot claim that result. Selector labels are larger. Appearance controls preserve the current plan; outline uses tinted edges and readable text, with solid fill/text options.

Add/search, inspector parameters, delete/move/connect/disconnect and Blueprint-inspired pins remain governed edits. Drag uses direct previews; graph connections express completion dependencies, while file/data parameters remain explicit. Editable JSON arguments must be applied/validated before storage/approval. Shift+A adds, canvas-focused Delete removes, Alt-click breaks links and Ctrl-drag transfers links with cycle checks. These are adapted gestures, not Unreal's engine language. Zoom/legend defaults are lower-left and scrollbars are consistent. A sliding dark Off/On history switch retains keyboard accessibility.

Main-workflow Snakemake export/static verification binds an original saved workflow and independently verified completed evidence, reusing results rather than rerunning source operations. Export needs fresh exact scope and write mode. Static package validation does not prove Snakemake replay; no new execution authority is inferred.

## Verification and remaining work

Verification counts and limits are recorded in delivery guides. Browser fixtures cover results, CSV calculations, retention, Planner and adapters; fixture models are not live-model acceptance.

Playwright is pinned for development. Engines/minimal-Linux runtime stay in ignored project-local test directories; profiles/data are temporary and separate from normal/shared browser caches. Runtime requires no browser test tools. See the checkpoint 25 guide.

Checkpoint 26 now adds JSON recipe composition, optional Builder→fixture tests→Critic preparation, durable runs, cooperative cancellation, bounded intermediate previews and recovery proposals. Remaining reads can resume; writes use fresh targets and fresh authorization. No automatic write reuse/retry. [Delivery and acceptance](../docs/development/checkpoints/CHECKPOINT26_RECIPES_AND_RECOVERY.md). Transactional/write-intermediate resume, parallel scheduling, broader memory and laptop/PC release evaluation remain incomplete.

## Record navigation

[Architecture](ARCHITECTURE.md), [roadmap](PRODUCT_ROADMAP.md), [documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md). This overview feeds model context; full-file identity still covers the preserved history below. Historical next steps are not current scope.
28.2: [paired evaluation](../docs/development/checkpoints/CHECKPOINT28_2_EVALUATION.md), ranking OFF. Direct read-only Execute; writes need Allow writes/Authorize/Execute. Initial model trial OFF 3/6, ON 2/6; focused 3/3 both modes; ranking benefit unproven.

<!-- historical-checkpoints -->

# Checkpoint history

Historical checkpoint descriptions moved to [docs/development/STATUS_HISTORY.md](../docs/development/STATUS_HISTORY.md) (2026-11-01) to keep this file within the context loader's size limit. Add new history entries there, not here.
