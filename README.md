# GeoAgent Skill Harness

GeoAgent Skill Harness is a CLI-first, local-first, containerized platform for planning controlled geospatial workflows, executing allowlisted GIS operations, deterministically validating results, and recording reproducible reports and traces.

The prototype runs under Ubuntu WSL with Docker Desktop. It uses one shared local Ollama/Qwen runtime instead of placing a large model inside every agent container.

## Current status

Checkpoints 1–7D are complete for the initial vector-to-PostGIS vertical slice.

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

- `convert_vector`;
- raster workflows;
- generalized retries and cancellation;
- resumable workflow state;
- task queues and scheduling;
- trace-schema migration;
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

Status: planned.

It should eventually support controlled conversion among GeoJSON, GeoPackage, and Shapefile while preserving path, CRS, overwrite, and verification policy.

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

### Container builds

`.github/workflows/container-build.yaml` independently builds:

```text
docker/agent/Dockerfile
docker/gis-tools/Dockerfile
```

It:

- uses BuildKit caching;
- does not push images;
- loads each image for validation;
- verifies the configured runtime user is `geoagent`;
- runs the installed CLI;
- supplies no PostGIS secret;
- makes no Ollama request;
- makes no PostGIS connection.

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

- Only the vector-to-PostGIS vertical slice is complete.
- `convert_vector` is not implemented.
- Raster processing is not implemented.
- Critic output is returned in memory rather than saved separately.
- Plans and approvals are local runtime files.
- PostGIS is externally managed.
- Ollama is externally managed.
- Write enablement is controlled operationally through environment settings.
- Existing tables and artifacts cannot be overwritten.
- Deletion is unavailable.
- General retries and cancellation are not implemented.
- Interrupted workflows are not yet resumable through a state machine.
- No task queue exists.
- No production authentication exists.
- No multi-user deployment exists.
- Docker model-network egress is not restricted through a dedicated proxy.
- Real integration tests depend on the local development environment.

## Roadmap

### Checkpoint 7B — Structured failure handling

Status: implemented; final acceptance is documented in
`context/CURRENT_STATUS.md`.

Implemented:

- stable failure categories and codes;
- explicit failure stages;
- stable CLI exit codes;
- secret-redacted structured failure records;
- retry dispositions of `never`, `safe_read_only`, and `manual_review`;
- safe retry classification for read-only model and MCP calls;
- no automatic retry of database writes;
- manual review after uncertain or interrupted execution;
- operator cancellation with exit code 130;
- structured failure evidence in traces;
- failure summaries in Markdown reports;
- successful traces with `failure: null`.

Exit-code policy:

| Exit code | Meaning |
|---:|---|
| `1` | Deterministic validation failed |
| `2` | Invalid input, configuration, policy, approval, conflict, or not found |
| `3` | Timeout or dependency unavailable |
| `4` | Invalid external response or execution failure |
| `5` | Unclassified internal error |
| `130` | Operator cancellation |

Retry policy:

| Disposition | Meaning |
|---|---|
| `never` | Do not retry automatically |
| `safe_read_only` | A bounded retry may be added for an explicitly read-only operation |
| `manual_review` | Inspect state before retrying, especially after database execution |

The current harness classifies retry safety but does not yet implement an
automatic retry loop. That work belongs to Checkpoint 7C together with durable
workflow state and resumption.

### Checkpoint 7C — Durable workflow state and safe resumption

Status: implemented.

The harness can persist and validate a durable lifecycle record for one exact planned workflow. Every transition records its sequence, previous state, next state, responsible actor, reason, timestamp, and optional structured failure.

#### Workflow lifecycle

```text
planned
  → approved
  → executing
  → validating
      ├──→ validated_success
      └──→ validation_failed

executing
  ├──→ execution_failed
  └──→ cancelled

validating
  ├──→ execution_failed
  └──→ cancelled
```

#### Transition policy

- Only a human actor can record approval.
- Only the Executor can begin execution.
- Only the deterministic verifier can record validation transitions.
- Only an operator can cancel a workflow.
- Terminal states cannot transition again.
- Transition sequences and revisions must be contiguous.
- Transition timestamps must be monotonic.
- Stale revision updates are rejected.
- Initial state files cannot be overwritten.
- Failure evidence is required for failed or cancelled states.
- The plan digest and approval identity remain attached to the workflow state.

#### Durable state storage

Workflow state is stored beneath the configured state root:

```text
workflow-state/<task-id>.state.json
```

The default local setting is:

```dotenv
GEOAGENT_STATE_ROOT=workflow-state
```

Inside the Executor container, the configured path is:

```dotenv
GEOAGENT_STATE_ROOT=/workspace/workflow-state
```

State files are:

- schema validated with Pydantic;
- secret redacted before persistence;
- limited to the trusted state root;
- checked for UTF-8 and JSON validity;
- limited in file size;
- created without overwrite;
- updated atomically;
- protected by expected revision checks;
- readable by the non-root Executor container.

Runtime state files are excluded from Git. Only the directory placeholder is tracked:

```text
workflow-state/.gitkeep
```

#### Resume assessment

The resume assessment is deterministic and read-only.

| Current evidence | Disposition |
|---|---|
| Planned and not executed | `resume_allowed` |
| Approved and not executed | `resume_allowed` |
| Executing | `manual_review_required` |
| Validating | `manual_review_required` |
| Execution failed | `manual_review_required` |
| Validation failed | `manual_review_required` |
| Cancelled after execution may have started | `manual_review_required` |
| Cancelled before execution | `terminal` |
| Deterministically validated success | `terminal` |

`resume_allowed` does not authorize immediate or automatic execution. It only means that the state history contains no evidence that a database write started. The exact plan and approval must still be revalidated before the Executor begins work.

`manual_review_required` means that a PostGIS write may have started. The operator must inspect the target table, trace, report, approval, and structured failure before deciding what to do next.

#### Inspect workflow state

```bash
geoagent inspect-workflow-state \
  workflow-state/example.state.json \
  --state-root workflow-state \
  --pretty
```

This command:

- loads the file only from the trusted state root;
- validates it against the workflow-state schema;
- displays structured JSON;
- does not change the state file;
- does not execute any GIS or database operation.

#### Assess safe resumption

```bash
geoagent assess-workflow-resume \
  workflow-state/example.state.json \
  --state-root workflow-state \
  --pretty
```

The result includes:

```json
{
  "current_state": "planned",
  "disposition": "resume_allowed",
  "database_write_may_have_started": false,
  "automatic_execution_allowed": false,
  "state_modified": false
}
```

The displayed values are expected output, not Bash commands.

#### Container assessment

The Executor receives the workflow-state directory through a read-only mount:

```yaml
- ./workflow-state:/workspace/workflow-state:ro
```

Run the containerized assessment with:

```bash
make state-container \
  STATE_TASK_ID=checkpoint7c-state-check
```

Planner and Critic containers do not receive the workflow-state mount.

The container assessment must not modify the state file. This can be verified by comparing hashes before and after execution:

```bash
sha256sum \
  workflow-state/checkpoint7c-state-check.state.json
```

#### Security properties

- State inspection never invokes arbitrary shell commands.
- State assessment never invokes MCP tools.
- State assessment never accesses PostGIS.
- The Executor receives state through a read-only mount.
- Planner and Critic containers receive no state access.
- Secrets are redacted before state persistence.
- Path traversal outside the trusted state root is rejected.
- State-file overwriting is blocked during initial creation.
- Stale revisions are rejected during updates.
- Database writes are never automatically retried.
- An interrupted or uncertain write requires manual inspection.
- Assessment never modifies workflow state.
- Assessment never authorizes automatic execution.

#### Current limitations

- Resume assessment recommends an action but does not perform it.
- Automatic retry is not implemented.
- Automatic workflow resumption is not implemented.
- PostGIS writes are never automatically retried.
- Process-level locking for concurrent writers is not implemented.
- Do not run two state writers for the same task simultaneously.
- The production Planner, approval, Executor, and verifier flow does not yet update durable state automatically at every boundary.
- Recovery after manual review requires creating an explicitly approved follow-up action.

### Checkpoint 7D — Schema versioning and compatibility

Status: implemented.

GeoAgent artifacts use explicit schema versions governed by one central registry. Artifact loaders check compatibility before performing full Pydantic validation.

#### Registered artifact types

The registry currently covers:

- `context_pack`;
- `workflow_plan`;
- `approval_record`;
- `execution_envelope`;
- `failure_record`;
- `workflow_trace`;
- `critic_assessment`;
- `critic_evidence_pack`;
- `workflow_state`;
- `resume_assessment`.

All registered artifacts currently use:

```text
current version: 1.0
writable version: 1.0
supported read versions: 1.0
registered migration sources: none
```

#### Compatibility dispositions

| Disposition | Meaning |
|---|---|
| `current` | The artifact uses the current readable and writable version |
| `supported_read` | The artifact can be read, but new writes use another version |
| `migration_required` | A registered explicit migration is required |
| `unsupported_older` | The older version is not readable and has no registered migration |
| `unsupported_future` | The artifact was created by a newer unsupported schema |
| `invalid_version` | The version does not use the required `major.minor` format |

#### Version-aware loading

Persisted artifact loading follows this order:

```text
read bounded input
→ parse JSON
→ require explicit schema_version
→ consult central registry
→ reject unreadable version
→ validate with the artifact Pydantic schema
```

For Planner results, the version is nested at:

```text
plan.schema_version
```

Other registered persisted artifacts currently use a top-level field:

```json
{
  "schema_version": "1.0"
}
```

Protected boundaries include:

- saved Planner results;
- approval records;
- workflow traces used by the Critic;
- durable workflow-state files;
- incoming execution envelopes;
- structured Critic model responses.

Missing versions do not receive an implicit default when loading external or persisted artifacts. They fail closed before normal schema validation.

#### Inspect schema policies

```bash
geoagent schema-policies --pretty
```

This command displays the registry without modifying it.

#### Assess compatibility

```bash
geoagent assess-schema-compatibility \
  workflow_trace \
  1.0 \
  --pretty
```

A current version returns exit code `0`:

```json
{
  "artifact_type": "workflow_trace",
  "artifact_version": "1.0",
  "disposition": "current",
  "readable": true,
  "writable": true,
  "migration_required": false,
  "artifact_modified": false
}
```

An unsupported version returns exit code `1` while still emitting a structured assessment:

```bash
geoagent assess-schema-compatibility \
  workflow_trace \
  2.0 \
  --pretty
```

An unknown artifact type returns exit code `2`.

#### Assess migration requirements

```bash
geoagent assess-schema-migration \
  workflow_state \
  2.0 \
  --pretty
```

The assessment is read-only and reports:

```json
{
  "source_version": "2.0",
  "target_version": "1.0",
  "compatibility": "unsupported_future",
  "migration_available": false,
  "manual_review_required": true,
  "artifact_modified": false,
  "migration_performed": false
}
```

An exit code of `1` is expected when manual review is required.

#### Security and compatibility rules

- Every persisted versioned artifact must declare its schema version.
- Artifact versions must use `major.minor` format.
- Unknown future versions fail closed.
- Unsupported older versions fail closed.
- Missing versions fail closed.
- Invalid versions fail closed.
- Only the registered writable version may be produced by current code.
- No loader silently adds a version to external input.
- No loader silently upgrades an artifact.
- No compatibility command modifies an artifact.
- No migration command currently exists.
- Original unsupported artifacts must be preserved for review.
- Model-generated structured responses are treated as untrusted and version checked.

#### Current limitations

- Only schema version `1.0` is implemented.
- No migration function is registered.
- No real backward-compatible read version exists yet.
- `supported_read` and `migration_required` policies are implemented but cannot occur under the current all-`1.0` registry.
- Future schema evolution must include fixtures, migration tests, rollback guidance, and explicit operator approval before migration is enabled.

### Checkpoint 8 — `convert_vector`

Planned:

- controlled format conversion;
- trusted input and output roots;
- explicit target format;
- CRS preservation or explicit transformation;
- safe multi-layer handling;
- deterministic output inspection;
- trace integration;
- overwrite approval policy;
- no arbitrary GDAL command strings.

### Later GIS skills

Potential additions:

- vector reprojection;
- geometry repair;
- clip;
- dissolve;
- spatial join;
- buffer;
- simplify;
- area and length calculations;
- raster inspection;
- raster reprojection;
- raster clipping;
- zonal statistics;
- vector-to-raster;
- raster-to-vector.

Every new skill must include typed schemas, path policies, permissions, deterministic verification, sample data, automated tests, and trace integration.


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

ENABLE_WRITE_TOOLS=false is the persistent safe default. It is
enabled only for an exact approved execution and restored immediately
afterward.

The Executor does not mount GIS inputs, outputs, evidence directories,
or database credentials. It submits a typed approval-bound envelope
through the fixed run_approved_recipe MCP tool and validates the
returned recipe identity, status, and run-result digest.



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