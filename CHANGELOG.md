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
