# Changelog

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
