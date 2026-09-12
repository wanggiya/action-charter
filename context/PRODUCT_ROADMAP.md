# ActionCharter Product Roadmap

Updated: 2026-09-07

## Product direction

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

Checkpoint 17 owns the complete guided operating interface described in
`docs/INTERFACE_PRODUCT_SCOPE.md`, including PostGIS, GIS adapters, recipes,
Snakemake, skills and the currently implemented GeoServer inspection and
publication boundaries. Checkpoint 18 follows with pilot operations and
bounded memory; it is not a substitute for completing the interface.

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
