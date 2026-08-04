# Current Status

### Checkpoint 3C: deterministic PostGIS validation

The `validate-postgis-layer` CLI command performs read-only,
deterministic checks against an allowlisted PostGIS schema.

Checks include:

- table existence;
- registered geometry column;
- row count;
- SRID;
- declared and actual geometry type;
- invalid geometry count;
- null geometry count;
- spatial extent.

Database identifiers are validated and quoted. SQL statements are fixed;
users and agents cannot submit arbitrary SQL. The database connection is
read-only, and connection errors are returned with credentials redacted.

Example:

```bash
docker compose --profile tools run --rm mcp-gis \
  geoagent validate-postgis-layer \
  --schema agent_sandbox \
  --table checkpoint3b_sample_points \
  --expected-row-count 2 \
  --expected-srid 4326 \
  --expected-geometry-type POINT \
  --pretty

## Checkpoint 2 — read-only MCP interface

Status: implemented; final acceptance depends on user-provided test and
container-build output.

Completed:

- fail-closed ENABLE_WRITE_TOOLS and ALLOW_OVERWRITE settings;
- schema and PostgreSQL identifier validation;
- health_check MCP tool;
- inspect_vector_dataset MCP tool;
- plan-only plan_load_vector_to_postgis MCP tool;
- fixed three-tool allowlist;
- STDIO MCP protocol smoke test;
- security and tool tests;
- read-only MCP container;
- no database credentials, database network, or writable project mounts;
- no Ollama integration or model calls.

Not implemented:

- PostGIS loading;
- PostGIS deterministic validation;
- approvals and overwrite workflow;
- trace persistence;
- Markdown reports;
- agent-to-MCP integration;
- Ollama integration.

Next checkpoint candidate:

Checkpoint 3 should add a controlled PostGIS connection and deterministic
read-only database validation before any database loading is enabled.