# Checkpoint 27 plan: reliable reuse, visible outcomes and prototype evaluation

Recorded: 2026-10-16. **Design and delivery plan only; not implemented by this document.**

This records the operator's decisions after checkpoint 26. Preserve the earlier
[roadmap](../context/PRODUCT_ROADMAP.md) and [checkpoint 26 closeout](CHECKPOINT26_CLOSEOUT.md)
as history. Resume from the delivery order and acceptance criteria below rather
than reconstructing the conversation or introducing another agent architecture.

## Implementation status

[2026-10-20 technical acceptance and remaining gates](CHECKPOINT27_EVALUATION.md): core implementation is ready for operator interface acceptance. 27.6 packaging remains deliberately sequenced after the pre-demo gates and chosen-data/demo validation. Six final actual-model workflows executed correctly; optional Critic quality remains unverified under its timeout bound.


**27.1 delivered:** automatic successful-run records, deterministic tags and semantic
deduplication, private evidence references, own-chat discovery, fail-soft indexing
and interface/CLI inspection. [Implementation, limits and acceptance](CHECKPOINT27_RETENTION.md).
**27.2 delivered:** exclusive Recipe list/Keywords reference browsing, bounded
Planner search/inspection, safe catalog visibility and own-chat adaptation through
ordinary conversation. Manual composition remains Advanced. [Current delivery/acceptance](CHECKPOINT27_DISCOVERY.md).
27.3 annotation indexing is now delivered through the existing assessment, without extra model calls. Evaluation and packaging boundaries below remain explicit. The original design and acceptance criteria remain
preserved; delivery of 27.1 does not imply checkpoint 27 completion.

## Delivery clarification after calculations

[Post-calculation plan](POST_CALCULATION_DELIVERY_PLAN.md) makes result-panel usability and actual-model evaluation explicit checkpoint 27 work, with later capability acquisition/learning pilots and private domain knowledge still proposed. It preserves the 30+ cross-chat gate and distinguishes future agents/policies from delivered services.

## Interaction and visualization follow-up — 2026-10-20

[27.3/27.4d delivery](CHECKPOINT27_ANALYSIS_AND_LAYOUT.md) implements chat-scoped
persistent collision-aware placement, preserved manual positions, return-lane
connections, cyan recorded/advisory evidence styles and the prominent warning
Allow writes switch beside Authorize/Execute. Settings shares the same policy;
model text cannot change availability. Ten chart views, explicit complete verified
CSV grouping and bounded WGS84 line/polygon/attribute snapshots extend Results.
Existing assessment responses enrich retained methods as separate advisory notes.
General obstacle routing, arbitrary geometry/CRS/layers and mature BI breadth stay
outside this foundation; the documented 28.3 expansion carries those requirements.
These changes do not substitute fixture responses for actual local-model evidence
or complete the 28.1/28.2/29 pre-demo gates.

[28.1 acquisition](OPTIONAL_CAPABILITY_ACQUISITION_PLAN.md) is now explicitly
optional at runtime, OFF by default and task-scoped, with existing capabilities
first and bounded generation only for a concrete gap. Its small tested pilot
remains required before demo; no mandatory acquisition stage is added to workflows.

## Current delivery order and demo gate

Operator addition (2026-10-18): [runtime write-control design](RUNTIME_WRITE_CONTROL_DESIGN.md).
27.7 now provides session controls for the main workflow/recipe paths;
[implemented behavior and limitations](CHECKPOINT27_RUNTIME_WRITES.md).

Operator revision (2026-10-19) sets the order: **remaining 27.3 evidence feedback →
remaining 27.4 visualization → 27.5 synthetic fixture evaluation → 28.1 generated
capabilities → 28.2 learning/RL → 29 advanced private memory → demo/real-data
acceptance**. Preserve existing numbering/history and the 30+ cross-chat deferral.
Learning remains opt-in at runtime, but implementation and validation of all three
later gates are required before the demo. Documents may be prepared earlier;
27.6 packaging follows the revised demo acceptance. Identify candidate data now,
without running real-data/live-service workflows before the applicable gates and
permission. Overwrite remains a separate operation-specific follow-up.

## Agreed direction

Additional operator-authorized slice: [bounded calculations and cumulative Planner budgets](BOUNDED_CALCULATIONS.md), with the [original design](BOUNDED_CALCULATION_DESIGN.md) preserved. This does not claim completion of checkpoint 27. It reuses Planner and deterministic services without a new agent or unrestricted code-generation path.

Normal use should be:

**Describe → clarify genuine missing inputs → review → authorize writes → execute
→ inspect actual results → automatically retain successful work → reuse with new inputs.**

Users should not need to ask “make this reusable”, type recipe JSON, supply
intermediate filenames, manually tag records or register each successful workflow.
Keep the existing Advanced controls available for inspection and optional
parameter generalization. Individual operations and graph block actions remain
necessary: recipes combine operations rather than replace them.

Planner owns discovery, composition, adaptation and optional recipe authoring.
Critic interprets recorded evidence and proposes applicability/limitations.
The Execution engine is deterministic software, not an LLM reasoning agent.
No separate Builder reasoning role, new model, container, MCP server or memory
architecture is required for this normal journey. Preserve legacy compatibility.

## Human, agent and backend responsibilities

| Work | Human action | Agent action | Backend service |
| --- | --- | --- | --- |
| Retain successful workflows | None routinely; optional rename/delete | Critic may describe applicability and limitations | Check eligibility; save, deduplicate, tag/index and link exact evidence; exclude credentials and authority |
| Reuse a workflow | Describe the new task; answer missing semantic questions; review/authorize consequential changes | Planner discovers relevant records and adapts them into an explicit workflow | Retrieve bounded candidates, check versions/contracts/paths, allocate safe mechanical outputs and validate the proposal |
| Enrich recipe descriptions | Optional correction | Critic proposes title, explanation and limitations from bounded evidence | Derive baseline metadata without a model; store provenance and bounded enrichment; continue on model failure |
| Visualize outcomes | Open results; optionally choose another supported chart/map | Agent may explain patterns using artifact/evidence references | Render bounded views from actual supported artifacts and distinguish them from model commentary |
| Evaluate laptop journeys | Perform initial acceptance; judge usability and objective suitability | Planner/Critic perform their existing roles under evaluation | Run fixtures, compare expected results and measure timing, failures and interventions |
| Prepare prototype/demo | Choose audience and approve any later publication | Agents may draft descriptions/demo narratives | Provide reproducible examples, setup/packaging checks and accurate limitations |

Agents handle uncertain interpretation. Services handle persistence, indexing,
validation, permissions and execution because these must work when a model fails.
Humans own intent, real-world suitability and consequential authorization. Do not
invent a percentage of automation: measure interventions per journey instead.
Development acceptance deliberately needs more human observation than normal use.

## Dependency-ordered delivery and acceptance

### 27.1 — Automatic successful-workflow records

Reuse durable runs and recipe/catalog services. After execution finishes, save a
successful-workflow record automatically with no additional model call. Keep
recording independent of Critic availability and browser lifetime.

A record describes **what passed with these bindings**, not proof that every new
input will work. Link source run/plan digests, operation/contract versions,
completion/required-validation evidence and supported output contracts. Keep
sensitive exact-scope details behind their existing private evidence references;
index only necessary safe metadata. Never copy credentials, password-file contents,
secrets, approval tokens or reusable authorization into a recipe.

Derive baseline title/tags such as `csv`, `inspection`, `cleaning` and `aggregation`
from trusted operation metadata. Separate exact successful-run identity from a
method-family index: similar methods can have different bindings and evidence.
Deduplication must not merge materially different filters, keys or parameters or
lose the successful source evidence. Define bounded retention/inventory behavior.

Acceptance:

- Successful inspection and multi-step CSV fixture runs create discoverable records
  without a “make reusable” request, JSON form, registration decision or model call.
- Failed, cancelled, interrupted or validation-failed runs cannot be labelled as
  successful recipes. Missing required validation is not success. Metadata-only
  inspections remain metadata outputs, never CSV-producing sources.
- Repeated completion handling is idempotent; restarting/reopening preserves records
  without reexecuting work. Recording failure preserves the completed run, reports
  the problem and permits an idempotent indexing retry, not an operation retry.
- Same-method runs retain distinct evidence/bindings where needed without duplicate
  identical definitions. Contract/source changes do not inherit old validity.
- Credentials/authorization are absent from reusable/indexed content. Retained
  success does not establish that a target still exists or remains unchanged.

### 27.2 — Planner retrieval and validated adaptation

Depends on 27.1. Make search useful before adding sophisticated memory. Retrieve
bounded operation/tag/contract matches through shared services and let Planner
adapt the selected method into an editable plan. Automatically allocate mechanical
CSV intermediate outputs; ask only for missing semantic choices such as join keys.

Acceptance:

- A similar natural-language request finds an automatically retained method and
  produces a valid proposal for different temporary fixture inputs without manual
  recipe selection, JSON or repeating registration.
- Interface and CLI use shared discovery/composition/validation contracts.
- Changed inputs, columns, filters, keys and output paths are explicit in review.
  Incompatible or stale contracts reject safely, preserving the previous plan.
- No stored approval is reused. Consequential writes still require fresh exact
  authorization and explicit execution through the existing flow.
- The interface shows the reused record and its evidence/applicability boundary;
  a generalized parameter template is not implied by one successful execution.

### 27.3 — Optional Critic enrichment

Delivered visibility slice: [advisory Critic graph branch](CHECKPOINT27_CRITIC_GRAPH.md), separate review/execution states, exact-run provenance and read-only restoration. Evidence-bound recipe notes are now indexed separately from immutable baseline metadata; laptop evaluation remains a separate acceptance gate.

Uses 27.1 evidence; it must not block 27.2. Extend the existing bounded outcome
assessment rather than introduce a required extra authoring conversation. Critic
may suggest a better title, method summary, applicability and limitations. Treat
those as model-derived annotations, distinct from observed success and trusted tags.

Acceptance:

- A model timeout, malformed response or disabled enrichment does not prevent
  baseline saving, indexing or reuse. Baseline functionality adds zero model calls.
- Calls are bounded, sequential on the laptop, cached against evidence and not
  silently replayed on refresh. Expose provenance and unavailable status.
- Critic cannot change deterministic execution status, enable an operation, grant
  authority or claim untested general applicability.
- Optional parameter generalization/synthetic testing remains available in
  Advanced, outside the ordinary successful-record save path.

### 27.4 — Contract-bound outcome visualization

[27.4c Results workspace](CHECKPOINT27_RESULTS_WORKSPACE.md) now delivers operation-specific tabs, resizing/expansion, searchable/paged tables, linked point selection and explicit hash-verified CSV reads through the shared API/CLI service. 27.4d adds ten bounded chart views, explicit complete verified CSV grouping and first-layer WGS84 line/polygon/attribute snapshots. Larger query/geometry/rendering scope moves to 28.3.

27.4a recorded-result delivery now shows selected-operation formulas, compact
input/output references, bounded saved tables and readable checks, restored only
for the matching chat and plan. [Acceptance and limits](CHECKPOINT27_RECORDED_RESULTS.md).
[27.4b](CHECKPOINT27_VISUALIZATION.md) now delivers per-row bar/scatter charts from saved table previews and offline first-layer WGS84 point snapshots. Fixture acceptance covers limits, unsupported/legacy data and restoration without file rereads/model calls. Broader geometry/layer support and laptop evaluation remain open.

Build on existing bounded previews and inspector/outcome components. Start with
CSV tables and a small supported chart set, then GeoJSON/vector map previews
where actual artifacts and declared CRS permit it. Document supported formats,
size limits and unavailable cases; do not promise arbitrary raster/database views.

Acceptance:

- Synthetic CSV fixtures show expected rows and a chart with correct categories,
  totals and labels. Supported geospatial fixtures show expected geometry and CRS.
- Every view identifies its artifact/run and displays any truncation, sampling or
  unsupported-format boundary; it never silently presents partial data as complete.
- Unsafe paths, oversized/malformed artifacts, HTML-like field values and invalid
  coordinates fail safely or show bounded literal content. No automatic live
  database query, external data upload or undeclared tile dependency is introduced.
- Opening a visualization neither executes a workflow nor triggers model calls.
  Model explanations remain separate from rendered data and deterministic checks.

### 27.5 — Actual laptop/model evaluation

Depends on the relevant reuse/visualization journeys. Preserve offline fixture
coverage, but separately measure the configured local model on the operator's
machine. Use fixed synthetic spatial, CSV and combined fixture examples, including a failure
and recovery. Compare with a documented manual baseline where practical.

Acceptance:

- Record model/version/settings, machine/runtime, input fixtures and repeatable
  prompts. Report attempt counts, valid-plan rate, timeouts, elapsed time, model
  calls, human interventions and output correctness for all attempts, not only wins.
- Each of the three domains completes planning, review, authorized execution,
  deterministic checks, viewing, automatic retention and a reuse attempt.
- Cancellation/restart and fresh-authority recovery preserve truthful outcomes.
  Do not repeat production writes or use live services without separate permission.
- Separate fixture-proven backend behavior from observed local-model quality.
  Establish any performance target from measured baseline; do not invent parity
  claims or accept invalid model output to improve reported success rates.

### 27.6 — Prototype installation, examples and demo preparation

Depends on 27.5 findings. Retain the existing one-command launcher. Provide a
function-based example index, install/dependency guidance, supported-platform
boundaries, end-to-end operator instructions and public-fixture demo materials
suitable for LinkedIn. Prepare bounded packaging/release materials only.

Operator sequencing decision: defer installable-package implementation until the
chosen data workflows and demo acceptance have been validated. Then prepare a
versioned installation artifact, built frontend assets, explicit runtime/model
requirements, startup diagnostics and separate writable user-data/configuration
locations. Validate clean installation, restart and preservation of chats/outputs
on each claimed platform. The artifact format remains undecided pending those
findings; documenting this work does not implement or publish a package.

Acceptance:

- A documented clean-environment setup/startup passes on each claimed platform;
  untested operating systems remain explicitly unverified.
- Spatial, tabular and combined examples have expected outputs and verification
  steps. Ordinary use needs no manual JSON or repeated recipe registration.
- Packaging excludes secrets, personal data, runtime records and browser profiles.
  Documentation describes real capabilities and limitations. No KNIME/Ansible
  Automation Platform parity claim without comparative evidence.
- Publication, release creation, Git changes and live-service writes require their
  own operator instructions. Preparing a demo does not authorize publishing it.

### 27.7 — Runtime write availability (implemented slice)

Added without renumbering existing slices. [Delivery, limits and acceptance](CHECKPOINT27_RUNTIME_WRITES.md). Use a backend policy service with API
session identity/revision, existing-style Settings switch, status and shared
interface/CLI enforcement. Changing availability grants no workflow authority;
Authorize/Execute must bind and recheck exact scope, expiry and session/revision.
OFF blocks later write dispatch; current work follows its supported boundary.
Transitions/restart cannot revive previous approval. Preserve readable historical
evidence and explicit administrative locks. [Full design, migration decisions,
acceptance and deferred replacement](RUNTIME_WRITE_CONTROL_DESIGN.md).

## Memory/privacy boundary to preserve

Recipe discovery is not permission to pool conversation memory. Cross-chat
transcripts, excerpts, summaries and automatic private-method sharing remain
**deferred to checkpoint 30 or later**, with a fresh operator decision.

Before implementing automatic retention, define the visibility contract: safe
operation-level method metadata versus private exact bindings/evidence. Automatic
records must not silently send another chat's paths, literals or history to the
model. Cross-chat reuse of private details must not become an implicit dependency
of 27.2. Demonstrate first within the originating chat and with curated/public
method templates; any broader sharing policy requires an explicit decision.

## Deferred work

No new agent hierarchy, indexed conversation-memory redesign, shared chat memory,
parallel execution, transactional write resume, automatic dependency installation
or unrestricted library execution. Prior memory/curator proposals remain preserved
for later checkpoints. Automatic successful records do not imply generalized
recipes; existing authoring/test controls remain optional Advanced capabilities.

## Resume instructions

At the next implementation turn, inspect actual Git status and current recipe,
durable-run, Critic and Planner discovery code before editing. Preserve user changes.
27.1/27.2 are already delivered. Use the latest delivery/evaluation report, then proceed through the remaining explicit gates in dependency order.
Keep normal user interactions minimal; do not replace backend fixture checks with
manual frontend data entry. Exercise complete browser journeys when available,
use temporary fixtures, and report implemented, verified, unverified and deferred
items separately. Run meaningful backend/frontend checks for changed boundaries.

This document authorizes no runtime implementation by itself. The current task is
only to preserve the agreed plan. Git/publication remains operator-controlled.
