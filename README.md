# GeoAgent Skill Harness

GeoAgent Skill Harness is a CLI-first, local-first, containerized platform for planning controlled geospatial workflows, executing allowlisted GIS operations, deterministically validating results, and recording reproducible reports and traces.

The prototype runs under Ubuntu WSL with Docker Desktop. It uses one shared local Ollama/Qwen runtime instead of placing a large model inside every agent container.

## Current status

Checkpoints 1–10 are complete. The project includes the original
vector-to-PostGIS vertical slice, controlled vector conversion,
reusable approval-gated recipes, durable execution evidence,
natural-language recipe proposals, and guided operator review.

The implemented workflow is:

```text
task request
→ concise task-specific context
→ structured Planner plan
→ deterministic plan policy
→ exact-plan human approval
→ typed execution envelope
→ approval-gated Executor
→ internal MCP workflow
→ vector inspection
→ controlled PostGIS loading
→ deterministic PostGIS validation
→ Markdown report and structured trace
→ deterministic critic evidence
→ read-only Critic assessment
```

The system does not allow an LLM to determine whether execution succeeded. Final success is derived only from deterministic validation.

## Implemented capabilities

- GeoJSON, GeoPackage, and Shapefile inspection;
- trusted input-root path enforcement;
- structured vector metadata;
- controlled vector loading into PostGIS;
- allowlisted database schemas and validated identifiers;
- deterministic PostGIS validation;
- Markdown workflow reports;
- structured, secret-redacted traces;
- exact-plan human approval records;
- SHA-256 plan identity;
- typed execution envelopes;
- internal MCP Streamable HTTP transport;
- approval-gated composite MCP execution;
- shared Ollama OpenAI-compatible model client;
- deterministic task-specific context packs;
- structured, policy-validated Planner Agent;
- independent Planner container;
- independent Executor container;
- deterministic Critic evidence packs;
- schema-constrained Critic Agent;
- independent read-only Critic container;
- secret-free GitHub-hosted Python tests;
- independent GitHub container builds.

Not yet implemented:

- raster workflows;
- generic recipe dispatch for every registered skill;
- automatic retry and automatic workflow resumption;
- task queues and scheduling;
- real artifact-schema migrations;
- skill scaffolding and generated contract tests;
- Snakemake export and replay;
- GeoServer publication;
- production authentication;
- multi-user deployment;
- strict network egress proxying;
- remote production orchestration.

## Architecture

```text
                              Shared Ollama/Qwen
                              ↑                 ↑
                              │ model network   │ model network
                              │                 │
                    ┌─────────┴─────────┐ ┌─────┴────────────┐
                    │  Planner Agent    │ │  Critic Agent    │
                    │                   │ │                   │
                    │  context → plan   │ │ evidence → review│
                    │  no tools         │ │ no tools         │
                    │  no writes        │ │ no writes        │
                    │  no PostGIS       │ │ no PostGIS       │
                    └─────────┬─────────┘ └──────────────────┘
                              │
                        structured plan
                              │
                    deterministic policy
                              │
                      exact-plan approval
                              │
                    ┌─────────▼─────────┐
                    │  Executor Agent   │
                    │                   │
                    │ approved composite│
                    │ MCP workflow only │
                    │ no direct PostGIS │
                    │ no Ollama         │
                    └─────────┬─────────┘
                              │
                     internal control network
                              │
                    ┌─────────▼─────────┐
                    │  GIS/MCP service  │
                    │                   │
                    │ GDAL / GeoPandas  │
                    │ allowlisted tools │
                    │ deterministic     │
                    │ verifier          │
                    └─────────┬─────────┘
                              │
                    external backend network
                              │
                    ┌─────────▼─────────┐
                    │ External PostGIS  │
                    │                   │
                    │ separately managed│
                    │ persistent storage│
                    └───────────────────┘
```

## Core design

### Model

One shared Ollama/Qwen endpoint serves the model-enabled agents.

The Planner and Critic use the same runtime but receive different:

- manifests;
- instructions;
- context;
- schemas;
- permissions;
- container mounts.

The Executor and GIS/MCP service do not require direct model access.

### Agent

An agent is a constrained role consisting of:

- manifest;
- purpose;
- instructions;
- trusted context;
- allowed capabilities;
- model access where required;
- deterministic response policy.

An agent is not equivalent to a model. Multiple agents can share one model endpoint.

### Loop

The controlled loop is:

```text
plan
→ approve
→ execute
→ validate
→ report
→ critique
```

### Harness

The harness owns:

- structured schemas;
- task context;
- permissions;
- plan policy;
- approval identity;
- MCP boundaries;
- redaction;
- timeouts;
- errors;
- reports;
- traces;
- deterministic final status.

### Container

Containers isolate role-specific dependencies and permissions.

Planner, Executor, Critic, and GIS/MCP run as separate services.

### Skill

A skill is a reusable, typed, tested GIS workflow with:

- controlled arguments;
- path policy;
- permission classification;
- structured output;
- deterministic verification;
- automated tests.

### Verifier

The verifier is deterministic Python and fixed SQL. It is not an LLM agent.

### Trace

A trace is structured evidence about a workflow. It is not a substitute for validation.

## Agent boundaries

### Planner Agent

The Planner:

- receives a concise task-specific context pack;
- selects only implemented skills;
- returns structured JSON;
- describes assumptions and risks;
- performs no execution.

The Planner has:

- no MCP tools;
- no shell;
- no unrestricted SQL;
- no filesystem writes;
- no database writes;
- no PostGIS credentials;
- no GIS-data mounts;
- no report or trace mounts.

Planner output is accepted only after:

1. JSON parsing;
2. Pydantic schema validation;
3. implemented-skill allowlist validation;
4. required-argument validation;
5. path-policy validation;
6. schema and identifier validation;
7. shell, SQL, secret, and destructive-operation rejection;
8. workflow-order validation;
9. approval-policy validation;
10. deterministic-validation requirement checks;
11. rejection of execution or validation claims.

### Executor Agent

The Executor:

- loads a saved Planner result;
- loads a human approval record;
- verifies the exact plan digest;
- verifies the approved step scope;
- builds a typed execution envelope;
- calls one composite approval-gated MCP tool.

The Executor has:

- no Ollama access;
- no arbitrary shell;
- no unrestricted SQL;
- no direct PostGIS connection;
- no PostGIS password;
- no GIS-data mount;
- no report or trace write mount;
- no raw PostGIS loader tool.

The Executor cannot modify the approved plan or add new tool arguments.

### Critic Agent

The Critic:

- reads a deterministic evidence pack;
- identifies unresolved risks;
- explains failed or incomplete checks;
- returns schema-constrained JSON;
- performs no execution.

The Critic has:

- no MCP access;
- no PostGIS access;
- no shell;
- no unrestricted SQL;
- no filesystem writes;
- no database writes;
- read-only trace and report mounts;
- model-network access only.

The Critic cannot change `deterministic_status`.

For `validated_success`, it must return:

```json
{
  "conclusion": "supported",
  "success_claimed": true,
  "edits_performed": false,
  "database_actions_performed": false
}
```

For failed or incomplete evidence, it cannot claim success.

## Network boundaries

| Component | Model network | Control network | PostGIS backend |
|---|---:|---:|---:|
| Planner | Yes | No | No |
| Executor | No | Yes | No |
| Critic | Yes | No | No |
| GIS/MCP | No | Yes | Yes |
| External PostGIS | No | No | Yes |

The MCP HTTP endpoint is available only on the internal Docker control network and is not published to the host.

## Filesystem boundaries

| Component | Filesystem access |
|---|---|
| Planner | Manifest and context read-only |
| Executor | Manifest, plan, and approval read-only |
| Critic | Manifest, context, traces, and reports read-only |
| GIS/MCP | Inputs read-only; approved report and trace roots writable |
| PostGIS | Separately managed persistent storage |

Project-owned containers:

- run as the non-root `geoagent` user;
- use read-only root filesystems where applicable;
- drop all Linux capabilities;
- enable `no-new-privileges`;
- do not mount the Docker socket.

### Runtime write permissions

The independent Executor is a control-plane service. It has read-only
access to trusted context, manifests, canonical recipes, approvals,
plans, and workflow state. It has no GIS input mount, output mount,
database credentials, or direct artifact-writing permission.

The MCP GIS container performs approved GIS operations as the non-root
user and group `10001:10001`. Its filesystem is read-only except for
explicit bind-mounted artifact destinations.

For local bind mounts, prepare the approved vector output directory
without granting world-write access:

```bash
sudo chown "$(id -u):10001" data/output
sudo chmod 2775 data/output

The host user remains the directory owner. Group 10001 allows the
non-root GIS container to create outputs, and the setgid bit makes new
entries inherit the approved group.

| Host path          | Container path                | Access     |
| ------------------ | ----------------------------- | ---------- |
| `context`          | `/workspace/context`          | read-only  |
| `data/input`       | `/workspace/data/input`       | read-only  |
| `data/output`      | `/workspace/data/output`      | read-write |
| `plans`            | `/workspace/plans`            | read-only  |
| `approvals`        | `/workspace/approvals`        | read-only  |
| `workflow-recipes` | `/workspace/workflow-recipes` | read-only  |
| `traces`           | `/workspace/traces`           | read-write |
| `reports`          | `/workspace/reports`          | read-write |


Filesystem permission does not itself authorize execution.
ENABLE_WRITE_TOOLS remains disabled by default, and a write requires
an exact canonical recipe, matching unexpired approval, validated
execution envelope, fixed MCP tool, hard-coded dispatcher, and
deterministic verifier.


Be careful with the nested code fence when pasting. If VS Code closes the section incorrectly, use `~~~bash` for the inner command:

```markdown
~~~bash
sudo chown "$(id -u):10001" data/output
sudo chmod 2775 data/output
~~~

## Repository structure

```text
geoagent-skill-harness/
├── .github/
│   └── workflows/
│       ├── test.yaml
│       └── container-build.yaml
│
├── agents/
│   ├── planner/
│   │   └── manifest.yaml
│   ├── executor/
│   │   └── manifest.yaml
│   └── critic/
│       └── manifest.yaml
│
├── approvals/
│   └── local runtime approval records
│
├── context/
│   ├── PROJECT_SUMMARY.md
│   ├── ARCHITECTURE.md
│   ├── CURRENT_STATUS.md
│   ├── DATASET_CATALOG.json
│   ├── SKILLS_INDEX.yaml
│   └── DECISIONS.jsonl
│
├── data/
│   ├── input/
│   └── output/
│
├── docker/
│   ├── agent/
│   │   └── Dockerfile
│   └── gis-tools/
│       └── Dockerfile
│
├── plans/
│   └── local structured Planner results
│
├── reports/
│   └── generated Markdown reports
│
├── scripts/
│   ├── mcp_smoke.py
│   ├── ollama_smoke.py
│   └── related protocol checks
│
├── skills/
│   └── human-readable skill contracts
│
├── src/
│   └── geoagent_harness/
│       ├── approvals/
│       ├── context_pack/
│       ├── critic/
│       ├── executor/
│       ├── mcp_client/
│       ├── mcp_server/
│       ├── model/
│       ├── orchestrator/
│       ├── planner/
│       ├── skills/
│       ├── verifier/
│       ├── agent_manifest.py
│       ├── cli.py
│       ├── reporting.py
│       ├── schemas.py
│       └── trace.py
│
├── tests/
├── traces/
├── .dockerignore
├── .env.example
├── .gitignore
├── compose.yaml
├── Makefile
├── pyproject.toml
└── README.md
```

The `src/` layout separates importable package code from repository configuration and tooling.

After installation, imports use:

```python
from geoagent_harness...
```

not:

```python
from src.geoagent_harness...
```

## Requirements

Development environment:

- Ubuntu WSL;
- Python 3.11 or newer;
- Python 3.12 recommended for parity with CI;
- Docker Desktop with WSL integration;
- an externally managed PostGIS container;
- Ollama running on the laptop;
- a local Qwen model such as `qwen3:4b-instruct`.

Recommended Ubuntu packages:

```bash
sudo apt update

sudo apt install -y \
  git \
  make \
  curl \
  jq \
  ripgrep \
  python3 \
  python3-pip \
  python3-venv \
  gh
```

Keep the repository in the WSL Linux filesystem:

```text
~/projects/geoagent-skill-harness
```

Using the Linux filesystem generally performs better and avoids Windows-mounted filesystem permission differences.

## Local installation

Create the virtual environment:

```bash
python3 -m venv .venv
```

Upgrade pip:

```bash
.venv/bin/python -m pip install --upgrade pip
```

Install development dependencies:

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

Equivalent Make command:

```bash
make install
```

Verify dependency consistency:

```bash
.venv/bin/python -m pip check
```

Run tests:

```bash
.venv/bin/pytest
```

## Environment configuration

Create local configuration:

```bash
cp .env.example .env
```

Recommended model configuration for Docker containers:

```dotenv
MODEL_PROVIDER=ollama
MODEL_BASE_URL=http://host.docker.internal:11434/v1
MODEL_NAME=qwen3:4b-instruct
MODEL_TIMEOUT_SECONDS=120
MODEL_MAX_TOKENS=1024
```

Keep `/v1` because the shared client uses Ollama’s OpenAI-compatible endpoint.

### WSL versus Docker model URL

A process running directly in WSL normally uses:

```text
http://127.0.0.1:11434/v1
```

A Docker container uses:

```text
http://host.docker.internal:11434/v1
```

Use a one-command override for WSL:

```bash
MODEL_BASE_URL=http://127.0.0.1:11434/v1 \
  .venv/bin/geoagent plan-task \
  --request "Inspect the approved sample dataset." \
  --pretty
```

Do not permanently export the WSL URL before running Docker Compose. Shell variables override `.env`, and `127.0.0.1` inside a container refers to the container itself.

Remove a temporary exported override with:

```bash
unset MODEL_BASE_URL
```

### Write policy

Writes remain disabled by default:

```dotenv
ENABLE_WRITE_TOOLS=false
ALLOW_OVERWRITE=false
ALLOWED_SCHEMAS=agent_sandbox
```

Write enablement does not replace human approval. Controlled execution requires both:

```text
valid exact-plan approval
AND
ENABLE_WRITE_TOOLS=true
```

Return write tools to disabled after a controlled execution.

### PostGIS secret

The PostGIS password belongs in:

```text
.secrets/postgis_password
```

It must not be placed in:

- `.env.example`;
- source code;
- model prompts;
- plans;
- approval records;
- reports;
- traces;
- Git;
- GitHub Actions secrets for offline CI.

## External PostGIS

This repository does not create, stop, delete, or own PostGIS.

The external container must join:

```text
geoagent-backend
```

Configure the network name with:

```dotenv
GEOAGENT_BACKEND_NETWORK=geoagent-backend
```

The PostGIS service and storage belong to the separately managed PostGIS/GeoServer Compose project.

Verify the external network:

```bash
docker network inspect geoagent-backend
```

Verify the PostGIS container:

```bash
docker ps --filter name=postgis
```

Database persistence, backup, restore, roles, databases, and PostGIS extension initialization remain responsibilities of the external PostGIS deployment.

## Implemented skills

### `inspect_vector`

Supported inputs:

- GeoJSON;
- GeoPackage;
- Shapefile.

Returned metadata:

- driver;
- layer names;
- CRS;
- geometry type;
- feature count;
- fields;
- extent.

The skill rejects paths outside the trusted input root and does not execute arbitrary shell commands.

### `load_vector_to_postgis`

The loader:

- accepts an approved source path;
- accepts a selected source layer;
- validates schema and table identifiers;
- restricts targets to allowlisted schemas;
- creates a new table;
- uses controlled library and database operations;
- rejects disabled writes;
- exposes no arbitrary SQL.

Existing tables are not silently overwritten.

### `validate_postgis_layer`

The deterministic verifier checks:

- table existence;
- geometry-column existence;
- row count;
- SRID;
- declared and actual geometry type;
- invalid geometry count;
- null geometry count;
- extent;
- optional expected values.

Validation uses fixed SQL and validated identifiers.

### `generate_report`

Reports are generated deterministically from structured workflow evidence.

### `convert_vector`

Status: implemented.

The conversion skill:

- accepts approved GeoJSON, GeoPackage, and Shapefile inputs;
- creates GeoJSON or GeoPackage outputs;
- enforces trusted input and output roots;
- blocks overwrite;
- validates source and target layers;
- preserves CRS, fields, feature count, geometry type and extent;
- records null and invalid geometry counts;
- withholds success until deterministic validation passes.

## Human approval boundary

Validated plans can be saved beneath:

```text
plans/
```

Approval records are stored beneath:

```text
approvals/
```

Runtime files in these directories are ignored by Git.

An approval records:

- the SHA-256 digest of the exact canonical plan;
- explicitly approved step IDs;
- approved or denied decision;
- approver;
- reason;
- optional expiration;
- redacted human corrections.

Any plan change changes the digest and invalidates the previous approval.

An approval does not:

- execute a plan;
- enable write tools;
- permit overwrite;
- permit deletion;
- authorize additional arguments.

Example commands:

```bash
geoagent plan-digest \
  plans/example-plan.json \
  --pretty
```

```bash
geoagent approve-plan \
  plans/example-plan.json \
  --step step_2 \
  --step step_4 \
  --approver local-user \
  --reason "Approved controlled writes." \
  --valid-for-minutes 60 \
  --pretty
```

```bash
geoagent verify-plan-approval \
  plans/example-plan.json \
  approvals/example-approval.json \
  --pretty
```

## Execution boundary

An approved plan is translated into a typed execution envelope before MCP execution.

The current envelope accepts only this sequence:

```text
inspect_vector
→ load_vector_to_postgis
→ validate_postgis_layer
→ generate_report
```

The envelope rejects:

- changed paths;
- changed source layers;
- changed schemas;
- changed target tables;
- unapproved arguments;
- unsafe identifiers;
- changed task IDs;
- missing required steps;
- changed step order;
- incomplete approval;
- expired approval;
- denied approval;
- preexisting execution claims.

The Executor calls only:

```text
run_approved_vector_postgis_workflow
```

The GIS/MCP service independently reloads and verifies the plan, approval, digest, schema, step scope, and execution envelope before database execution.

## MCP boundary

The MCP server supports:

- STDIO for local protocol tests;
- Streamable HTTP for internal container communication.

The network-visible allowlist is:

```text
health_check
inspect_vector_dataset
plan_load_vector_to_postgis
validate_postgis_layer
run_approved_vector_postgis_workflow
```

The raw PostGIS loader is not exposed through the Executor-facing MCP boundary.

The Streamable HTTP endpoint:

- uses the internal Docker control network;
- publishes no host port;
- validates expected Host and Origin values;
- returns stateless JSON responses;
- retains STDIO compatibility for local tests.

## Deterministic final status

Possible workflow outcomes include:

```text
validated_success
validation_failed
execution_failed
```

A workflow can return `validated_success` only when deterministic validation passes.

The Planner, Executor, Critic, reports, and model responses cannot override that decision.

## Reports and traces

A completed workflow records:

- task ID;
- original request;
- context references;
- selected skills;
- plan SHA-256;
- approval ID;
- approved step IDs;
- redacted tool arguments;
- tool results;
- deterministic validation results;
- artifacts;
- warnings;
- final status;
- human corrections;
- timestamps;
- software and container versions.

Reports and traces:

- use trusted output roots;
- redact secrets;
- reject unsafe task IDs;
- cannot be silently overwritten;
- are generated only from structured data.

## Critic evidence

Before calling the Critic model, the harness builds a deterministic evidence pack.

It:

- accepts only JSON traces beneath the trusted trace root;
- accepts only Markdown reports beneath the trusted report root;
- rejects path traversal;
- rejects oversized files;
- validates the trace schema;
- checks status and validation consistency;
- checks approval completeness;
- redacts structured and textual secrets;
- records source SHA-256 hashes;
- identifies missing or inconsistent evidence.

The model receives this concise evidence pack rather than unrestricted project files or complete project history.

## Common commands

Install dependencies:

```bash
make install
```

Run the complete local test suite:

```bash
make test
```

Inspect sample data:

```bash
make inspect
```

Validate Compose:

```bash
make config
```

Build all project images:

```bash
make build
```

Validate agent manifests:

```bash
make agent-info
```

Run the local MCP protocol smoke test:

```bash
make mcp-smoke
```

Run the Planner container:

```bash
make planner-smoke
```

Run the Critic container using the default accepted evidence:

```bash
make critic-container
```

Run the Critic for another existing task:

```bash
make critic-container \
  CRITIC_TASK_ID=actual-task-id
```

Run complete Checkpoint 6 acceptance:

```bash
make checkpoint6-accept \
  CRITIC_TASK_ID=checkpoint5e-points-20260809a
```

## Continuous integration

GitHub Actions separates offline verification from laptop-dependent integration.

### Offline Python tests

`.github/workflows/test.yaml` runs on:

```text
Ubuntu 24.04
Python 3.12
```

It:

- installs `.[dev]`;
- runs `pip check`;
- prints diagnostic dependency versions;
- runs all offline pytest tests;
- supplies no secrets;
- does not call Ollama;
- does not connect to PostGIS;
- creates no external Docker networks.

Typer/Rich help tests call `click.unstyle()` before asserting option names so terminal color formatting does not make tests environment-dependent.


### Container contract tests

`.github/workflows/container-build.yaml` independently builds and validates:

```text
docker/agent/Dockerfile
docker/gis-tools/Dockerfile
docker/skill-test-runner/Dockerfile
```

The workflow:

- uses BuildKit caching;
- does not push images;
- loads each image for runtime validation;
- verifies that every image runs as the non-root `geoagent` user;
- supplies no PostGIS secret;
- makes no Ollama request;
- makes no PostGIS connection;
- validates the complete Docker Compose configuration.

Runtime contracts use:

```text
no network
read-only root filesystem
all Linux capabilities dropped
no-new-privileges
temporary /tmp filesystem
read-only public fixture mounts
```

The agent-image contract loads the Planner, Executor and Critic manifests inside the built image. This verifies that the installed CLI, package, manifests and role definitions work without contacting a model or MCP service.

The GIS-image contract performs real read-only operations against committed fixtures:

```text
data/input/sample_points.geojson
data/input/sample_dem.tif
```

It runs vector and raster inspection inside the built GIS image and verifies that raster path traversal is rejected through a controlled policy error.

The skill-test-runner contract verifies that the isolated runner fails closed when no valid candidate bundle is mounted. Detailed candidate generation, hashing, testing and promotion behavior remains covered by the offline pytest suite.

These contracts validate container packaging and safe read-only runtime behavior. They do not claim that a complete model, MCP or PostGIS workflow ran successfully.

### Local integration

These commands intentionally remain outside GitHub-hosted CI:

```bash
make planner-smoke
make critic-container
make checkpoint6-accept
```

They may require:

- Ollama;
- the selected Qwen model;
- Docker Desktop;
- external PostGIS;
- `geoagent-backend`;
- local secret files;
- existing plans, approvals, traces, and reports.

A future secured self-hosted runner may run integration tests. Normal GitHub-hosted CI remains secret-free and independent of the developer laptop.

## GitHub CLI

Authenticate interactively from WSL:

```bash
gh auth login \
  --hostname github.com \
  --git-protocol https \
  --web
```

Check authentication:

```bash
gh auth status
```

List recent workflow runs:

```bash
gh run list --limit 10
```

Watch the newest test workflow:

```bash
GEOAGENT_RUN_ID="$(
  gh run list \
    --workflow test.yaml \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId'
)"

gh run watch "$GEOAGENT_RUN_ID" \
  --compact \
  --exit-status
```

View a failed workflow:

```bash
gh run view RUN_ID --log-failed
```

Never place GitHub tokens in commands, documentation, `.env`, or chat messages.

## Security rules

- No unrestricted shell tool.
- No unrestricted SQL tool.
- Model output is untrusted.
- Planner and Critic have no executable tools.
- Executor calls only the approved composite MCP workflow.
- Inputs are read-only.
- Writes are restricted to designated roots.
- PostGIS schemas and identifiers are validated.
- Credentials are mounted from secret files.
- Credentials are redacted from prompts, logs, reports, and traces.
- Existing tables and artifacts are not silently overwritten.
- File, table, schema, and database deletion is blocked.
- Human approval is bound to an exact plan digest.
- MCP HTTP is internal and has no host port.
- Containers run as non-root.
- Containers drop all Linux capabilities.
- Containers do not mount the Docker socket.
- Deterministic validation exclusively determines success.

## Automated tests

The test suite covers:

- agent manifests;
- context selection and redaction;
- model settings and client behavior;
- Planner schema and policy;
- approval identity and expiration;
- execution-envelope translation;
- Executor policy and runtime;
- MCP tool allowlists;
- MCP transport security;
- vector inspection;
- controlled loading;
- PostGIS validation;
- report generation;
- trace generation and redaction;
- Critic evidence;
- Critic model policy;
- container security;
- CLI registration;
- path and identifier rejection.

Run:

```bash
.venv/bin/pytest
```

Current verified local and GitHub baseline:

```text
234 passed
```

The exact count may increase as new tests are added. Zero failures is the acceptance requirement.

## Development process

Work through one checkpoint at a time.

Every checkpoint should include:

1. immediate goal;
2. files created or modified;
3. complete code;
4. exact commands;
5. expected output;
6. automated tests;
7. manual verification;
8. README and `CURRENT_STATUS.md` updates;
9. known limitations;
10. Git review and commit;
11. no claim that commands passed until their output is provided.

## Known limitations

- Generic recipe dispatch does not yet support every registered GIS capability.
- Adding a new recipe template currently requires synchronized edits across several trusted Python modules.
- Adding a novel skill algorithm still requires a reviewed trusted adapter and verifier implementation.
- Model-generated implementation code cannot promote or trust itself.
- The PostGIS recipe template requires broader generic dispatcher integration.
- Automatic retry, cancellation and workflow resumption are intentionally unavailable.
- Critic output is returned in memory rather than persisted as a separate authoritative artifact.
- Plans, recipes and approvals use local filesystem storage.
- Existing tables and artifacts cannot be overwritten.
- Deletion is unavailable.
- PostGIS and Ollama are externally managed.
- No task queue, production authentication or multi-user deployment exists.
- Network egress is not controlled through a dedicated proxy.
- Real Ollama, PostGIS and write-enabled integration tests depend on the local development environment.

## Roadmap

Completed checkpoint details are maintained in
`context/CURRENT_STATUS.md`.

## Roadmap status

### Checkpoint 11 — Skill scaffolding and contracts

Completed:

- deterministic standard skill-package planning;
- isolated, non-overwriting scaffold generation;
- typed schema, policy, service and verifier placeholders;
- planned registry metadata without executable entrypoints;
- static contract validation without importing generated code;
- explicit separation between generated scaffolds and trusted implementations.

### Checkpoint 12 — Snakemake export and replay

Completed:

- immutable digest-addressed Snakemake exports;
- exact recipe and approval verification;
- shell-free trusted replay adapters;
- isolated non-root workflow-runner container;
- replay through the existing Executor-to-MCP boundary;
- durable evidence and completion-marker verification;
- trusted recipe-and-approval inventory discovery.

### Checkpoint 13 — Declarative Skill SDK and raster inspection

Completed:

- versioned declarative skill definitions;
- fixed permission profiles and trusted adapter catalog;
- immutable skill-contract bundles;
- isolated generic scaffolds and candidate materialization;
- network-disabled candidate tests;
- digest-bound test evidence;
- deterministic promotion assessment and planning;
- transactional promotion with registry modification last;
- promoted read-only `inspect_raster` skill;
- deterministic GeoTIFF test fixture;
- safe Rasterio metadata inspection;
- CLI, dispatcher and constrained recipe-proposal integration.

### Checkpoint 13L — Container contract CI

Completed:

- independent agent, GIS-tools and skill-test-runner builds;
- non-root runtime-user verification;
- Planner, Executor and Critic manifest loading inside the agent image;
- vector and raster inspection inside the GIS image;
- controlled raster path-escape rejection;
- fail-closed skill-test-runner behavior;
- no-network, read-only and non-privileged runtime contracts;
- complete Compose configuration validation.

### Checkpoint 14 — Controlled raster transformation

Completed:

- implemented a trusted Rasterio conversion and reprojection adapter;
- allowlisted nearest, bilinear and cubic resampling;
- required explicit source and target CRS metadata;
- preserved band count, data types and nodata metadata;
- restricted sources and targets to approved roots;
- rejected symlinks, unsafe target names and existing outputs;
- wrote through a temporary GeoTIFF and finalized without overwrite;
- withheld success until independent deterministic validation;
- added a trusted verifier identity to write-capable adapter definitions;
- preserved the verifier through deterministic promotion planning;
- defined `convert_raster` through declarative YAML;
- generated its immutable contract, isolated scaffold and candidate;
- tested the candidate in the network-disabled skill-test container;
- promoted the exact digest-verified candidate transactionally;
- added direct plan, conversion and validation CLI commands;
- added constrained raster recipe proposal and compilation support;
- required exact step-scoped approval for raster writes;
- added hard-coded dispatcher and verifier allowlists;
- executed and validated a real two-step raster recipe;
- recorded SHA-256 input/output evidence and raster lineage;
- persisted immutable run results, evidence and reports;
- verified read-only container planning and overwrite rejection.

### Checkpoint 14A — Declarative recipe catalog

Completed:

- consolidated trusted recipe-template metadata into one strictly validated data-only YAML catalog;
- defined fixed parameter profiles and fixed assessment-policy identifiers;
- declared deterministic step IDs, skill order, dependencies, parameter bindings, literal bindings and output IDs;
- rejected duplicate IDs, invalid identifiers, unsafe dependencies, inconsistent skill graphs, symlinked catalogs and unknown schema fields;
- replaced the hard-coded Python template registry with a catalog-backed compatibility interface;
- retained strict Pydantic validation for model-proposed parameters;
- rejected unknown templates, arbitrary parameters and unsafe PostGIS identifiers before compilation;
- generated the proposal-only Ollama prompt deterministically from the catalog and trusted parameter schemas;
- compiled `WorkflowRecipe` step graphs generically from catalog data;
- retained exact legacy parity checks for the original five templates during migration;
- proved that a new template using existing trusted profiles, policies and skills requires no new compiler branch;
- preserved the existing approval, execution, evidence and Snakemake interfaces;
- added a read-only `recipe-template-catalog` CLI validation command;
- mounted the catalog read-only at the Planner’s explicit `/workspace` working directory;
- added a network-disabled, read-only container CI catalog contract;
- passed 720 automated tests.

The recipe catalog is declarative but trusted. It cannot contain Python, imports, entrypoints, verifiers, shell commands, SQL, approval decisions, permission grants or execution claims. A new recipe can be added without Python changes only when it uses existing trusted skills, parameter profiles and assessment policies.

### Checkpoint 14B — Isolated Builder agent

In progress:

Completed first slice:

- registered a fixed Builder identity through the existing root-level agent-manifest system;
- prohibited Builder tools, shell, SQL, filesystem writes, database writes and additional permission fields;
- added typed request, artifact and proposal schemas;
- restricted proposals to six allowlisted artifact kinds and bounded target prefixes;
- rejected absolute, hidden, traversing, non-normalized and incorrectly typed paths;
- limited file count, individual file size and total proposal size;
- required exact correspondence between requested and proposed artifacts;
- prevented claims of tool use, filesystem modification, testing, validation, approval, trust, promotion or execution;
- kept all candidate content in memory and untrusted.

Completed second slice:

- added deterministic JSON-only Builder prompt construction;
- embedded only the typed, secret-redacted Builder request and required proposal schema;
- invoked the existing shared OpenAI-compatible Ollama client at temperature zero;
- rejected non-JSON, fenced, non-object and schema-invalid responses;
- deterministically required exact task, artifact-path and artifact-kind correspondence;
- rejected model claims of permissions, writes, tools, testing, validation, trust, promotion or execution;
- added proposal-only runtime wiring without CLI, container or filesystem authority.

Completed third slice:

- added a dedicated Builder Compose service using the hardened non-root agent image;
- connected the Builder only to the model network;
- mounted only `agents/builder/manifest.yaml` through its read-only manifest directory;
- inherited a read-only root filesystem, capability dropping, `no-new-privileges` and bounded temporary storage;
- withheld MCP, PostGIS, secrets, context, source, data, evidence, approval, output and candidate-workspace mounts;
- limited the initial container command to static Builder-manifest validation;
- added deterministic container-policy tests independent of Ollama.

Completed fourth slice:

- added one checked-in typed Builder request fixture;
- added a bounded read-only request loader;
- rejected missing, empty, oversized, symlinked, nested, non-regular, malformed and schema-invalid request files;
- added the `builder-propose` CLI command;
- emitted validated proposal results only through standard output;
- used structured model-failure exit codes;
- mounted only the exact Builder request file and Builder manifest read-only;
- executed a live proposal through the isolated Builder container without adding a candidate workspace or write mount.

Completed fifth slice:

- added strict loading of operator-saved Builder generation results from an approved root;
- rejected symlinks, oversized files, path escapes, malformed JSON and schema-invalid generations;
- calculated a canonical SHA-256 digest for each validated Builder generation;
- added a trusted operator-side materializer separate from the Builder container;
- materialized only schema-declared candidate files into an isolated candidate root;
- created candidates atomically through a temporary directory and `os.replace`;
- used digest-addressed candidate directories and refused existing destinations;
- wrote a deterministic `BUILDER_CANDIDATE.json` manifest;
- verified that the saved generation file remained unchanged during materialization;
- calculated the resulting candidate-tree SHA-256 digest;
- added the `materialize-builder-proposal` CLI command;
- preserved explicit false claims for testing, validation, trust, promotion and execution.

Completed sixth slice:

- added deterministic static inspection for materialized Builder candidates;
- required candidates to be direct children of the approved candidate root;
- rejected symlinked roots, candidate directories, nested directories and files;
- validated the strict `BUILDER_CANDIDATE.json` schema;
- required the candidate directory name to match its task and generation digest;
- required the actual file set to match the manifest exactly;
- verified the SHA-256 digest of every declared candidate file;
- parsed Python, JSON and YAML syntax without importing or executing candidate code;
- verified that the complete candidate-tree digest remained stable during inspection;
- added the read-only `inspect-builder-candidate` CLI command;
- preserved explicit false claims for imports, execution, testing, validation, trust and promotion.

Completed seventh slice:

- extended the existing hardened skill-test runner with an explicit Builder-candidate mode;
- preserved the original declarative-skill candidate behavior;
- required exactly one supported candidate manifest;
- validated `BUILDER_CANDIDATE.json` through the trusted typed schema;
- mounted Builder candidates read-only with no network access;
- extended only the bounded candidate package paths required by declared tests;
- emitted typed test evidence containing task, generation and candidate-tree digests;
- recorded pytest collection, pass, failure, skip and error counts;
- verified that the candidate-tree digest remained unchanged during tests;
- added bounded, non-symlinked Builder test-evidence storage;
- required a fresh static inspection before accepting test evidence;
- required exact task, generation and candidate-tree digest matches;
- added the `assess-builder-candidate-tests` CLI command and operator Make targets;
- completed a real network-disabled container test with one passing test;
- kept passing tests insufficient for deterministic GIS validation, trust or promotion.

Completed eighth slice:

- assembled one exact human-review package from the validated Builder generation, candidate manifest, static inspection and isolated-test assessment;
- required task, model, generation and candidate-tree identities to match across all records;
- verified that proposed file contents matched the candidate manifest digests;
- retained proposed repository paths as unapproved destinations;
- persisted the complete review package as deterministic canonical JSON;
- used a digest-addressed immutable review directory;
- wrote the review through a temporary directory and atomic finalization;
- refused symlinked review roots and existing review packages;
- rehashed the candidate before and during review persistence;
- added the `create-builder-review-package` CLI command;
- completed a real review-package creation and digest verification;
- preserved false human-review, approval, trust, promotion and execution claims.

Completed ninth slice:

- added a typed human decision bound to one immutable Builder review-package digest;
- required a unique decision ID, reviewer identity, timezone-aware timestamp and rationale;
- supported explicit approved and rejected outcomes;
- required approved paths to be an exact subset of reviewed candidate paths;
- prohibited rejected decisions from approving paths or authorizing promotion planning;
- securely reloaded canonical `REVIEW.json` packages from the approved review root;
- verified review directory identity, canonical serialization and SHA-256 digest;
- persisted decisions separately as canonical `DECISION.json`;
- used immutable digest-addressed decision directories and atomic finalization;
- reverified the review package before and during decision persistence;
- added the `record-builder-review-decision` CLI command;
- recorded and digest-verified one real approved decision;
- kept file copying, registry modification, implementation trust, promotion and execution false.

Remaining:

- run a separate Ollama-backed Builder agent in an isolated container;
- accept only typed implementation requests and return bounded candidate proposals;
- provide fixed templates and explicitly selected project context;
- allow materialization only into an isolated untrusted candidate workspace;
- permit proposals for adapter code, schemas, policies, tests and catalog entries;
- prohibit access to MCP, PostGIS, credentials, approvals, evidence, outputs, trusted registries and trusted source writes;
- validate generated paths, extensions, file counts and size limits before writing;
- perform static inspection before importing candidate code;
- execute candidate tests without network access;
- bind test evidence to the exact candidate digest;
- require explicit human review and transactional promotion;
- prevent generated output from granting permissions, selecting arbitrary trusted entrypoints or promoting itself.

The Builder reduces repetitive implementation work but receives no execution or trust authority. Generated content remains an untrusted candidate until the existing validation and promotion pipeline accepts its exact digest.

### Checkpoint 14C — Spatial data contracts and dirty-data benchmark

Planned:

- define versioned, data-only spatial-data contracts;
- support vector CRS, geometry type, field type, nullability, unique-key, feature-count, extent and geometry-validity rules;
- add a read-only `assess_spatial_data_contract` skill;
- return typed violations, warnings and deterministic readiness status;
- preserve contract identity and version in workflow evidence;
- create bounded dirty-vector fixtures with missing CRS, invalid geometry, schema drift, null identifiers and duplicate identifiers;
- verify that invalid inputs fail before approval-gated transformation or release;
- extend raster contracts later without weakening vector validation.

Spatial contracts establish what a usable dataset means before a model proposes downstream work. The dirty-data benchmark makes failure handling visible, repeatable and testable.

### Checkpoint 14D — Agent identity and operational history

Planned:

- assign stable logical IDs to Planner, Builder, Executor and Critic roles;
- generate unique instance, run, task and correlation IDs;
- preserve parent-child relationships between proposal, approval, execution, validation and critique;
- write append-only typed operational events;
- record timestamps, component versions, artifact digests, status transitions and redacted failures;
- keep secrets, unrestricted prompts and private chain-of-thought out of operational history;
- support deterministic lookup of every event related to one workflow run.

Operational history should explain what happened, which component acted and which exact artifacts were used. It must not attempt to store hidden model reasoning.

### Checkpoint 14E — Authoritative results and release packages

Planned:

- extend completed results with candidate, validated, released and rejected lifecycle states;
- persist Critic output as a separate immutable record;
- assemble one digest-addressed release package per completed authoritative run;
- include the exact recipe, approval, run result, validation evidence, Critic record, artifact manifest, lineage and deterministic report;
- bind every release component through SHA-256 references;
- provide read-only release inspection and verification;
- prohibit release claims when required validation, evidence or Critic records are missing;
- keep release creation separate from later PostGIS or GeoServer promotion.

A release package turns existing evidence files into one portable and inspectable product result without giving the model authority to declare success.

### Checkpoint 14F — Pilot-ready demonstration

Planned:

- prepare one fixed dirty-vector scenario and one controlled raster scenario;
- demonstrate contract failure and successful correction;
- show constrained local-model proposal and deterministic recipe compilation;
- show exact approval, isolated execution and independent validation;
- show correlated agent history and the separate Critic result;
- create and inspect an immutable release package;
- export and dry-run the approved workflow through Snakemake;
- provide a repeatable script and presentation walkthrough from a clean checkout.

This checkpoint packages the existing architecture into a clear product demonstration rather than adding broad new infrastructure.

### Checkpoint 15 — Expanded PostGIS workflows and controlled release

Planned:

- add controlled spatial transformations;
- add bounded read-only spatial queries;
- add deterministic PostGIS export and validation;
- create versioned staging targets rather than overwriting current layers;
- compare candidate and current datasets using schema, count, extent, geometry and digest evidence;
- require exact approval before promoting a validated candidate;
- preserve previous-version and rollback metadata;
- integrate new operations through trusted skills and declarative recipes;
- prohibit direct model-selected SQL or production-table replacement.

### Checkpoint 16 — Restricted GeoServer publication

Planned:

- plan publication without mutation;
- publish only approved, promoted and validated release artifacts;
- use restricted GeoServer credentials unavailable to model containers;
- allowlist workspace, datastore, layer and style targets;
- verify layer identity, service availability and advertised spatial metadata;
- record publication evidence and release lineage;
- separate publication approval from dataset execution approval.

### Checkpoint 17 — Guided interface and Snakemake productization

Planned:

- provide a guided operator experience for requests, contracts, recipes and approvals;
- visualize workflow status and correlated agent activity;
- navigate validation evidence, Critic results, release packages and reports;
- keep the first interface read-only except for explicit existing approval actions;
- expose Snakemake export, static validation, dry-run and approved replay as one guided workflow;
- display completion markers only after validated execution and durable evidence persistence;
- provide portfolio-ready real GIS demonstrations.

### Checkpoint 18 — Pilot operations and bounded memory

Planned:

- collect pilot feedback and recurring operational failure categories;
- add memory only for reviewed operational facts that improve future planning;
- require provenance, scope, version, retention and deletion metadata;
- separate project facts from agent-run history;
- prohibit secrets, credentials, private reasoning and unreviewed model conclusions;
- add memory retrieval only after pilot evidence demonstrates a concrete need.

## Container filesystem authorization

GeoAgent uses separate read-only input/control mounts and narrowly
scoped writable evidence/output mounts.

| Path | Executor | MCP GIS | Purpose |
|---|---:|---:|---|
| `/workspace/context` | read-only | read-only | Trusted skill registry and policy context |
| `/workspace/workflow-recipes` | read-only | read-only | Immutable validated recipes |
| `/workspace/approvals` | read-only | read-only | Digest-bound human approvals |
| `/workspace/data/input` | unavailable | read-only | Approved GIS source data |
| `/workspace/data/output` | unavailable | read/write | Approved GIS output artifacts |
| `/workspace/recipe-runs` | unavailable | read/write | Immutable typed execution results |
| `/workspace/recipe-evidence` | unavailable | read/write | Hashed lineage and QA evidence |
| `/workspace/reports` | unavailable | read/write | Deterministic Markdown reports |
| PostGIS credentials | unavailable | secret file only | Controlled database access |

The GIS container runs as a non-root user. Writable host directories
use group `10001` and setgid permissions so files created by the
container remain manageable from the host:

```bash
sudo chown "$(id -u):10001" \
  data/output recipe-runs recipe-evidence reports

sudo chmod 2775 \
  data/output recipe-runs recipe-evidence reports
```

ENABLE_WRITE_TOOLS=false is the persistent safe default. It is
enabled only for an exact approved execution and restored immediately
afterward.

The Executor does not mount GIS inputs, outputs, evidence directories,
or database credentials. It submits a typed approval-bound envelope
through the fixed run_approved_recipe MCP tool and validates the
returned recipe identity, status, and run-result digest.


## Skills and recipes

A skill is a trusted primitive capability implemented and tested in
code. Examples include inspecting a vector dataset, converting a
vector file, loading a table into PostGIS and validating a PostGIS
layer.

A recipe is a declarative workflow assembled from registered skills.
Recipes define step order, dependencies, validated parameters and
output identifiers. They do not contain arbitrary Python, shell
commands or SQL.

This distinction allows operators and local models to create new
workflows without writing code whenever the necessary primitive
skills already exist.

Examples of no-code recipe changes include:

- inspecting a different dataset;
- converting to a different approved format;
- changing a safe output path;
- selecting a source layer;
- changing an approved PostGIS schema or table;
- combining existing inspection, transformation, validation and
  reporting steps;
- replaying a previously validated workflow.

A genuinely new capability still requires a new skill implementation
and deterministic verifier. Future skill-scaffolding tools will
generate the repetitive package structure, schemas, registry entry
and contract tests, but generated implementations will not become
trusted automatically.


## Decision principles

When extending the project:

- preserve the three-agent separation;
- continue using one shared model runtime;
- keep PostGIS externally managed;
- keep execution behind typed MCP tools;
- keep approval bound to exact plan identity;
- keep model output untrusted;
- keep deterministic validation as the success gate;
- keep hosted CI secret-free;
- avoid adding broad capabilities merely for convenience;
- prefer small, tested vertical checkpoints.

## License

A license has not yet been selected.

Before accepting external contributions or distributing the project broadly, add an explicit open-source or proprietary license.


### GIS skill scaffolding

GeoAgent can generate isolated skeletons for new GIS skills:

```bash
geoagent plan-skill-scaffold request.json --pretty

geoagent generate-skill-scaffold \
  request.json \
  --scaffold-root skill-scaffolds \
  --pretty

geoagent validate-skill-scaffold \
  skill-scaffolds/example_skill \
  --pretty
```

Generated scaffolds are untrusted and remain planned. They are not automatically copied into the application, registered, approved, or executed.


### Declarative Skill SDK

GeoAgent provides a controlled path from a versioned declarative skill definition to a trusted installed GIS skill.

A file such as `skill-definitions/inspect_raster.skill.yaml` declares skill intent and metadata only. It cannot provide executable Python, arbitrary imports, shell commands, entrypoints, verifiers, approvals or execution results.

The trusted skill lifecycle is:

```text
.skill.yaml definition
→ deterministic profile and adapter assessment
→ immutable digest-addressed contract
→ isolated generic scaffold
→ static contract validation
→ trusted adapter materialization
→ isolated candidate bundle
→ network-disabled container tests
→ digest-bound test evidence
→ read-only promotion assessment
→ exact promotion plan
→ explicit transactional promotion
→ implemented registry entry
```

The permission profile determines the skill’s access class, approval requirement and validation requirement. The adapter identifier must exist in a fixed trusted catalog. Unknown profiles, adapters and unsafe combinations fail closed.

Generated scaffolds remain untrusted. Passing static scaffold contracts does not make their code implemented or trusted. Candidate code is produced only by an allowlisted trusted adapter renderer and is tested in a separate non-root container with:

- no network;
- no model endpoint;
- no MCP service;
- no PostGIS credentials;
- a read-only candidate mount;
- a read-only container filesystem;
- dropped Linux capabilities;
- `no-new-privileges`.

Candidate test evidence records the exact definition digest, candidate-tree digest, test outcome and test counts. Promotion requires that the current candidate and test record still match those digests.

Promotion is an explicit transaction. It copies only the exact files listed in the promotion plan, installs the trusted registry entry last and removes newly copied files if promotion cannot complete. It does not execute the promoted skill.

The first skill promoted through this pipeline is `inspect_raster`. It:

- reads one raster beneath an approved input root;
- rejects path traversal and symlinks;
- opens the raster read-only with Rasterio;
- returns typed dimensions, CRS, bounds, transform, band, datatype and nodata metadata;
- verifies that inspection did not change the source file;
- has no filesystem-write, database-write or approval authority.

Run the promoted skill directly:

```bash
.venv/bin/geoagent inspect-raster \
  data/input/sample_dem.tif \
  --input-root data/input \
  --pretty
```

The constrained recipe-proposal system also recognizes the fixed `inspect_raster` template. A request can be validated and compiled into this non-executing step:

```json
{
  "step_id": "step_1",
  "skill_id": "inspect_raster",
  "depends_on": [],
  "arguments": {
    "path": "data/input/sample_dem.tif"
  },
  "output_ids": [
    "raster_metadata"
  ]
}
```

Because this skill is read-only, deterministic recipe policy returns no approval-required steps. The existing recipe execution envelope remains write-approval-gated, so a purely read-only recipe is not given a fabricated approval. A separate controlled read-only recipe execution policy can be added later.

This SDK reduces the manual work required to add standard skills, but it does not allow YAML or model output to invent and trust arbitrary GIS algorithms. Novel implementations still require a trusted adapter, domain-specific tests and explicit promotion.

### Approved Snakemake replay

GeoAgent can export an exact approved recipe into a deterministic Snakemake package:

```bash
geoagent list-approved-recipes --pretty

geoagent plan-snakemake-export \
  workflow-recipes/RECIPE.json \
  approvals/RECIPE-APPROVAL.json \
  --pretty

geoagent export-approved-recipe-snakemake \
  workflow-recipes/RECIPE.json \
  approvals/RECIPE-APPROVAL.json \
  --export-root snakemake-exports \
  --pretty

geoagent validate-snakemake-export \
  snakemake-exports/EXPORT_DIRECTORY \
  --pretty

Run a non-executing DAG check in the isolated workflow container:

make snakemake-dry-run \
  SNAKEMAKE_EXPORT_DIR=EXPORT_DIRECTORY

The generated Snakefile contains no shell rule. It calls one trusted adapter that revalidates the export and exact approval before using the existing Executor-to-MCP boundary. Real replay requires an explicit operator procedure that temporarily enables MCP writes and restores the disabled default afterward.

Be sure both nested code blocks are closed correctly.
