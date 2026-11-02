# Current implementation status

[Full-data delivery; F5 partial](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md); [resume](WORK_RESUME.md). [Goals](../docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md).

Updated: 2026-10-30

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
