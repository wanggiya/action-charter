Chart interaction: add consistent click/keyboard details across all ten chart types, including verified aggregate slices and histogram/box/summary statistics. Outside click, blank-chart click or Escape dismisses details; changing data/axes clears them. Existing table-row linking stays independent.

Runtime/UI follow-up: report the actual Planner contract in API health/startup and check it before a conversational model request. An incompatible runtime is blocked before model invocation. Remove the extra Information button; select a block to reopen the Inspector and X to close it.

Planner/UI follow-up: focus CSV calculation contracts for broad explicit skill selections; mark runtime diagnostics csv-revision-v3 and identify missing markers as legacy API. Add an Information-panel X, width recovery and reopening from its button or node selection.

Planner revision follow-up: recognize “Add a calculation creating doubled = amount * 2” and “Do not use PostgreSQL or PostGIS”; use the validated existing CSV inspection to scope filename-free calculation follow-ups. Preserve bounded correction, typed argument checks and separate authorization.

Planner follow-up: CSV requests that explicitly exclude PostgreSQL/PostGIS no longer expand descriptive spatial schemas solely because of those negative mentions. Unexpected-field correction now instructs removal of undeclared properties without exposing unknown field names. Explicit skill selections and backend validation remain unchanged.

# Checkpoint 27.3 / 27.4d — analysis and stable graph layout (2026-10-20)

- Preserve chat graph positions across restoration; reserve free space for new operations, outcomes and Critic nodes in both orientations. Add return-lane connections and distinct recorded/advisory evidence styling.
- Put the warning Allow writes switch beside Authorize/Execute, sharing Settings' backend session policy and stale-authority invalidation.
- Add horizontal bar, column, line, area, pie, donut, scatter, histogram, box and summary views, scoped presentation settings and explicit verified full-CSV count/sum/mean/min/max grouping through shared API/CLI services.
- Capture bounded WGS84 lines, multipart geometry, polygon holes and literal attributes alongside compatible point snapshots; link map/table/attribute selection without current-file or tile reads.
- Fix selected prerequisite closure, explicit source-path grounding, omitted-inspection/arithmetic coverage and occupied-CSV proposal correction; narrow spatial sequences use typed argument decoding.
- Index existing Critic method suggestions separately from immutable successful-method metadata, with provenance, own-chat visibility and fail-soft status. Request structured assessments with a 15-second request bound.
- Verified 1,825 backend tests and final-profile six correct actual-model workflows with changed reuse fixtures. Optional Critic timed out in all six; earlier failures and limitations are preserved in the technical acceptance report.
- Add an isolated actual-model evaluation driver and extend chart/map/layout/write-policy regression journeys. Broader BI/GIS rendering is planned as 28.3; capability/learning/private-memory pre-demo gates remain unchanged.

# Checkpoint 27.4c — Results workspace and verified CSV inspection

- Refine result views into connected page tabs with a shared content surface, clear page headings and keyboard tab navigation; preserve operation selection and view state.
- Replace nested Outcome cards with operation-selected Overview/Table/Map/Chart/Checks views; add View output, a visible divider, expansion and full-width narrow-screen access while preserving the graph.
- Add loaded-row search/sort, column visibility, 25-row paging and linked table/chart/point selection. Maps gain pan, zoom, Fit extent and selected-point coordinates; unsupported views explain their limits.
- Add explicit hash-verified bounded CSV artifact reads using the same API/CLI service. Preserve recorded delimiters, reject changed/missing/unsafe artifacts and mismatched scope, and ignore delayed responses after context changes. Reads do not hold the execution-progress lock.
- Keep saved snapshots as default. No implicit model/operation/database/tile request or permission change occurs during visualization; larger reads require the explicit Load verified CSV action. Full-file analytics, broader geometry, export and remaining checkpoint gates stay open.
- Verified 1,804 backend tests, frontend typecheck/build and 63 synthetic browser cases, including 10 Results cases and existing CSV/adapter/Planner/retention/calculation/visualization journeys. No live-service acceptance or publication is claimed.

# Checkpoint 27.4b — recorded charts and point maps

- Add collapsible per-row bar/scatter charts from saved table previews, bounded to 20 rows/32 columns with explicit omissions, sample scope and numeric display limits.
- Capture first-layer WGS84 Point snapshots during shared vector inspection, capped at 32 examined features. Show offline longitude/latitude maps, CRS, skipped/truncated counts and a geometry snapshot digest; unsupported and legacy data remain explicit.
- Bind visualizations to existing recorded operation/chat/plan/run scope. Opening views makes no model, workflow, file, database or tile request; drafts inherit no results. CLI receives the same vector snapshot contract.
- Keep polygons/lines, multipoints, projected/reprojected or multilayer maps, arbitrary raster/database views and full-file chart aggregation outside this slice. Existing pre-demo capability/learning/memory gates are unchanged.
- Verified frontend typecheck/build, 1,792 backend tests, eight visualization and 12 recorded-calculation browser cases using temporary fixtures. Narrow-panel screenshots were inspected; model responses are fixtures, not live-model acceptance.

# Optional capability acquisition — design clarification only

- Record checkpoint 28.1 as OFF by default, explicitly enabled per task and triggered by a demonstrated capability gap after existing operation/recipe lookup, not workflow size alone.
- Define bounded candidate/test responsibilities, persistent reuse of accepted versions, separate installation/write/execution authority and measurable effort/correctness evaluation. No acquisition feature is implemented by this update.
- Preserve pre-demo acquisition/learning/private-memory gates and checkpoint history; record pending graph placement/connections and prominent warning-icon write controls as checkpoint 27 work.

# Fix evidence-only recipe authorization

- Preserve conservative plan gates when compilation otherwise produces an evidence-only recipe with no trusted approval-required operation. This fixes `recipe has no approval-required steps` during Authorize.
- Add optional recipe-step `additional_approval_required`: it can strengthen registry requirements, never lower them. Omit false defaults from canonical serialization; ordinary writer recipes retain existing identities. Corrected evidence-only recipes get new scope/digests and require fresh authority; historical records are preserved.
- Recheck every approved step's authority before dispatch. Keep Authorize free of execution and retain session/revision/expiry checks.
- Verified 1,787 backend tests, frontend typecheck/build and browser reproduction of the failing authorization shape, using temporary fixtures and mocked PostGIS validation. No live database/service operations.

# Fix development hook-order failure during authorization

- Reproduce the exact App hook-order mismatch when a plain TypeScript hook gains an effect during Vite hot reload.
- Reload safely for source `use-*.ts` changes; restore saved chat/workflow state without automatic authorization or execution. Unsaved UI edits may reset during development updates.
- Add an isolated Vite/browser regression covering initial authorization and post-update restoration/authorization, with no execution or React console errors.
- Verified: 1,784 backend tests, frontend typecheck/build, both development hook-refresh cases and seven Critic browser cases passed.

# Advisory Critic graph visibility — checkpoint 27 slice

- Show requested recorded assessments as a secondary dashed Critic branch, separate from execution status, validation and executable operations.
- Add compact findings/limitations and exact-run provenance; restore pending reviews with scoped read-only polling and link matching history records to the graph.
- Preserve successful outputs when Critic is unavailable; draft edits and unrelated chats cannot inherit a recorded assessment.
- Isolate backend test policy storage from a running operator session; bind plan approval authority to the project owning approval storage.
- Broader authorization interaction, enrichment/evaluation, generated capabilities, learning/RL and advanced memory remain unfinished.
- Verified 1,784 backend tests, frontend typecheck/build, seven Critic, 12 calculation/results and five runtime-write browser cases with temporary fixtures. Live-model quality/latency remains unverified.

# Runtime write controls — checkpoint 27.7 implemented slice

- Settings now changes write availability in the running API, with confirmed status, stale-update rejection, optional read-only lock and CLI control. No routine restart is needed; model configuration still requires one.
- Bind new managed approvals to session/revision through separate durable receipts. Recheck write dispatch, reject cached/direct bypasses and stale authority, preserve active-operation verification/partial evidence and readable old records. No overwrite operation is added.
- Main workflow/recipe and approved MCP paths integrate the policy. Specialized legacy GeoServer/promotion/rollback writes remain fail-closed in managed sessions pending their own binding support; standalone legacy explicit startup mode remains separate.
- Operator revised the demo gate: generated capabilities (28.1), learning/RL (28.2) and advanced private memory (29) must be implemented and validated before demo or real-data testing. These are unfinished; current evaluation uses synthetic fixtures. No Git/publication/live-service action.
- Verified 1,783 backend tests, frontend typecheck/build and 23 temporary-fixture browser cases; no live-model/database/service acceptance is implied.
- See docs/CHECKPOINT27_RUNTIME_WRITES.md for implementation boundaries and manual acceptance.

# Record runtime write controls and checkpoint 27 demo gate

- Document planned 27.7 runtime availability, shared session/revision enforcement, Settings status/switch, authorization invalidation, operation boundaries, CLI/migration requirements and measurable temporary-fixture acceptance.
- Preserve checkpoint numbering; deliver 27.7 before remaining evidence, visualization, evaluation and demo preparation. Separate overwrite from enabling writes. Keep RL/code acquisition/advanced memory outside demo prerequisites and packaging implementation after data/demo acceptance.
- Documentation only: no permission switch, authorization change, new operation, runtime agent or live-data action is implemented here. See docs/RUNTIME_WRITE_CONTROL_DESIGN.md.

# Recorded operation results — checkpoint 27.4a

- Show selected-operation formula, input/output paths, bounded table rows and readable independent checks; use shared cards in Outcome and durable history. Keep raw/audit details collapsed.
- Restore evidence by both chat ID and exact plan digest; explicit history selection binds the run, pending edits remove old evidence, and stale reads cannot replace a newer scope/selection. Guard delayed startup graph loads against replacing a restored chat; bind Critic commentary to the selected run.
- Report write-tools availability with the existing launcher flag. New CSV transforms retain up to 10 preview rows within the unchanged byte/cell limits; historical previews are preserved. No model call or execution is needed to inspect results.
- Verified 1,769 backend tests, frontend typecheck/build, 12 calculation browser cases and six recipe/cancel/recovery/restart cases with temporary files and fixture models, plus nine intercepted-API UI cases. Maps/charts, agent evidence evaluation, capability acquisition and optional learning remain future work. See docs/CHECKPOINT27_RECORDED_RESULTS.md.

# Record post-calculation delivery gates

- Document remaining checkpoint 27 result usability and agent/evidence evaluation, followed by proposed bounded capability acquisition, optional learning-policy experiments and private domain knowledge/corrections. Preserve checkpoint history and the 30+ cross-chat decision gate.
- Distinguish implemented services from future capabilities; no new agent runtime, generated-code executor, RL policy, model training or sharing is enabled by this documentation.

# Ground Planner reuse claims in available provenance

- Constrain generated reused_recipe_ids to supplied successful examples or successfully inspected sources; omit the optional field when no source is eligible. Refresh prompt/decoder constraints after each discovery exchange and before correction.
- Keep backend provenance/relevance checks and one correction; repeated unsupported claims report planner_reuse_unverified with useful model guidance and preserve plan/transcript. Ordinary planning requires no manual recipe selection.
- Preserve focused calculation hints across correction and report actual per-call prompt/schema sizes. Add discovery, history-preservation, relevance, HTTP and browser failure regressions; no extra model call or execution authority.
- Verified 1,769 backend tests, frontend validation and 13 isolated browser cases. One actual qwen3:4b-instruct planning check passed in one call (52.08 seconds) with no authorization/execution.

# Calculation request coverage after historical-record inspection

- Confirmed that a saved plan claimed doubled-column creation but actually contained only inspect_csv; the frontend did not lose a stored formula. Historical records remain unchanged.
- Check explicit calculated-column request coverage before accepting new conversational proposals. A missing operation uses the existing single correction attempt; repeated omission reports planner_scope_incomplete and preserves the saved workflow/transcript without execution.
- Clarified that Planner may propose approval-required operations without receiving execution permission; shortened simple calculation instructions without changing manifest permissions or the operation allowlist.
- Calculation-focused decoding binds inspection/calculation/export arguments to skill IDs, namespaces expression definitions and uses closed alternatives for exclusive CSV sources; full backend checks and the complete allowlist remain.
- Simple single-column requests can constrain the requested operation skeleton; the model still supplies all semantic arguments. General workflows retain flexible steps. One actual qwen3:4b-instruct check restored the temporary historical failure and produced the correct two-step plan/formula in one call (34.44 seconds), without authorization or execution.
- Added an isolated historical-restoration browser regression followed by actual corrected calculation, exact authorization, output verification and refresh. Verified 1,764 backend tests, frontend validation and six isolated calculation browser cases. This is a narrow coverage guard, not general semantic correctness.

# Inspector operation and audit clarity

- List actual current-plan operations with formulas and selectable graph links; flag an explicit calculation request whose saved plan lacks the calculation operation.
- Show readable formulas in calculation nodes and authorization review. Collapse raw arguments, group authority/observed facts and keep one performer line; move compact task history below operation content.
- Presentation only: missing operations are never fabricated and approval/execution rules remain unchanged.
- Verified 1,744 backend tests, frontend typecheck/build and 11 isolated calculation/CSV browser cases with real temporary-file execution and fixture model replies.

# Planner decoder schema and response diagnostics

- Conversational Planner now sends its structural Reply schema to the model endpoint. Decoder patterns/bounds are omitted for local grammar compatibility; full backend validation remains unchanged.
- Added explicit MODEL_RESPONSE_FORMAT compatibility mode, no silent fallback/retry, safe response-shape/finish/size diagnostics and separate output-token truncation handling.
- Required conversational proposal gates now bind upward from trusted registry contracts without recording authorization; repeated calculation schema unions are shared to reduce prompt overhead.
- Corrected misleading root JSON findings labelled as a plan-field type error. Truncated discovery replies cannot dispatch tools; existing workflows remain preserved.
- Verified 1,744 backend tests, frontend validation and 17 browser fixture cases. One real qwen3:4b-instruct planning check passed in one call with the exact request; no authorization/execution. See docs/PLANNER_STRUCTURED_OUTPUT.md for evidence and limits.

# Calculation planning repair follow-up

- Fixed schema focusing for “multiplied,” “divided” and new numeric columns; simple calculation requests receive relevant contracts without changing the full operation allowlist.
- Added a complete non-executing calculation reply example and grounded single correction, without automatic fallback plans or extra retries.
- Repeated schema-repair promises now report planner_repair_deferred, preserved schema findings and safe effort diagnostics instead of asking users for technical approval rules. Existing plans and authority boundaries remain intact.
- Verified 1,726 backend tests, frontend validation and 11 targeted browser fixture cases. Exact-wording, repair/preservation and HTTP regressions cover a deferral before successful planning. Live-model reliability remains unverified.

# Bounded calculations and cumulative Planner effort

- Added calculate_csv_columns through the shared table registry/runner, Planner, graph formula editor and CLI: numeric arithmetic/comparisons/conditionals, explicit missing behavior, fresh-output approval and independent row checks.
- Enforced definition size/complexity and shared four-model/two-discovery attempt budgets; optional launcher deadline and actual token-usage receipts. Explicit conversational recipe/assessment calls share the budget; the opt-in post-turn helper remains separately accounted.
- Verified 1,711 backend tests, frontend typecheck/build and 23 browser fixture cases; added a typed calculation example. No arbitrary Python generation, new agent/MCP server, RL or live-data changes. See docs/BOUNDED_CALCULATIONS.md.

# Planner-owned recipe discovery and reference browser

- Added bounded read-only search/inspect capabilities to the existing Planner through typed JSON exchanges and shared API/CLI services. Two discovery exchanges plus final generation/one correction cap Planner inference at four calls per turn; direct planning requires no extra discovery calls.
- Sanitized catalog structures omit registered private literals/descriptions/fixtures. Only parameterized/schema-enum definitions can compose automatically; other structures need current bindings in a normal validated plan. Own-chat evidence/history scope and final contract checks remain enforced.
- Recipe browsing is optional reference. Secondary discussion shortcuts sit under More actions; manual composition stays in Advanced and is labelled Validate composition and open draft. Replies/receipts identify reported reuse without granting authority or claiming new-data success.
- Added discovery/fallback/privacy/budget/timeout/contract-change and API/CLI tests, plus ordinary-chat browser discovery and fresh-authority execution. Verified 1,663 backend tests, frontend typecheck/build and 35 browser fixture cases. Local-model quality and remaining checkpoint 27 features are still unverified/pending. See docs/CHECKPOINT27_DISCOVERY.md.

# Checkpoint 27.2 — focused recipe browsing and Planner reuse

- Reusable recipes now switches between Recipe list and Keywords, showing one body at a time. Keywords open a filtered summary list; source evidence and Advanced authoring remain in details rather than the browsing list.
- Planner retrieves up to three current, evidence-matching own-chat methods (8 KB cap) and proposes ordinary validated adaptations. History OFF disables automatic retrieval; explicit own-chat selection remains possible. Old output/credential/authority bindings are excluded from examples, and changes during generation invalidate them. Interface and existing CLI share the same service.
- Reduced unnecessary prompt overhead with focused domain schemas, preserved allowlists/constraints, removed redundant rules/schema display titles and kept safe CSV output allocation explicit. Added safe stage/bytes/timing/schema-count diagnostics on model failures and successful receipts. Timeout configuration is unchanged; local-model latency still needs evaluation.
- Verified 1,653 backend tests, frontend typecheck/build and 35 browser fixture groups covering exclusive views, keyword filters, own-chat adaptation, different CSV inputs, fresh authority, timeout preservation and existing CSV/private-chat/recovery behavior. Remaining checkpoint 27 features stay documented as pending; no Git/publication or live-service change performed.

# Checkpoint 27.1 — automatic successful-workflow retention

- New durable executions capture operation contracts before dispatch and automatically retain eligible successful method metadata, tags and source evidence. No model call, authoring request or registration is required.
- Added transactional bounded indexing, semantic grouping with distinct run evidence, current-contract diagnostics, own-chat discovery and fail-soft indexing-only retry. No credentials, raw bindings, transcripts or reusable authority are copied into the index. Optional Critic failure cannot block saving.
- Reusable recipes shows automatic successful records alongside existing generalized templates, with operation order and recorded-outcome inspection. Existing Advanced controls remain. Shared API/CLI services preserve parity; runtime index is excluded from Docker build contexts.
- Verified 1,646 backend tests, frontend typecheck/build and 17 browser fixture groups (5 retention plus 12 existing Planner/recovery groups). Planner retrieval/adaptation and later checkpoint 27 work remain planned; old runs without snapshots, synchronous legacy execution and Snakemake export are not auto-indexed. See docs/CHECKPOINT27_RETENTION.md.

# Checkpoint 27 planning record — documentation only

- Recorded dependency-ordered automatic successful-workflow retention, Planner adaptation, optional Critic enrichment, artifact visualization, actual laptop evaluation and prototype/demo preparation, with measurable acceptance.
- Assigned human/Planner/Critic/backend responsibilities; preserved minimal routine human interaction, exact authority, optional Advanced generalization and deferred cross-chat memory.
- Linked the plan from README, current status and roadmap. No runtime, UI, dependency, Git or publication behavior changed.

# Agent-container CLI startup repair

- Fixed eager interface-package imports that made lightweight agent CLI startup require optional GIS libraries. Existing public API exports load lazily when requested; GIS execution still requires its declared runtime dependencies.
- Added fresh-interpreter regressions that block GIS imports and exercise the five existing agent-image contracts: CLI help, Planner/Executor/Critic manifests and recipe catalog. Full backend suite: 1,625 passed. Docker image revalidation awaits CI because no local daemon is running.

# Right-side outline action material

- Right-side header and authorization actions explicitly retain the shared outline edge gradient. Disabled header actions dim their text/icon and border rather than fading away the whole gradient; their disabled behavior is unchanged.
- Browser acceptance checks every header action plus the enabled Execute control after authorization. Solid-fill styling is unchanged.

# Workflow camera and recipe material follow-up

- Replaced fixed wheel jumps and competing CSS transitions with proportional frame-based zoom anchored at the pointer (within scroll bounds); buttons use the same camera animation, with reduced-motion support.
- Camera previews avoid rendering the full interface per frame; node dragging uses the displayed scale, retains fractional positions and reduces costly visual effects during interaction. Starting a pan or node drag stops zoom motion.
- Reusable recipe headings/disclosures use the outline edge-gradient material. Advanced controls remain available.
- Verified 1,620 backend tests, frontend typecheck/build and all six expanded Planner browser groups. Camera checks exercise wheel/trackpad-sized deltas, anchoring, drag persistence, recipe styling and unchanged plan identity; no camera interaction authorizes or executes a workflow.

# CSV Planner source-contract follow-up

- Exposed mutually exclusive file/ancestor sources in tabular argument JSON schemas, including both join inputs. Backend rejection of ambiguous sources remains unchanged.
- Conflicting-source correction now names the consumer step, explains metadata versus CSV-producing ancestors and tells Planner to omit the unused field, without raw Pydantic input dumps.
- Added regressions for correction through the actual conversation service and source-choice schemas. Verified 1,620 backend tests and frontend typecheck/build; model quality still requires laptop acceptance.

# Checkpoint 26 — Planner recipes and Critic outcome closeout

- Planner owns conversational composition and bounded recipe authoring; legacy Builder imports remain compatible. Normal users need no JSON or manual intermediate output paths. Explicit paths and semantic parameters remain reviewed inputs.
- Recipe candidates use isolated fixture tests and separate Critic review before optional registration. Current-chat candidates restore without regeneration.
- Requested outcome assessment runs in the backend after durable execution, caches bounded Critic findings and cannot override deterministic status. Failures preserve execution evidence; explicit assessment retry never repeats operations.
- Preserved cancellation, conservative recovery, private-chat ownership and exact write authorization. Added natural-language browser acceptance and backend regressions; see docs/CHECKPOINT26_CLOSEOUT.md for verified scope and deferred work.

# Checkpoint 26 — reusable recipe composition and durable runs

- Added versioned JSON recipe definitions with typed bindings, exact hashes, CSV output contracts, deterministic expansion and shared operation validation. Three builtins and explicit registration reuse the existing recipe executor; historical recipe formats remain compatible.
- Planner can select bounded discovered recipes. The interface supports recipe composition and chat binding. On-demand Builder proposals run synthetic fixture tests before a separate Critic review; one explicit registration retests the exact candidate and grants no execution authority.
- Main-workflow execution now has durable background runs, cooperative cancellation after active verification, per-step previews, restart interruption detection and safe recovery proposals. Read-only recovery excludes completed steps; write recovery uses fresh targets and fresh authorization, without automatic write reuse/retry.
- Added shared API/CLI adapters and isolated backend/browser acceptance. Fixed spatial inspection/evidence paths outside the shell working directory, rechecked authorization before later writes, and preserved existing synchronous endpoints. Snakemake export remains synchronous.
- Verified 1,600 tests, frontend typecheck/build and 22 production-browser fixture groups; local-model quality and live-service acceptance remain unverified.
- See docs/CHECKPOINT26_RECIPES_AND_RECOVERY.md for acceptance and unfinished checkpoint work. No live-service or Git/publication action performed.

# Chat history clarity and deferred cross-chat memory

- Planner schema-repair permission deferrals now receive one bounded correction instead of being saved as successful empty proposals. Repeated deferrals fail visibly and preserve the previous workflow; genuine missing-input questions remain supported.

- Added an OFF-by-default Automatic method notes helper: independent typed Planner boundary, one serial request after changed validated workflows/graph bindings, private exact-scope cache and unvalidated-note receipts. Failures preserve plans; OFF/source changes invalidate results. Settings opt-in and shared API/CLI inspection require no manual method-management steps. Evidence learning and cross-chat sharing remain deferred.

- Documentation only: recorded a proposed independent method-memory helper, stable Planner contract, agent/service responsibilities, laptop resource/evaluation gates and deferred integration. No runtime or UI behavior changed; automatic notes and cross-chat sharing remain deferred.

- Persist Chat memory across chats and refreshes using one browser preference, migrating the initially open chat’s old setting once. Settings’ Include private declarations switch also survives reopening and refresh. Chat contents remain isolated.

- Simplified chat memory to one per-chat ON/OFF switch. Chat selection restores its own latest validated workflow directly, recreating a missing proposal artifact without model regeneration. Removed method generation/review/selection controls from normal UI; experimental API/CLI is retained, and automatic notes remain deferred.

- Added an OFF-by-default method-memory agent prototype: explicit current-chat source selection, one-shot generation, editable proposals, versioned reviewed/unvalidated saves, deletion and deliberate Planner inclusion. Shared backend API/CLI checks enforce feature gates and private ownership. Local-model quality remains operator acceptance; cross-chat/background features remain deferred.

- Chat presentation: compact disclosure headings, role-labelled saved-history bubbles, grouped collapsible context controls and a draggable message-area separator. Removed the repeated title below the chat selector.

- Renames controls to Saved chat history and Include recent chat messages, explaining that OFF retains the workflow and transcript.
- Adds Context sent to Planner with distinct next-request settings and actual completed-request inclusion counts; opening-message/workflow fields remain compatible with older records.
- Defers cross-chat memory until checkpoint 30 or later, with proposed intervening operational and single-chat privacy scopes; no sharing feature, agent or dependency is added.

# Checkpoint 26.1 revision — one conversation, one task

- Removes separate task controls and cross-chat linking; each conversation automatically owns private transcript/plan memory.
- Retains context when changing between spatial and CSV work; new chats start independently.
- Saves private memory/conversation state atomically and preserves legacy JSON/former shared-task records without importing their live foreign context.
- Remembers validated graph edits within their owning conversation; identical generated workflows reuse immutable definitions while preserving private request histories and strict reviewed-plan storage.
- Cross-conversation sharing remains discussion only; semantic summaries, indexed core facts and curator corrections are not implemented.

# Checkpoint 26.1 — task-scoped planning conversations

- Adds explicit tasks within one chat and cross-chat continuation, with source-linked bounded history and task-specific dataset context.
- Commits task/conversation updates atomically in local SQLite; preserves legacy JSON and rejects stale revisions/unsafe storage.
- Adds Planner task controls, explicit validated workflow binding and CLI/API parity. Switching clears workspace authority; no extra model/dependency/background agent is added.
- Indexed core memory, curator corrections, templates and remaining checkpoint 26 orchestration are not implemented.

# Planned project memory — documentation only

- Records task separation across chats, source-linked versioned memory, curator proposals for corrections/freshness, optional historical retrieval and reusable methods.
- Defines frontend/backend/API/CLI changes and dependency-ordered checkpoint 26 slices with measurable acceptance.
- Defers implementation for laptop capacity; documents lightweight local indexing and on-demand curation. No runtime capability, dependency or agent is added.

# Checkpoint 25 — persisted library browsing and dataflow clarity

- Reopens verified saved scan inventories in expandable scan/library/function lists with bounded lazy pagination.
- Connects information-card inputs, operations and planned/recorded results with themed arrows and declared step dependencies.
- Indexes examples by function; preserves historical checkpoint paths.
- Documents existing conversation history, summary options and proposed output visualization/demo acceptance for checkpoints 26–27; no new agent-history implementation.

# Checkpoint 25 — shared contracts and automatic library discovery

- Matches library discovery controls to Settings styling and reuses the readable sliding ON/OFF switch; clarifies persistent installation versus candidate scanning.

- Catalogs existing operation contracts and installed adapters consistently across backend, CLI, Planner and Add.
- Statically discovers installed Python declarations/signatures/docs without importing candidate modules; records bounded, hash-verified snapshots and incomplete coverage.
- Adds a tested data-only CSV projection package with explicit installation, exact package binding, separate workflow approval and verified lineage.
- Adds Operations & libraries in Settings and a complete temporary-backend browser journey.
- Pins Playwright and isolates browser/audio test downloads from normal/shared browser caches.

# CI frontend dependency coverage

- Installs pinned pnpm/locked frontend dependencies and supported Node before the offline suite; frontend typecheck/build also runs in CI.
- Makes dependency checks consistent across graph regression tests; CI explicitly requires them rather than silently skipping.

# Read-only startup recovery and readable graph selection

- Loads saved workflow sources at startup and restores the remembered saved revision, falling back to the current conversation’s existing saved proposal.
- Protects open plans, pending edits and stale conversation replies; recovery makes no model call, new save, approval or execution.
- Increases graph selector labels/options to readable 13–14 px text.

# Resizable workflow workspace and collapsible results

- Adds bounded Planner/information panel drag handles with keyboard adjustment and optional saved widths.
- Shows a recorded, read-only outcome block for the matching current workflow; editing/switching scope hides it.
- Makes per-operation outcome details and workflow-source groups independently collapsible.
- Records operator-reported success of the seven-operation CSV workflow; no automatic rerun is performed.

# Saved plan restoration and input presentation

- Restores the exact current plan when opening a saved graph from either navigation path, clearing stale presentation/review state without granting authority.
- Groups equivalent bare/relative input references for display while preserving stored arguments and hashes.
- Distinguishes blue input resources from cyan tools and contains long node labels.

# Exact step-numbering diagnostics

- Exposes the trusted sequential-ID rule in schema findings and the bounded correction request, including dependency/data-reference repair.
- Documents that numbering corrections preserve producer identities and cannot bypass validation or grant execution authority.

# CSV inspection versus artifact dataflow

- Makes both planner prompts explicit that CSV inspection returns metadata, not a CSV-producing intermediate.
- Adds a first-transform path/later-transform source_step example and names invalid consumers/references in policy findings.
- Tests a model correction from an inspection source_step to the original input path without weakening validation.

# Conversation correction findings and readable switch

- Gives the one correction attempt the bounded rejected candidate and actual schema/policy findings.
- Reports those findings through the API and Planner instead of an empty generic generation failure.
- Changes history selection to a sliding dark bracket with bright selected text and visible connecting track.

# Sliding history-context switch

- Shows Off left and On right, with a light active thumb sliding along a connecting track.
- Retains keyboard/screen-reader switch behavior and respects reduced-motion preference.

# Timeout mitigation and declared input visibility

- Adds optional trusted MODEL_REASONING_EFFORT forwarding, preserving model defaults unless explicitly configured.
- Gives model timeouts specific guidance without automatic retry or execution.
- Shows declared input file nodes and exact source/intermediate/output references in planned graphs.
- Replaces the history checkbox with a same-line accessible On/Off switch.

# Bounded conversation history and model diagnostics

- Retains full transcripts while bounding recent model history and total prompt bytes; removes duplicate schemas.
- Adds an explicit previous-message context control and last-completed-turn usage display, preserving the current workflow.
- Reports safe model failure codes and guidance without inheriting historical execution authority.

# Planner model failure handling

- Fixes function-local imports shadowing model exceptions in the HTTP handler, which caused socket hangups on conversation model failures.
- Adds HTTP regressions for model HTTP 404 and missing model configuration; failures return bounded JSON without execution.

# Checkpoint 24 — bounded tabular workflows

- Adds eight typed pandas/table-bridge operations to planner, graph, shared execution and CLI.
- Preserves string identifiers, bounds previews/data, verifies output/source hashes and records intermediate lineage.
- Requires exact authorization for create-only CSV outputs; rejects unsafe paths, incompatible references and arbitrary expressions.
- Adds structured parameter editing and bounded outcome tables; records partial CSV outputs on failed attempts.
- Verifies 1,484 backend tests, frontend typecheck/build, six real-backend CSV browser checks and nine spatial/UI regression groups.
- Adds public fixtures, typed examples and manual acceptance; orders remaining registry, orchestration and prototype work as checkpoints 25–27.

# Paired review layout and browser regression

- Restores left-aligned headings/descriptions/labels with right-edge operation/value/status pairs.
- Fixes the shared legacy 58% value-width cap and preserves file/identifier casing.
- Places Authorize/Execute on one row without resubmitting approval or scrolling away after success.
- Makes Snakemake choices scroll from the top while search/close stay pinned.
- Removes camera interpolation/draft-ID instability and verifies interactions in isolated production Chromium.

# Drag previews and checkpoint review

- Removes whole-App updates from node-drag frames and keeps connected curves/labels tracking the preview.
- Aligns inspector values with Outcome/review and preserves identifier/boolean casing.
- Pins yellow/orange Snakemake choices above the scrolling Add list.
- Documents remaining frontend acceptance and final review gates before any requested commit/push.

# Main-workflow Snakemake export and verification

- Adds Export to Snakemake and Verify Snakemake package to Add and conversational Planner.
- Binds a saved original plan and verified successful source evidence; retained operations reuse results without reexecution.
- Requires exact plan authorization for package creation, statically verifies its source scope/hashes and records export history.
- Blocks missing/tampered source evidence, changed scope, invalid topology, expired authority, package tampering and symlinks.

# Pinned Add panel and smoother form typing

- Keeps Add search/close above a separately scrolling list and darkens the translucent whole panel.
- Isolates Add search and authorization field typing from workflow rendering.
- Emphasizes the 30-minute authorization duration and aligns full-width Outcome content to the right.

# Information-panel and block-toolbar alignment

- Aligns Outcome/review values and status to a common right edge, with consistent labels and typography.
- Moves detailed validation JSON into a disclosure and labels outcome artifact references.
- Aligns Add and other block action icons/text on one baseline.

# Host launcher configuration and secrets

- Loads allowlisted non-secret .env settings as data, preserving terminal overrides.
- Resolves host service defaults and secret-file paths so the local API can use the existing PostGIS configuration.
- Keeps passwords in files and startup output limited to readiness; .env cannot enable writes/overwrite or override operational roots.
- Preserves isolated acceptance endpoint and missing-secret overrides.

# Authorization review and execution diagnostics

- Aligns review typography, inputs, operation headings and parameter rows; brings status/failure messages into view.
- Keeps layout-only node dragging available during review/run and avoids interrupting active drags with review fitting.
- Adds secret-free PostGIS/evidence failure codes and failed-step recovery guidance for governed execution conflicts.

# Outline edge tint and timeline alignment

- Fades Outline color from the top/bottom edges into a clear center.
- Aligns compact timeline connectors and markers, improves label spacing/tooltips and refines selected/running frames.
- Adds a focused frontend inspection-to-PostGIS acceptance walkthrough.

# Optional conversation skill selection

- Restores persistent optional skill selection below Send, with automatic planning when empty.
- Records per-turn selected/workflow skills and displays additions/removals; restores selections from saved chats without inventing legacy metadata.
- Clarifies that GeoJSON-to-GeoPackage conversion needs an output path, not a database schema or mandatory layer names.
- Adds staged frontend acceptance and a 27-case results template.

# Conversational Planner and compact workspace

- Adds recoverable planning dialogue with clarification, validated complete revisions, bounded transcripts and stale-turn protection.
- Preserves the current plan while composing/waiting/failing and keeps authorization/execution separate.
- Adds compact expandable timeline/block controls, near-white Outline text and animation-frame bounded graph dragging.
- Documents frontend dialogue and staged PostGIS acceptance.

# Hue-matched material and familiar pin gestures

- Tints translucent fills with their semantic border color and simplifies Add's label.
- Adds bidirectional pin dragging, Alt-click break, Ctrl-drag atomic rewiring, pin/block context menus, hover feedback and pin-to-empty add/connect.
- Supports right-button canvas pan while retaining governed DAG validation and approval boundaries.

# Governed operation dependency editing

- Adds visible Add/Delete/Move/Connect/Disconnect/Parameters controls, inspector dependency editing and data-port connections for current plans.
- Adds optional digest-bound dependencies with cycle/reference/mandatory-ancestry validation; historical plans retain their existing digests and sequential mapping.
- Docks zoom/legend defaults lower-left, unifies scrollbars and gives Outline a half-transparent fill with opaque content.
- Keeps operation drafts blocked until validation/storage and rechecks authorization for changed scope.

# Refined timeline material and status readability

- Makes Outline the initial material while preserving prior text-color choice and later explicit preferences.
- Fixes filled Evidence-backed status foreground and applies material to Governed/Draft badges.
- Separates timeline statuses, track and stage labels; fills stage labels only and frames selected/running stages instead of all event cards.
- Adds timeline spacing; animation and further block actions remain subsequent work.

# Complete interface appearance coverage

- Adds selected outlines for Execution History and Outcome, with cyan Saved records/Settings/Advanced controls.
- Extends solid/outline and filled-text preferences to graph selection, timeline stages, workflow blocks and information surfaces.
- Preserves category/status colors, selected-node emphasis and separate authorization highlights.

# Configurable action-button appearance

- Adds Settings controls for solid-fill or transparent-outline action buttons and black/white filled text, with a live preview and browser-local persistence.
- Applies shared button appearance across header, planning and review actions, while retaining semantic Execute/Authorize colors and graph presentation.
- Adapts white-text fill shades for readable contrast; appearance changes preserve current workflow state.

# Separate authorization and docked execution controls

- Adds Settings gear, orange exclamation Authorize and yellow Play/Execute controls.
- Docks execution review, history and outcomes beside the graph, with responsive stacking.
- Removes the redundant read-only inspection checkbox; required operations use separate exact authorization followed by independently verified execution.
- Highlights authorization-required operations and retains approval digest/expiry checks.

# Repeatable interface acceptance

- Adds isolated source snapshots, public fixtures, deterministic proposal seeding, artifact audits and a 32-case operator test/bug/retest process.
- Keeps acceptance credentials and runtime records separate from normal workflows; preparation creates no approval or execution.
- Fixes the frontend API proxy to follow the selected launcher port.
- Keeps durable inspection runtime records out of Git.

# Planning context and inspector visibility

- Enlarges the context composer, removes redundant caption and keeps the inspector visible with Text planner.
- Starts Task history collapsed and adds governed input filename normalization.
- Documents proposed navigation; executable graph editing remains outstanding.

# Compact planning graph and suggestions

- Uses short generated workflow/intake titles with full step and request text in the inspector.
- Reuses Plan skill recommendations while typing natural-language planning context; additions remain explicit.
- Keeps top-navigation redesign and executable graph editing separate.

# Text planner skill selection

- Adds searchable, scrollable skill selection with readable names and removable tags.
- Aligns Text planner button styling and marks automatically saved graph proposals accurately.
- Keeps capability IDs, approval rules and executable editing boundaries unchanged.

# Direct text planning

- Adds Text planner agent: context composer, adjacent validated graph and automatic proposal storage.
- Introduces a generated-plan storage route that reports no human review, approval or execution.
- Retains validated plans after storage failures for storage-only retry.

# Conversation workspace simplification

- Shows only the active task stage and collapses history, recovery and technical controls.
- Combines reviewed Intent storage and plan generation into one explicit user action, retaining separate backend validation and recoverable planning failures.

# Planner runtime identification

- Exposes a loaded Planner contract revision through API health and launcher output.
- Clarifies read-only inspection approval guidance while preserving any extra model-proposed approval gate.

# Planner structure correction

- Adds an exact inspection response-shape example and one shared JSON/schema/policy correction budget.
- Revalidates fresh proposals and displays safe field findings; no authority or execution is inferred.

# Checkpoint 23 — metadata scope compatibility

- Recognizes a closed vocabulary of equivalent vector/raster metadata labels and complete enumerations; unsupported outputs still fail before Planner inference.
- Preserves immutable reviewed Intent, shows original and canonical metadata scope, and identifies unsupported labels in findings.
- Applies the same scope mapping during planning and storage and rejects changed derived mappings.

# Checkpoint 23 — actionable model diagnostics

- Distinguishes Intent/Planner model configuration, connection, timeout, rejection and response failures without exposing raw exceptions.
- Adds read-only API-process model settings inspection and frontend recovery guidance; launcher reports missing model selection.
- Makes conversation-and-execution layout an explicit completion criterion; broader capabilities remain later work.

# Checkpoint 23 — task/input workspace foundation

- Opens Task workspace directly to a fresh request; historical context remains optional.
- Adds existing-file and filename/relative-path input selection, visible pending draft graph and readable Intent response.
- Checks selected input availability before inference and rejects resolved input mismatches; CLI supports --selected-input.
- Restores Why ActionCharter and detailed current-status checkpoint history; only the current overview enters model context, with full-file digest retained.
- Governed execution continuation and complete live-demo acceptance remain in progress.

# Documentation organization

- Replaced the incremental README with capability-based onboarding and checkpoint-free workflow/agent diagrams.
- Added documentation/context indexes and audience/update rules.
- Shortened current status and preserved earlier README/status as labelled development snapshots.
- Clarified frontend-only startup versus the combined launcher; no execution contracts changed.

# Checkpoint 22O — closeout

- Consolidated current scope, acceptance limits and commit/PR instructions.
- Recorded explicit input selection and approval-free read-only continuation as Checkpoint 23 acceptance requirements.
- Documentation only; no execution authority or model behavior changed.

# Checkpoint 22N

- Added 12-case real-service integration matrix for reviewed Intent → plan → decision → recipe without execution.
- Saved-plan continuation displays readable reviewed objectives while retaining exact stored provenance.
- Scoped Checkpoint 23 around conversation/graph, governed continuation and a validated demo; broader capabilities deferred.

# Checkpoint 22M

- Extended reviewed-intent planning/storage to explicit inspect_raster metadata alongside vector metadata.
- Shared exact-scope checks, persisted selected capability and retained legacy vector compatibility.
- Added matching capability selector and raster lifecycle/rejection regressions; no execution authority added.

# Checkpoint 22L

- Added explicit history-free Intent reasoning, review, storage and recovery while retaining existing historical source checks.
- Added frontend Start without history and omitted unused graph history nodes.
- Added nullable-pair/citation validation and fresh-task lifecycle/API regressions; no inferred approval or execution.

# Checkpoint 22K

- Added one-current-stage navigation and automatic advancement after successful review/storage.
- Recovery opens the appropriate stage; edits invalidate downstream proposals; failures keep the stage and reveal feedback.
- Corrected labels for reviewed/stored artifacts; no new approval gates or backend authority.

# Checkpoint 22J

- Added bounded read-only review inventory and CLI parity.
- Added collapsible saved context/intent recovery with source rechecking, sorting and restoration of request/answers.
- Added regressions for stale sources, unsafe paths, damaged artifacts and limits; no inferred work authority.

# Checkpoint 22I

Explicit reviewed-intent plan storage, exact provenance/scope checks, existing Plan continuation and CLI parity; no inferred approval or execution.

# Checkpoint 22H UI correction

- Matched Context & intent to the established header button styling.
- Made retrieval prerequisites and checked-history selection visible; retained history loading/failure messages across query edits.

# Checkpoint 22H

- Added nonmodal context/intent panel with explicit history selection, review, clarification and bounded Planner handoff.
- Added typed frontend API boundaries, downstream invalidation and Intent/data/history plan graph projection.
- Added wide/narrow layout and exact frontend acceptance guide; no backend authority changes.

# Checkpoint 22G

- Added typed local Intent inspection/review/reopening and Planner handoff API routes.
- Added HTTP regressions for preserved approval, exact scope, stale context, unresolved intent and rejected authority fields.
- Updated current status and live API validation guide; no frontend controls or automatic execution.

# Checkpoint 22F conservative approval correction

- Accept and preserve an additional approval requirement on the exact reviewed read-only inspection plan. Report the gate explicitly; never infer or bypass approval.
- Added regression confirming true remains true and saving/execution/approval remain false.

# Checkpoint 22F diagnostic correction

- Exact handoff rejection now names field mismatches with bounded credential-redacted arguments. Scope checks remain unchanged.
- Added regression for detailed flag/path diagnostics and credential redaction.

# Checkpoint 22F

- Added rechecked reviewed-intent handoff to capability Planner for one exact read-only vector inspection.
- Added changed-path, extra-step, unsupported-skill and in-flight stale-source regressions.
- Updated current status and exact terminal acceptance guide; no plan saving, execution or frontend changes.

# Checkpoint 22E

- Added one bounded Intent re-evaluation for explicit answers and unresolved proposals; no forced status changes.
- Added canonical resolved-intent review, immutable storage/reopen CLI and runtime ignore rule.
- Added rejection regressions and terminal validation guide; Planner handoff remains separate.

# Checkpoint 22D

- Added explicit bounded clarification answers and reasoning-only Intent HTTP endpoint.
- Improved current-task/dataset clarification prompt; added redaction, bounds and HTTP stale-context regressions.
- Updated current status and terminal/API validation guide. No execution authority or frontend changes.

# Checkpoint 22C

- Added bounded reasoning-only Intent CLI with strict proposal validation and before/after context checks.
- Added fake-model regression tests and terminal acceptance guide. No frontend or execution authority changes.

# Changelog

## Checkpoint 22B — exact context review and storage

- Recheck selected source snapshots and confirmed context digest before immutable review storage.
- Reject stale/tampered context on reopening; keep review separate from plan approval.
- Add review CLI/API routes, runtime ignore rule, tests and validation guide.

## Checkpoint 22A — selected task-context retrieval

- Add bounded deterministic CLI/API retrieval with checked event citations, redaction and snapshot identity.
- Keep retrieval unreviewed and separate from approval, models and execution.
- Add selected-scope, bounds, tamper and snapshot tests; update current documentation.

## Checkpoint 21D — saved-task history recovery

- List independently checked task histories and reopen their source-backed context after restarting the interface.
- Keep historical inspection separate from active planning and execution authority; damaged histories appear as findings.

## Checkpoint 21 — task-history failure visibility and product sequence

- Stop planning with an actionable message if the task request cannot be recorded, so a failed plan cannot appear without a task ID.
- Prioritize reviewed intent and a task-centered agent interface before new data-tool families.

## Checkpoint 21C — current task and context inspector

- Capture explicit Planner request, selection, outcome/failure, plan-decision note, and matching governed run outcome under one current task ID.
- Show a checked, collapsible context view beside the graph and reopen the current task within the browser session.
- Preserve complete bounded request text in the original redacted event while previewing a short cited summary.

## Checkpoint 21B — local task-history API

- Add an explicit loopback endpoint to record a task request and subsequent history events, and a checked context endpoint.
- Keep historical decision notes separate from human approval authority and execution.

## Checkpoint 21A — task history foundation

- Add bounded append-only task events with redaction, chain verification and explicit CLI commands.
- Derive deterministic cited context from the first and latest task events without model or execution authority.

## Checkpoint 20 — verified authority and evidence graph

- Join exact saved Planner definitions to recipe definitions, and exact durable runs to stored traces, Critic records and releases in the read-only flow graph.
- Put routine graph digests behind expandable audit details.
- Add grouped read-only graph sources for saved plans, stored recipes, durable runs, and exported traces; show declared dependencies and recorded outcomes without changing execution state.
- Draw approval and result graph connections only when the existing independent inventory verification confirms the exact relationship.
- Link canonical Critic result records to fresh trace/report evidence by exact identity and content references in the read-only Assurance inventory.
- Link a verified Critic record and trace/report pair to an independently inspected immutable release manifest only when all component paths and digests match.
- Show bounded recorded output artifacts in durable-run graphs with producer links; label stored digests separately from a fresh physical-file check.
- Distinguish local graph source identities and active workflow state from durable runs, and explain output-list truncation.
- Keep the graph timeline reachable on short windows and show why Current workflow is unavailable when no recipe is open.
- Move the four journey controls into the top bar on wide screens while preserving their second-row layout on narrow screens; remove redundant workspace copy.

- Reverify saved plan decisions against the exact plan, required steps,
  decision, and expiry when projecting the inventory.
- Distinguish verified and blocked authority in the saved-plan list without
  changing approval or execution authority.

## Checkpoint 19 — navigable default journey

- Put Plan, Review graph, Run, and Check outcome in a prominent responsive
  navigation strip; move expert entry points behind Advanced.
- Open the saved recipe chooser from Run when no recipe is active, while keeping
  explicit approval, execution, and verification controls intact.
- Route Review graph to the current validated plan, and Run through unfinished
  plan review or its stored recipe before falling back to recipe inventory.
- Show the Planner's current review boundary and a link to the next existing
  control, without automatically saving, approving, or executing anything.
- Bound the graph canvas and timeline to the graph column, and make draggable
  graph controls track the pointer without rerendering the workflow per move.
- Make the timeline's final event reachable with its own horizontal scroll,
  navigation buttons, end padding, and room for status and labels.
- Record operator-reported WSL browser and full PostGIS acceptance. Preserve
  the unresolved high-intervention UX as a post-history integration target.

## Checkpoint 18

- Add one loopback-only launcher for the interface API and frontend.
- Keep write tools and overwrite disabled by default, with a deliberate flag
  for the existing bounded approval-gated execution path.
- Add non-mutating prerequisite and optional-service diagnostics plus clean
  coordinated shutdown.
- Preserve the CLI and externally managed Ollama, Docker, PostGIS, GeoServer,
  and Snakemake boundaries.
- Split future long-context work into governed task history and deterministic
  context assembly (Checkpoint 21), followed by the Context Curator and Intent
  Agent (Checkpoint 22), so derived memory cannot silently become authority.
- Add separate `interface-validate` and aggregate `validate` Make targets while
  preserving `make test` as the Python/offline suite.
- Treat any valid GeoServer HTTP response as service reachability during
  startup diagnostics, while leaving authenticated REST authorization to the
  existing bounded GeoServer actions.
- Launch the pinned local Vite executable as a direct child of the startup
  supervisor so shutdown signals reach the actual frontend process; report an
  unexpected clean child exit as a startup failure.

## Checkpoint 17AY

- Compile the established four-step Planner PostGIS sequence into a governed recipe.
- Dispatch typed vector load, deterministic PostGIS validation, and bounded report intent.
- Require independent validation of the database load before success and preserve immutable evidence reporting.
- Correct the repeated-export frontend contract to accept a valid existing export with `export_performed: false`.
- Record a fresh end-to-end interface acceptance run creating and validating a two-row EPSG:4326 POINT table in PostGIS before evidence, Critic, release, and export completion.

## Checkpoint 17AX

- Close the Checkpoint 17 guided-interface prototype at its safe authority boundary.
- Revalidate repeated exact Snakemake exports instead of returning a duplicate error.
- Record the simplified Checkpoint 18 product direction and advanced-mode boundary.

## Checkpoint 17AW

- Add interface preview for the existing approval-gated Snakemake export plan.
- Require confirmation of the exact export-plan digest before package creation.
- Generate and statically validate the replay package without running Snakemake
  or re-executing the recipe.

## Checkpoint 17AV

- Add deterministic recipe-run release readiness over exact recipe, approval,
  result, evidence, trace, report, Critic record, and operational history.
- Add explicit interface actions to prepare release evidence, review the exact
  candidate digest, and create an immutable authoritative release.
- Correct operational-history approval events for recipe-derived traces so
  they record a recipe digest instead of a null plan digest.

## Checkpoint 17AU

- Add explicit digest review and immutable recording for one validated Critic
  assessment.
- Rebuild deterministic evidence before recording and preserve the separate
  release boundary.

## Checkpoint 17AT

- Add an explicit, digest-bound Critic model invocation for one stored
  WorkflowTrace/report pair.
- Validate the response through existing Critic policy while keeping it in
  memory and granting no release authority.

## Checkpoint 17AP

- Keep Planner task typing responsive by debouncing graph-affecting state.
- Submit the exact current request and preserve saved-plan restoration.

## Checkpoint 17AO

- Show safe deterministic-policy findings for rejected Planner candidates.
- Offer explicit retry without returning or persisting the invalid plan.

## Checkpoint 17AN

- Add bounded project input and output-location selection to Templates and Plan.
- Bind selected input resources into Planner context without granting execution.

## Checkpoint 17AM

- Let the interface accept input/output filenames under the governed
  `data/input` and `data/output` roots while preserving explicit paths.

## Checkpoint 17AL

- Handle deliberate interface API `Ctrl+C` shutdown without a traceback.
- Document Vite development refreshes versus ordinary interface state updates.

## Checkpoint 17AK

- Restore the original task request and exact allowed-skill selection with a
  saved Planner result.
- Add an explicit append-only fresh-decision path after expired or blocked plan
  approval verification while preserving prior evidence.

## Checkpoint 17AJ

- Made the Planner-to-saved-recipe transition visible by closing competing
  overlays before opening the exact recipe inventory.

## Checkpoint 17AI

- Added a source-pinned local interface API launcher with import and route
  diagnostics.
- Documented stale-process and WSL port troubleshooting.
- Replaced misleading generic malformed-POST wording with `request payload is
  invalid`.

## Checkpoint 17AH

- Added the Planner recipe-save endpoint to the loopback POST allowlist.
- Added an HTTP route regression test and retained exact idempotent save resume.

## Checkpoint 17AF

- Added an exact SHA-256-bound handoff from newly stored Planner recipes to the
  existing saved-recipe approval workspace.
- Refresh and prioritize the matching artifact without automatically preparing
  approval or performing execution.

## Checkpoint 17AE

- Redesigned the Planner recipe compilation transition for clearer hierarchy.
- Added explicit digest review and immutable storage for Planner-derived recipe
  candidates, with server-side recompilation and authority reverification.
- Kept recipe approval and execution as separate later actions.

## Checkpoint 17AD

- Added a non-executing bridge from independently verified Planner results to
  deterministically validated governed recipe candidates.
- Required canonical `path` and `target_path` arguments for Planner-generated
  `convert_vector` steps and kept recipe review, approval, and execution as
  separate authority boundaries.

## Checkpoint 17AC

- Corrected saved-plan selection and replaced the horizontal strip with a
  compact auto-collapsing, vertically scrolling and sortable navigator.
- Added a bounded saved-plan inventory with matching decision evidence.
- Added restart-safe restoration of exact plan, prepared scope, and latest
  append-only decision while requiring fresh independent verification.
- Kept inventory and restoration read-only and non-executing.

## Checkpoint 17AB

- Rendered preview rejection locally as a large persistent `PREVIEW BLOCKED`
  result instead of an off-screen general Planner notice.
- Added a non-executing Planner envelope preview using existing Executor policy.
- Explicitly reject approved plans outside the currently supported four-step
  PostGIS vertical slice instead of presenting false execution readiness.
- Kept execution unavailable and reported the exact preview digest.

## Checkpoint 17AA

- Added visible step arguments and approval/validation flags before plan
  decisions.
- Added independent verification of immutable plan and approval evidence,
  including decision, expiry, digest, and required-step coverage.
- Kept verification non-mutating and non-executing.

## Checkpoint 17Z

- Corrected repeated reviewed-plan saves so an exact already-stored artifact
  resumes the interface flow without being overwritten.
- Added append-only approve or deny recording for exact prepared Planner-result
  requests.
- Reprepared and revalidated immutable plan evidence before recording, with
  server-derived scope and stale-request rejection.
- Prevented approval records for read-only plans and kept both decisions
  strictly separate from execution.

## Checkpoint 17Y

- Added exact, non-writing approval-request preparation for immutable Planner
  results.
- Revalidated plan identity and policy server-side and derived approval scope
  from the trusted plan rather than browser input.
- Distinguished read-only plans that require no approval from plans awaiting a
  human decision; neither path executes work.

## Checkpoint 17X

- Added explicit review and canonical SHA-256 confirmation before a Planner
  result can be stored.
- Added immutable, non-overwriting full `PlannerResult` persistence beneath the
  fixed `plans/` root with policy revalidation and symlink rejection.
- Kept plan storage separate from human approval and execution while preserving
  compatibility with the existing CLI approval loader.

## Checkpoint 17W

- Connected a new Plan workspace to the existing Planner Agent and configured
  model service rather than introducing a browser-only planning simulation.
- Added strict request and response schemas, bounded failures, and explicit
  planning-only authority with no persistence, approval, or execution.
- Added a Blueprint-style projection of the validated planner result.
- Replaced lexical Planner authority with explicit registry-verified skill
  selection and reduced the model payload to task, relevant datasets and exact
  selected-skill metadata after local-model validation exposed prompt dilution.
- Added distinct safe interface errors for invalid JSON, invalid plan schema and
  deterministic policy rejection.
- Replaced the fixed Planner checkbox grid with a scalable searchable skill
  picker, request-based recommendations, selected-skill chips and keyboard
  navigation while keeping recommendations non-authoritative.
- Documented grouped CLI-to-interface parity so remaining operational families
  can be implemented without exposing a shell or pretending unsupported
  commands are available.

## Checkpoint 17V

- Added a bounded read-only inventory of durable interface execution attempts.
- Added a top-level Runs workspace for reopening completed, failed, interrupted,
  or still-running progress after closing the browser or restarting the API.
- Persisted recipe identity and step dependencies with new attempts so the
  interface can reconstruct the exact run-specific graph without inventing
  tools or control order.
- Kept reopening strictly observational: it cannot resume, retry, approve, or
  execute a recipe.

## Checkpoint 17U-A

- Added real runner-backed live execution progress to the guided interface.
- Added digest-bound progress lookup and explicit step failure localization.
- Connected saved recipe, approval, execution, validation and evidence state to
  one live read-only workflow graph derived from the exact recipe dependencies.
- Added resumable gate navigation, separate input-data projection, corrected
  control sockets and non-overlapping governance/execution layout.
- Removed whole-graph rerendering from each approval text-field keystroke.
- Distinguished denied human authority from failed execution and added an
  explicit active-workflow exit control.
- Persisted interface execution progress atomically, classified abandoned
  running attempts as interrupted after restart, and surfaced fail-closed
  recovery guidance without automatic retry.
- Changed the denied workflow state to a red stop treatment while preserving
  its distinct governance semantics.
- Kept final success claims bound to the authoritative governed execution
  response; progress state cannot create a success claim.

All notable changes to ActionCharter will be documented in this file. The
project follows Semantic Versioning after the initial public alpha.

## [Unreleased]

- Added Checkpoint 17AS explicit digest review and immutable persistence for an
  adapted recipe-run trace and deterministic report. The service rebuilds the
  candidate before writing, rejects stale or duplicate targets, revalidates the
  stored pair, and grants no Critic, release, or execution authority.
- Corrected the Assurance workspace so its large Critic evidence header scrolls
  away with the content instead of remaining pinned over long evidence lists.
- Added minimize and restore controls to the adapted-trace review drawer while
  preserving its selected candidate and in-progress review confirmation.

- Added Checkpoint 17AR deterministic recipe-run trace adaptation previews.
  Exact recipes, approvals, evidence, steps, statuses, and durable timestamps
  must agree before the existing Critic evidence builder accepts an in-memory
  candidate. Recipe authority now has its own trace digest field and no model,
  persistent trace, Critic result, release, or execution is produced.

- Added Checkpoint 17AQ read-only Critic assurance inventory. The interface
  reuses the deterministic Critic evidence builder without calling a model,
  recording a result, creating a release, or executing work.

- Added Checkpoint 17T first governed interface execution, disabled by default,
  digest-confirmed, server-reverified, allowlisted, validated and durably evidenced.
- Exposed optional template parameters including vector `target_format`, reduced
  the interface to one active process panel, and enlarged execution artifact results.
- Added bounded, redacted per-step outcome and validation visualization to the
  completed interface run instead of showing only status and artifact paths.
- Matched optional selector styling to the existing form, added a close control
  for the complete approval flow, and tested target-format enforcement through
  the real deterministic proposal compiler.
- Reserved approval-header space so the close control cannot cover the
  `No execution` authority indicator.
- Added Checkpoint 17S exact execution-envelope previews with ordered skill,
  argument, output, validation and evidence-destination inspection while keeping
  execution unavailable.
- Added Checkpoint 17R large authority-outcome cards and independent, non-executing
  verification of immutable recipe approvals against current deterministic policy.

### Changed

- Adopted ActionCharter as the public project and distribution name.
- Broadened the public description from a GIS-only harness to a governed
  professional-tool execution architecture with GIS as its reference domain.
- Reorganized the README around the governed flow, agent authority boundaries,
  complete PostGIS lifecycle, supported environment, and newcomer quick start.
- Synchronized the project summary, architecture, runtime boundaries, current
  status, and roadmap with the completed 15A–15K implementation.

### Added

- Checkpoint 17A read-only workflow interface foundation with a blueprint-style
  connected graph, node inspector, timeline, minimap, responsive layout and a
  schema-validated sanitized demonstration fixture.
- A repository-native React, TypeScript and Vite frontend setup without the
  hosting-provider scaffold, plus a capability-expansion backlog for a governed
  pandas adapter and named external-service adapters.
- Measured graph fitting, a live pannable minimap, and switchable horizontal
  and vertical workflow layouts with a mobile-first vertical default.
- Fixed canvas controls and minimap positioning, plus repository-level ignores
  for frontend dependencies, build output, caches and test reports.
- Kept local checkpoint transfer archives and environment-specific GeoServer
  publication evidence outside version control.
- Checkpoint 17B bounded, redacted projection of one exact validated workflow
  trace into the interface graph contract, with same-origin loading, response
  limits, runtime validation and a safe demonstration fallback.
- Checkpoint 17C capped workflow catalog export and a validated read-only run
  selector that loads only task-ID-bound same-origin projections.
- Checkpoint 17D evidence-backed node inspector details with bounded aggregate
  facts, timing and safe findings, validated in both Python and the browser.
- Checkpoint 17E expandable safe evidence previews for trace, plan, approval,
  validation and artifact records, with digest display and basename-only
  artifact references.
- Checkpoint 17F trace-derived operation topology, capped safe operation names,
  recorded-order links and graph-size-driven horizontal and vertical layouts.
- Process-first node titles with embedded performer labels, a semantic minimap,
  wheel zoom with Shift-wheel horizontal navigation, and a selectable
  edge-aligned workflow timeline.
- A durable interface product-scope matrix covering planning, GIS tools,
  PostGIS lifecycle, recipes, Snakemake, skills, evidence, release and the
  existing bounded GeoServer capabilities.
- Checkpoint 17G semantic process categories separated from performer identity,
  professional category accents, ownership group frames, matching minimap
  semantics and corrected consistent node corner geometry.
- Increased semantic border, label, icon and ownership-frame contrast, added
  performer badges, and aligned each timeline status above its marker with the
  process action below.
- Separated adjacent ownership frames and changed successful timeline events
  from uniform validation green to restrained process-category accents.
- Completed the charcoal palette across navigation, headings, inspector and
  controls; added non-passive wheel zoom, empty-canvas drag panning, responsive
  inspector placement, off-white Evidence semantics and notched agent corners.
- Checkpoint 17H typed control, governance, tool, data and evidence
  connections; adjacent request and bounded input-data nodes; hollow
  triangular agent sockets and circular data/tool sockets; separate upper
  agent interaction and lower recorded-operation lanes; edge labels, legend and
  minimap connections; axis-aware shape-compatible endpoints; explicit stale
  runtime notices instead of silent demonstration fallback; and no unrecorded
  optional components.
- Simplified the minimap to thin lines and outline-only nodes, inset sockets
  above their lines, constrained the graph beneath the inspector, removed the
  extra rounded viewport border, and added draggable handles to graph controls
  and the connection legend.
- Connected Executor only to the first recorded operation and Validation only
  to the last, and exposed Snakemake only when runtime or operation metadata
  explicitly records it.
- Checkpoint 17I explicit Evidence and Proposal modes. Evidence projections
  remain immutable; Proposal mode creates a separate in-memory draft with node
  creation, deletion, field editing and orientation-aware dragging, while
  retaining no approval, tool, filesystem or execution authority.
- Checkpoint 17J bounded typed-connection editing in browser-local proposals:
  compatible source/target selection, duplicate and cycle rejection, explicit
  incident-connection deletion, and filled connected versus hollow available
  sockets. The editor still grants no persistence or execution authority.
- Added Blueprint-style press-drag-release connection wiring with a live draft
  wire, unoccupied compatible input enforcement, and bounded performer
  selection while retaining the Inspector connection controls as a fallback.
- Checkpoint 17K reuses the trusted CLI recipe-template catalog in the browser,
  validates a bounded runtime catalog projection, renders selected template
  steps and dependencies as a proposal graph, collects required parameters,
  and downloads a CLI-compatible non-executable recipe proposal. Structurally
  edited template graphs are withheld from download until a graph contract can
  represent them exactly.
- Moved template selection out of the node Inspector into a dedicated top-bar
  template workspace with explanatory workflow/recipe/skill concepts, readable
  recipe cards, included-skill and required-input summaries, and responsive
  request/parameter controls. Added the CLI/interface equivalence test strategy.
- Added a versioned Checkpoint 17L vector-conversion proposal and regression
  test as the first CLI/interface parity baseline. The baseline validates the
  trusted catalog and deterministically compiles without save, approval or
  execution authority.
- Added the Checkpoint 17M loopback-only typed interface service and a visible
  Compile proposal action. The service reuses the existing trusted catalog,
  skill registry, Pydantic proposal contract and deterministic compiler while
  withholding filesystem, shell, save, approval and execution authority.
- Added Checkpoint 17N digest-bound reviewed recipe storage. The interface
  requires a separate confirmation and save action after compilation; the
  backend recompiles, verifies the displayed recipe digest, writes immutably
  beneath the fixed recipe root, and performs no approval or execution.
- Added Checkpoint 17O read-only stored-recipe inventory, a persistent Recipes
  control, and an explicit post-save transition that preserves the success
  result until the operator chooses to continue. Inventory exposes bounded
  identity, ordered skills and gate summaries only.
- Added Checkpoint 17P read-only approval-request preparation for one exact
  stored recipe. The service rehashes the recipe, reruns deterministic policy,
  binds the required steps into a canonical request digest, and records no
  human decision or execution.
- Corrected 17P navigation by adding an explicit return from graph preview to
  template setup and automatically scrolling and focusing the prepared
  approval result in long recipe inventories.
- Promoted the prepared-only, no-decision and no-execution statement into a
  large high-contrast authority banner so the current boundary cannot be
  mistaken for a recorded approval.
- Added Checkpoint 17Q explicit append-only approve/deny recording bound to the
  exact prepared request and recipe digests. Required steps are derived
  server-side, operator text is redacted, and recording provides no execution
  authority.

- A complete governed PostGIS candidate-to-current lifecycle: bounded
  inspection, deterministic comparison and assessment, digest-bound promotion
  planning and approval, serializable execution, and independent verification.
- Governed rollback planning, separate rollback approval, serializable rollback
  execution, and independent digest-bound verification of restored state.
- A reproducible Python 3.11 Codespaces development container with Docker
  Compose access and automatic development-dependency installation.
- An Android remote-development guide covering browser-based Codespaces,
  Termux as an SSH/Git client, cost control, validation scope, and secret
  handling.
- Checkpoint 16A bounded, GET-only GeoServer inspection for one exact
  allowlisted workspace, datastore, feature type, and published layer.
- Checkpoint 16B digest-bound planning, explicit human approval, fixed-path
  activation, post-write validation, and independent verification for one
  already-configured GeoServer layer, live-validated against GeoServer 2.28.0.
- Effective-layer inspection that correctly derives omitted layer-level
  enable/advertise flags from the authoritative feature-type resource, plus
  typed compensation outcomes for failed publication validation.

## [0.9.0] - 2026-09-04

### Added

- Isolated Planner, Executor, Critic, Builder and GIS/MCP boundaries.
- Exact digest-bound approvals and deterministic validation.
- Controlled vector, raster and PostGIS skills.
- Declarative recipes and approval-gated Snakemake replay.
- Spatial-data contracts and a generated dirty-vector benchmark.
- Isolated Builder candidate testing, promotion and activation verification.
- Correlated append-only operational history.
- Immutable Critic records and authoritative workflow release packages.
- A repeatable Checkpoint 14F pilot demonstration.

## [0.8.0] - 2026-08-20

### Added

- Approval-gated reusable GIS recipes with durable execution evidence.

[Unreleased]: https://github.com/wanggiya/action-charter/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/wanggiya/action-charter/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/wanggiya/action-charter/releases/tag/v0.8.0

- Checkpoint 20: saved recipes now display independently verified exact recipe approval links and blocked decisions in the interface inventory.
- Checkpoint 20: durable interface execution attempts now record approval identity and display independently checked recipe authority at run start.
- Checkpoint 20: new interface runs persist canonical result and evidence digests; the run browser independently verifies exact durable files before presenting a linked result.
- Checkpoint 20: Critic recipe candidates now require an exact, unique run and evidence relationship; the candidate can reopen its linked run graph.
- Interface navigation: rename Review graph to Flow graph, expose it in Advanced, and clarify the graph source selector without triggering execution.
- Flow graph source selection is visible beside the graph title on desktop and mobile and can switch away from and back to the current run without resetting it.

Checkpoint 21D refresh correction: preserve task-context, Inspector and page scroll positions during checked refresh; isolate nested details toggles; add Advanced → Task history navigation. Verify by scrolling the context, refreshing, and opening/closing Source event without collapsing the outer pane.

Checkpoint 21D layout correction: move history selection/refresh controls outside the scrollable context, reserve a stable context height, and disable Inspector scroll anchoring. After this focused fix, prioritize backend task/artifact verification and reviewed context services before further interface redesign.

Graph-source header correction (v19): the screenshots identify Refresh graph sources, not Refresh checked context. Replace option-dependent flex wrapping with explicit responsive grid columns and a constrained selector. Metadata occupies a consistent second row; narrow screens use a deliberate single-column header. Validate by refreshing graph sources repeatedly with long saved names at the same window width. Backend work follows this focused correction.

Checkpoint 21E: explicit task artifact references can be independently checked against bounded current evidence bytes through a read-only API. This verifies file identity only, not semantic relationships or authority. Five history tests passed locally; full WSL suite pending. See `docs/CHECKPOINT21E.md`.

Checkpoint 21F adds read-only recorded plan/approval relationship inspection with authoritative schemas and existing approval verification. Six focused task tests passed; no execution authority is granted. Automatic reference attachment and recipe/outcome checks remain open. See `docs/CHECKPOINT21F.md`.

Checkpoint 21G links actual plan saves and approval/denial records to the active task with file-byte references. Completed artifact operations survive visible history failures. Seven focused task tests and frontend build passed locally; full WSL suite pending. See `docs/CHECKPOINT21G.md`. Recipe/outcome links remain open.

Checkpoint 21H corrects selected-skill Planner prompts, removes unconditional unrelated PostGIS instructions, includes conversion arguments, and allows one fully revalidated policy correction. 54 focused tests passed; full WSL suite and live-model check pending. See `docs/CHECKPOINT21H.md`.

Checkpoint 21I records an exact task reference after storing a reviewed Planner-derived recipe and surfaces history failures without undoing storage. 23 focused tests and frontend build passed locally; full API suite pending. Recipe semantic relationships and outcomes remain open. See `docs/CHECKPOINT21I.md`.

Checkpoint 21J checks full recipe definitions against their recorded source plans using the same backend mapping as compilation. 24 focused tests passed; full API suite pending. Outcome links remain open. Task-history discoverability is explicitly deferred to task-centered UI redesign. See `docs/CHECKPOINT21J.md`.

Checkpoint 21K links task-derived completed run result/evidence references and checks exact recorded outcome relationships without revalidating live outputs or granting authority. 25 focused tests and frontend build passed locally; full WSL suite pending. Interrupted attempts and recovery acceptance remain open. See `docs/CHECKPOINT21K.md`.

Checkpoint 21L records completed-run recipe approval references, verifies their current recipe policy/scope/expiry relationships, and separates historical identity from current permission. 26 focused tests and frontend build passed locally; full WSL API suite and recovery acceptance remain. See `docs/CHECKPOINT21L.md`.

Checkpoint 21M adds attempt/recovery task notes and a closeout acceptance checklist. 27 focused tests passed locally; full WSL API suite and deliberate end-to-end recovery acceptance remain pending. Advanced relationship graph direction is documented. Checkpoint 21 implementation is delivered for acceptance, not yet declared complete. See `docs/CHECKPOINT21M.md`.
