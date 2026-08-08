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