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

Status: in progress.

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

Current work:

- independent read-only planner container.

Not yet implemented:

- structured Planner Agent;
- independent operational planner container;
- Executor Agent loop;
- approval workflow;
- Critic/Report Agent model integration.

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

## Next checkpoint

Checkpoint 6 should implement the read-only Critic/Report Agent.

Planned scope:

- read completed traces and reports;
- independently assess unresolved risks;
- identify failed or incomplete checks;
- generate a structured critique;
- prevent file and database edits;
- prevent success claims that conflict with deterministic validation.