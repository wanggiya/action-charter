# Current Status

## Checkpoint 1 — Repository and vector inspection

Status: completed.

Implemented:

- repository and container scaffold;
- independent planner, executor, and critic manifests;
- `inspect_vector` skill;
- trusted input-root path enforcement;
- structured vector metadata;
- CLI command, sample data, and tests.

## Checkpoint 2 — Read-only MCP interface

Status: completed.

Implemented:

- fail-closed write and overwrite settings;
- fixed MCP tool allowlist;
- MCP health check;
- vector inspection tool;
- plan-only PostGIS-load tool;
- STDIO MCP smoke test;
- read-only MCP container;
- no arbitrary shell or unrestricted SQL.

## Checkpoint 3 — Controlled PostGIS workflow

Status: completed.

Implemented:

- connection to externally managed PostGIS;
- password supplied through a mounted secret file;
- allowlisted target schemas;
- controlled vector loading;
- deterministic PostGIS validation;
- table, geometry column, row count, SRID, geometry type,
  invalid geometry, null geometry, and extent checks;
- Markdown report generation;
- structured, secret-redacted trace generation;
- artifact overwrite protection;
- final success derived only from deterministic validation.

## Checkpoint 4 — Shared model and Planner Agent

Status: completed.

Completed:

- shared Ollama connectivity;
- OpenAI-compatible shared model client;
- Pydantic request and response validation;
- model client unit tests;
- real Ollama smoke test using `qwen3:4b-instruct`.
- deterministic task-specific context-pack construction;
- fixed trusted context sources with SHA-256 references;
- context and request secret redaction;
- structured Planner Agent schemas;
- deterministic planner policy enforcement;
- JSON-only Ollama planning requests;
- rejection of unimplemented skills, arbitrary shell, unrestricted SQL,
  destructive operations, and false execution claims;
- real Planner Agent smoke test using `qwen3:4b-instruct`.
- independent non-root, read-only Planner container;
- model-network-only access;
- no MCP, PostGIS, database credential, artifact-write, or Docker-socket access.

## Checkpoint 5 — Executor and approval boundary

Status: completed.

### Checkpoint 5A — Exact-plan approvals

Implemented:

- canonical JSON plan representation;
- SHA-256 plan identity;
- append-only approval records;
- exact approved-step scope;
- approved and denied decisions;
- approver, reason, expiration, and human corrections;
- approval redaction and overwrite blocking;
- changed, expired, denied, and incomplete approval rejection.

### Checkpoint 5B — Deterministic execution handoff

Implemented:

- original request preserved in Planner results;
- typed execution envelopes;
- exact four-skill sequence enforcement;
- consistent paths and database targets;
- approved input roots and PostGIS schemas;
- safe identifiers and task IDs;
- fixed tool and argument allowlists;
- `execution_performed=false` before MCP execution.

### Checkpoint 5C — Internal MCP transport

Implemented:

- MCP 1.29 Streamable HTTP transport;
- stateless JSON responses;
- fixed internal `/mcp` endpoint;
- DNS-rebinding host and origin restrictions;
- unexposed container port;
- internal Docker control network;
- narrow read-only MCP client;
- container-to-container health smoke test;
- STDIO compatibility retained for local tests.

### Checkpoint 5D — Independent Executor runtime

Implemented:

- non-root, read-only Executor container;
- control-network-only connectivity;
- no Ollama, PostGIS, backend, credential, GIS-data, artifact,
  or Docker-socket access;
- read-only plan, approval, and manifest mounts;
- dedicated client for one approval-gated composite MCP tool;
- raw PostGIS loading removed from the MCP network boundary;
- independent server-side plan, approval, digest, envelope, and
  schema verification;
- fail-closed behavior when write tools are disabled.

### Checkpoint 5E — Approved validated execution

Implemented:

- one real approved vector-to-PostGIS workflow;
- controlled new-table loading;
- deterministic PostGIS validation;
- final success derived only from validation;
- approval digest, approval ID, and approved steps stored in traces;
- approval evidence included in Markdown reports;
- reports and traces protected from overwrite;
- write tools returned to disabled state after execution;
- automated, container, and manual acceptance checks.

## Checkpoint 6 — Critic/Report Agent

Status: completed.

### Checkpoint 6A — Deterministic evidence pack

Implemented:

- trusted trace and report roots;
- path-containment and file-size enforcement;
- WorkflowTrace schema validation;
- secret redaction for structured and textual evidence;
- deterministic approval and validation consistency checks;
- SHA-256 evidence references;
- concise evidence supplied instead of raw project history;
- incomplete and contradictory evidence handling.

### Checkpoint 6B — Structured Critic Agent

Implemented:

- schema-constrained JSON-only Ollama response;
- shared local Qwen model runtime;
- strict Critic manifest validation;
- deterministic status preservation;
- success-claim consistency enforcement;
- model-output redaction;
- no tools, SQL, shell, execution, or writes;
- unit tests using a fake model client;
- real local Ollama verification.

### Checkpoint 6C — Independent Critic container

Implemented:

- independent non-root Critic service;
- read-only container filesystem;
- read-only trace, report, context, and manifest mounts;
- model-network-only connectivity;
- no MCP control network;
- no PostGIS backend network;
- no database credentials or Docker socket;
- all Linux capabilities dropped;
- `no-new-privileges` enabled;
- containerized Ollama assessment;
- artifact hash verification before and after critique.

### Checkpoint 6D — Acceptance and documentation

Implemented:

- repeatable Checkpoint 6 acceptance target;
- complete automated test suite;
- Compose validation;
- live containerized Critic policy check;
- evidence integrity verification;
- architecture, status, README, and decision updates.

## Checkpoint 7 — CI and structured failure handling

Status: completed.

### Checkpoint 7A — GitHub-hosted CI

Implemented:

- secret-free offline test workflow on Ubuntu 24.04 and Python 3.12;
- separate agent and GIS-tools container-build jobs;
- modern GitHub Actions runtimes;
- pip dependency validation;
- ANSI-portable Typer CLI help tests;
- non-root container-user checks;
- container CLI smoke tests;
- no Ollama, PostGIS, database credentials, or write-enabled integration
  execution in GitHub-hosted CI.

### Checkpoint 7B — Structured failure handling

Implemented:

- stable failure categories and machine-readable failure codes;
- failure stages covering configuration, planning, approval, execution,
  validation, reporting, critique, model, MCP, and artifacts;
- stable CLI exit codes;
- secret-redacted structured failure records;
- retry classification as `never`, `safe_read_only`, or `manual_review`;
- read-only model and MCP retry safety classification;
- manual-review policy for interrupted or uncertain database writes;
- timeout, unavailable dependency, invalid response, execution failure,
  validation failure, cancellation, and internal-error classification;
- operator cancellation mapped to exit code 130;
- structured failure evidence stored in workflow traces;
- deterministic failure evidence included in Markdown reports;
- successful traces explicitly record `failure: null`;
- shared redaction utilities used by traces and failure records;
- automated tests for model, MCP, CLI, cancellation, trace, and report
  failure behavior.

Safety rules:

- database writes are never automatically retried;
- an interrupted write requires manual database inspection;
- model and MCP error text is redacted before logging or persistence;
- deterministic validation remains the only success gate.

### Checkpoint 7C — Durable workflow state and safe resumption

Implemented:

- schema-validated durable workflow-state records;
- lifecycle states for planned, approved, executing, validating,
  successful, failed, and cancelled workflows;
- append-only, contiguous transition history;
- monotonic revisions and timestamps;
- deterministic transition allowlist;
- actor restrictions for human approval, execution, validation, and
  cancellation;
- exact plan-digest and approval identity preservation;
- structured failure evidence in failed and cancelled states;
- atomic initial-state creation without overwrite;
- atomic revision updates with stale-revision rejection;
- trusted state-root path containment;
- state-file size and UTF-8 validation;
- secret redaction before persistence;
- non-root-container-readable state permissions;
- read-only state inspection CLI;
- read-only resume-assessment CLI;
- deterministic classification as `resume_allowed`,
  `manual_review_required`, or `terminal`;
- manual review whenever a PostGIS write may have started;
- read-only workflow-state mount in the Executor container;
- no workflow-state access for Planner or Critic containers;
- no automatic execution, retry, or state modification during assessment.

Known limitations:

- resume assessment recommends an action but does not execute it;
- automatic retry is not implemented;
- PostGIS writes are never automatically retried;
- concurrent writers are not protected by an operating-system file lock;
- durable state is not yet automatically created and updated by the
  production Planner, approval, Executor, and verifier flow.

### Checkpoint 7D — Schema versioning and compatibility

Status: completed.

Implemented:

- central registry for versioned artifact types;
- explicit current, writable, and supported-read versions;
- version policies for context packs, workflow plans, approvals,
  execution envelopes, failures, traces, Critic artifacts, workflow
  states, and resume assessments;
- explicit `schema_version` in workflow traces;
- pre-validation version checks at persisted artifact boundaries;
- nested workflow-plan version validation;
- version-aware approval, trace, and workflow-state loading;
- version checks for incoming execution envelopes;
- version checks for Critic model responses;
- current-version, supported-read, migration-required,
  unsupported-older, unsupported-future, and invalid-version
  dispositions;
- fail-closed handling of missing and unknown versions;
- rejection of future versions before Pydantic validation;
- read-only schema-policy inspection;
- read-only compatibility assessment;
- read-only migration assessment;
- stable CLI exit behavior for compatible, incompatible, and invalid
  requests;
- automated tests confirming that compatibility assessment never
  modifies artifacts.

Current policy:

- all registered artifact schemas currently use version `1.0`;
- only version `1.0` is currently readable and writable;
- no automatic or manual migration implementation is registered;
- older unsupported artifacts fail closed;
- future artifacts fail closed;
- migration assessment provides guidance but never rewrites an
  artifact.

Known limitations:

- no schema migrations are implemented;
- no artifact is rewritten or upgraded automatically;
- compatibility is checked only at the boundaries currently registered;
- schema evolution beyond `1.0` has not yet been exercised with a real
  backward-compatible version.


## Checkpoint 8 — Controlled vector conversion

Status: in progress.

### Checkpoint 8A — Conversion schema and policy

Implemented:

- typed vector-conversion plans;
- GeoJSON and GeoPackage output allowlist;
- approved input-root enforcement;
- approved output-root enforcement;
- safe output filenames and layer identifiers;
- one explicit source layer per conversion;
- CRS-required policy;
- overwrite rejection;
- structured plan-only CLI command;
- schema-registry coverage;
- no file creation during planning;
- automated policy and CLI tests.

Not yet implemented:

- conversion execution;
- deterministic output verification;
- approval-gated MCP integration;
- conversion traces and reports.

### Checkpoint 8B — Controlled conversion execution

Implemented:

- write-disabled-by-default conversion service;
- GeoJSON and GeoPackage creation;
- one selected source layer;
- no reprojection or geometry mutation;
- temporary output creation;
- atomic final-file publication;
- existing-target and overwrite rejection;
- incomplete-output cleanup;
- non-root-readable output permissions;
- structured `converted_pending_validation` result;
- explicit withholding of final success;
- CLI execution command;
- automated service and CLI tests.

Not yet implemented:

- deterministic conversion verification;
- approval-gated MCP conversion workflow;
- conversion traces, reports, and production state transitions.


### Checkpoint 8C — Deterministic conversion validation

Status: completed.

Implemented:

- independent source and converted-output inspection;
- trusted input-root and output-root enforcement;
- output existence and non-empty checks;
- driver and layer verification;
- CRS preservation checks;
- feature-count preservation checks;
- attribute-field preservation checks;
- geometry-type preservation checks;
- null and invalid geometry comparisons;
- extent comparison with bounded tolerance;
- structured validation results;
- final success withheld unless every deterministic check passes.


### Checkpoint 8R — Reusable skill and recipe framework

Status: in progress.

#### Checkpoint 8R.1 — Typed skill registry

Status: completed.

Implemented:

- strict skill-registry schemas;
- implemented and planned skill states;
- safe entrypoint syntax validation;
- unique skill identifiers;
- fixed trusted registry path;
- bounded YAML loading;
- fail-closed registry validation.

#### Checkpoint 8R.2 — Shared registry loading

Status: completed.

Implemented:

- one authoritative skill-registry parser;
- Planner context integration;
- approval-policy integration;
- removal of duplicated skill YAML parsing;
- verifier metadata preserved in Planner context.

#### Checkpoint 8R.3 — Capability metadata

Status: completed.

Implemented:

- inspection, transformation, database-load,
  validation, and reporting skill categories;
- read-only, artifact-write, database-write,
  and evidence-write access classes;
- approval requirements derived from trusted metadata;
- deterministic validation requirements;
- write skills required to declare trusted verifiers;
- no dynamic execution of registry entrypoint strings.

#### Checkpoint 8R.4 — Reusable recipe policy

Status: completed.

Implemented:

- typed reusable workflow recipes;
- registered-skill references;
- deterministic DAG validation;
- dependency-cycle rejection;
- topological step ordering;
- logical output declarations;
- canonical recipe JSON and SHA-256 identity;
- calculated write, approval, and validation scope;
- recipes prohibited from claiming execution.

#### Checkpoint 8R.5 — Immutable recipes and approvals

Status: completed.

Implemented:

- trusted recipe storage root;
- bounded recipe draft and artifact loading;
- secret redaction before persistence;
- immutable digest-named recipe files;
- overwrite protection;
- tamper and filename-identity detection;
- append-only recipe approvals;
- exact recipe SHA-256 binding;
- explicit approval-required step scope;
- approved, denied, incomplete, changed, and expired
  approval handling;
- operator CLI commands for saving, approving, and
  verifying recipes;
- no recipe execution introduced at this checkpoint.

#### Checkpoint 8R.6 — Approval-gated recipe execution

Status: completed.

Implemented:

- typed recipe execution envelopes;
- exact recipe digest and approval binding;
- hard-coded skill dispatch without dynamic entrypoint imports;
- deterministic topological recipe execution;
- per-step execution and validation results;
- generic server-side `run_approved_recipe` MCP tool;
- independent Executor MCP client support;
- independent Executor CLI command;
- read-only recipe, approval, context, and manifest mounts;
- no GIS libraries or direct GIS data access in the Executor image;
- lazy GIS imports preserving the Executor dependency boundary;
- server-side recipe, approval, registry, schema, and envelope checks;
- non-root GIS artifact writes restricted to the approved output mount;
- corrected MCP transport and tool-error classification;
- mixed read-only and validated step-result consistency policy;
- real Executor-to-MCP vector conversion;
- deterministic successful result assertions;
- write tools restored to disabled state after acceptance.

```markdown
#### Checkpoint 8R.7 — Durable recipe evidence

Status: complete

Implemented:

- Typed recipe run evidence and artifact references.
- Input/output SHA-256 hashing and lineage edges.
- Immutable digest-addressed recipe run-result storage.
- Immutable digest-addressed evidence storage.
- Deterministic Markdown reporting without model-authored status.
- Non-root writable mounts for output, run records, evidence, and reports.
- Typed `PersistedRecipeExecutionResult` MCP response.
- Independent Executor verification of recipe identity, approval,
  validation semantics, and run-result digest.
- Fail-closed manual-review policy for incomplete post-execution
  persistence.
- Offline schema, storage, reporting, persistence, server, Executor,
  and import-boundary tests.

Acceptance run:

- Recipe: `checkpoint8r7_acceptance`
- Execution: approval-gated through the independent Executor
- Final status: `validated_success`
- Output artifact: `data/output/checkpoint8r7_acceptance.gpkg`
- Run-result JSON: persisted and digest validated
- Evidence JSON: persisted and digest validated
- Markdown report: persisted and deterministically validated
- Output artifact SHA-256: matched recorded evidence
- Write tools restored to disabled after execution

## Checkpoint 9 — Natural-language recipe proposals

Status: complete

The Planner can now use the shared local OpenAI-compatible Ollama
runtime to interpret a natural-language GIS request as a strictly
typed, non-executable `RecipeProposal`.

Implemented boundaries:

- The model can select only one fixed trusted template:
  - `inspect_vector`
  - `inspect_and_convert_vector`
  - `vector_to_postgis`
- Model output is parsed as JSON and validated with Pydantic.
- Unknown templates, arbitrary skills, shell commands, SQL, extra
  fields, unsupported schema versions, changed requests, and false
  execution claims fail closed.
- Incomplete proposals produce deterministic clarification questions.
- Ready proposals compile through fixed Python templates into a typed
  `WorkflowRecipe`.
- The trusted skill registry and recipe policy derive write,
  approval, validation, and dependency requirements.
- Compilation does not save, approve, invoke MCP, or execute.
- Recipe saving remains a separate explicit operator action.
- Existing append-only approval and approval-gated MCP execution
  remain unchanged.

Real acceptance result:

1. Qwen interpreted a natural-language vector-conversion request.
2. It produced an `inspect_and_convert_vector` proposal.
3. The proposal passed schema validation.
4. Deterministic assessment declared it ready.
5. The compiler created the fixed two-step recipe.
6. Recipe policy identified `step_2` as approval-required,
   write-performing, and validation-required.
7. The operator explicitly saved the immutable recipe.
8. No approval or GIS execution occurred during proposal generation
   or compilation.
9. The complete offline test suite passed.

Trust boundary:

`Natural language -> untrusted model proposal -> schema validation
-> deterministic assessment -> trusted compiler -> recipe policy
-> explicit operator save -> human approval -> MCP execution`

## MVP status

The initial vector-to-PostGIS vertical slice is implemented:

```text
task-specific context
→ structured plan
→ deterministic plan policy
→ exact-plan human approval
→ typed execution envelope
→ approval-gated MCP execution
→ vector inspection and PostGIS load
→ deterministic PostGIS validation
→ Markdown report and structured trace
→ deterministic critic evidence
→ read-only structured critique
