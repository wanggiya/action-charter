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

Status: in progress.

### Checkpoint 5A — Exact-plan approval records

Status: completed.

Implemented:

- canonical JSON representation of validated workflow plans;
- SHA-256 plan identity;
- append-only JSON approval records;
- exact approved-step scope;
- approved and denied decisions;
- approver, reason, expiration, and human-correction fields;
- recursive redaction of approval text;
- trusted plan and approval roots;
- approval-record overwrite blocking;
- deterministic approval verification;
- automatic invalidation when a plan changes;
- CLI commands for plan digest, approval creation, and verification.

Security boundary:

- approvals contain a plan digest rather than complete tool arguments;
- approval does not execute any tool;
- approval does not enable PostGIS writes by itself;
- changed and expired plans fail verification;
- runtime plan and approval files are ignored by Git.

Next:

- Checkpoint 5B will transform an approved plan into a deterministic,
  typed execution request without executing it.

  ### Checkpoint 5B — Deterministic execution envelope

Status: completed.

Implemented:

- original redacted request preserved in Planner results;
- typed execution-envelope schema;
- one fixed composite workflow tool;
- exact four-skill vertical-slice enforcement;
- consistent inspection and loading paths;
- consistent loading and validation targets;
- input paths restricted beneath `data/input`;
- allowlisted target schemas;
- validated database identifiers and task IDs;
- unsupported tool arguments rejected;
- exact-plan approval verification before handoff;
- arbitrary tool names unrepresentable;
- explicit `execution_performed=false`;
- CLI command for building an execution envelope.

The envelope does not call MCP, connect to PostGIS, or execute the workflow.

Next:

- Checkpoint 5C will expose the existing composite workflow through
  authenticated-by-network, internal MCP transport while keeping execution
  disabled by default.