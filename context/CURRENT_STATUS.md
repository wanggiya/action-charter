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
