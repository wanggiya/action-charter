# GeoAgent Skill Harness

GeoAgent Skill Harness is a CLI-first, local-first, containerized platform for planning controlled geospatial workflows, executing allowlisted GIS tools, deterministically validating results, and saving reproducible reports and traces.

The prototype runs under Ubuntu WSL with Docker Desktop. It uses one shared Ollama/Qwen model runtime on the laptop rather than placing a large model in every agent container.

## Current implementation

Checkpoints 1–4 are complete.

Implemented:

- deterministic vector inspection;
- controlled vector loading into PostGIS;
- deterministic PostGIS validation;
- Markdown workflow reports;
- structured, secret-redacted traces;
- read-only MCP inspection and planning tools;
- controlled MCP loading and validation tools;
- shared Ollama OpenAI-compatible client;
- deterministic task-specific context packs;
- structured, policy-validated Planner Agent;
- independent hardened planner container.

Not yet implemented:

- Executor Agent runtime loop;
- persistent human approval records;
- Critic/Report Agent model integration;
- vector conversion;
- raster processing;
- generalized retries and task queues.

## Architecture

```text
                           Shared Ollama/Qwen
                                   ↑
                                   │ model network
                                   │
                         ┌───────────────────┐
                         │ Planner container │
                         │ plan only         │
                         │ no GIS tools      │
                         │ no PostGIS access │
                         └───────────────────┘
                                   │
                          structured plan
                                   ↓
                     Future approval/orchestrator
                                   │
                                   ↓
                         ┌───────────────────┐
                         │ Executor container│
                         │ approved MCP only │
                         └───────────────────┘
                                   │
                           internal control
                                   ↓
                         ┌───────────────────┐
                         │ GIS/MCP container │
                         │ GDAL/GeoPandas    │
                         │ fixed SQL/tools   │
                         └───────────────────┘
                                   │
                          geoagent-backend
                                   ↓
                         External PostGIS
```

Planner, executor, and critic are independent logical agents. They share one model runtime but have separate manifests, instructions, mounts, networks, and permissions.

The deterministic verifier is ordinary Python and SQL code, not an LLM agent. A workflow cannot report success until deterministic validation passes.

## Repository structure

```text
approvals/                      ignored append-only approval records
plans/                          ignored structured Planner results
agents/                         agent manifests and permissions
context/                        concise trusted project context
data/input/                     read-only source datasets
data/output/                    approved generated data
docker/agent/                   lightweight agent image
docker/gis-tools/               isolated GIS and MCP image
reports/                        generated Markdown reports
scripts/                        protocol and model smoke tests
skills/                         human-readable skill contracts
src/geoagent_harness/           installable Python package
  context_pack/                 deterministic context selection
  mcp_server/                   allowlisted MCP interface
  model/                        shared Ollama-compatible client
  orchestrator/                 deterministic workflow orchestration
  planner/                      structured Planner Agent
  skills/                       executable GIS skill implementations
  verifier/                     deterministic correctness checks
tests/                          automated tests
traces/                         structured execution traces
```

The `src/` layout separates importable package code from repository tooling. After installation, imports use `geoagent_harness`, not `src.geoagent_harness`.

## Requirements

Development environment:

- Ubuntu WSL;
- Python 3.11 or newer;
- Docker Desktop with WSL integration;
- an existing PostGIS container;
- Ollama running on the laptop;
- an installed local model such as `qwen3:4b-instruct`.

Recommended Ubuntu packages:

```bash
sudo apt update
sudo apt install -y git make curl jq python3 python3-venv python3-pip
```

Keep the repository in the WSL Linux filesystem, for example:

```text
~/projects/geoagent-skill-harness
```

## Installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
```

Equivalent Make target:

```bash
make install
```

## Environment configuration

Create the local configuration:

```bash
cp .env.example .env
```

Example shared-model settings:

```dotenv
MODEL_PROVIDER=ollama
MODEL_BASE_URL=http://host.docker.internal:11434/v1
MODEL_NAME=qwen3:4b-instruct
MODEL_TIMEOUT_SECONDS=120
MODEL_MAX_TOKENS=1024
```

`host.docker.internal` is used by containers. A command running directly in WSL can temporarily override it with:

```bash
MODEL_BASE_URL=http://127.0.0.1:11434/v1
```

Database write controls remain fail-closed:

```dotenv
ENABLE_WRITE_TOOLS=false
ALLOW_OVERWRITE=false
ALLOWED_SCHEMAS=agent_sandbox
```

The PostGIS password must remain in:

```text
.secrets/postgis_password
```

It must not be placed in prompts, source files, reports, traces, Git, or `.env.example`.

## External PostGIS

This repository does not create, stop, delete, or own PostGIS.

The existing PostGIS container must be attached to the external Docker network:

```text
geoagent-backend
```

The network name is configured with:

```dotenv
GEOAGENT_BACKEND_NETWORK=geoagent-backend
```

PostGIS data persistence belongs to the separately managed PostGIS/GeoServer Compose project.

## Tests and commands

Run the complete automated suite:

```bash
make test
```

Inspect the sample vector:

```bash
make inspect
```

Validate Compose configuration:

```bash
make config
```

Build container images:

```bash
make build
```

Validate the three agent manifests:

```bash
make agent-info
```

Run the MCP protocol smoke test:

```bash
make mcp-smoke
```

Run the independent Planner Agent container:

```bash
make planner-smoke
```

The planner smoke test creates a plan only. It does not load PostGIS, invoke MCP execution tools, write reports, or modify datasets.

## Planner Agent security boundary

The planner container:

- runs as the non-root `geoagent` user;
- has a read-only root filesystem;
- drops all Linux capabilities;
- enables `no-new-privileges`;
- joins only the model network;
- receives no PostGIS variables or password;
- receives no GIS data, report, trace, output, or Docker socket mounts;
- mounts its manifest and project context read-only;
- has no executable tools in its manifest.

Model output is untrusted. A plan is accepted only after:

1. JSON parsing;
2. Pydantic schema validation;
3. implemented-skill allowlist validation;
4. required-argument validation;
5. shell, SQL, secret, and destructive-operation rejection;
6. approval-policy validation;
7. workflow-order validation;
8. deterministic-validation requirement checks;
9. rejection of execution or validation claims.

## Implemented vector-to-PostGIS workflow

The controlled deterministic workflow can:

1. inspect an approved GeoJSON, GeoPackage, or Shapefile;
2. load a selected vector layer into a new table in an approved schema;
3. validate the resulting PostGIS layer;
4. generate a Markdown report;
5. save a structured, redacted trace.

PostGIS validation checks:

- table existence;
- geometry column existence;
- row count;
- SRID;
- declared and actual geometry type;
- invalid geometry count;
- null geometry count;
- extent;
- optional expected values.

Writes are disabled by default. Existing tables and artifacts cannot be overwritten without an approval design that is not yet implemented. Deletion is blocked in the MVP.

## Security rules

- No unrestricted shell tool.
- No unrestricted SQL tool.
- Source inputs are read-only.
- Output writes are limited to designated roots.
- Database credentials are file-mounted and redacted.
- Model output never determines success.
- Destructive file, table, schema, and database deletion is unavailable.
- Existing artifacts are not silently overwritten.
- Network access is limited by container role.
- PostGIS validation is deterministic and read-only.

See `SECURITY.md` for additional trust-boundary information.


## Deterministic execution handoff

An approved plan is converted into a typed execution envelope before any MCP
tool can be called.

The current envelope supports only:

```text
inspect_vector
→ load_vector_to_postgis
→ validate_postgis_layer
→ generate_report

## Human approval boundary

Validated plans can be saved beneath `plans/`. Approval records are stored
beneath `approvals/`. Runtime JSON files in both directories are ignored by
Git.

An approval contains:

- the SHA-256 digest of the exact canonical plan;
- approved step IDs;
- approved or denied decision;
- approver and reason;
- optional expiration;
- redacted human corrections.

An approval does not execute a plan or enable write tools. If any plan field,
argument, target table, step, or policy value changes, the digest changes and
the previous approval becomes invalid.

Approval commands:

```bash
geoagent plan-digest plans/example-plan.json --pretty

geoagent approve-plan \
  plans/example-plan.json \
  --step step_2 \
  --step step_4 \
  --approver local-user \
  --reason "Approved controlled writes." \
  --valid-for-minutes 60 \
  --pretty

geoagent verify-plan-approval \
  plans/example-plan.json \
  approvals/approval-example.json \
  --pretty

## Executor Agent and approved execution

The Executor runs independently from the Planner and GIS containers.

It receives read-only access to:

- one saved Planner result;
- one append-only approval record;
- its own agent manifest.

It has access only to Docker’s internal control network. It receives no
Ollama configuration, PostGIS network, database credentials, GIS data,
artifact mounts, or Docker socket.

Before execution, both Executor and MCP independently verify:

- the exact plan digest;
- approval decision and expiration;
- approved step scope;
- fixed skill order;
- tool and argument allowlists;
- input path and schema policy;
- consistent loading and validation targets;
- the complete execution envelope.

Raw `load_vector_to_postgis` is not exposed through MCP. The only write-capable
network tool is:

```text
run_approved_vector_postgis_workflow
It remains unavailable while ENABLE_WRITE_TOOLS=false.

A completed load is not success. Success requires deterministic PostGIS
validation and the final status validated_success.

## Known limitations

- The Planner Agent can create plans but cannot execute them.
- The Executor and Critic runtime loops are not implemented.
- Human approvals are not yet stored as structured records.
- Planner skill selection is based on deterministic keyword relevance.
- The local model may vary its wording even at temperature zero.
- Docker Compose network isolation is not a complete host firewall.
- Shapefiles require their related sidecar files.
- The external PostGIS lifecycle remains outside this repository.
- The prototype currently targets one local user and one active workflow.