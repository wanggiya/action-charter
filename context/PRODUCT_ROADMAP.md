# ActionCharter Product Roadmap

Updated: 2026-10-22

Planner reliability follow-up: schema-repair permission deferrals now use one correction attempt and preserve saved workflows on failure. Calculation follow-up recognizes multiplied/divided/new-column wording, supplies complete non-executing examples and distinguishes repeated repair deferrals from missing user scope. The correction budget and backend checks are unchanged. Conversational Planner now requests a portable decoder schema and distinguishes malformed JSON from reported output truncation; required proposal gates bind upward from registry contracts and backend policy remains authoritative. One local CSV planning smoke passed; broader evaluation remains open. [Protocol and diagnostics](../docs/PLANNER_STRUCTURED_OUTPUT.md). A historical plan claimed calculated columns but contained only inspect_csv. New explicit calculated-column requests check operation presence before storage, use focused instructions/typed source decoding and a narrow single-column skeleton and receive one correction on omission; old records remain unchanged. Reuse provenance now constrains generated IDs to supplied/inspected sources and refreshes after discovery; unverified claims still reject. These are narrow regression guards, not checkpoint completion.

Inspector follow-up: actual operation list and formula visibility, collapsed raw/audit details and compact history. This changes presentation only; a missing calculation is reported, never inserted or authorized automatically.

History usability follow-up: Execution History now lists named saved workflow runs directly and opens their outcomes without changing the active plan. Full learning/inspection coverage gates remain open.

Same-chat inspection follow-up: enforce loaded API `inspection-source-v2` before submission and test vector → raster → display → recorded facts → CSV. This is a reliability correction within checkpoint 28, with unchanged authority and deferred knowledge/RL scope.

## Checkpoint 28 revised consolidation target — 2026-10-22

[Target, baseline and ordered delivery](../docs/CHECKPOINT28_DISCOVERY_RESTRUCTURE.md): characteristics-first discovery with progressive verification, shared readers and focused agent context. Streaming CSV is now implemented with provisional metadata and complete streamed identity/counts; spatial discovery, multi-inspection, zero-model routing and measured learning remain gates. Existing bounded features stay compatible. No extra mandatory agents/containers; private domain knowledge remains 29 and cross-chat 30+.

## Checkpoint 28.1 bounded acquisition pilot — 2026-10-20

[Implementation and acceptance](../docs/CHECKPOINT28_1.md): a default-OFF per-chat switch lets Planner prepare one closed CSV text adapter family. Synthetic/held-out/effect checks precede explicit installation; normal review/authorization/execution follows. Fixtures and one actual-model OFF/ON/changed-input-reuse profile pass; operator acceptance and broader reliability remain explicit. This is generated data-only configuration, not unrestricted Python. Existing adapters/recipes remain first choice. General Python isolation is deferred; proceed to 28.2 only after this pilot is accepted. Then 28.3 visualization, 29 private knowledge and the established demo/package gates remain in order.

## Post-calculation delivery clarification

[Ordered plan and acceptance gates](../docs/POST_CALCULATION_DELIVERY_PLAN.md): 27.4a recorded-result usability; 27.3/27.5 agent evidence feedback and evaluation; proposed 28.1 bounded capability acquisition then 28.2 optional learning-policy evaluation; 29 private domain knowledge/corrections; existing 30+ cross-chat decision gate. 27.4a is now implemented for recorded operation cards, bounded tables and readable checks with chat/plan/run binding; [acceptance and limits](../docs/CHECKPOINT27_RECORDED_RESULTS.md). [27.4b visualizations](../docs/CHECKPOINT27_VISUALIZATION.md) deliver bounded bars/scatter and offline WGS84 point snapshots. Broader geometry/layer support and subsequent capabilities remain open. Preserve the existing operational/privacy checkpoint scope and finish each acceptance gate before starting its dependent work.

## Runtime writes and pre-demo gate — planned

[Design](../docs/RUNTIME_WRITE_CONTROL_DESIGN.md) and [27.7 delivery](../docs/CHECKPOINT27_RUNTIME_WRITES.md): next finish 27.3 evidence feedback, remaining 27.4 visualization and synthetic 27.5 evaluation. Then implement/validate 28.1 capabilities, 28.2 learning/RL and 29 advanced private memory before demo/real-data acceptance; 27.6 packaging follows.
Preserve historical numbering. 27.7 runtime write controls are delivered for the main workflow/recipe paths;
Settings availability must remain separate from exact authorization/execution,
with session/revision enforcement and explicit administrative restrictions.
Overwrite is a separate follow-up; use fresh outputs for initial data testing.
Capability lists must distinguish executable operations from scanned functions.
Operator revision (2026-10-19): generated capabilities (28.1), the learning/RL pilot (28.2) and advanced private memory (29) must be implemented and validated before demo or real-data testing. Runtime learning may remain opt-in; a design-only feature or unevaluated claim does not satisfy the gate. Cross-chat sharing remains 30+. Packaging follows the revised demo acceptance.

## Optional capability acquisition — decision recorded 2026-10-19

[28.1 design and measurable acceptance](../docs/OPTIONAL_CAPABILITY_ACQUISITION_PLAN.md):
OFF by default, explicit task opt-in, existing operations/recipes first. Size alone
never triggers generation. Prepare/test a restricted candidate only for a real gap,
with hard attempt/call/runtime/resource bounds. Reuse accepted installed versions;
installation, write availability, exact authorization and execution stay separate.
Evaluate saved effort against a fixed baseline, including failures. The bounded text pilot is now implemented; its acceptance and limits are linked above. Runtime optionality does not remove the pre-demo pilot gate.

## Immediate priority

Checkpoints 23–25 established the conversational interface, bounded tabular operations and governed extension contracts. Checkpoint 26 delivered bounded sequential execution, private-chat restoration, recipe composition and conservative recovery; see [closeout and limits](../docs/CHECKPOINT26_CLOSEOUT.md). The next implementation scope is **checkpoint 27**, below. Historical checkpoint proposals remain preserved. No release publication is authorized.

## Checkpoint 27 — technical acceptance; operator validation next

[Technical acceptance report](../docs/CHECKPOINT27_EVALUATION.md): 1,825 backend tests, 54 browser cases and six correct final-profile local-model executions. Earlier failures remain recorded; optional Critic timed out in the final profile. This is not a general reliability or release-readiness claim. 27.6 remains deferred until after the agreed pre-demo gates and selected-data acceptance.

[Detailed plan, human/agent/service responsibilities and measurable acceptance](../docs/CHECKPOINT27_PLAN.md).

1. **27.1 Automatic successful-workflow records — delivered:** new durable runs save/index/deduplicate eligible successes without a model call or registration ceremony. Own-chat discovery, separate source evidence and fail-soft indexing preserve privacy/authority. [Delivery and acceptance](../docs/CHECKPOINT27_RETENTION.md).
2. **27.2 Planner discovery/adaptation — delivered:** the existing Planner has bounded read-only catalog search/inspect and own-chat examples; ordinary chat handles reuse, with reference-only Recipe list/Keywords and manual composition in Advanced. Sanitized shared structures exclude private fixed literals. Fresh authority remains required. [Acceptance and limits](../docs/CHECKPOINT27_DISCOVERY.md).
3. **27.3 Optional Critic enrichment — delivered:** [Advisory graph visibility](../docs/CHECKPOINT27_CRITIC_GRAPH.md) is delivered; [Evidence-bound advisory method notes](../docs/CHECKPOINT27_ANALYSIS_AND_LAYOUT.md) now reuse existing assessments; immutable baseline identity/tags and own-chat visibility remain intact. Failure does not block baseline saving/reuse. Generalization remains optional Advanced work.
4. **27.4 Outcome visualization:** [27.4c Results workspace](../docs/CHECKPOINT27_RESULTS_WORKSPACE.md) adds single-view tabs, resizing/expansion, linked selections and explicit verified CSV reads. recorded tables plus [27.4b bars/scatter and WGS84 point snapshots](../docs/CHECKPOINT27_VISUALIZATION.md) are delivered. [27.4d analysis/layout](../docs/CHECKPOINT27_ANALYSIS_AND_LAYOUT.md) adds ten chart views, verified full-CSV grouping, first-layer WGS84 lines/polygons/attributes and persistent collision-aware placement. Bounds and run identity remain explicit; broader rendering is 28.3 and evaluation remains separate.
5. **27.5 Laptop/model evaluation:** spatial, tabular and combined journeys, including retention/reuse, measured failures, time, interventions and correctness.
6. **27.6 Prototype/demo preparation:** existing launcher, installation/platform checks, function-based examples and public-data demo/release materials. Implement a versioned installable package after data/demo acceptance, with clean-install/restart and user-data preservation checks; package format is undecided. No publication.

7. **27.7 Runtime write availability — implemented slice:** backend-enforced Settings switch, session/revision-bound authorization, direct-entry-point/CLI enforcement and disable/restart behavior. [Design and measurable gates](../docs/RUNTIME_WRITE_CONTROL_DESIGN.md). [Evidence-only authorization fix](../docs/CHECKPOINT27_AUTHORIZATION_FIX.md) preserves conservative plan gates in recipes. Overwrite remains a separate follow-up.

27.2 depends on 27.1; 27.3 enriches but does not gate either. Finish evaluation before claiming prototype readiness. Normal human work is intent/clarification, review, exact authorization and result judgment; agents interpret, while services persist/index/validate/execute. 27.1–27.4 and the 27.7 toolbar follow-up have bounded implementations; actual-model evidence and the operator acceptance gate remain separate. Legacy runs without contract snapshots are not backfilled. No new agent hierarchy or cross-chat memory is implied.

## Bounded-calculation extension — implemented slice

[Original design](../docs/BOUNDED_CALCULATION_DESIGN.md) and [implemented behavior/acceptance](../docs/BOUNDED_CALCULATIONS.md).
The existing Planner proposes typed calculations, backed by a trusted
table-expression validator/evaluator and cumulative request-budget enforcement.
No new agent/subagent, arbitrary Python or training is proposed. Candidate plus
one repair shares a four-call whole-turn ceiling with discovery; other limits and
laptop deadline calibration are documented. The operator authorized this bounded extension before demo work; it does not add a checkpoint 27
completion requirement or bypass the checkpoint-30 cross-chat decision gate.

## Checkpoint 26 operational delivery order

| Slice | Dependency and acceptance | Current boundary |
| --- | --- | --- |
| **26.6 — durable cancellation** | Existing typed runner: persist queued/running/final steps; cancel during active validation, skip later dispatch, reopen orphaned runs as interrupted without replay. | Implemented cooperative boundary cancellation and project lease; no forceful transaction/thread cancellation. |
| **26.7 — reusable recipe middle layer** | 25 contracts and existing recipes: compose spatial→CSV recipes, reject metadata-as-table and stale hashes; Planner-authored fixtures run privately, Critic reviews, one registration persists. | Implemented bounded JSON composition, three builtins and optional Planner authoring and Critic review. No arbitrary library execution, nested recipes or automatic registration. |
| **26.8 — recovery and intermediate inspection** | 26.6/26.7: inspect step previews/partial targets; resume remaining reads or prepare fresh write targets, requiring fresh authority. | Implemented conservative recovery proposals and bounded previews. Verified write-intermediate reuse and transactional resume remain open. |
| **26.9 — operational acceptance** | Complete API/CLI/browser journeys including failure, cancellation, refresh/restart, registration and recovery; report laptop model limitations. | 1,618 backend tests and 27 browser fixture groups pass; local-model evaluation moves to 27, broader recovery remains deferred. |

[Current closeout, acceptance and limits](../docs/CHECKPOINT26_CLOSEOUT.md). Checkpoint 26 closes the bounded sequential orchestration, private-chat context and reusable-recipe delivery. Earlier 26.2–26.5 indexed memory/curation proposals remain preserved as design history and move to checkpoints 28–29 after laptop evaluation; they are not completed features. Verified write-intermediate reuse and transactional resume are later operation-specific work, not prerequisites for the delivered conservative recovery. Checkpoint 27 is next: laptop evaluation, outcome visualization and prototype/release preparation. Cross-chat memory remains checkpoint 30 or later with a fresh decision.

## Dependency-ordered checkpoints 24–27

| Checkpoint | Depends on | Coherent functionality | Measurable acceptance |
| --- | --- | --- | --- |
| **24 — bounded tabular workflows** | 23's typed plan/graph/approval/recipe services | Explicit pandas-backed inspect, select, filter, missing-value handling, join, aggregation and CSV export; bounded previews, intermediate ancestor-output references, deterministic verification, CLI/interface parity and a compatible GeoJSON-attributes bridge. Reuse the existing registry rather than exposing Python functions. | A fixture pipeline of every operation yields exact expected rows/columns/values and evidence; a spatial→tabular pipeline passes. Read-only inspection requires no invented approval. Unsafe paths/expressions, malformed/oversized tables, incompatible references, missing/expired/mismatched authority and output collisions reject without unrelated writes. Model proposal, manual graph editing, review/execute/outcome/history and CLI use shared contracts. |
| **25 — operation contracts and governed extensions** | 24's working multi-domain operation contracts | Consolidate stable IDs/readable labels, typed inputs/outputs/parameters, dependencies/runtime requirements, effects/gates and preview/validation contracts into a shared searchable registry. Adapt existing IDs compatibly. Automatically inventory installed Python distributions and statically discover function/class/method signatures/docs/types with searchable, hash-bound snapshots and explicit incomplete native/dynamic coverage. Add documented package/adapter authoring, isolated testing and explicit installation, using one small example. | Existing plan/recipe digests and fixtures retain their behavior. CLI/UI contract discovery agrees; all-library scans and selected scans enumerate declarations without importing candidates, report bounds/coverage and cannot authorize execution. A small extension is packaged, tested and explicitly installed, with invalid signatures/contracts/entrypoints rejected. Installing a dependency never enables or approves its operation; arbitrary library functions remain unavailable. |
| **26 — scheduling and recovery correctness** | 25's consistent contracts; existing DAG order, persisted attempts and approvals | Extend existing dependency scheduling and durable state with cooperative cancellation, partial-output reporting, safe retry/resume, reusable workflow parameters and intermediate inspection. Add correlated agent/session event history and source-linked bounded summaries after reviewing the existing conversation storage; preserve transcripts and non-authoritative context. Preserve exact authority per consequential attempt. | Stop/restart/cancel at queued, read, write and validation boundaries produces durable truthful states and identified partial outputs. Failed/changed/expired-authority writes cannot repeat automatically. Read-only retry and explicitly reapproved write recovery demonstrate correct dependencies with no duplicate table/file writes. Reusable workflows and intermediate previews are source/digest-bound. |
| **27 — reliable reuse and evaluated laptop/PC prototype preparation** | 24–26 acceptance | First automatically retain/index validated successful workflows without model calls, use Planner for checked adaptation and optional Critic enrichment; then preserve the previous 26 benchmark direction: compare correctness, interventions, elapsed time and recovery against manual/general-agent work. Prepare one-command setup, explicit dependency guidance, spatial/tabular/combined examples, full manual acceptance and bounded portable packaging/release materials. Add contract-bound outcome charts/maps, a functional example index and public-fixture LinkedIn demo materials before release preparation. | Successful fixture runs become durable discoverable records without manual authoring; failures never become successes, reuse is validated and writes need fresh authority. Clean-environment installation/startup checks pass on documented supported platforms. All three examples produce expected evidence. Benchmark results and capability/limitation tables are reproducible, packaging contains no secrets/runtime/private datasets, and release materials are prepared without publishing. No KNIME/Ansible parity claim is made. |

Order: **24 → 25 → 26 → 27**. Finish each checkpoint's functionality and relevant automated/interface acceptance before starting the next. Missing browser/live-service acceptance is reported explicitly, never substituted with model text. Only temporary fixtures are used by automation; live services require separate explicit permission.

## 28.3 — Visualization expansion before representative demo acceptance

After 28.1 capability and 28.2 learning pilots, extend the current analysis foundation
using established rendering libraries where breadth/performance justify them:
grouped/stacked charts, bubbles/heatmaps, temporal axes, multiple map layers,
declared-CRS transformation, styling/legends, optional basemaps and linked filters.
Then add saved dashboards/export and appropriate raster/large-data support.
Acceptance uses fixed fixtures, correct totals/geometry, explicit scope and measured
laptop resource limits. Select the supported subset needed for the chosen demo;
no Tableau/Google parity or arbitrary-format claim is implied. See the
[ordered visualization expansion](../docs/CHECKPOINT27_ANALYSIS_AND_LAYOUT.md).
Advanced private domain memory remains 29, cross-chat remains 30+, demo/real-data
acceptance follows the agreed gates, and 27.6 installable-package work follows that
acceptance. Nothing is published by this roadmap.

## Cross-chat memory deferred: checkpoint 30 or later

The operator deferred cross-chat memory for several checkpoints. Checkpoints 26–29 keep conversation history/context separate; do not add cross-chat retrieval, shared summaries or sharing controls. Proposed later order: **28 operational pilots/resource measurements → 29 single-conversation retention/privacy → 30 or later explicit sharing decision gate**, after existing 26–27 work. [Dependencies and measurable acceptance](../docs/DEFERRED_CROSS_CHAT_MEMORY.md). Considering implementation at that gate requires a fresh operator decision; no shared-memory work is authorized now.

## Product direction

### Independent helper — first experimental integration

The [helper design/current slice](../docs/METHOD_MEMORY_HELPER_DESIGN.md) includes an OFF-by-default Settings opt-in, one serial request after changed validated workflow/bindings, private exact-scope cache and typed unvalidated Planner advice. No extra model/container or manual method-management UI is added. Opening a chat makes no model call. Fixtures do not establish local-model quality or complete checkpoint 26. Evidence extraction, corrections/revocation, semantic applicability and global scheduling remain future gates; shared services enforce authority. Cross-chat sharing retains its checkpoint-30-or-later gate. Original history remains below.

### Historical memory proposal — deferred beyond checkpoint 27

After scheduling/recovery foundations, deliver **26.1 one conversation/one task → 26.2 private indexed conversation memory → 26.3 curator/corrections → 26.4 methods/optional history → 26.5 operational acceptance**. [Architecture and measurable acceptance](../docs/PROJECT_MEMORY_ARCHITECTURE.md) define each slice. The operator authorized incremental work: 26.1 now follows one conversation = one task with private memory and local SQLite; indexed memory and curator/method slices remain planned. Prioritize local indexes and on-demand bounded curation. The optional [method-memory agent prototype](../docs/METHOD_MEMORY_PROTOTYPE.md) is an on-demand logical role in the existing API/model runtime, OFF by default. Its experimental backend supports selected-source procedure proposals, reviewed/unvalidated private method versions and explicit Planner inclusion; these manual controls are removed from normal UI in favor of one Chat memory switch and automatic latest-workflow restoration. The workflow-only helper now has a separate opt-in; evidence learning, indexed memory, automatic corrections and checkpoint 26 completion remain unfinished. No background agent or extra model is added. Preserve checkpoint 27 visualization/demo/release preparation and historical checkpoint records.

ActionCharter is a local-first, approval-gated execution and release system for AI agents using professional tools. A local model may interpret a request and propose a constrained workflow, but deterministic policy, typed schemas, human approval, trusted adapters, independent validation, evidence, and reproducible replay determine what becomes authoritative. GIS is the first complete reference domain, not the architectural limit.

The project should not compete by exposing the largest number of MCP tools. Its differentiation is the controlled path from an uncertain request and imperfect spatial data to a validated, auditable, reproducible spatial-data product.

## Existing foundation

The implemented foundation already includes:

- isolated Planner, Executor, Critic, GIS, workflow-runner, and candidate-test boundaries;
- typed plans, exact approvals, execution envelopes, workflow state, failures, evidence, and reports;
- trusted vector, PostGIS, raster inspection, and raster conversion operations;
- reusable recipes with constrained local-model proposal, deterministic compilation, approval, execution, validation, and evidence;
- immutable Snakemake export and replay through the existing Executor-to-MCP boundary;
- declarative skill contracts, isolated candidate generation and testing, digest-bound evidence, and explicit promotion;
- one data-only recipe catalog that drives trusted template discovery, parameter profiles, assessment policies, prompts, and deterministic step graphs.
- a complete PostGIS lifecycle from bounded inspection and deterministic
  comparison through exact promotion approval, serializable execution,
  independent verification, governed rollback, and independent rollback
  verification.

## Presentation target

The presentation-ready prototype should demonstrate one complete story:

```text
dirty spatial input
-> read-only data-contract assessment
-> constrained local-model recipe proposal
-> deterministic compilation and policy
-> exact human approval
-> isolated GIS execution
-> independent validation
-> separate Critic assessment
-> immutable release package
-> reproducible Snakemake replay
-> guided evidence view
```

The main message is:

> ActionCharter does not require users to trust an LLM with professional infrastructure. It uses the model for constrained interpretation and proposal, while deterministic software controls authority, execution, validation, evidence, and release.

## Checkpoint 14B — Isolated Builder agent

### Function

Add a separate Ollama-backed Builder role that proposes implementation candidates for new skills and catalog extensions.

The Builder receives a typed request, fixed templates, a bounded context bundle, and an explicit allowlist of candidate files. It returns structured candidate content. A trusted materializer validates paths, extensions, file counts, and size limits before writing only to an isolated candidate workspace.

### Required boundaries

- Model network access only; no control or backend network.
- Read-only access to selected templates and bounded project context.
- Write access only to one untrusted candidate directory.
- No Docker socket, MCP endpoint, PostGIS credentials, approvals, trusted registry, output data, recipe evidence, or trusted source write mount.
- No direct model filesystem writes; the model returns bounded structured output to a trusted writer.
- Static inspection before importing candidate code.
- Network-disabled candidate tests using the existing skill-test runner.
- Before/after candidate digests and bounded JSON test evidence.
- Explicit human promotion through the existing transactional promotion boundary.

### Why

This reduces repetitive implementation work without allowing model output to grant permissions, select arbitrary trusted entrypoints or verifiers, modify the registry, approve itself, execute GIS writes, or promote itself.

### Presentation scope

Demonstrate proposal and isolated candidate generation if stable. Do not let Builder implementation delay the user-facing controlled-workflow demonstration.

## Checkpoint 14C — Spatial data contracts and benchmark

### Function

Create versioned spatial data contracts and a read-only `assess_spatial_data_contract` skill.

Initial vector rules should cover:

- expected CRS;
- allowed geometry types;
- required fields and field types;
- nullability thresholds;
- unique-key requirements;
- feature-count boundaries;
- invalid, empty, and duplicate geometry thresholds;
- expected or permitted extent;
- mixed-geometry policy.

The result should identify the contract and dataset digests, list deterministic checks and violations, and explicitly state that no filesystem or database mutation occurred.

Create a dirty-spatial-data benchmark containing deterministic fixtures for wrong or missing CRS, invalid geometry, null geometry, duplicate identifiers, missing fields, incorrect field types, unexpected extent, empty data, mixed geometry, raster nodata problems, and raster resolution mismatch.

### Why

Data contracts turn an abstract safety architecture into an obvious GIS-quality demonstration. The benchmark provides repeatable evidence that the harness detects real spatial-data failures rather than merely generating plausible plans.

### Presentation scope

Vector contracts and a small dirty-vector benchmark are required. Raster contract rules may follow after the presentation if time is limited.

## Checkpoint 14D — Agent identity and operational history

### Function

Add structured identities and append-only operational events across all agent containers.

Use distinct fields:

- `agent_id`: stable logical role such as planner, executor, critic, or builder;
- `agent_instance_id`: one container startup;
- `agent_run_id`: one invocation;
- `task_id`: workflow identity;
- `correlation_id`: joins all work for the same operation;
- `parent_run_id`: delegation, retry, or replay ancestry.

Record bounded state transitions such as `run_started`, `input_validated`, `proposal_generated`, `policy_assessed`, `approval_verified`, `tool_requested`, `tool_completed`, `validation_completed`, `evidence_persisted`, `run_failed`, and `run_completed`.

Persist operational facts—not hidden chain-of-thought—including timestamps, role and instance identity, artifact digests, model and software versions, selected recipe and skill IDs, tool outcomes, policy decisions, failure codes, and evidence references.

### Why

Agent identity makes the multi-container architecture understandable, debuggable, and auditable. Correlation IDs connect Planner, Executor, GIS, Critic, Builder, and Snakemake activity without pretending that all agents share one implicit memory.

### Presentation scope

Show one workflow timeline joined by `correlation_id` and containing distinct Planner, Executor, GIS, and Critic runs.

## Checkpoint 14E — Authoritative results and release packages

Status: complete for the presentation-required authoritative workflow path.

### Function

Create one immutable release package for every completed run that is eligible to be treated as an authoritative candidate.

Implemented structure:

```text
releases/<release-id>.<release-sha256>.release/
|- CANDIDATE.json
|- RELEASE.json
`- files/
   |- plans/<plan>.json
   |- approvals/<approval>.json
   |- traces/<trace>.json
   |- reports/<report>.md
   |- critic-results/<package>/CRITIC_RESULT.json
   `- operational-history/<correlation>.events.jsonl
```

The release manifest includes the release and subject identities, exact candidate digest, complete component manifest, release time and explicit non-execution and non-registry-modification claims. The candidate record preserves the deterministic readiness decision and its approval, validation, Critic and evidence-completeness claims.

Critic output is persisted separately. Deterministic evidence may reference the Critic record, but model analysis is not confused with authoritative validation and cannot change workflow status.

Initial release states:

- `candidate`;
- `validated`;
- `released`;
- `rejected`.

### Why

A release package gives the workflow a clear final product. It lets an operator, reviewer, or presentation audience inspect exactly what ran, what changed, what passed, what the Critic concluded, and which artifacts are authoritative.

### Presentation scope

The real `checkpoint14e-release-demo-v1` vector-to-PostGIS workflow generated and independently verified one immutable six-component package. Connecting the fixed presentation workflow to Snakemake replay evidence remains part of Checkpoint 14F.

Recipe-specific assembly, predecessor-release metadata and publication state remain later extensions; they do not weaken the completed workflow release boundary.

## Checkpoint 14F — Pilot-ready demonstration

### Function

Prepare a stable demonstration dataset, scripted request, expected approval, deterministic output, failure example, release package, and replay path.

The demonstration should show:

- a dirty dataset failing a spatial contract;
- a valid vector or raster request proposed through the local model;
- the catalog-generated recipe and step graph;
- the exact approval-required step;
- controlled execution and independent validation;
- agent history and Critic output;
- the immutable release package;
- a Snakemake dry run or approved replay.

### Why

The project already has substantial infrastructure. A fixed end-to-end narrative converts that infrastructure into something understandable and memorable for employers, collaborators, and pilot users.

## Checkpoint 15 — Expanded PostGIS workflows and controlled release

Status: complete for the governed candidate-to-current promotion and rollback
lifecycle implemented in Checkpoints 15A–15K.

### Function

The implemented sequence provides:

- bounded relation inspection with no arbitrary SQL;
- deterministic candidate-to-current comparison and change assessment;
- digest-bound promotion planning and exact human approval;
- serializable, locked and reverified promotion execution;
- independent post-promotion inspection and evidence;
- deterministic rollback planning and separate human approval;
- serializable, locked and reverified rollback execution; and
- independent post-rollback inspection and evidence.

Completed lifecycle:

```text
bounded inspection
-> deterministic comparison and assessment
-> exact promotion plan and approval
-> transactional promotion
-> independent promotion verification
-> exact rollback plan and separate approval
-> transactional rollback
-> independent rollback verification
```

### Why

Staging separates successful technical execution from authoritative production state. Candidate/current comparison lets reviewers see feature-count, schema, CRS, geometry, extent, and content changes before approving promotion.

## Candidate future directions

The next numbered checkpoint is intentionally undefined while the completed
architecture, documentation, demonstration goals, and pilot priorities are
reviewed. The following sections are design candidates, not a committed
sequence.

## Candidate — Restricted GeoServer publication

Status: selected as Checkpoint 16. Checkpoint 16A implements bounded read-only
catalog inspection before any publication authority is introduced.

### Function

Add publication planning, execution, and verification only for authoritative promoted releases.

Required capabilities:

- validated workspace and datastore allowlists;
- restricted GeoServer credentials;
- publication plan with no side effects;
- exact approval for publication;
- controlled layer creation or update;
- service verification;
- publication URL, layer identity, style identity, and release lineage evidence;
- explicit failure and rollback guidance.

### Why

Publishing before staging and promotion could expose an unreviewed candidate. GeoServer must consume an authoritative release, not merely the latest successful execution.

## Candidate — Guided product interface and Snakemake productization

Checkpoint 17A status: implemented for review. The initial read-only interface
uses a schema-validated demonstration graph and makes node authority and
evidence visible without adding browser execution authority. Live evidence
projection, proposal-only graph editing and guided Snakemake operations remain
later Checkpoint 17 slices.

Checkpoint 17B status: implemented for review. It adds an offline, bounded and
redacted projection from one exact validated workflow trace to the frontend
graph contract. A live HTTP evidence service, run inventory and graph editing
remain deferred.

Checkpoint 17C status: implemented for review. It adds a capped offline run
inventory, atomic derived-projection export and a strict read-only selector.
Live HTTP serving, automatic refresh and proposal editing remain deferred.

Checkpoint 17D status: implemented for review. It adds evidence-backed node
details using bounded aggregate facts, timing and safe findings. Complete
artifact navigation, responsive inspector sheets and proposal editing remain
deferred.

Checkpoint 17E status: implemented for review. It adds expandable safe evidence
previews with explicit categories, status, digest metadata and basename-only
artifact references. Full artifact-content rendering remains deferred until
each artifact family has a dedicated sanitization contract.

Checkpoint 17F status: implemented for review. It derives the operation chain
from recorded tool calls, caps it at twenty operations, neutralizes unsafe
operation labels and sizes both graph orientations from real topology.
It also establishes process-first node labels with embedded performers, a
matching semantic minimap and a selectable full-width process timeline. Live
timestamps and explicit failure placement remain part of the execution-state
interface slice.

Checkpoint 17G status: implemented for review. It separates semantic process
category, owner group and performer; applies the shared professional node,
group and minimap visual language; and retains legacy projection rendering.
The next interface slice can build input and planning interactions against
stable visual and schema semantics.
The following structural slice must add typed control and data edges plus an
agent interaction lane above owned tool/data operations before editable plans
are introduced.

Checkpoint 17H status: implemented for review. Typed control, governance,
tool, data and evidence edges now drive a two-lane trace graph. Request and
bounded Input Data enter the Planner separately. Planner and Executor use
triangular interaction sockets and circular data/tool sockets. Executor enters
the first recorded operation, recorded operation order forms the processing
path, and only the final operation enters validation. Unrecorded optional
components are omitted.
Ports follow the selected layout axis and only matching hollow socket families
connect. Selected-run projection failures are explicit rather than hidden by a
shared demonstration fallback.
Proposal-mode node placement and typed reconnection remain future editing work.
Snakemake replay must become an explicit trace-producer field for complete
historical projection; 17H displays it only from recorded runtime/operation
metadata and never guesses from a task ID.

Checkpoint 17 owns the complete guided operating interface described in
`docs/INTERFACE_PRODUCT_SCOPE.md`, including PostGIS, GIS adapters, recipes,
Snakemake, skills and the currently implemented GeoServer inspection and
publication boundaries. Checkpoint 18 follows with pilot operations and
bounded memory; it is not a substitute for completing the interface.

Checkpoint 17I status: implemented for review. Evidence mode remains immutable;
Proposal edit creates a separate in-memory draft and supports bounded node
creation, field editing, deletion and orientation-aware movement. Draft changes
cannot execute or persist. The next slices must add typed connection editing,
request/input composition, backend proposal compilation, policy feedback,
digest-bound approval, governed execution, live state and evidence navigation.

The interface should eventually complete routine workflows without requiring
the operator to type CLI commands. The CLI remains fully supported for scripts,
CI, diagnostics and advanced operation. Both interfaces must share contracts;
the browser must not reimplement or bypass the governed backend.

Checkpoint 17J status: implemented for review. Browser-local proposals now
support compatible typed connection creation and incident-connection deletion,
with explicit endpoint selection, duplicate rejection and cycle prevention.
The next slice is the versioned proposal contract plus safe save/compile
boundary; Planner, policy, approval and execution remain later governed slices.

Checkpoint 17K status: implemented for review. The validated CLI recipe catalog
is projected into the browser without introducing a second template source.
Operators can select a trusted template, enter required parameters, inspect its
declared graph and download the same non-executable proposal contract consumed
by the CLI compiler. The next slice adds a loopback-only typed assessment and
compilation service; explicit persistence, policy, approval, execution, live
state and evidence remain separate later gates.

Template discovery belongs in a dedicated top-level workspace near workflow
selection, not inside selected-node inspection. Capability maturity will be
tested through paired cases: establish a governed CLI baseline, then run a
comparable interface case with different safe identifiers and targets and
compare normalized contracts, gates, validation and evidence.

The graph foundation includes measured fit-to-viewport, a live pannable
minimap, and user-selectable horizontal or vertical layouts, with vertical as
the narrow-screen default.

The candidate capability-registry and pandas-adapter sequence is preserved in
`context/CAPABILITY_EXPANSION.md`. It follows the interface and pilot evidence
work and does not permit browser package installation or raw socket access.

### Function

Build a thin guided interface over existing backend contracts. It should display rather than reimplement orchestration.

Recommended views:

- request and proposal;
- catalog recipe and step graph;
- approval review;
- data-contract checks;
- agent execution timeline;
- validation results;
- artifact lineage;
- Critic conclusion;
- release package;
- Snakemake export, DAG, dry-run, replay, and completion status.

User-facing Snakemake actions should be limited to:

- export reproducible workflow;
- validate export;
- dry-run replay;
- run approved replay;
- inspect replay evidence.

### Why

The interface makes the security and evidence model visible. Snakemake should appear as the reproducibility engine, not as another programming surface users must understand.

### Presentation scope

A read-only interface is sufficient. Execution controls may remain CLI-driven until authorization and error handling are mature.

## Candidate — Pilot operations and bounded memory

### Function

Run real pilot workflows, observe failures and operator behavior, and only then add operational memory.

Permitted memory candidates include accepted corrections, frequently selected contract profiles, stable dataset aliases, repeated failure resolutions, and operator-approved defaults. Every memory record should have provenance, scope, version, expiration or review policy, and a deletion mechanism.

Do not store hidden reasoning, secrets, unrestricted conversation history, or automatically inferred permissions.

### Why

Memory designed before pilot use tends to preserve imagined needs and stale assumptions. Pilot evidence should determine what is useful, safe, and worth retaining.

## Skill strategy

Do not maximize the number of MCP tools. Prefer a small, curated skill surface with clear access classes, schemas, deterministic policy, verification, and evidence.

### Presentation-priority skills

- `assess_spatial_data_contract`;
- `compare_spatial_dataset_versions`;
- `inspect_release_package`;
- `verify_release_package`;
- optionally `summarize_validation_failures` as a read-only reporting skill.

### Later PostGIS skills

- `inspect_postgis_table`;
- `query_postgis_read_only`;
- `transform_postgis_layer`;
- `compare_postgis_tables`;
- `export_postgis_layer`;
- `validate_postgis_export`.

### Later raster skills

- `validate_raster_contract`;
- `compare_rasters`;
- `clip_raster`;
- `resample_raster`;
- `build_raster_overviews`.

### Later publication skills

- `plan_geoserver_publication`;
- `publish_geoserver_layer`;
- `verify_geoserver_layer`;
- `deprecate_geoserver_layer`.

Avoid unrestricted shell, generic filesystem mutation, generic network access, unrestricted SQL, or direct infrastructure-administration skills. External MCP servers may be integrated later as untrusted proposal or read-only information sources, but they should not bypass the existing policy and execution boundaries.

## Open-source direction

Open-source the core before attempting an open-core or commercial split. The immediate goals are credibility, reproducibility, collaboration, pilot adoption, and portfolio value—not premature feature monetization.

Public components should include schemas, policy, CLI, SDKs, Docker deployment, validators, benchmark fixtures, Snakemake export, demonstration interface, threat model, and examples.

Keep credentials, customer data, organization-specific policies, private contracts, managed-hosting configuration, and customer deployment details outside the public repository.

Consider Apache-2.0 after checking dependency and fixture licenses. Add or maintain `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md`, and publish versioned releases rather than relying only on `main`.

## Priority before the presentation

Required:

- vector spatial-data contracts;
- dirty-vector benchmark;
- agent run identity and correlated operational events;
- immutable release package with separate Critic record;
- one polished vector or raster end-to-end demonstration;
- one Snakemake export/replay demonstration;
- a read-only guided evidence view or carefully prepared CLI walkthrough.

Useful if stable:

- minimal Builder proposal and isolated candidate generation;
- raster contract rules;
- candidate/current comparison outside production PostGIS.

Defer if schedule is tight:

- production-style PostGIS promotion;
- full GeoServer publication;
- write-enabled web interface;
- broad external MCP integration;
- autonomous operational memory;
- commercial packaging.

## Prototype release definition

The prototype is ready to present when one fixed scenario can be repeated from a clean checkout and produces the same validated structure:

```text
request
-> proposal
-> catalog recipe
-> approval
-> execution
-> validation
-> agent history
-> Critic record
-> release package
-> Snakemake replay evidence
```

The prototype does not need to be a general-purpose GIS platform. It needs to prove that model-assisted GIS work can be constrained, inspected, approved, validated, reproduced, and released.

Checkpoint 14F satisfies this presentation definition for one fixed vector
scenario. The repository now includes deterministic readiness assessment and a
clean-checkout walkthrough; the demonstrated run completed plan approval,
PostGIS execution and validation, correlated history, separate Critic evidence,
authoritative release inspection, and approved Snakemake replay. Broader
raster contracts and publication remain later work. The separately implemented
15A–15K lifecycle now covers governed PostGIS promotion and rollback.

## Checkpoint 15: controlled PostGIS operations

Checkpoint 15A establishes bounded read-only inspection of one exact table:

- allowlisted schema and conservative table identity;
- fixed catalog and aggregate queries only;
- bounded columns, keys, geometry columns and observed types;
- relation, schema, key, CRS, count, quality and extent facts;
- CLI and read-only MCP access with credential-redacted failures.

The later 15B–15K increments preserve separation between observation,
authorization, mutation and independent verification without introducing
unrestricted SQL.

Checkpoint 15B adds the comparison increment as a read-only composition over
inspection. It compares normalized metadata and data-quality facts for two
exact relations in one repeatable-read transaction and reports bounded typed
differences. It grants no promotion authority.

Checkpoint 15C adds a fixed non-mutating policy assessment over comparison
evidence. It distinguishes compatible facts, review-required observational
drift and incompatible structural change while withholding approval and
promotion authority.

Checkpoint 15D adds deterministic promotion planning for compatible evidence.
It binds exact reference, candidate and absent archive identities; inspection
snapshots; the change assessment; approval scope; transactional choreography;
rollback; and post-promotion validation into one canonical SHA-256 plan.

Checkpoint 15E records a human decision for an exact 15D plan digest in
canonical, write-once approval evidence. Approved scope is fixed to the
archive-reference and promote-candidate mutations; corrections require a new
plan.

Checkpoint 15F completes transactional promotion with locked snapshot
reverification, archive-absence verification, fixed identifier-safe renames,
rollback on failure, post-promotion validation and immutable execution evidence.

Checkpoint 15G adds independent read-only post-promotion verification and a
separate immutable verification package.

Checkpoint 15H adds deterministic rollback planning only for a fully verified
15D/15F/15G evidence chain. It fixes the future locking, candidate restoration,
reference restoration and validation choreography, while withholding approval
and execution authority.

Checkpoint 15I records immutable human approval for exactly the two mutation
steps in an exact 15H rollback plan. Checkpoint 15J consumes that approval only
after explicit digest confirmation and performs the fixed rollback atomically,
with locked input reverification, candidate-absence proof, post-rollback
validation and immutable execution evidence.

Checkpoint 15K independently reloads and rehashes the rollback plan, approval
and execution package, verifies their exact identity and scope bindings, and
inspects the restored relations through a separate read-only transaction. It
persists distinct digest-addressed verification evidence and closes the
governed promotion and rollback lifecycle.

### Checkpoint 16B — governed activation of an existing GeoServer layer

Status: complete and live-validated on GeoServer 2.28.0. One exact allowlisted layer that already has
an existing feature type and catalog layer may be enabled and advertised through
one fixed PUT to the authoritative feature-type resource only after digest-bound planning and explicit human approval.
Execution revalidates the unchanged pre-state, validates the resulting state,
and compensates failed transitions; independent read-only verification produces bounded findings. Workspace,
store, feature-type, style and deletion administration remain out of scope.
### Checkpoint 17L — CLI/interface parity baseline

- Commit one safe RecipeProposal fixture and its trusted catalog source.
- Prove deterministic, non-mutating compilation through the CLI and tests.
- Compare the future interface result by normalized contract semantics.
- Keep save, approval, execution, validation and evidence as later explicit
  authority increments.

Next: add a loopback-only typed proposal assessment/compilation service. It
must call existing Python domain services directly, accept no arbitrary command
or path, and perform no persistence or execution.
### Checkpoint 17M — loopback proposal compilation

- Serve trusted catalog and deterministic compilation on `127.0.0.1` only.
- Validate bounded requests and responses with existing backend and browser
  contracts.
- Display compiled step order and approval/validation gate counts.
- Retain explicit no-save, no-approval and no-execution claims.

Next: reviewed recipe persistence through a distinct typed endpoint and visible
operator action. Do not combine persistence with approval or execution.
### Checkpoint 17N — digest-bound reviewed recipe storage

- Display the exact compiled recipe digest and ordered steps.
- Require a separate explicit operator review confirmation.
- Recompile and verify the digest immediately before immutable storage.
- Write only beneath the fixed ignored recipe root with no overwrite.
- Preserve `approval_performed=false` and `execution_performed=false`.

Next: inventory stored recipes and prepare a separate exact approval action.
Do not combine approval recording with execution.
### Checkpoint 17O — stored recipe inventory

- Keep save evidence visible until an explicit operator transition.
- Provide a persistent read-only Recipes inventory.
- Show exact digest, ordered skills and future approval/validation gates.
- Exclude arguments, identities and execution controls.

Next: prepare an exact approval request for a selected stored recipe, while
keeping decision recording and execution as separate later actions.
### Checkpoint 17P — exact approval-request preparation

- Select one canonical stored recipe by safe filename and digest.
- Rehash it and rerun deterministic policy.
- Bind all required approval steps into a canonical request digest.
- Display the exact scope without accepting or recording a decision.

Next: explicit append-only human decision recording bound to the prepared
request and recipe digest. Execution remains a later separate gate.
### Checkpoint 17Q — append-only recipe approval decision

- Collect an explicit approve or deny decision in a separate drawer.
- Bind it to the exact prepared request and canonical recipe digests.
- Derive required steps server-side and redact operator text.
- Persist append-only approval evidence with optional bounded expiry.
- Continue to expose no execution action.

Next: independently verify the recorded approval against the immutable recipe
and current deterministic policy before any execution control exists.
### Checkpoint 17R — independent recipe approval verification

- Promote append-only evidence and nothing-executed outcomes into large status cards.
- Reload the immutable recipe and approval from fixed roots.
- Recompute the recipe digest and rerun deterministic policy.
- Verify decision, expiry and exact required-step scope without modifying evidence.
- Continue to expose no execution action.

Next: add a deterministic execution preview that names the exact approved recipe,
steps, tools, inputs and evidence destinations before execution authority exists.
### Checkpoint 17S — exact execution preview

- Reverify the immutable recipe and approval immediately before preview.
- Build the existing governed recipe execution envelope.
- Show ordered skills, access classes, dependencies, redacted arguments and outputs.
- Show validation requirements and future run/evidence destination roots.
- Expose no execution action or execution authority.

Next: add one separately confirmed execution action for the exact previewed
envelope, with live state and fail-closed evidence persistence.
### Checkpoint 17T — first governed interface execution

- Require explicit confirmation of the exact execution-preview SHA-256.
- Keep execution disabled unless `ENABLE_WRITE_TOOLS=true` is explicit at startup.
- Rebuild recipe, approval, policy, preview and execution envelope server-side.
- Invoke the existing allowlisted approved-recipe boundary.
- Persist and display run, evidence and report identities.
- Prevent concurrent duplicate execution in one interface-service process.

Next: add live step progress, durable execution state, failure localization,
interruption handling and safe retry/recovery guidance.

### Checkpoint 17U — live execution state and recovery

Checkpoint 17U-A status: implemented for review. The real recipe runner emits
typed step transitions, and the loopback interface projects them through an
exact execution-preview digest lookup. The interface displays queued, running,
completed, failed and interrupted states and marks the known failure or
interruption location. Atomic progress snapshots survive API restarts and
provide fail-closed recovery guidance. Elapsed time, durable run inventory,
browser-session restoration and separately approved retry remain future work.

### Checkpoint 17V — durable attempt inventory and graph restoration

Status: implemented for review. The loopback API enumerates at most 200 safe
progress artifacts beneath the fixed execution-state root and returns bounded
identity and status summaries. The interface exposes a Runs workspace and can
reconstruct a run-specific read-only graph from recipe identity, skills and
dependencies stored with new attempts. Reopening has no approval, retry or
execution authority. A separately approved retry design remains future work.

### Checkpoint 17W — Planner Agent interface entry point

Status: implemented for review. A top-level Plan workspace sends one bounded
request through the existing Planner Agent, trusted context pack, configured
model client and schema validation. It displays proposed steps and approval
requirements and can project the validated result as a planning-only graph.
It does not persist, approve or execute the plan. Local 4B-model validation led
to a correction in the same checkpoint: lexical skill inference was replaced
with explicit registry-verified selection, and the generation payload was
reduced to the request, relevant datasets and selected skills.

### Checkpoint 17X — reviewed Planner-result storage

Checkpoint 17X status: implemented for review. The Plan workspace now displays
the canonical digest for an exact validated result and requires explicit review
before a distinct save action. The backend revalidates the full Planner-result
schema, selected implemented skills, deterministic policy and digest, then
creates one non-overwriting CLI-compatible artifact beneath `plans/`.

No approval or execution occurs. Next: prepare and record an exact human plan
decision bound to the immutable result.

### Checkpoint 17Y — exact plan-approval preparation

Checkpoint 17Y status: implemented for review. A stored Planner result can now
be reloaded and revalidated to derive its exact approval-required step scope and
canonical request digest. Read-only plans report that approval is not required.
No decision is recorded and no execution occurs. Next: append-only approve or
deny recording for plans whose trusted scope requires human authority.

### Checkpoint 17Z — append-only plan decision

Checkpoint 17Z status: implemented for review. Plans with trusted
approval-required steps now expose an explicit approve-or-deny form. The server
reprepares the exact request and derives scope before using the existing
append-only approval service. Read-only plans cannot produce approval records.
No execution occurs. Next: independently verify recorded plan authority.

### Checkpoint 17AA — plan-decision inspection and verification

Checkpoint 17AA status: implemented for review. Exact secret-redacted arguments
and approval/validation flags are visible before a plan decision. A separate
verification action rereads immutable plan and approval evidence and checks
digest, decision, expiry, and complete required-step coverage. Neither artifact
is modified and nothing executes. Next: non-executing Planner envelope preview.

### Checkpoint 17AB — Planner execution-envelope preview

Status: implemented for review. Verified plan authority can be translated by
the existing Executor policy into a typed non-executing envelope. The currently
supported shape remains the fixed vector-to-PostGIS four-step vertical slice;
other valid plans are rejected rather than falsely presented as executable.
Next: restart-safe plan/approval inventory before exact execution authority.

### Checkpoint 17AC — restart-safe plan restoration

Status: implemented for review. Recent immutable plans and matching decisions
can be restored without regeneration or duplicate approval. Restored decisions
require fresh independent verification. Next: expand typed Executor support
beyond the fixed PostGIS slice before adding exact execution authority.

### Checkpoint 17AD — verified plan to governed recipe candidate

Status: implemented for review. An independently verified Planner result can be
compiled into the existing typed recipe contract for supported dispatcher
skills. The candidate is deterministically validated and digest-bound but is
not saved, approved, or executed. Next: persist the exact reviewed candidate
and enter the existing recipe approval and execution sequence without
transferring plan approval.

### Checkpoint 17AE — reviewed Planner recipe storage

Status: implemented for review. The operator can confirm the exact compiled
recipe digest and ordered steps, after which the server reverifies source
authority, recompiles, revalidates policy, compares identity, and immutably
stores the recipe. No recipe approval or execution occurs. Next: guide the
stored artifact through the existing recipe approval and execution surfaces
without requiring the operator to rediscover it manually.

### Checkpoint 17AF — exact stored-recipe approval handoff

Status: implemented for review. The post-storage action opens a freshly loaded
recipe inventory bound to the exact stored digest and prioritizes the matching
artifact. Approval preparation remains explicit. Next: preserve this identity
through approval, verification, execution preview, execution, and outcome
verification as one visible end-to-end interface journey.
### Checkpoint 17AM — rooted interface data paths

- [x] Accept filename-only input and output parameters in trusted templates.
- [x] Canonicalize them before recipe hashing and approval.
- [x] Preserve explicit paths and the existing CLI workflow.
- [ ] Complete remaining interface parity for every supported governed action.

### Checkpoint 17AN — governed resource selection

- [x] Inventory governed project inputs through the loopback API.
- [x] Select existing input and output locations in trusted templates.
- [x] Bind selected inputs into Planner context without granting authority.
- [x] Preserve explicit safe relative paths as an advanced workflow.

### Checkpoint 17AO — actionable Planner rejection

- [x] Preserve safe deterministic policy findings at the HTTP boundary.
- [x] Display the rejection prominently in Plan.
- [x] Provide explicit retry without weakening or bypassing policy.

### Checkpoint 17AP — responsive Planner authoring

- [x] Remove task typing from the per-keystroke graph rerender path.
- [x] Preserve bounded skill recommendations and exact submission.
- [x] Preserve immutable saved-plan restoration.

### Checkpoint 17AQ — deterministic Critic assurance

- [x] Inventory trusted WorkflowTrace/report pairs through the interface.
- [x] Reuse deterministic Critic evidence validation without a model call.
- [x] Surface validation, approval completeness, gaps, warnings, and hashes.
- [x] Preview completed recipe-run evidence as a validated WorkflowTrace.
- [x] Persist an explicitly reviewed adapted trace and report.
- [x] Add explicit model Critic invocation with in-memory validated results.
- [x] Add immutable Critic result recording.
- [x] Add governed release readiness and release creation.

### Checkpoint 17AR — recipe-run trace adaptation preview

- [x] Correlate immutable recipe, approval, evidence, and durable timing.
- [x] Represent recipe authority with its own trace digest field.
- [x] Prove adapted candidates through the existing Critic evidence builder.
- [x] Reject identity-incomplete or contradictory runs without guessing.
- [x] Persist an explicitly reviewed adapted trace and deterministic report.

### Checkpoint 17AS — reviewed adapted-trace persistence

- [x] Require operator confirmation of the exact adapted-trace digest.
- [x] Rebuild the candidate from immutable source evidence before writing.
- [x] Store the trace and deterministic report without overwriting.
- [x] Revalidate the stored pair through the existing Critic evidence builder.
- [x] Invoke the Critic model through a separate explicit action.
- [ ] Record a validated Critic result immutably.

### Checkpoint 17AT — explicit read-only Critic assessment

- [x] Bind invocation to exact stored trace and report digests.
- [x] Require explicit operator confirmation before model use.
- [x] Reuse the existing Critic schema and deterministic conclusion policy.
- [x] Keep the validated result in memory with no release authority.
- [x] Record the exact reviewed Critic result immutably.

### Checkpoint 17AU — immutable Critic-result recording

- [x] Require explicit review of the complete Critic-result digest.
- [x] Rebuild and compare deterministic evidence before recording.
- [x] Reuse atomic digest-addressed Critic-result storage.
- [x] Keep release creation and execution unavailable.
- [x] Assess release readiness from the immutable record.

### Checkpoint 17AV — governed recipe release

- [x] Assess recipe releases as recipes rather than inventing planner authority.
- [x] Bind recipe, approval, run result, recipe evidence, trace, report, Critic
  record, and operational history by identity and digest.
- [x] Prepare operational history through a visible non-executing interface step.
- [x] Require confirmation of the exact readiness-candidate digest.
- [x] Create an atomic immutable release without rerunning tools or changing data.
- [x] Export and validate the exact approved recipe through Snakemake (17AW).

### Checkpoint 17AW — governed Snakemake export

- [x] Rebuild approval authority before export planning.
- [x] Preview the exact replay entrypoint, file set, steps, and plan digest.
- [x] Require a separate confirmation of the reviewed export-plan digest.
- [x] Generate the immutable package through the existing export service.
- [x] Run static contract validation immediately after generation.
- [x] Keep Snakemake invocation and recipe replay outside this checkpoint.
- [x] Close the guided prototype with an honest Snakemake isolation boundary (17AX).

### Checkpoint 17AX — guided prototype closure

- [x] Audit the interface path from request through release and export.
- [x] Make repeated exact export requests idempotent and visibly revalidated.
- [x] Keep actual replay in the isolated workflow-runner rather than granting
  Docker or arbitrary process authority to the loopback browser API.
- [x] Record default-versus-advanced UX and capability-expansion requirements.
- [x] Mark Checkpoint 17 complete for prototype release preparation.

### Checkpoint 17AY — complete PostGIS interface vertical slice

- [x] Compile the fixed inspect/load/validate/report Planner sequence into a recipe.
- [x] Add typed hard-coded dispatch for the existing PostGIS load and verifier.
- [x] Preserve separate recipe approval and independent post-write validation.
- [x] Materialize the authoritative report only during immutable run persistence.
- [x] Complete one fresh operator-run PostGIS acceptance workflow through export.

Checkpoint 17 is complete at the guided prototype boundary after a fresh
PostGIS operator acceptance run. Checkpoint 18
starts product simplification, unified local startup, conversational task
history, stronger intent decomposition, tabular data, and governed capability
discovery.

### Checkpoint 18 — reproducible local startup

- [x] Start the loopback interface API and frontend with one command.
- [x] Validate pinned local prerequisites without installing packages.
- [x] Report optional Ollama, Docker, PostGIS, and GeoServer availability.
- [x] Disable write and overwrite authority by default.
- [x] Require an explicit flag for bounded write-tool authority.
- [x] Stop both child services cleanly with one interrupt.
- [x] Validate the launcher in the reference Ubuntu 24.04 WSL2 environment
  (operator-reported startup and checks).
- [ ] Publish the first alpha release from protected `main` after CI passes.

### Checkpoint 19 — simplified default workspace

- [x] Make Plan → Review graph → Run → Check outcome the primary navigation.
- [x] Move expert entry points into an Advanced navigation without removing them.
- [x] Navigate from a reviewed plan through the existing governed recipe and
  approval path to a validated outcome (operator-reported full PostGIS run).
- [x] Validate the responsive interface and full local workflow in WSL2
  (operator-reported browser and PostGIS run; artifact audit remains optional).

Checkpoint 19 closes the navigable prototype. Reducing repeated manual gates
to one reviewed task decision depends on governed history/context and remains
an explicit Checkpoint 22 integration requirement, not a claim of current UX.

### Checkpoint 20 — automatic authority-chain projection

- [x] Verify plan-to-decision relationships server-side and display blocked
  records distinctly in the saved-plan inventory.
- [x] Compare bounded canonical authority, result, trace, Critic, and release identities and digests server-side.
- [x] Connect only verified relationships in read-only local flow graphs.
- [x] Move routine digest display into expandable audit details.

Physical output freshness checks and a simplified task-level decision flow are later work; stored output digests are presented as recorded evidence.

### Checkpoint 21 — governed task history

- [ ] Append immutable requests, clarifications, selections, decisions,
  outcomes, failures, and artifact references under one task identity.
  The CLI, checked store and loopback API are available. New Planner sessions record selected inputs, a planning outcome or failure, and a history-only decision note; exact task-derived recipe runs record a result or failure. Historic artifact correlation remains open.
- [x] Build deterministic bounded task-event context packages with redaction, source
  references, size limits, and reproducible selection rules.
- [ ] Include independently verified existing artifact references and historic task recovery.
- [x] Expose a bounded current-task context preview beside the flow graph.
- [x] Keep original records authoritative; summaries remain derived views.

### Checkpoint 22 — reviewed context and intent reasoning

- [ ] Show the exact bounded task context and source references before model use.
- [ ] Add an Intent Agent that clarifies the goal and proposes a goal-level process
  without approval or execution authority.
- [ ] Map reviewed intent through the existing Planner to implemented typed skills;
  preserve deterministic policy and make unavailable-skill findings actionable.

### Checkpoint 23 — task-centered agent interface

- [ ] Put task conversation/context beside the reviewable process graph.
- [ ] Converge routine plan/recipe bookkeeping behind one reviewed task scope and
  one explicit consequential decision, followed by deliberate Run.
- [ ] Show current validated output and responsible failure first; keep durable
  attempts, internal artifacts, Snakemake, Critic and release in Advanced.
- [ ] Compare a fresh PostGIS task to the Checkpoint 19 flow for user actions,
  elapsed time, comprehension, failure recovery and exact evidence.

### Checkpoints 24–27

- [x] Add governed Pandas tabular-data processing (Checkpoint 24).
- [x] Add governed installed-library capability discovery and one tested installed adapter (Checkpoint 25).
- [ ] Complete scheduling/cancellation/durable recovery (Checkpoint 26).
- [ ] Benchmark against manual and general-agent work and prepare the laptop
  alpha release after product acceptance (Checkpoint 27).

See `context/AGENT_INTERFACE_SEQUENCE.md` for the acceptance boundaries.

Checkpoint 20 recipe decision linkage: read-only saved recipe inventory independently verifies exact recipe approvals; execution and evidence graph linkage remains open.
Checkpoint 20 execution linkage: run-start recipe and approval identity verification is implemented for new interface attempts; authoritative result and evidence joins remain open.
Checkpoint 20 result linkage: exact persisted recipe result and evidence relationship now checked for new interface attempts; output artifact, Critic, and release joins remain open.
Checkpoint 20 Critic candidate relationship: exact run-to-trace preview linkage is implemented; recorded Critic result and release joins remain open.

Checkpoint 20 graph source navigation: local saved plans, recipes, and durable attempts appear as separate read-only graph sources beside exported traces. Richer verified relationships and simplified end-user journey remain future work.
Checkpoint 20 Critic record linkage: the read-only Assurance inventory now verifies exact stored Critic records against current trace/report evidence; release linkage remains open.
Checkpoint 20 release linkage: read-only Assurance now connects an exact verified Critic record plus current trace/report references to a verified immutable release package; full artifact lineage remains open.
Checkpoint 20 recorded artifact graph: verified recipe evidence now exposes bounded output references and recorded producer steps, while fresh physical output verification remains open.

Checkpoint 21D implemented: reopen independently checked saved task histories without restoring workflow scope or authority. Remaining Checkpoint 21 work includes verified artifact relationships and recovery boundaries before reviewed intent in Checkpoint 22.

Checkpoint 21E: explicit task artifact references can be independently checked against bounded current evidence bytes through a read-only API. This verifies file identity only, not semantic relationships or authority. Five history tests passed locally; full WSL suite pending. See `docs/CHECKPOINT21E.md`.

Checkpoint 21F adds read-only recorded plan/approval relationship inspection with authoritative schemas and existing approval verification. Six focused task tests passed; no execution authority is granted. Automatic reference attachment and recipe/outcome checks remain open. See `docs/CHECKPOINT21F.md`.

Checkpoint 21G links actual plan saves and approval/denial records to the active task with file-byte references. Completed artifact operations survive visible history failures. Seven focused task tests and frontend build passed locally; full WSL suite pending. See `docs/CHECKPOINT21G.md`. Recipe/outcome links remain open.

Checkpoint 21H corrects selected-skill Planner prompts, removes unconditional unrelated PostGIS instructions, includes conversion arguments, and allows one fully revalidated policy correction. 54 focused tests passed; full WSL suite and live-model check pending. See `docs/CHECKPOINT21H.md`.

Checkpoint 21I records an exact task reference after storing a reviewed Planner-derived recipe and surfaces history failures without undoing storage. 23 focused tests and frontend build passed locally; full API suite pending. Recipe semantic relationships and outcomes remain open. See `docs/CHECKPOINT21I.md`.

Checkpoint 21J checks full recipe definitions against their recorded source plans using the same backend mapping as compilation. 24 focused tests passed; full API suite pending. Outcome links remain open. Task-history discoverability is explicitly deferred to task-centered UI redesign. See `docs/CHECKPOINT21J.md`.

Checkpoint 21K links task-derived completed run result/evidence references and checks exact recorded outcome relationships without revalidating live outputs or granting authority. 25 focused tests and frontend build passed locally; full WSL suite pending. Interrupted attempts and recovery acceptance remain open. See `docs/CHECKPOINT21K.md`.

Checkpoint 21L records completed-run recipe approval references, verifies their current recipe policy/scope/expiry relationships, and separates historical identity from current permission. 26 focused tests and frontend build passed locally; full WSL API suite and recovery acceptance remain. See `docs/CHECKPOINT21L.md`.

Checkpoint 21M adds attempt/recovery task notes and a closeout acceptance checklist. 27 focused tests passed locally; full WSL API suite and deliberate end-to-end recovery acceptance remain pending. Advanced relationship graph direction is documented. Checkpoint 21 implementation is delivered for acceptance, not yet declared complete. See `docs/CHECKPOINT21M.md`.

Checkpoint 22A implemented for validation: explicitly scoped keyword retrieval from checked task histories. Next are exact context review/storage and bounded Intent Agent reasoning/clarification. No automatic memory or frontend conversation redesign is claimed. See `docs/CHECKPOINT22.md`.

Checkpoint 22B implemented for validation: explicit context review/storage and stale-source rejection on reopening. Next is bounded Intent reasoning/clarification. Context review is not approval of work. See `docs/CHECKPOINT22B.md`.


## Checkpoint 22C — Intent reasoning

CLI `reason-task-intent` now consumes a rechecked context review and proposes intent or clarification without creating a plan or granting authority. Context is checked again after inference. See `docs/CHECKPOINT22C.md` for validation. API/UI integration and reviewed Intent-to-Planner handoff remain next.


## Checkpoint 22D — Intent clarification API

Explicit clarification answers are available through `reason-task-intent --clarification` and `POST /api/v1/intent/reason`. Each stateless call checks reviewed history, proposes intent or questions and grants no work authority. Current-task prompt improved after live model feedback. See `docs/CHECKPOINT22D.md`; UI and reviewed Planner handoff follow.


## Checkpoint 22E — resolved Intent review

Intent may make one fresh re-evaluation when supplied answers leave a clarification response. Unresolved output stays blocked. CLI proposal inspection and explicit digest review now store resolved reasoning under ignored `reviewed-intents/`; reopening rechecks sources and record bytes. This grants no work authority. See `docs/CHECKPOINT22E.md`. Actual Planner handoff and review API/UI follow.


## Checkpoint 22F — reviewed Planner handoff

CLI `plan-reviewed-intent` now produces an unsaved plan from a rechecked intent review, initially bounded to one exact `inspect_vector` input and metadata output scope. It rejects broader capabilities and never executes or infers approval. See `docs/CHECKPOINT22F.md`. Review/handoff API, conversation UI and broader supported envelopes follow.


## Checkpoint 22G — Intent review/handoff API

The local API now supports checked proposal inspection, exact resolved-intent review, rechecked reopening and bounded Planner handoff through the same CLI services. No work approval or execution is granted. See `docs/CHECKPOINT22G.md`; conversation UI beside the graph follows.


## Checkpoint 22H — Context & intent interface

The new **Context & intent** panel uses explicitly selected history, checked review storage, structured reasoning and the bounded Planner handoff. It sits beside the graph on wide screens and above it on narrow screens. No plan is saved or executed. See `docs/CHECKPOINT22H.md` for the full frontend test flow. Saved-review recovery and integration with the existing governed run flow follow.


## Checkpoint 22I implementation

Bridge reviewed-intent inspection plans to immutable saved plans and existing approval review. Next: recover saved context/intent reviews, then simplify the conversational path. Broad execution envelopes remain future work.


## Checkpoint 22J — saved-review recovery

Checked saved-review recovery implemented. Next simplify the task-centered conversation journey and graph provenance. Durable chat and broader Intent capabilities remain future work.


## Checkpoint 22K — focused task stages

One-current-stage Context & intent journey implemented. Prioritize fresh-task reasoning without mandatory historical context next, then wider explicit capability envelopes. Unified conversation/run interface and durable chat remain future work.


## Checkpoint 22L — fresh tasks

Fresh-task Intent reasoning no longer requires historical context. Explicit null source identity, no invented citations, reviewed-intent recovery and graph omission are implemented. Next broaden explicit supported capability envelopes; durable chat and unified run journey remain future work.


## Checkpoint 22M — inspection envelopes

Bounded vector/raster metadata handoff implemented with shared scope checks and explicit selection. Checkpoint 22 integration acceptance now covers history-backed/history-free reasoning, review, recovery and plan storage. Next unify the task/conversation and governed execution journey; write-capable Intent scopes and general library functions remain future work.


## Checkpoint 22N and Checkpoint 23 scope

22N integration acceptance implemented; 22O closeout remains. Checkpoint 23 is limited to three bundled groups: conversation/graph, exact governed continuation, acceptance/demo. Target a reproducible demonstration by October 4 evening, America/New_York. LinkedIn publication follows successful acceptance, not the calendar alone. Pandas, arbitrary packages and 3D remain deferred.

## Checkpoint 25 operator follow-up and next delivery slices

25: persisted, verified scan inventories are browsable by expandable scan/library/function groups after reopening Settings. Review/selected-operation/outcome cards show input → operation → result arrows and actual declared dependencies. Examples are indexed by function in [examples/README.md](../examples/README.md), retaining checkpoint paths.

26: scheduling/cancellation/recovery first; then correlated agent history and summaries. [Existing behavior and options](../docs/AGENT_HISTORY_DIRECTION.md) are documented; no new agent-history implementation is included in 25.

27: bounded output visualization (tables/charts/vector maps, with raster support clearly scoped), then public-data demo and laptop/PC installation/evaluation/release materials. [Acceptance and demo direction](../docs/OUTPUT_VISUALIZATION_DIRECTION.md). No publication is authorized.

Checkpoint 26.1 delivery/acceptance: [private conversation memory](../docs/CHECKPOINT26_CONVERSATIONS.md). It uses existing durable state without claiming completion of cancellation, retry/resume or the whole checkpoint.

Operator revision: [current conversation model](../docs/CHECKPOINT26_CONVERSATIONS.md) supersedes separate task controls and cross-chat continuation. Each chat retains its own context across topic changes. Cross-conversation memory is deferred for discussion, not implementation; 26.2–26.4 should first work within one conversation.

### 28.2 implementation slice

[Delivery and remaining evaluation](../docs/CHECKPOINT28_2.md): optional own-chat verified-check ranking and conversation settings gear implemented. Offline selector cases compare a fixed baseline; representative end-to-end model improvement is still unverified. Keep optional OFF and finish that acceptance gate before declaring the broader learning requirement complete. Then 28.3 and 29 retain their order.

28.2 follow-up: [execution interaction and paired evaluation](../docs/CHECKPOINT28_2_EVALUATION.md) implement direct read-only Execute, separate write gates and six paired temporary cases. Ranking stays optional OFF until its predeclared model-benefit threshold is demonstrated. 28.3/29 and the demo gates are not silently advanced.

Measured 28.2 status: the initial local-model comparison did not demonstrate benefit (OFF 3/6, ON 2/6). Intermediate request/source and oracle defects are preserved in the evaluation notes. Coverage/source/fresh-output fixes improve deterministic handling but do not justify a general learning claim or default enablement.

Final focused post-fix local-model checks passed selection/filtering/combined tasks with both modes (3/3 each, one call per task). This is a regression result, not the six-case/two-repetition learning-benefit gate; rankings remain experimental OFF. See the paired evaluation notes for preserved negative/intermediate results.

28.2 scope reliability follow-up: narrowly recognized single-file metadata requests use an inspector-only decoder and backend extra-step rejection. Broader semantic coverage remains an acceptance limit.

### Proposed 28.2 follow-up — inspection on send

[Design and measurable acceptance](../docs/INSPECTION_ON_SEND_DESIGN.md): implement bounded inspector eligibility first, durable submission binding second, composer/graph/CLI integration third, and regression plus actual-model acceptance last. Start with one local CSV inspector; broader workflows and writes keep explicit execution gates. Design only; no new agent or default automatic execution is delivered. Existing 28.2/28.3/29 gates retain their order.

### Deferred harness and specialization research — 2026-10-21

[Recorded direction](../docs/DEFERRED_AGENT_HARNESS_RESEARCH.md): specialize in verified data-science/engineering workflows and measure time/reliability against a fair same-small-model harness baseline. Codex remains a separately configured product reference. DeepSeek Harness source review and any reuse/migration are deferred; no comparative advantage is established and no research implementation is authorized by this note. Existing checkpoint order remains unchanged.

### 28.2 bounded inspection submission delivered — 2026-10-21

[Delivery](../docs/CHECKPOINT28_2_INSPECTION_SUBMIT.md): explicit default-OFF Linux CSV inspection on send, ordinary stricter table limits, source/contract/revision binding, durable receipt/run identity and frontend/CLI parity. This supersedes the earlier design-only status of that slice, not broader 28.2 acceptance. [Learning without RL](../docs/LEARNING_WITHOUT_RL.md) prioritizes measured case reuse, failure feedback and context-aware retrieval before adaptive policies or training. Those alternatives remain proposed; external-harness research stays deferred.

### Operator clarification — inspection is format-independent (2026-10-21)

[Requested expansion and acceptance](../docs/INSPECTION_ON_SEND_EXPANSION.md): inspection-on-send should cover supported non-writing inspection tasks, including vector/raster and eventually bounded multi-inspection graphs, using one preference. CSV-only eligibility is the current pilot restriction. Documented only; no runtime expansion is delivered. Finish within 28.2 alongside honest non-RL learning acceptance; next numbered checkpoint stays 28.3 visualization, then 29 private domain knowledge. No live-service permission or external-harness research is implied.

### 28.3 first result-exploration slice — 2026-10-21

[Delivery and acceptance](../docs/CHECKPOINT28_3_RESULTS.md): shared typed result queries, complete bounded CSV filters/sort/paging and source profiles, filtered chart totals, stable table/chart identities, map displayed extent/type summary and Planner result_view proposals. Preserve old previews/workflows and exact write controls. No added agent or dependency. This is not full 28.3 completion or closure of the outstanding 28.2 format-independent inspection/learning gates; richer spatial/raster exploration, grounded explanations and measured scale remain.

## Domain knowledge acquisition direction — recorded 2026-10-21

[Design and acceptance](../docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md): automatically capture scoped dataset definitions, domain methods, preferences and recipes with evidence and corrections. Checkpoint 29 first validates private single-chat reuse; project knowledge across chats remains a checkpoint-30-or-later decision, then sanitized portable packages. No sharing or training implementation is authorized by this documentation update. Existing inspection/visualization and pre-demo gates remain.

## 28.2 single-dataset inspection expansion — implementation

[Scope and acceptance](../docs/INSPECTION_ON_SEND_EXPANSION.md): local vector/raster inspectors now share bounded automatic submission with CSV, including source-package hashes, closed adapter contracts, private spatial snapshots and normal recorded results. Multi-inspection graphs and service reads remain unfinished. This does not complete 28.2 learning or 28.3 visualization/private knowledge gates.

## 28.3 vector-first spatial views

[Delivery and acceptance](../docs/CHECKPOINT28_3_SPATIAL_VIEWS.md): explicit hash-bound vector layers/display reprojection and linked sampled attributes precede bounded raster image rendering and exact pixel inspection. Existing snapshots, shared CLI/API and write boundaries remain. Resource/recovery acceptance and documented limitations precede knowledge checkpoint 29; this does not close learning/private-memory gates or enable cross-chat sharing.

28.3 follow-up: typed Planner spatial settings and backend-formatted recorded-fact explanations are implemented; same-chat inspection binds the latest source before storage. These do not constitute domain learning, new statistics or checkpoint-29 memory. See the spatial-view acceptance guide.

## Characteristics-first spatial discovery — 2026-10-22

The [ordered consolidation plan](../docs/CHECKPOINT28_DISCOVERY_RESTRUCTURE.md) now includes metadata-only TIFF/GPKG/SHP readers, progressive package hashing and a shared `discover-dataset` CLI. Configured large-source discovery guards do not expand geometry/pixel display or processing. GeoJSON streaming and legacy spatial CLI/MCP migration remain separate work. The [resume record](WORK_RESUME.md) tracks accepted checks and next steps: narrow zero-model routing, bounded multi-inspection, evaluated experience retrieval, then checkpoint-28 closeout. Private knowledge stays 29 and cross-chat sharing 30+; no RL or demo-readiness claim.

### Remaining-order amendment — documentation only, 2026-10-22

First reproduce/fix the reported raster-opacity endpoint issue and expand readable
inspection metadata toward gdalinfo coverage, keeping expensive statistics explicit.
Then deliver narrow zero-model inspections, bounded multi-inspection, spatial
CLI/MCP parity, evaluated optional method/failure retrieval and complete checkpoint-28
acceptance. [Detailed criteria and roles](../docs/CHECKPOINT28_DISCOVERY_RESTRUCTURE.md#revised-remaining-work--operator-agreement-2026-10-22).
Checkpoint 29 adds private sourced definitions/methods, retrieval and corrections;
cross-chat sharing stays 30+. Synthetic tests precede broader realistic-data/demo
work, which should follow evaluated learning/private-knowledge acceptance. No new
mandatory agent/container or model-weight RL is implied. This amendment records
planned work only; it does not implement features or authorize Git/publication.

### Raster detail follow-up — 2026-10-22

The first remaining slice now adds bounded technical TIFF metadata and expandable
Outcome details, with independent temporary-fixture GDAL CLI comparisons. Opacity
endpoints/current percentage are explicit; the reported fault remains unreproduced
in endpoint drag/keyboard checks. This does not close checkpoint 28 or deliver full
statistics scans, zero-model routing, multi-inspection, parity migration or learning.
Final checks and resume state are recorded in the discovery guide and WORK_RESUME.

## Checkpoint 28 closeout — 2026-10-22

[Engineering acceptance](../docs/CHECKPOINT28_CLOSEOUT.md) completes the agreed
implementation/validation sequence: characteristics-first readers, technical
raster metadata, exact zero-model submissions, bounded multi-inspection, shared
CLI/MCP discovery, cancellation/recovery, results and evaluated optional reuse.
Final backend/frontend/browser gates passed. Preserve the failed paired model
trial and separate corrected vector retest; no recommendation benefit is claimed
and ranking stays OFF by default. This closes checkpoint 28 engineering, not the
broader learning/private-knowledge/demo gate or known scale/model limitations.
Next numbered work is checkpoint 29 private sourced knowledge and corrections;
cross-chat/project sharing stays 30+ and separately decided. No implementation of
29, model-weight training, Git or publication is implied by this closeout.
