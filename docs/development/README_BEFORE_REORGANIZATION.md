# Historical README snapshot

This preserved snapshot contains superseded descriptions and incremental delivery notes. It is not current setup or capability guidance. See the root README and CURRENT_STATUS for current behavior.

# ActionCharter

[![Tests](https://github.com/wanggiya/action-charter/actions/workflows/test.yaml/badge.svg)](https://github.com/wanggiya/action-charter/actions/workflows/test.yaml)
[![Container contracts](https://github.com/wanggiya/action-charter/actions/workflows/container-build.yaml/badge.svg)](https://github.com/wanggiya/action-charter/actions/workflows/container-build.yaml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/wanggiya/action-charter?quickstart=1)

**A governed execution harness for AI agents using professional tools.**

ActionCharter lets models interpret requests and propose work without giving
them unrestricted authority over shells, databases, filesystems, credentials,
or production systems. Deterministic software validates the proposal, binds
approval to its exact scope, dispatches only allowlisted operations, verifies
the resulting state, and preserves tamper-evident evidence.

> **Models propose; deterministic software authorizes, executes, validates,
> and records evidence.**

### Current prototype status

Checked context retrieval, reviewed Intent, vector/raster metadata planning, immutable plan storage and saved-review recovery are implemented. Existing CLI and governed recipe execution remain available. The new Intent journey is not yet a single request-to-run experience: see [Checkpoint 22 closeout](docs/CHECKPOINT22O.md) for boundaries and validation, and [Checkpoint 23 plan](docs/CHECKPOINT23_PLAN.md) for the next integrated journey.

### Context and intent development

Task histories preserve explicit events and checked artifact relationships. The
new backend context retriever searches only histories the operator selects and
returns bounded excerpts with original source digests. Its output is
**retrieved, not reviewed**: it grants no approval. CLI and local API access
support explicit review and immutable context storage. The reasoning-only Intent
Agent can consume a reviewed record and explicit clarification answers; sources
are checked before and after inference. Intent proposes questions or objectives,
never work authority. The first Context & intent panel and an exact inspection handoff are available;
integration with saved plans and governed execution follows. See [Checkpoint 22](docs/CHECKPOINT22.md).

The default interface now starts with **Plan → Flow graph → Run → Check
outcome**. Run opens the saved recipe chooser when no recipe is active;
planning alone does not authorize execution. Advanced reveals templates,
recipes, run inventory, Assurance, draft graph editing, and the trace selector.
The command line and the exact approval and verification gates remain available.
See `docs/CHECKPOINT19.md` for the current interface scope and validation.

Checkpoint 17AD can compile an independently verified Planner result into a
typed governed recipe candidate for supported dispatcher skills. Compilation
does not save, approve, or execute the recipe; recipe authority remains a
separate review sequence.

Checkpoint 17AE adds explicit digest review and immutable storage for that
candidate. Saving revalidates the source plan, approval evidence, recipe policy,
and digest; it still grants no recipe approval and performs no execution.

Checkpoint 17AF carries the exact stored recipe into the existing approval
workspace and prioritizes it in the refreshed inventory. Approval preparation
remains a separate explicit operator action.

Checkpoint 17AQ adds a read-only Assurance workspace for deterministic Critic
evidence inspection. It validates existing WorkflowTrace/report pairs and shows
their status, approval completeness, gaps, warnings, and hashes without calling
a model, recording a Critic result, creating a release, or executing work.

Checkpoint 17AR previews a truthful bridge from completed interface recipe runs
to Critic-compatible workflow traces. It requires matching immutable recipe,
approval, evidence, step, status, and durable timing records; incomplete legacy
runs remain blocked. The preview is in-memory and writes no trace or release.

Checkpoint 17AS lets an operator review the exact adapted-trace digest and
immutably store its trace/report pair. The backend rebuilds and revalidates the
candidate before writing. Evidence storage does not invoke the Critic, record a
Critic result, create a release, or execute work.

Checkpoint 17AT adds a separate explicit Critic action for one exact stored
trace/report pair. The service rechecks both evidence hashes before calling the
configured model and validates its response against the existing Critic schema
and deterministic conclusion policy. The assessment remains in memory: it is
not a Critic record, does not create a release, and executes nothing.

Checkpoint 17AU adds a second explicit review boundary for the validated
assessment. The backend rechecks the stored trace/report hashes, evidence
identity, deterministic status, complete Critic result, and reviewed result
digest before creating an immutable digest-addressed record. Recording still
creates no release and performs no execution.

Checkpoint 17AV completes the next governed boundary for recipe runs. Assurance
binds the exact recipe, approval, run result, recipe evidence, trace, report,
Critic record, and operational history into a deterministic readiness
candidate. A release is created only after the operator reviews and confirms
that exact candidate digest; packaging does not rerun tools or modify data.

Checkpoint 17AW exposes the existing Snakemake export boundary in the recipe
workspace. After independent approval verification, an operator previews the
exact export plan and digest, then separately confirms generation. The service
creates and statically validates the Snakefile, replay configuration, and
manifest without invoking Snakemake or re-executing the recipe.

Checkpoint 17AY closes the guided-interface prototype after final acceptance
identified and corrected a Planner-to-recipe gap for the established
inspect/load/validate/report PostGIS sequence. Repeating the same exact
Snakemake export now revalidates the existing package rather than failing as a
duplicate. The default Checkpoint 18 experience will simplify the visible path
to **Plan → Flow graph → Run → Check outcome**, while recipes, raw digests,
release composition, Snakemake, skills, and infrastructure move into an
Advanced workspace. See `context/CHECKPOINT18_DIRECTION.md`.

The current reference implementation applies this architecture to geospatial
data with GeoPandas, GDAL, rasterio, PostGIS, and GeoServer-oriented workflows.
GIS is the first reference domain, not the architectural limit.

> ActionCharter is an alpha research and pilot implementation. It is not yet a
> hardened multi-user production control plane.

## Why ActionCharter?

Giving a model access to a powerful tool is easy. The harder problem is proving
that an AI-assisted operation:

1. used the correct input;
2. selected an allowed operation;
3. remained inside an explicitly bounded scope;
4. received approval for the exact consequential steps;
5. executed only what was approved;
6. produced a valid result;
7. was independently verified; and
8. left evidence that can be inspected later.

Generated text never becomes authority merely because a model generated it.
ActionCharter turns an uncertain proposal into a chain of typed, digest-bound,
and independently checkable artifacts.

## Governed execution flow

```mermaid
flowchart TD
    A["User request"] --> B["Planner proposal"]
    B --> C["Schema and policy validation"]
    C --> D["Digest-bound plan"]
    D --> E["Human approval"]
    E --> F["Allowlisted execution"]
    F --> G["Deterministic validation"]
    G --> H["Independent verification"]
    H --> I["Immutable evidence and release"]
    C -->|Rejected| X["Fail closed"]
    E -->|Denied or expired| X
    G -->|Invalid result| X
    H -->|State mismatch| X
```

For consequential mutations, rollback is another governed operation. It
requires its own deterministic plan, exact approval, transactional execution,
and independent verification; it is not an emergency bypass.

## Agents and authority

Planner, Executor, and Critic are intentionally separated. The Planner and
Critic may use the same local model runtime, but they receive different
contexts and permissions. The Executor has no model authority. Professional
tools and credentials remain behind controlled adapters and the internal MCP
boundary.

```mermaid
flowchart TD
    U["User / Operator"] --> P["Planner"]
    P --> G["Deterministic governance layer"]
    U --> A["Exact human approval"]
    A --> G
    G --> E["Executor"]
    E --> T["Allowlisted adapters / MCP"]
    T --> S["GIS, PostGIS, filesystem"]
    S --> V["Independent verifier"]
    V --> R["Evidence and release"]
    S --> C["Critic"]
    C --> R
    M["Local model runtime"] --> P
    M --> C
```

| Component | May do | May not do |
|---|---|---|
| Planner | Interpret a bounded request and propose a typed plan | Execute tools or approve work |
| Executor | Run an already-authorized typed operation | Use a model or invent operations |
| Critic | Assess bounded evidence and identify unresolved risks | Change authoritative workflow state |
| Governance layer | Enforce schemas, policy, digests, scope, and approval | Treat generated text as permission |
| Human operator | Approve or deny an exact consequential scope | Implicitly approve a changed plan |
| Verifier | Reload authoritative artifacts and inspect resulting state | Trust an executor's success claim |

The Builder explores generated extensions under a separate lifecycle:
candidate generation, bounded materialization, offline tests, review,
digest-bound promotion, activation, and post-activation verification. Generated
code remains untrusted until those deterministic controls succeed.

## Skills, recipes, and workflows

These terms describe different layers and should not be used interchangeably:

| Concept | Meaning | Example |
|---|---|---|
| Skill | One bounded capability with a typed contract and policy boundary | `inspect_raster` |
| Recipe | A reusable, parameterized definition that connects trusted skills | Inspect a raster, convert it, then validate the result |
| Workflow | One proposed, approved, running, or completed instance with specific inputs, state, timing, and evidence | Convert `dem.tif` to EPSG:3857 in a particular run |

A recipe may contain several skill steps. A workflow may be created from a
recipe, but it becomes a distinct run with its own plan, approval requirements,
results, validation, and evidence. Interface templates select trusted recipes;
they do not install skills or represent completed workflows. See
[Core concepts and equivalence testing](docs/CORE_CONCEPTS.md).

The first versioned CLI/interface parity scenario is documented in
[Checkpoint 17L](docs/CHECKPOINT17L.md). It compiles one trusted vector
conversion proposal without saving, approving or executing it, establishing
the baseline for the next typed interface-service slice.

[Checkpoint 17M](docs/CHECKPOINT17M.md) adds the first live interface backend:
a loopback-only typed service for loading the trusted template catalog and
compiling an exact proposal in memory. Start it alongside Vite:

```bash
# terminal 1
.venv/bin/geoagent serve-interface-api --project-root .

# terminal 2
corepack pnpm@10.17.1 --dir interface dev
```

For backend route development, `bash scripts/serve_interface_dev.sh` pins imports
to the current checkout and prints source/route diagnostics. See
[Interface API troubleshooting](docs/INTERFACE_API_TROUBLESHOOTING.md).

The interface can now preview, download and compile a trusted-template
proposal. It still cannot save, approve or execute one.

[Checkpoint 17N](docs/CHECKPOINT17N.md) adds a separate reviewed-save action.
The interface displays the complete compiled step order and recipe SHA-256,
requires explicit operator confirmation, then recompiles and verifies that
digest before immutable storage under `workflow-recipes/`. Saving still grants
no approval or execution authority.

[Checkpoint 17O](docs/CHECKPOINT17O.md) adds a read-only inventory of immutable
stored recipes. The successful save card now provides **Done — view saved
recipes**, and the top bar provides a persistent **Recipes** control. Inventory
cards show exact digests, ordered skills and future approval/validation gates
without exposing arguments or granting approval or execution authority.

[Checkpoint 17P](docs/CHECKPOINT17P.md) lets an operator prepare an exact
approval request for one stored recipe. It revalidates the canonical recipe and
policy, binds every required step to the recipe digest, and displays a separate
approval-request digest. Preparation records no decision and cannot execute.

[Checkpoint 17Q](docs/CHECKPOINT17Q.md) adds a separate append-only human
approve/deny action. The backend reprepares the request, verifies both digests,
derives the step scope server-side, redacts operator text, and stores approval
evidence beneath `approvals/`. Recording a decision still cannot execute.
The interface then independently reloads and verifies the exact recipe and approval
against current policy. Large authority cards distinguish append-only evidence,
verified approval scope, and the separate fact that nothing has executed. See
`docs/CHECKPOINT17R.md`.
After verification, the interface can build and inspect the exact governed
execution envelope—including ordered skills, redacted arguments, declared outputs,
validation requirements and evidence roots—without running it. See
`docs/CHECKPOINT17S.md`.

[Checkpoint 17T](docs/CHECKPOINT17T.md) adds explicitly confirmed execution of
one exact approved preview when write tools were enabled at API startup.
[Checkpoint 17U](docs/CHECKPOINT17U.md) makes runner progress atomic, durable
and restart-aware, including failed-step and interruption localization.
[Checkpoint 17V](docs/CHECKPOINT17V.md) adds the read-only **Runs** inventory so
completed, failed, interrupted or active attempts can be reopened as their
run-specific graph after a browser or API restart. Reopening never retries or
executes a recipe.

[Checkpoint 17W](docs/CHECKPOINT17W.md) adds the first live Planner Agent entry
point: a natural-language request is processed by the existing trusted context,
agent manifest, configured model client and plan schema validator, then rendered
as a planning-only graph. See [interface and CLI parity](docs/INTERFACE_CLI_PARITY.md)
for the remaining governed workflow families.
[Checkpoint 17X](docs/CHECKPOINT17X.md) adds a separate reviewed-save boundary
for that validated result. The interface displays the canonical plan SHA-256,
requires explicit review, reruns schema and deterministic policy checks, and
stores the full CLI-compatible `PlannerResult` immutably beneath `plans/`.
Saving does not approve or execute the plan.
[Checkpoint 17Y](docs/CHECKPOINT17Y.md) can then prepare the exact approval
scope from the immutable plan. It revalidates the stored result and reports
read-only plans as approval-not-required without pretending a decision exists.
Preparation records no approval and performs no execution.
[Checkpoint 17Z](docs/CHECKPOINT17Z.md) adds the distinct append-only human
decision for plans containing approval-required steps. Approve and deny both
remain evidence-only operations; read-only plans cannot create meaningless
approval records.
[Checkpoint 17AA](docs/CHECKPOINT17AA.md) exposes exact step arguments and both
approval and validation flags before the decision, then independently verifies
the recorded evidence without modifying artifacts or executing the plan.
[Checkpoint 17AB](docs/CHECKPOINT17AB.md) previews the existing typed Executor
envelope for the supported four-step PostGIS workflow. Unsupported plan shapes
fail explicitly; previewing never executes work.
[Checkpoint 17AC](docs/CHECKPOINT17AC.md) restores saved Planner results and
their latest decision after browser or API restart, without model regeneration
or duplicate approval. Restored evidence must be independently verified again.

Checkpoint 17T adds the first interface execution action for that exact preview.
It remains disabled by default, requires explicit write-tool startup authority and
operator confirmation, revalidates every artifact server-side, dispatches only
registered recipe skills, and records run, evidence and report artifacts. See
`docs/CHECKPOINT17T.md`.

## Complete PostGIS reference lifecycle

Checkpoints 15A–15K provide the strongest end-to-end demonstration of the
governance model:

```mermaid
flowchart TD
    A["15A Inspect"] --> B["15B Compare"]
    B --> C["15C Assess"]
    C --> D["15D Plan promotion"]
    D --> E["15E Approve promotion"]
    E --> F["15F Execute promotion"]
    F --> G["15G Verify promotion"]
    G --> H["15H Plan rollback"]
    H --> I["15I Approve rollback"]
    I --> J["15J Execute rollback"]
    J --> K["15K Verify rollback"]
```

The inspection, comparison, and assessment stages are read-only and accept no
arbitrary SQL. Promotion and rollback execute only fixed, approved relation
renames inside serializable transactions. Separate verifiers reload the exact
plan, approval, and execution evidence and inspect PostGIS through independent
read-only transactions.

Representative commands:

```bash
geoagent inspect-postgis-table --schema agent_sandbox --table sample_points --pretty

geoagent compare-postgis-tables \
  --reference-schema agent_sandbox --reference-table current_layer \
  --candidate-schema agent_sandbox --candidate-table candidate_layer --pretty

geoagent assess-postgis-change \
  --reference-schema agent_sandbox --reference-table current_layer \
  --candidate-schema agent_sandbox --candidate-table candidate_layer --pretty
```

The remaining lifecycle is exposed through `plan-postgis-promotion`,
`record-postgis-promotion-approval`, `execute-postgis-promotion`,
`verify-postgis-promotion`, `plan-postgis-rollback`,
`record-postgis-rollback-approval`, `execute-postgis-rollback`, and
`verify-postgis-rollback`.

Checkpoint 16A adds bounded, read-only inspection of one exact allowlisted
GeoServer workspace, datastore, and layer without accepting arbitrary REST
paths or modification methods:

```bash
geoagent inspect-geoserver-layer \
  --workspace geoagent_test \
  --datastore actioncharter_postgis \
  --layer checkpoint3e_sample_points \
  --pretty
```

See the [Checkpoint 16A local setup](docs/CHECKPOINT16A.md) for allowlists and
password-file configuration, including the dedicated GeoServer test user,
workspace-scoped REST role, PostGIS-backed datastore, and Docker network.

Checkpoint 16B adds the first governed GeoServer mutation. It can only enable
and advertise an existing allowlisted feature type and its published layer
after the current state has been captured in an exact SHA-256 plan and a human
approval binds that digest. The executor revalidates the state before one fixed
PUT to the authoritative feature-type resource, validates the complete effective
result, and compensates to the pre-state if the
transition fails. A separate command independently reinspects the layer.
See [Checkpoint 16B](docs/CHECKPOINT16B.md).

## Implemented capabilities

| Boundary | Current implementation |
|---|---|
| Planning | Bounded task context, schema-constrained plans, and deterministic policy |
| Authorization | Append-only approvals bound to exact SHA-256 identities and step scope |
| Execution | Typed envelopes and fixed approval-gated MCP operations |
| Data quality | Versioned vector contracts and deterministic dirty-data benchmarks |
| GIS operations | Controlled vector and raster inspection/conversion and PostGIS loading |
| PostGIS lifecycle | Bounded inspection through independently verified promotion and rollback |
| Evidence | Redacted traces, reports, lineage, and digest-addressed records |
| Operational history | Typed events with stable run, task, and correlation identities |
| Critic | Separate read-only assessment that cannot alter authoritative status |
| Release | Immutable workflow packages with independent inspection |
| Reproducibility | Approval-gated Snakemake export, validation, dry-run, and replay |
| Generated extensions | Isolated Builder candidates, offline tests, promotion, and activation verification |

## Pilot demonstration

Checkpoint 14F connects proposal, deterministic compilation, human approval,
PostGIS execution, validation, operational history, Critic evidence,
authoritative release inspection, and Snakemake replay.

Its first gate is read-only and deterministic:

```bash
make checkpoint14f-readiness
```

It verifies a clean vector control, an invalid-geometry case, the contract
identity, and the exact workflow-input digest. It does not call a model, create
approval, execute a workflow, modify data, or create a release. See the
[Checkpoint 14F demonstration](demonstrations/checkpoint14f/README.md) for the
complete walkthrough.

## Quick start

### Start the local product

After installing the Python and pinned frontend dependencies, start the
loopback API and interface together:

```bash
make interface-start
```

The launcher checks the local environment, reports optional Ollama, Docker,
PostGIS, and GeoServer availability, then opens the frontend at
`http://127.0.0.1:5173`. One `Ctrl+C` stops both processes. It never installs
packages or starts containers.

Execution authority is disabled by default. For a reviewed local workflow that
needs the existing bounded write tools, use the deliberate opt-in:

```bash
bash scripts/start_actioncharter.sh --enable-write-tools
```

This does not enable overwrite, arbitrary SQL, arbitrary Python, shell access,
Docker control, or Snakemake replay. Run `make interface-check` for diagnostics
without starting either service. Ubuntu 24.04 on WSL2 is the reference local
development environment; the CLI remains available for automation and repair.

Validation remains intentionally separated by responsibility:

```bash
make test                 # Python/offline suite
make interface-validate   # frontend typecheck and production build
make validate             # Python, frontend, launcher and Compose checks
```

The frontend does not yet declare a `pnpm test` script because it has no
component-test runner. A real frontend test command will be added with the
first component and API-client tests rather than using the name for a build.

### Requirements

- Linux or WSL2;
- Python 3.11 or newer;
- Docker Engine with Compose v2 for containerized boundaries;
- optional local Ollama-compatible endpoint for Planner, Builder, and Critic;
- optional externally managed PostGIS for database workflows.

The primary development environment is **Ubuntu 24.04 LTS under WSL2**. Hosted
CI exercises the offline suite and container contracts on Ubuntu. Other modern
Linux environments are expected to work but are not tested to the same level.

Offline unit tests and read-only fixture checks do not require model or
database credentials.

### Install and test

```bash
git clone https://github.com/wanggiya/action-charter.git
cd action-charter
make install
make test
```

Run two read-only checks:

```bash
make inspect
make checkpoint14f-readiness
```

Validate and build the container topology:

```bash
make config
make build
```

Copy `.env.example` to `.env` only when configuring local services. Never
commit `.env`, credentials, private datasets, or generated operational
evidence.

### Remote development

The repository includes a GitHub Codespaces development-container
configuration for remote Linux development from a browser, including an
Android phone. Codespaces is the recommended execution environment; native
Termux is limited to editing, Git, and use as an SSH client because it does not
reproduce the project's complete Linux, GIS, Docker Compose, and PostGIS
boundaries.

See [remote development from Android](docs/REMOTE_DEVELOPMENT.md) for setup,
validation, cost-control, security, and recovery guidance.

## Local model configuration

ActionCharter uses an OpenAI-compatible chat-completions interface and is
developed against a shared local Ollama runtime:

```dotenv
MODEL_PROVIDER=ollama
MODEL_BASE_URL=http://host.docker.internal:11434/v1
MODEL_NAME=qwen3:8b
MODEL_TIMEOUT_SECONDS=120
```

The model is used for constrained interpretation and assessment. It does not
receive PostGIS credentials or determine deterministic success.

## Security model

Core invariants include:

- model output is always untrusted input;
- `ENABLE_WRITE_TOOLS=false` is the safe default;
- no interface accepts unrestricted shell commands or arbitrary SQL;
- approvals bind exact artifact identities and explicit consequential steps;
- trusted inputs and registries remain read-only at execution boundaries;
- approved paths must remain under bounded roots and symlinks fail closed;
- credentials are excluded from prompts, results, traces, and reports;
- generated code is tested inside an isolated, network-disabled workspace;
- independent deterministic verification—not model confidence—is the success gate;
- incomplete or inconsistent evidence withholds authoritative status.

Read [SECURITY.md](SECURITY.md) and the
[runtime boundaries](context/RUNTIME_BOUNDARIES.md) before deploying or
extending an execution path.

## Repository guide

| Path | Purpose |
|---|---|
| `src/geoagent_harness/` | Core policies, agents, adapters, workflows, evidence, and release code |
| `agents/` | Trusted role manifests and bounded instructions |
| `context/` | Architecture, status, decisions, catalogs, and trusted context |
| `skill-definitions/` | Declarative trusted skill definitions |
| `skills/` | Installed GIS skill contracts and documentation |
| `benchmarks/` | Deterministic spatial-contract fixtures and expectations |
| `demonstrations/` | Repeatable operator walkthroughs |
| `docs/` | Operator and development guides |
| `.devcontainer/` | Reproducible Codespaces and Dev Container configuration |
| `docker/` and `compose.yaml` | Isolated runtime boundaries |
| `tests/` | Offline policy, schema, security, and workflow tests |

Detailed project records:

- [architecture](context/ARCHITECTURE.md);
- [current implementation status](context/CURRENT_STATUS.md);
- [project summary](context/PROJECT_SUMMARY.md);
- [product roadmap](context/PRODUCT_ROADMAP.md);
- [accepted architectural decisions](context/DECISIONS.jsonl);
- [dataset catalog](context/DATASET_CATALOG.json);
- [skills index](context/SKILLS_INDEX.yaml);
- [changelog](CHANGELOG.md).

## Current scope and non-goals

ActionCharter demonstrates a complete governed PostGIS mutation and rollback
lifecycle, but remains a single-operator alpha rather than a production control
plane. Production authentication, multi-user authorization, strict network
egress enforcement, broader domain adapters, and a guided interface remain
future work.

The project deliberately does not compete by exposing the largest possible
tool catalog. Its focus is the controlled path from uncertain intent to
validated, inspectable, reversible, and reproducible action.

## Compatibility

The public project and Python distribution are named ActionCharter. The
initial `0.9.x` releases retain the `geoagent_harness` Python package and the
`geoagent` and `geoagent-mcp` commands. Existing evidence fields, Compose
service names, and established internal `GeoAgent*` types also remain
compatibility interfaces.

A future namespace migration requires a separately reviewed compatibility
plan; it is not part of the public-project rename.

## Read-only workflow interface

Checkpoint 17A introduces a polished blueprint-style workflow explorer under
[`interface/`](interface/). It visualizes the complete governed path as
connected nodes and exposes node authority, evidence references and execution
status in a read-only inspector. It uses React, TypeScript, Vite, Zod and plain
CSS; the browser cannot approve or execute work.

```bash
cd interface
pnpm install --frozen-lockfile
pnpm dev
```

See [Checkpoint 17A](docs/CHECKPOINT17A.md) for the frontend trust boundary and
the planned progression from visualization to proposal-only graph editing.
Future pandas and external-service capabilities are recorded in the
[capability expansion backlog](context/CAPABILITY_EXPANSION.md).
If `pnpm` starts Windows `CMD.EXE` from WSL, follow the
[WSL frontend setup](docs/WSL_FRONTEND_SETUP.md) before installing packages.

To inspect a real validated workflow without granting browser filesystem
access, generate the bounded local projection described in
[Checkpoint 17B](docs/CHECKPOINT17B.md). Invalid or absent runtime projections
fall back to the sanitized demonstration graph.

Checkpoint 17C adds a bounded run inventory and read-only header selector. See
[Checkpoint 17C](docs/CHECKPOINT17C.md) to export all validated local traces in
one command without remembering individual task IDs.

Checkpoint 17D makes each projected node inspectable. Selecting a node shows a
bounded summary, aggregate observed facts, timing and safe findings derived
from the validated trace—never the original request, tool payloads, secrets or
private paths. See [Checkpoint 17D](docs/CHECKPOINT17D.md).

Checkpoint 17E adds expandable evidence cards to relevant nodes. These display
the important verified metadata—category, state, safe reference, digest and
bounded facts—without turning the browser into a raw trace or filesystem
viewer. See [Checkpoint 17E](docs/CHECKPOINT17E.md).

Checkpoint 17F replaces the fixed tool placeholder with actual recorded
operation nodes and dynamically sizes both graph orientations. See
[Checkpoint 17F](docs/CHECKPOINT17F.md) and the complete
[interface product scope](docs/INTERFACE_PRODUCT_SCOPE.md).

Checkpoint 17G establishes the semantic visual system: process category and
performer are independent, related work appears in ownership frames, and graph,
minimap and inspector share a restrained professional palette. See
[Checkpoint 17G](docs/CHECKPOINT17G.md).

Checkpoint 17H separates agent/control interaction from tool/data flow using a
typed edge contract and distinct graph lanes. User Request and referenced
Input Data enter the Planner separately; hollow triangular sockets identify
agent interaction, circular sockets identify data/tool relationships, and
Executor connects only to the first recorded operation. Operations then follow
trace order and only the final operation connects to validation.
Sockets use left/right sides horizontally and top/bottom sides vertically.
After updating the projection contract, re-export ignored runtime JSON files;
catalog-selected runs now report stale or invalid projections instead of
silently displaying the same demonstration graph. See
[Checkpoint 17H](docs/CHECKPOINT17H.md).

The projection includes only components supported by each trace. Snakemake is
visible when its runtime or operation is explicitly recorded; older replay
evidence without engine metadata cannot be inferred from a task name.

Checkpoint 17I adds a separate proposal-editing foundation. Evidence view
remains immutable, while Proposal edit creates a browser-local draft whose
nodes can be added, renamed, deleted and repositioned. The draft cannot approve
or execute work and is discarded on exit. See
[Checkpoint 17I](docs/CHECKPOINT17I.md).

Checkpoint 17J makes the proposal topology editable. From the selected block,
an operator can create a compatible typed connection, inspect its direction,
or delete it. A connection can also be drawn directly by holding an output
socket, dragging the live wire and releasing it on a compatible empty input.
Duplicate, incompatible, occupied, self-referential and cyclic connections are
rejected locally. Filled sockets are connected and hollow sockets remain
available. Performer assignment uses bounded project roles. The proposal is
still browser-local and cannot execute or persist.
See [Checkpoint 17J](docs/CHECKPOINT17J.md).

Checkpoint 17K connects the interface to the repository's existing trusted
recipe templates. Export `context/RECIPE_TEMPLATES.yaml` through the existing
`recipe-template-catalog` CLI command, then select a template and fill its
required parameters in the Inspector. The interface renders its declared step
graph and can download a validated, non-executable proposal accepted by the
existing proposal compiler. See [Checkpoint 17K](docs/CHECKPOINT17K.md).

For template input and output fields, the interface accepts either a filename
or an explicit path. Filename-only inputs resolve under `data/input`, and
filename-only outputs resolve under `data/output`; the compiled recipe displays
the canonical path before approval. Explicit safe relative paths and the CLI's
path/root options remain supported. See
[Checkpoint 17AM](docs/CHECKPOINT17AM.md).

The completed interface is intended to operate the full governed lifecycle
without requiring routine command-line use. The CLI remains supported for
automation, CI, debugging and expert workflows; both surfaces will use the same
backend contracts and authority boundaries.

## Contributing

Contributions are welcome when they preserve ActionCharter's trust boundaries.
Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report
vulnerabilities through the private process in [SECURITY.md](SECURITY.md), not
through a public issue.

## Citation and license

ActionCharter was created by **Jay Qi**. Citation metadata is available in
[CITATION.cff](CITATION.cff).

Copyright 2026 Jay Qi. Licensed under the Apache License, Version 2.0. See
[LICENSE](LICENSE) and [NOTICE](NOTICE).

The **Flow graph** source selector can load local saved plans, saved recipes, and durable runs through the interface API. Use **Refresh** to update the list; exported traces remain a separate, manually prepared source. Graph selection only inspects evidence and does not approve or run work. See `docs/CHECKPOINT20.md`.

Checkpoint 20 adds a read-only flow graph of verified plan, recipe, decision, execution and evidence relationships. A missing, expired or mismatched record does not gain a connection. Recorded output hashes are historical evidence rather than a fresh check of the physical file. See [Checkpoint 20](docs/CHECKPOINT20.md) for the relationship rules and acceptance steps.

Checkpoint 21A adds explicit task-event recording and a deterministic context view via `record-task-event` and `build-task-context`. It does not yet connect the interface actions to one task automatically. See [Checkpoint 21](docs/CHECKPOINT21.md).

Checkpoint 21B exposes explicit task-event recording and checked context inspection through the local interface API. It does not yet connect task history to the visible Planner and Run journey; see [Checkpoint 21](docs/CHECKPOINT21.md).

Checkpoint 21C records new Planner sessions under one task ID and previews checked task context in the graph inspector. Existing saved artifacts are not assigned to a task without evidence, and task-history decision notes do not authorize execution. See [Checkpoint 21](docs/CHECKPOINT21.md).

The remaining product sequence is [task identity → reviewed agent intent → task-centered interface → tabular tools → governed capability growth → evaluation](context/AGENT_INTERFACE_SEQUENCE.md).

Task history can now be reopened from **Task history → Saved tasks** in the graph inspector. Each listed history has its event chain checked; source references are available under each context entry. This inspects history only and does not resume approval or execution. See `docs/CHECKPOINT21.md`.

Checkpoint 21E: explicit task artifact references can be independently checked against bounded current evidence bytes through a read-only API. This verifies file identity only, not semantic relationships or authority. Five history tests passed locally; full WSL suite pending. See `docs/CHECKPOINT21E.md`.

Checkpoint 21F adds read-only recorded plan/approval relationship inspection with authoritative schemas and existing approval verification. Six focused task tests passed; no execution authority is granted. Automatic reference attachment and recipe/outcome checks remain open. See `docs/CHECKPOINT21F.md`.

Checkpoint 21G links actual plan saves and approval/denial records to the active task with file-byte references. Completed artifact operations survive visible history failures. Seven focused task tests and frontend build passed locally; full WSL suite pending. See `docs/CHECKPOINT21G.md`. Recipe/outcome links remain open.

Checkpoint 21H corrects selected-skill Planner prompts, removes unconditional unrelated PostGIS instructions, includes conversion arguments, and allows one fully revalidated policy correction. 54 focused tests passed; full WSL suite and live-model check pending. See `docs/CHECKPOINT21H.md`.

Checkpoint 21I records an exact task reference after storing a reviewed Planner-derived recipe and surfaces history failures without undoing storage. 23 focused tests and frontend build passed locally; full API suite pending. Recipe semantic relationships and outcomes remain open. See `docs/CHECKPOINT21I.md`.

Checkpoint 21J checks full recipe definitions against their recorded source plans using the same backend mapping as compilation. 24 focused tests passed; full API suite pending. Outcome links remain open. Task-history discoverability is explicitly deferred to task-centered UI redesign. See `docs/CHECKPOINT21J.md`.

Checkpoint 21K links task-derived completed run result/evidence references and checks exact recorded outcome relationships without revalidating live outputs or granting authority. 25 focused tests and frontend build passed locally; full WSL suite pending. Interrupted attempts and recovery acceptance remain open. See `docs/CHECKPOINT21K.md`.

Checkpoint 21L records completed-run recipe approval references, verifies their current recipe policy/scope/expiry relationships, and separates historical identity from current permission. 26 focused tests and frontend build passed locally; full WSL API suite and recovery acceptance remain. See `docs/CHECKPOINT21L.md`.

Checkpoint 21M adds attempt/recovery task notes and a closeout acceptance checklist. 27 focused tests passed locally; full WSL API suite and deliberate end-to-end recovery acceptance remain pending. Advanced relationship graph direction is documented. Checkpoint 21 implementation is delivered for acceptance, not yet declared complete. See `docs/CHECKPOINT21M.md`.


## Checkpoint 22C — Intent reasoning

CLI `reason-task-intent` now consumes a rechecked context review and proposes intent or clarification without creating a plan or granting authority. Context is checked again after inference. See `docs/CHECKPOINT22C.md` for validation. API/UI integration and reviewed Intent-to-Planner handoff remain next.


## Checkpoint 22D — Intent clarification API

Explicit clarification answers are available through `reason-task-intent --clarification` and `POST /api/v1/intent/reason`. Each stateless call checks reviewed history, proposes intent or questions and grants no work authority. Current-task prompt improved after live model feedback. See `docs/CHECKPOINT22D.md`; UI and reviewed Planner handoff follow.


## Checkpoint 22E — resolved Intent review

Intent may make one fresh re-evaluation when supplied answers leave a clarification response. Unresolved output stays blocked. CLI proposal inspection and explicit digest review now store resolved reasoning under ignored `reviewed-intents/`; reopening rechecks sources and record bytes. This grants no work authority. See `docs/CHECKPOINT22E.md`. Actual Planner handoff and review API/UI follow.


## Checkpoint 22F — reviewed Planner handoff

CLI `plan-reviewed-intent` now produces an unsaved plan from a rechecked intent review, initially bounded to one exact `inspect_vector` input and metadata output scope. It rejects broader capabilities and never executes or infers approval. See `docs/CHECKPOINT22F.md`. Review/handoff API, conversation UI and broader supported envelopes follow.


Checkpoint 22F preserves a Planner-added approval gate on an otherwise exact read-only plan. `additional_human_approval_required` reports it; reviewed intent never supplies that approval.


## Checkpoint 22G — Intent review/handoff API

The local API now supports checked proposal inspection, exact resolved-intent review, rechecked reopening and bounded Planner handoff through the same CLI services. No work approval or execution is granted. See `docs/CHECKPOINT22G.md`; conversation UI beside the graph follows.


## Checkpoint 22H — Context & intent interface

The new **Context & intent** panel uses explicitly selected history, checked review storage, structured reasoning and the bounded Planner handoff. It sits beside the graph on wide screens and above it on narrow screens. No plan is saved or executed. See `docs/CHECKPOINT22H.md` for the full frontend test flow. Saved-review recovery and integration with the existing governed run flow follow.


## Reviewed intent to saved plan

Context & intent now supports explicit plan review/storage and Continue in Plan. Storage retains intent/context provenance and does not approve work. See docs/CHECKPOINT22I.md; only inspect_vector metadata is supported by this handoff.


## Checkpoint 22J — saved-review recovery

Context & intent can now reopen saved reviews after refresh without model calls. Expand Resume a saved context or intent review and load the source-checked inventory. Stale reviews remain blocked. See docs/CHECKPOINT22J.md.


## Checkpoint 22K — focused task stages

Context & intent now shows one stage at a time: Context → Task → Plan → Continue. Completed details remain accessible; successful review/storage advances the view. Required approval decisions are unchanged. See docs/CHECKPOINT22K.md.


## Checkpoint 22L — fresh tasks

New tasks can choose Start without history in Context & intent. Historical context is optional; Intent review and exact plan/work-approval rules remain. The CLI reason-task-intent command can omit --review-filename. See docs/CHECKPOINT22L.md.


## Checkpoint 22M — inspection envelopes

The reviewed-intent bridge supports explicitly selected vector or raster metadata inspection. In Plan, choose Vector (feature count, fields, CRS) or Raster (width, height, band count, CRS). Planning/storage does not inspect or execute data. See docs/CHECKPOINT22M.md.


## Checkpoint 22N and Checkpoint 23 scope

Checkpoint 22 integration acceptance covers fresh/history-backed vector/raster metadata plans, real decision verification and recipe storage. Saved-plan continuation now displays a readable reviewed objective. See docs/CHECKPOINT22N.md. Checkpoint 23 will focus on a clearer task/conversation and governed run journey; see docs/CHECKPOINT23_PLAN.md.
