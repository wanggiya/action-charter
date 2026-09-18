# Current Status

Last updated: 2026-09-16

## Project summary

ActionCharter is a CLI-first, local-first governed execution harness for AI
agents using professional tools. Its current geospatial reference
implementation includes a complete, independently verified PostGIS promotion
and rollback lifecycle plus a live-validated, approval-gated GeoServer
publication boundary.

The current system combines:

* a shared local Ollama/Qwen model runtime;
* isolated Planner, Executor and Critic roles;
* strict Pydantic schemas;
* deterministic planning and recipe policies;
* append-only SHA-256-bound human approvals;
* an internal approval-gated MCP GIS service;
* controlled GeoPandas, GDAL and PostGIS operations;
* deterministic post-write validation;
* immutable recipes and execution records;
* durable lineage, evidence, traces and reports;
* immutable Critic records and authoritative release packages;
* natural-language recipe proposals;
* guided operator review and explicit recipe storage;
* prominent append-only authority outcomes and independent recipe-approval verification;
* exact, redacted execution-envelope preview with execution authority withheld;
* separately confirmed execution of an exact preview through the existing governed recipe runner;
* single-active-gate interface presentation with explicit optional recipe parameters;
* bounded execution-outcome and validation-fact inspection inside the completed-run panel;
* bounded PostGIS inspection, comparison and deterministic change assessment;
* digest-bound promotion and rollback planning and approval;
* serializable promotion and rollback execution; and
* independent post-promotion and post-rollback state verification.

The model is used to interpret requests and produce constrained proposals. It does not determine execution success, approve writes, call GIS tools or directly modify artifacts.

Final success is derived only from deterministic validation.

The PostGIS reference lifecycle is complete through Checkpoint 15K. The latest
full offline regression, including GeoServer Checkpoints 16A and 16B, completed
with **1,172 passing tests**.

Checkpoint 16 is now the restricted GeoServer publication prototype for the
existing local Docker environment. Checkpoint 16A establishes its first
boundary: bounded, GET-only inspection of one exact allowlisted workspace,
datastore, feature type, and published layer. It accepts no arbitrary REST path
and grants no publication, update, deletion, approval, or credential authority.

Checkpoint 16B implements the first approval-gated GeoServer mutation for an
already-configured layer. Planning and approval remain non-writing; execution
requires the write gate, exact plan and approval digest confirmation, unchanged
pre-state, and one fixed enable/advertise PUT to the authoritative feature type.
Failed transitions compensate to the inspected pre-state and produce a typed
outcome. A live GeoServer 2.28.0 execution successfully activated the exact
reviewed resource, and independent verification reinspected the target without
trusting the executor's success claim. Creating
workspaces, stores, feature types, styles, or arbitrary REST requests remains
deferred.

## Current workflow

```text
natural-language request
→ local Qwen proposal
→ strict proposal-schema validation
→ deterministic readiness assessment
→ trusted recipe compilation
→ operator review or clarification
→ explicit immutable recipe save
→ digest-bound human approval
→ typed execution envelope
→ independent Executor
→ approval-gated internal MCP
→ controlled GIS or PostGIS operation
→ deterministic validation
→ authoritative run result
→ durable evidence and lineage
→ Markdown report and structured trace
→ independent Critic assessment
→ immutable Critic-result record
→ deterministic release assessment
→ immutable authoritative release package
→ independent release inspection
→ deterministic promotion plan and exact approval
→ transactional PostGIS promotion
→ independent promotion verification
→ deterministic rollback plan and separate approval
→ transactional rollback
→ independent rollback verification
```

## Checkpoint 1 — Repository and vector inspection

Status: complete

Implemented:

* Python project and container scaffold;
* Planner, Executor and Critic manifests;
* `inspect_vector` skill;
* trusted input-root enforcement;
* GeoJSON, GeoPackage and Shapefile inspection;
* structured driver, layer, CRS, geometry, feature, field and extent metadata;
* CLI support;
* sample vector data;
* automated tests.

## Checkpoint 2 — Read-only MCP interface

Status: complete

Implemented:

* FastMCP GIS server;
* fixed MCP tool allowlist;
* health check;
* read-only vector inspection;
* plan-only vector-to-PostGIS operation;
* STDIO smoke testing;
* fail-closed write settings;
* no arbitrary shell;
* no unrestricted SQL;
* no raw write tool exposed through MCP.

## Checkpoint 3 — Controlled PostGIS workflow

Status: complete

Implemented:

* connection to an externally managed PostGIS deployment;
* password supplied through a mounted secret file;
* approved target-schema allowlist;
* conservative database identifier validation;
* controlled creation of new PostGIS tables;
* overwrite and destructive replacement blocking;
* deterministic PostGIS validation;
* Markdown report generation;
* structured secret-redacted traces;
* final success derived only from validation.

PostGIS validation covers:

* table existence;
* geometry-column existence;
* row count;
* SRID;
* declared and actual geometry type;
* invalid geometry count;
* null geometry count;
* extent;
* optional expected values.

## Checkpoint 4 — Shared model and Planner Agent

Status: complete

Implemented:

* one shared OpenAI-compatible Ollama endpoint;
* local Qwen model support;
* validated model settings;
* bounded timeout and token settings;
* typed chat requests and model results;
* deterministic task-specific context packs;
* structured Planner plans;
* JSON-only model requests;
* deterministic plan-policy validation;
* rejection of arbitrary shell, unrestricted SQL, destructive operations, unavailable skills and false execution claims;
* independent non-root Planner container;
* no MCP, PostGIS, credentials or filesystem-write access for the Planner.

## Checkpoint 5 — Approval and Executor boundary

Status: complete

### Exact-plan approvals

Implemented:

* canonical plan JSON;
* stable SHA-256 plan identity;
* append-only approval files;
* approved and denied decisions;
* exact approved-step scope;
* approver identity and reason;
* expiration;
* human corrections;
* secret redaction;
* overwrite blocking;
* rejection of changed, expired, denied or incomplete approvals.

### Typed execution handoff

Implemented:

* typed execution envelopes;
* preservation of the original request;
* fixed vector-to-PostGIS workflow order;
* consistent source paths and database targets;
* approved schema enforcement;
* safe identifiers and task IDs;
* fixed tool arguments;
* `execution_performed=false` before execution.

### Internal MCP transport

Implemented:

* MCP Streamable HTTP;
* stateless JSON responses;
* fixed internal `/mcp` endpoint;
* DNS-rebinding host and origin restrictions;
* no published host port;
* internal Docker control network;
* STDIO compatibility for local tests.

### Independent Executor

Implemented:

* non-root read-only Executor container;
* control-network-only connectivity;
* no model access;
* no direct PostGIS access;
* no database credentials;
* no GIS input or output mounts;
* no Docker socket;
* read-only recipe, plan, approval and state mounts;
* fixed approval-gated MCP tool allowlist;
* local and server-side envelope verification.

### Approved validated execution

Implemented:

* real approved vector-to-PostGIS execution;
* deterministic validation after loading;
* validation-derived final status;
* approval identity recorded in traces and reports;
* write tools restored to their disabled default after execution.

## Checkpoint 6 — Critic and evidence review

Status: complete

Implemented:

* bounded trace and report loading;
* trusted evidence roots;
* path-containment checks;
* file-size limits;
* schema validation;
* secret redaction;
* deterministic evidence hashes;
* validation and approval consistency checks;
* incomplete-evidence handling;
* schema-constrained Critic responses;
* deterministic preservation of authoritative status;
* independent read-only Critic container;
* model-network-only Critic access;
* no MCP, PostGIS, shell, SQL or write capabilities for the Critic.

## Checkpoint 7 — CI, failures, state and schema compatibility

Status: complete

### GitHub-hosted CI

Implemented:

* Ubuntu and Python 3.12 offline tests;
* dependency consistency checks;
* independent agent and GIS image builds;
* non-root container checks;
* CLI smoke tests;
* ANSI-portable CLI help tests;
* no Ollama, PostGIS, secrets or write-enabled integration execution in hosted CI.

### Structured failures

Implemented:

* stable failure categories;
* stable failure codes;
* explicit failure stages;
* deterministic CLI exit codes;
* secret-redacted failure records;
* retry dispositions:

  * `never`;
  * `safe_read_only`;
  * `manual_review`;
* operator cancellation handling;
* no automatic retry of uncertain database writes;
* failure evidence in traces and reports.

### Durable workflow state

Implemented:

* schema-validated state records;
* append-only transitions;
* monotonic revisions;
* atomic writes;
* exact plan and approval identity;
* deterministic resume assessment;
* manual-review requirements after a write may have begun;
* read-only state access for the Executor.

Automatic retry and automatic workflow resumption are intentionally not implemented.

### Artifact schema registry

Implemented:

* central artifact-type registry;
* current and writable schema versions;
* supported-read policy;
* migration-required assessment;
* rejection of missing or malformed versions;
* rejection of unsupported older versions;
* rejection of unknown future versions;
* schema checks before Pydantic artifact validation;
* no silent artifact migration.

Only schema version `1.0` currently exists. No real migration function is registered yet.

## Checkpoint 8 — Controlled vector conversion

Status: complete

Implemented:

* conversion planning;
* controlled conversion execution;
* trusted input and output roots;
* GeoJSON and GeoPackage output formats;
* GeoJSON, GeoPackage and Shapefile inputs;
* safe target filenames and layer names;
* source-layer selection;
* overwrite blocking;
* pending-validation execution results;
* deterministic conversion validation.

Validation checks:

* target file is non-empty;
* target driver;
* CRS preservation;
* feature-count preservation;
* field preservation;
* geometry-type preservation;
* null geometry count;
* invalid geometry count;
* extent preservation.

The conversion skill cannot claim final success before deterministic validation passes.

## Checkpoint 8R — Reusable skills and recipes

Status: complete

### Skill registry

Implemented:

* trusted `context/SKILLS_INDEX.yaml`;
* skill IDs and semantic versions;
* implemented and planned states;
* skill kinds;
* access classifications;
* approval requirements;
* validation requirements;
* safe Python entrypoint format;
* verifier references;
* duplicate-ID rejection;
* policy enforcement for read-only, artifact-write, database-write and evidence-write skills.

Registered skills include:

* `inspect_vector`;
* `convert_vector`;
* `load_vector_to_postgis`;
* `validate_postgis_layer`;
* `generate_report`.

### Recipe policy

Implemented:

* typed `WorkflowRecipe`;
* typed recipe steps;
* deterministic dependencies;
* topological ordering;
* output identifiers;
* registry-based skill validation;
* write-step identification;
* approval-required-step identification;
* validation-required-step identification;
* false execution-claim rejection.

### Immutable recipe storage

Implemented:

* canonical recipe JSON;
* stable recipe SHA-256;
* schema validation before storage;
* immutable content-addressed filenames;
* path and size boundaries;
* overwrite rejection.

### Recipe approvals

Implemented:

* append-only recipe approvals;
* exact recipe-digest binding;
* explicit approved write-step IDs;
* approved and denied decisions;
* optional expiration;
* corrections and reasons;
* verification against the current skill registry;
* changed or incomplete approval rejection.

### Approval-gated recipe execution

Implemented:

* typed recipe execution envelopes;
* local Executor verification;
* independent MCP server verification;
* fixed MCP tool allowlist;
* hard-coded step dispatch;
* tested vector inspection and conversion recipe execution;
* deterministic validation after write steps;
* final recipe status derived from step results.

The older fixed vector-to-PostGIS composite workflow remains implemented. Generic recipe dispatch for every PostGIS and reporting skill is not yet complete.

### Durable recipe evidence

Implemented:

* authoritative recipe run results;
* immutable execution records;
* evidence manifests;
* artifact references;
* SHA-256 hashes;
* lineage edges;
* validation summaries;
* deterministic Markdown reports;
* independent Executor verification of persisted results;
* rejection of mismatched run-result digests;
* manual-review failure when evidence persistence fails.

A real acceptance workflow produced:

* a validated GeoPackage output;
* an immutable recipe run result;
* an immutable evidence manifest;
* a deterministic Markdown report;
* matching output and evidence hashes.

## Checkpoint 9 — Natural-language recipe proposals

Status: complete

Implemented:

* typed non-executable `RecipeProposal`;
* fixed allowlisted templates:

  * `inspect_vector`;
  * `inspect_and_convert_vector`;
  * `vector_to_postgis`;
* model-output schema validation;
* strict extra-field rejection;
* unsupported-template rejection;
* false action-claim rejection;
* preservation of the authoritative original request;
* deterministic readiness assessment;
* missing-field detection;
* deterministic clarification questions;
* skill-availability checks;
* target-format consistency checks;
* trusted fixed-template compilation;
* deterministic recipe ID generation;
* recipe-policy validation after compilation;
* bounded proposal loading;
* proposal-only CLI commands.

The model cannot provide:

* arbitrary recipe steps;
* arbitrary skill IDs;
* Python entrypoints;
* shell commands;
* unrestricted SQL;
* approvals;
* execution results.

Real Qwen acceptance demonstrated:

```text
natural-language conversion request
→ constrained proposal
→ strict schema validation
→ deterministic assessment
→ fixed two-step recipe
→ explicit operator save
```

No approval or GIS execution occurred during proposal generation or compilation.

## Checkpoint 10 — Guided operator review

Status: complete

Implemented:

* typed `RecipeOperatorReview`;
* consistent ready and clarification-required states;
* clarification as a valid non-error outcome;
* deterministic human-readable review rendering;
* JSON review output for automation;
* summary output for operators;
* bounded review-file loading;
* path and size enforcement;
* future-schema rejection;
* explicit `save-reviewed-recipe` command;
* deterministic recompilation before saving;
* exact comparison with the reviewed compilation;
* changed-review rejection;
* immutable recipe storage;
* separate approval and execution boundaries.

The operator workflow is:

```text
natural-language request
→ local Qwen proposal
→ Pydantic validation
→ deterministic readiness assessment
→ clarification questions or trusted compilation
→ JSON or summary review
→ separate explicit save command
→ deterministic recompilation and comparison
→ immutable recipe
→ stop before approval
→ stop before execution
```

Real acceptance confirmed:

* Qwen generated a ready vector-conversion review;
* the proposal compiled to `inspect_vector -> convert_vector`;
* deterministic policy marked the conversion step as requiring approval and validation;
* the operator summary displayed the planned steps;
* the separate save command stored exactly one immutable recipe;
* no approval record was created;
* no GIS output was created;
* the complete test suite passed.

## Checkpoint 11 — Deterministic GIS skill scaffolding

Status: complete

GeoAgent can now plan, generate, and structurally validate reusable GIS skill skeletons without modifying the live application or trusted skill registry.

Implemented components:

- `SkillScaffoldRequest`
  - Versioned operator request for one new skill.
  - Uses existing `SkillKind` and `SkillAccess` values.
  - Cannot request execution, registry modification, or immediate promotion.

- `SkillScaffoldPlan`
  - Deterministically derives approval and validation requirements.
  - Rejects duplicate registered skill IDs.
  - Rejects unsafe kind/access combinations.
  - Produces fixed source and test paths.
  - Keeps the proposed registry entry in `planned` status.
  - Does not write files.

- Isolated scaffold generation
  - Writes only beneath a configured scaffold root.
  - Refuses to overwrite an existing bundle.
  - Generates source skeletons, test placeholders, a planned registry fragment, and a manifest.
  - Write-oriented skills receive a validation skeleton.
  - Generated services refuse execution until implemented.
  - Does not edit `src/`, `tests/`, or `context/SKILLS_INDEX.yaml`.

- Shared scaffold contract validation
  - Validates generated file presence and size.
  - Parses Python files without importing them.
  - Detects invalid Python syntax.
  - Rejects subprocess imports, dynamic execution calls, `os.system`, `os.popen`, and `shell=True`.
  - Confirms that the registry fragment remains planned.
  - Confirms that no entrypoint, verifier, promotion, trust claim, registry modification, or execution occurred.

- CLI commands
  - `geoagent plan-skill-scaffold`
  - `geoagent generate-skill-scaffold`
  - `geoagent validate-skill-scaffold`

- Schema registry
  - `skill_scaffold_request`
  - `skill_scaffold_plan`
  - `skill_scaffold_generation_result`
  - `skill_scaffold_contract_result`

Acceptance testing confirmed:

1. A read-only `inspect_raster` scaffold could be planned.
2. Planning produced no files.
3. Generation created an isolated bundle.
4. The bundle contained source and test skeletons.
5. The read-only scaffold contained no write verifier.
6. Contract validation passed without importing generated code.
7. No live skill package was created.
8. The trusted skill registry was unchanged.
9. No implementation, approval, promotion, or execution was claimed.

Important limitation:

The scaffold automates boilerplate, policy metadata, file layout, and baseline contract testing. It does not invent or trust a new GIS algorithm. A new primitive GIS operation still requires implementation, deterministic validation where applicable, focused tests, operator review, and explicit promotion to `implemented`.

## Checkpoint 12 — Approval-gated Snakemake export and replay

Status: complete

GeoAgent can now export one exact approved recipe as an immutable Snakemake replay package and execute it without creating a second GIS execution boundary.

Implemented components:

- Deterministic recipe/approval inventory
  - Scans canonical recipe artifacts.
  - Selects only `recipe-approval-*.json` from the shared approval root.
  - Matches recipes and approvals by canonical SHA-256 digest.
  - Re-runs deterministic approval verification.
  - Reports valid, denied, expired, incomplete, unmatched, and missing pairs.
  - Exposes `geoagent list-approved-recipes` for CLI and future frontend use.

- Typed Snakemake export planning
  - Rebuilds the exact recipe execution envelope.
  - Records recipe ID, recipe digest, approval ID, approved steps, and topological order.
  - Stores only plain canonical artifact filenames.
  - Performs no export or execution.

- Immutable export generation
  - Creates a digest-addressed package beneath `snakemake-exports/`.
  - Generates `Snakefile`, `geoagent-replay.json`, and `snakemake-export-manifest.json`.
  - Records SHA-256 digests for the workflow and configuration.
  - Refuses to overwrite an existing export.

- Static export contracts
  - Require the exact canonical Snakefile.
  - Reject changed workflow or configuration digests.
  - Reject `shell:`, subprocess, direct GIS skill calls, and database libraries.
  - Reject changed replay entrypoints, unsafe filenames, conflicting identities, and invalid step scope.
  - Do not run Snakemake or import arbitrary generated code.

- Trusted replay adapter
  - Revalidates the static export contract.
  - Loads exact canonical recipes and approvals from trusted roots.
  - Rebuilds and compares the execution envelope before execution.
  - Invokes only `execute_approved_recipe_via_mcp`.
  - Supports invocation from Snakemake's active asyncio runtime through a bounded single-worker bridge.
  - Writes a completion marker only after validated success.
  - Records durable run-result, evidence, and report references.

- Isolated workflow runner
  - Uses Python 3.12 and Snakemake 9.25.
  - Runs as a named non-root user matching the WSL host UID/GID.
  - Uses only the internal control network.
  - Has no model access, GIS libraries, PostGIS credentials, or direct GIS output mount.
  - Receives read-only Executor manifest, context, approvals, and recipes.
  - Receives one writable Snakemake export mount.
  - Uses bounded temporary cache/config locations under `/tmp`.
  - Keeps the container root filesystem read-only.

- CLI commands
  - `geoagent list-approved-recipes`
  - `geoagent plan-snakemake-export`
  - `geoagent export-approved-recipe-snakemake`
  - `geoagent validate-snakemake-export`

Acceptance results:

1. Five existing exact recipe/approval pairs were discovered deterministically.
2. A canonical approved recipe was exported.
3. Static contract validation passed.
4. Snakemake dry-run produced only `replay_approved_recipe` and `all`.
5. Dry-run performed no execution and created no completion marker.
6. A fresh recipe with a new output path was saved and approved.
7. The real Snakemake replay passed through Executor and MCP.
8. Vector conversion and deterministic validation succeeded.
9. Durable run result, evidence, report, and completion records were written.
10. Completion digests matched the stored evidence artifacts.
11. MCP writes were restored to disabled after execution.
12. Re-running the completed workflow was a no-op.

Security boundary:

Snakemake schedules one trusted composite replay. It does not execute recipe steps individually, invoke raw GIS commands, call shell rules, connect to PostGIS, or bypass approval verification.

## Agent boundaries

### Planner

The Planner:

* uses the shared local model;
* reads trusted context and manifests;
* creates plans and non-executable proposals;
* has no MCP tools;
* has no PostGIS access;
* has no shell or unrestricted SQL;
* has no filesystem or database-write authority.

### Executor

The Executor:

* has no model dependency;
* reads exact recipes, plans and approvals;
* constructs typed envelopes;
* calls only fixed approval-gated MCP tools;
* has no database credentials;
* cannot directly write GIS artifacts;
* validates returned identities, statuses and digests.

### Critic

The Critic:

* reads trusted traces and reports;
* uses the shared local model;
* has no MCP or PostGIS access;
* cannot execute or change authoritative status;
* cannot claim success without supporting evidence.

### MCP GIS service

The MCP GIS container:

* runs as a non-root user;
* uses a read-only container filesystem;
* reads trusted inputs, recipes, approvals and registry data;
* receives PostGIS credentials through a mounted secret file;
* writes only to explicitly mounted output and evidence roots;
* independently reconstructs and verifies execution requests;
* performs deterministic validation;
* does not expose raw shell or unrestricted SQL.

## Filesystem authorization

| Path                          |    Executor |          MCP GIS | Purpose                             |
| ----------------------------- | ----------: | ---------------: | ----------------------------------- |
| `/workspace/context`          |   read-only |        read-only | Trusted registry and policy context |
| `/workspace/workflow-recipes` |   read-only |        read-only | Immutable validated recipes         |
| `/workspace/approvals`        |   read-only |        read-only | Digest-bound approvals              |
| `/workspace/plans`            |   read-only |        read-only | Validated plans                     |
| `/workspace/data/input`       | unavailable |        read-only | Approved GIS inputs                 |
| `/workspace/data/output`      | unavailable |       read/write | Controlled GIS outputs              |
| `/workspace/recipe-runs`      | unavailable |       read/write | Authoritative run results           |
| `/workspace/recipe-evidence`  | unavailable |       read/write | Hashed lineage and QA evidence      |
| `/workspace/traces`           | unavailable |       read/write | Structured execution traces         |
| `/workspace/reports`          | unavailable |       read/write | Deterministic reports               |
| PostGIS credentials           | unavailable | secret file only | Controlled database access          |

Runtime-writable host directories use the non-root GIS container group, currently GID `10001`, with setgid permissions where configured.

`ENABLE_WRITE_TOOLS=false` remains the persistent safe default.

## Skills and recipes

A skill is a trusted primitive GIS capability implemented and tested in code.

A recipe is a declarative composition of registered skills containing:

* step IDs;
* skill IDs;
* dependencies;
* typed or policy-validated arguments;
* output identifiers;
* execution and validation state.

Recipes make new workflows low-code or no-code when the required primitive skills already exist.

Examples include:

* inspecting different datasets;
* converting different approved files;
* selecting source or target layers;
* changing safe output paths;
* changing approved PostGIS targets;
* combining inspection, transformation, validation and reporting;
* replaying previously validated processes.

Recipes do not safely implement entirely new GIS algorithms. A new primitive capability still requires:

* implementation code;
* strict schemas;
* path and permission policy;
* an approval classification;
* deterministic validation;
* registry metadata;
* automated tests.

The planned skill scaffolder will generate most of this repetitive structure, but generated implementations will not become trusted automatically.

## Testing and CI

Implemented:

* extensive offline pytest coverage;
* Python 3.12 GitHub-hosted tests;
* dependency consistency checks;
* import-boundary tests;
* security-policy tests;
* schema-registry tests;
* CLI tests;
* ANSI- and terminal-width-independent help tests;
* non-root container builds;
* agent and GIS image smoke tests.

Hosted CI remains secret-free and does not run:

* Ollama integration;
* PostGIS integration;
* approval-gated writes;
* laptop-dependent container workflows.

Those acceptance tests run locally.

## Current limitations

* Raster inspection, controlled GeoTIFF reprojection, deterministic validation and artifact lineage are implemented; additional raster operations such as clipping, mosaicking, raster algebra and format expansion are not yet implemented.
* Declarative skill definitions support fixed trusted profiles and adapters; arbitrary generated GIS algorithms cannot become trusted without implementation review and isolated tests.
* Purely read-only recipes can be proposed, assessed, compiled and saved, but the current recipe execution envelope remains approval-gated and therefore does not execute recipes with zero approval-required steps.
* Generic recipe dispatch does not support every registered skill.
* The PostGIS recipe template needs complete generic dispatcher integration.
* Automatic retry and automatic workflow resumption are not implemented.
* No real artifact migration function exists.
* No task queue or scheduler exists.
* Existing database tables and artifacts cannot be overwritten.
* Deletion is unavailable.
* Critic assessments can be persisted as separate immutable evidence, but remain non-authoritative and cannot alter deterministic status.
* PostGIS and Ollama are externally managed.
* No production authentication exists.
* No multi-user deployment exists.
* Network egress is not controlled through a dedicated proxy.
* Real integration tests depend on the local development environment.
* No production remote orchestrator exists.

## Completed extension checkpoints

### Checkpoint 11 — Skill scaffolding and contracts

Completed:

* deterministic planning of standard GIS skill packages;
* isolated and non-overwriting scaffold generation;
* typed schema, policy, service and verifier placeholders;
* planned registry fragments with no executable entrypoint;
* static contract validation without importing generated code;
* explicit separation between generated scaffolds and trusted implementations.

### Checkpoint 12 — Snakemake export and replay

Completed:

* immutable digest-addressed Snakemake exports for exact approved recipes;
* a canonical shell-free Snakefile;
* isolated non-root workflow-runner container;
* independent recipe, approval, digest and step-scope verification;
* replay through the existing Executor-to-MCP boundary;
* completion markers written only after validated execution and durable evidence persistence;
* trusted recipe-and-approval inventory discovery.

### Checkpoint 13 — Declarative Skill SDK and raster inspection

Completed:

* versioned declarative `.skill.yaml` definitions;
* fixed permission profiles and a trusted adapter catalog;
* deterministic policy assessment;
* immutable digest-addressed contract bundles;
* generic untrusted scaffold generation;
* static contract validation without execution;
* trusted adapter materialization into isolated candidates;
* isolated, non-root and network-disabled candidate testing;
* digest-bound JSON test evidence;
* deterministic promotion assessment and dry-run planning;
* explicit transactional promotion with registry mutation last;
* rollback of newly copied files if promotion fails;
* promotion of `inspect_raster` as an implemented read-only skill;
* deterministic GeoTIFF fixture generation;
* safe Rasterio-based metadata inspection;
* containment and symlink rejection;
* direct `inspect-raster` CLI integration;
* hard-coded recipe dispatcher allowlisting;
* constrained model proposal and deterministic recipe compilation support;
* 682 passing automated tests.

### Checkpoint 13L — Container contract CI

Completed:

* independently build the agent, GIS-tools and skill-test-runner images;
* verify every image uses the non-root `geoagent` user;
* load Planner, Executor and Critic manifests inside the real agent image;
* run vector inspection inside the real GIS image;
* run raster inspection inside the real GIS image;
* verify raster path traversal fails through a controlled policy error;
* run container contracts with no network, a read-only root filesystem, all Linux capabilities dropped and `no-new-privileges`;
* verify the skill-test runner fails closed when no valid candidate bundle is mounted;
* validate the complete Docker Compose configuration;
* keep hosted CI independent of Ollama, PostGIS, credentials and write-enabled integration execution.

### Checkpoint 14 — Controlled raster transformation

Completed:

* added a trusted Rasterio conversion and reprojection adapter;
* added fixed CRS, resampling, containment, symlink and overwrite policy;
* preserved bands, data types and nodata metadata;
* wrote new GeoTIFFs through temporary files without overwrite;
* withheld final success until independent validation;
* extended trusted adapter definitions with fixed verifier identities;
* required write-capable profiles to provide trusted verifiers;
* generated, tested and explicitly promoted `convert_raster`;
* added direct plan, execution and validation CLI commands;
* added constrained `inspect_and_convert_raster` recipe compilation;
* required exact approval for the raster write step;
* added hard-coded dispatcher and verifier bindings;
* executed and validated a real raster recipe;
* produced SHA-256 input/output evidence and lineage;
* persisted immutable recipe results, evidence and reports;
* verified conversion planning inside the non-root GIS container.

### Checkpoint 14A — Declarative recipe catalog

Completed:

* added one bounded, data-only `RECIPE_TEMPLATES.yaml` catalog;
* added strict catalog, template, argument and step-graph schemas;
* added fixed parameter profiles and assessment-policy identifiers;
* rejected catalog symlinks, invalid identifiers, duplicate IDs, unsafe dependencies and inconsistent skill graphs;
* replaced the synchronized Python template registry with a catalog-backed interface;
* preserved strict Pydantic parameter validation;
* generated the proposal-only model prompt from trusted catalog metadata;
* replaced recipe-specific compilation with deterministic catalog step compilation;
* retained legacy parity checks for the original five templates during migration;
* proved YAML-only addition of a template that reuses trusted profiles, policies and implemented skills;
* preserved recipe policy, approval, dispatcher, validation, evidence and Snakemake boundaries;
* added the read-only `recipe-template-catalog` CLI command;
* fixed the Planner working directory to its read-only catalog mount;
* added hosted container validation with no network, secrets, data or write mounts;
* passed 720 automated tests.

A catalog entry cannot provide executable code, imports, entrypoints, verifiers, shell commands, SQL, approvals, permission grants or execution claims. New executable GIS behavior still requires a separately implemented, tested and promoted trusted skill.

## Historical extension roadmap

The checkpoint proposals in this section record the path considered before the
PostGIS lifecycle was completed. They are retained for design history and do
not define the next checkpoint. Current planning is intentionally paused until
the completed 15A–15K architecture and product priorities are reviewed.

The detailed product direction, presentation scope and prototype-release definition are maintained in `context/PRODUCT_ROADMAP.md`.

### Checkpoint 14B — Isolated Builder agent

Completed second slice:

* added deterministic JSON-only Builder prompt construction;
* embedded only the typed, secret-redacted Builder request and required proposal schema;
* invoked the existing shared OpenAI-compatible Ollama client at temperature zero;
* rejected non-JSON, fenced, non-object and schema-invalid responses;
* deterministically required exact task, artifact-path and artifact-kind correspondence;
* rejected model claims of permissions, writes, tools, testing, validation, trust, promotion or execution;
* added proposal-only runtime wiring without CLI, container or filesystem authority.

Completed third slice:

* added a dedicated Builder Compose service using the hardened non-root agent image;
* connected the Builder only to the model network;
* mounted only `agents/builder/manifest.yaml` through its read-only manifest directory;
* inherited a read-only root filesystem, capability dropping, `no-new-privileges` and bounded temporary storage;
* withheld MCP, PostGIS, secrets, context, source, data, evidence, approval, output and candidate-workspace mounts;
* limited the initial container command to static Builder-manifest validation;
* added deterministic container-policy tests independent of Ollama.

Completed fourth slice:

* added one checked-in typed Builder request fixture;
* added a bounded read-only request loader;
* rejected missing, empty, oversized, symlinked, nested, non-regular, malformed and schema-invalid request files;
* added the `builder-propose` CLI command;
* emitted validated proposal results only through standard output;
* used structured model-failure exit codes;
* mounted only the exact Builder request file and Builder manifest read-only;
* executed a live proposal through the isolated Builder container without adding a candidate workspace or write mount.

Completed fifth slice:

* added bounded storage validation for operator-saved Builder generation results;
* restricted generation files to direct, non-symlinked files under an approved root;
* rejected oversized, malformed, schema-invalid or policy-inconsistent generations;
* bound accepted generations to canonical SHA-256 digests;
* added a trusted operator-side candidate materializer outside the Builder container;
* created isolated digest-addressed candidate directories atomically;
* wrote only the exact schema-declared files plus a deterministic candidate manifest;
* rejected path escapes, symlinks and existing candidate destinations;
* verified source-generation stability and calculated the final candidate-tree digest;
* added offline storage, materialization and CLI tests;
* kept all candidates explicitly untested, unvalidated, untrusted, unpromoted and unexecuted.

Completed sixth slice:

* added deterministic static inspection of isolated Builder candidates;
* required exact containment directly beneath the approved candidate root;
* rejected symlinked roots, candidates, directories and files;
* validated the candidate manifest through strict typed schemas;
* bound the directory identity to the task ID and generation SHA-256;
* required the actual and declared candidate file sets to match exactly;
* verified every declared file digest;
* parsed supported Python, JSON and YAML syntax without importing or executing candidate content;
* verified stable candidate-tree digests before and after inspection;
* added a read-only candidate-inspection CLI and offline failure tests;
* kept inspection separate from testing, validation, trust and promotion.

Completed seventh slice:

* extended the existing network-disabled skill-test runner with a separate Builder-candidate mode;
* retained the existing declarative-skill candidate contract;
* required exactly one supported candidate manifest;
* validated Builder candidate identity through `BUILDER_CANDIDATE.json`;
* mounted the exact candidate read-only with no network;
* extended only bounded candidate package paths needed for isolated pytest collection;
* emitted typed task, generation and candidate-tree test evidence;
* recorded deterministic pytest outcome counts;
* verified identical candidate-tree digests before and after testing;
* added bounded and symlink-rejecting Builder evidence storage;
* reran static inspection before assessing test evidence;
* required exact task, generation and candidate digest binding;
* added CLI and Make targets for test execution, evidence persistence and assessment;
* passed one real isolated container test;
* preserved false deterministic-validation, trust, promotion and GIS-execution claims.

Completed eighth slice:

* assembled a typed human-review package from the exact generation, candidate manifest, inspection and isolated-test assessment;
* required matching task, model, generation and candidate-tree identities;
* verified proposed content against the materialized manifest;
* represented candidate paths only as proposed, unapproved destinations;
* serialized the complete review package deterministically;
* persisted it in an immutable digest-addressed directory;
* used temporary staging and atomic finalization;
* rejected symlinked review roots and existing packages;
* verified stable candidate content before and during persistence;
* added a CLI command for review assembly and storage;
* created and digest-verified one real review package;
* kept human review, approval, trusted writes, promotion and execution explicitly false.

Completed ninth slice:

* added typed approved and rejected human decisions;
* bound every decision to an exact immutable review-package digest;
* required decision ID, reviewer identity, timezone-aware timestamp and rationale;
* limited approved paths to reviewed candidate paths;
* prohibited rejected decisions from approving paths or authorizing promotion planning;
* securely reloaded and rehashed canonical review packages;
* persisted decisions separately as canonical JSON;
* used immutable digest-addressed decision directories;
* used temporary staging and atomic finalization;
* reverified review identity before and during persistence;
* added a CLI command for recording human decisions;
* recorded and digest-verified one real approved decision;
* preserved false file-copy, registry-modification, trust, promotion and execution claims.

Completed tenth slice:

* securely loaded immutable Builder human-decision records;
* required canonical JSON, approved-root containment and digest-addressed directories;
* rejected symlinked, oversized, malformed, noncanonical and relocated decisions;
* added a typed non-writing promotion plan;
* required an approved decision with promotion-planning authorization;
* reverified the immutable review and exact candidate;
* bound plans to review, decision, generation and candidate-tree digests;
* selected only explicitly approved reviewed paths;
* verified candidate source files against manifest digests;
* rejected source or destination escapes, symlinks, missing sources and existing destinations;
* rehashed candidates after planning;
* added a read-only promotion-planning CLI command;
* successfully planned two real fixture destinations without creating them;
* preserved false copying, registry modification, trust, promotion and execution claims.

Completed eleventh slice:

* added canonical serialization and SHA-256 identity for Builder promotion plans;
* persisted plans as immutable `PLAN.json` files in digest-addressed directories;
* reran promotion planning before and during persistence;
* rejected plans that changed after their initial calculation;
* used temporary staging and atomic directory finalization;
* refused existing promotion-plan destinations instead of overwriting evidence;
* added secure loading of canonical promotion plans;
* rejected symlinked roots, directories and files;
* rejected missing, empty, oversized, malformed, noncanonical and schema-invalid plans;
* required promotion-plan directory names to match the task ID and exact content digest;
* added the `create-builder-promotion-plan` CLI command;
* created and verified one real immutable promotion plan;
* confirmed that repeated persistence of the same plan fails closed;
* preserved false file-copy, registry-modification, implementation-trust, promotion and execution claims.

Completed twelfth slice:

* added a typed result for atomic immutable-bundle promotion;
* separated bundle promotion from trusted-source activation;
* required exact operator confirmation of the decision ID and promotion-plan SHA-256;
* securely loaded the canonical digest-addressed `PLAN.json`;
* reran the complete decision, review, candidate and destination assessment before staging;
* copied only explicitly approved files into a new isolated bundle;
* preserved approved destination paths beneath the bundle's `files/` directory;
* verified every candidate source and staged file against its approved SHA-256;
* wrote a canonical data-only `PROMOTION.json` manifest;
* repeated promotion planning and staged-file verification immediately before finalization;
* finalized the complete bundle through one atomic directory rename;
* rejected symlinked promotion roots, changed candidates, incorrect confirmations and existing bundles;
* added the `promote-builder-candidate` CLI command;
* left trusted source, tests and registries unchanged;
* imported and executed no promoted code;
* withheld post-promotion verification, activation and implementation-trust claims.

Next Builder slice:

* independently load and inspect one immutable promotion bundle;
* verify the bundle directory identity, manifest and exact promoted file set;
* bind every promoted file to the persisted plan and candidate digests;
* reject symlinks, path escapes, malformed manifests and changed files;
* persist separate immutable post-promotion verification evidence;
* report the verified bundle as eligible for separate activation review;
* keep implementation trust false until explicit activation;
* keep activation, registry modification and execution separate.


### Builder promotion verification completed

The Builder release boundary now supports independent, read-only verification of an immutable promoted bundle.

Completed controls:

- reload and schema-validate the canonical promotion manifest;
- bind the bundle to the exact immutable promotion plan;
- verify task, decision, plan, candidate, and directory identities;
- reject symlinks and unexpected, missing, or changed files;
- verify every promoted file digest twice;
- detect bundle changes during verification;
- persist canonical `VERIFICATION.json` evidence atomically;
- address persisted evidence by its SHA-256 digest;
- refuse replacement of existing verification packages;
- reverify the bundle before and during evidence persistence;
- keep activation, registry modification, implementation trust, and execution false.

The real `builder-runner-integration-v1` promotion bundle passed verification and produced immutable verification evidence. The bundle is eligible for a separate activation review but is not activated or trusted.

### Builder activation review completed

The Builder trust pipeline now includes a separate human activation-review decision after immutable promotion verification.

Completed controls:

- require canonical immutable `VERIFICATION.json` evidence;
- reverify the promoted bundle at decision creation;
- bind the decision to verification, promotion-plan, and candidate-tree digests;
- bind the decision to the exact promotion directory and reviewed file set;
- require a timezone-aware human decision timestamp;
- enforce consistent approved and rejected decision claims;
- authorize only later activation planning after approval;
- persist canonical `ACTIVATION_DECISION.json` atomically;
- use digest-addressed, write-once decision directories;
- reverify the complete decision inputs before and during persistence;
- refuse replacement of an existing decision;
- keep activation, trusted-source copying, registry modification, implementation trust, and execution false.

The real `builder-runner-integration-v1` verified bundle received an approved activation-review decision for activation planning only. No activation or trust transition has occurred.


### Builder activation planning completed

Approved Builder activation-review decisions can now produce immutable, non-writing activation plans.

Completed controls:

- securely reload immutable activation-review decisions;
- require explicit approval and activation-planning authorization;
- reload canonical verification evidence and verify its digest;
- reverify the current promoted bundle before and after planning;
- securely reload the canonical promotion manifest;
- bind task, decision, verification, plan, candidate-tree, directory, and file identities;
- map only the complete verified atomic bundle;
- verify every activation source digest;
- reject missing files, symlinks, path escapes, duplicate mappings, and existing destinations;
- persist canonical `ACTIVATION_PLAN.json` atomically;
- use digest-addressed, write-once activation-plan directories;
- recreate the plan before and during persistence;
- refuse replacement of an existing activation plan;
- keep file copying, activation, registry modification, implementation trust, and execution false.

The real `builder-runner-integration-v1` bundle produced an immutable activation plan for two absent trusted-project destinations. No trusted-source mutation or activation has occurred.

### Transactional Builder activation completed

Approved immutable Builder activation plans can now install exact files into trusted project destinations.

Completed controls:

- require exact activation-decision ID and activation-plan SHA-256 confirmations;
- securely reload canonical `ACTIVATION_PLAN.json`;
- recreate and compare the complete activation plan before mutation;
- refuse existing destinations and path escapes;
- rehash every promoted source before staging;
- stage files beside their final destinations and verify staged digests;
- reverify the complete activation chain after staging;
- atomically rename each staged file into its trusted destination;
- verify every installed file before finalizing evidence;
- roll back files created by a failed partial activation;
- preserve pre-existing trusted files;
- persist canonical `ACTIVATION.json` evidence in a digest-addressed directory;
- keep registry modification, post-activation verification, implementation trust, and execution false.

The real `builder-runner-integration-v1` activation installed its adapter and test with their exact approved SHA-256 values. The activated test and complete repository suite passed, but formal persisted post-activation verification remains a separate pending boundary.

### Builder post-activation verification completed

Activated Builder files can now pass a separate deterministic trust transition.

Completed controls:

- securely load canonical activation and activation-plan evidence;
- reload the immutable activation-review and promotion-verification chain;
- independently reverify the promoted bundle;
- bind activation, plan, decision, verification, candidate-tree, and project identities;
- require exact activation-manifest and plan file mappings;
- verify activation-directory identity and reject unexpected evidence entries;
- reject missing activated files, path escapes, and symlinks;
- hash every installed file twice;
- detect changes to installed files or upstream evidence during verification;
- report `post_activation_verified` and `implementation_trusted` only after all checks pass;
- persist canonical `POST_ACTIVATION_VERIFICATION.json` atomically;
- use digest-addressed, write-once trust-evidence directories;
- repeat verification before and during trust-evidence persistence;
- refuse replacement of existing trust evidence;
- keep registry modification and implementation execution false.

The real `builder-runner-integration-v1` activation passed post-activation verification. Its exact installed adapter and test are now bound to immutable trust evidence with `implementation_trusted: true`.


Planned:

* add a separate Ollama-backed Builder container;
* accept typed implementation requests and bounded candidate proposals;
* provide fixed templates and explicitly selected read-only context;
* materialize only validated paths into an isolated untrusted candidate workspace;
* keep MCP, PostGIS, credentials, approvals, evidence, outputs, trusted registries and trusted source writes unavailable;
* perform static inspection before candidate import;
* run candidate tests without network access;
* record digest-bound test evidence;
* require explicit human review and transactional promotion;
* prevent generated content from granting permissions, selecting arbitrary trusted entrypoints or becoming trusted automatically.

### Checkpoint 14C — Spatial data contracts and dirty-data benchmark

Planned:

* define versioned data-only spatial-data contracts;
* support vector CRS, geometry, schema, nullability, unique-key, count, extent and validity rules;
* add a read-only deterministic contract-assessment skill;
* bind contract identities and results into workflow evidence;
* create dirty-vector fixtures covering representative spatial-data failures;
* reject unsuitable inputs before approval-gated transformation or release.

### Checkpoint 14D — Agent identity and operational history

Status: complete

Implemented:

* stable role identities for Planner, Executor, Critic, Builder, GIS, workflow-runner and harness components;
* trusted generation of unique instance, run, task and correlation IDs;
* explicit parent-run relationships across correlated stages;
* strict versioned operational-event and timeline schemas;
* append-only correlation-scoped JSONL storage;
* contiguous per-agent sequences and SHA-256 predecessor chains;
* bounded storage, file locking, durable append, approved-root containment and symlink rejection;
* status, timestamp, version, artifact-digest, evidence-reference and redacted-failure facts;
* trusted observers for validated Planner, Executor, GIS-workflow and Critic results;
* deterministic correlated timeline reconstruction and inspection;
* central schema-registry integration;
* exclusion of credentials, secrets and private model reasoning.

The real Checkpoint 14D GIS demonstration generated four validated events and reloaded them through the independent history reader. The source workflow passed GIS validation but lacked plan and approval evidence, so the observer correctly recorded `incomplete_evidence` as its terminal status.

Model-agent containers retain their existing read-only permissions. Trusted callers derive operational facts from validated results and evidence; agents do not self-author their history. A complete live Planner-to-Executor-to-GIS-to-Critic correlation will be exercised by the Checkpoint 14F presentation workflow.

### Checkpoint 14E — Authoritative results and release packages

Status: complete for authoritative workflow releases.

Implemented:

* strict candidate, validated, released and rejected lifecycle states;
* separate canonical, immutable and digest-addressed Critic-result evidence;
* deterministic non-writing workflow release assessment;
* complete task, plan, approval, validation, Critic and operational-history consistency checks;
* non-ready candidates and explicit violations for incomplete or invalid evidence;
* SHA-256 and size binding for every physical component;
* canonical `CANDIDATE.json` and `RELEASE.json` package records;
* verified component copies beneath project-relative paths;
* pre-staging, post-staging and pre-finalization source verification;
* atomic digest-addressed package finalization;
* write-once release IDs and duplicate refusal;
* independent candidate, manifest, directory, exact-file-set and component verification;
* rejection of path escapes, symlinks, missing files, unexpected entries, changed inputs and tampering;
* assessment, creation and inspection CLI commands;
* no registry modification or execution during the release lifecycle.

The real `checkpoint14e-release-demo-v1` workflow completed exact plan approval, isolated Executor and MCP execution, deterministic PostGIS validation, five-event operational history, separate Critic persistence, six-component release creation and independent inspection. Its authoritative release digest is `f9452eadae4f74c09ac9749535f5d9a2f20b8f2a4f594e1a1cb8793cf9c2d3bb`. Repeated creation with the same release ID failed closed.

The Planner model-facing current-status excerpt is now deterministically bounded to preserve context-window availability. The prompt retains the overview and latest status, reports truncation explicitly and continues to bind the complete trusted source file by SHA-256.

Recipe-specific release assessment remains future work. The completed Checkpoint 14E presentation scope covers authoritative workflow releases and does not perform PostGIS or GeoServer promotion.

### Checkpoint 14F — Pilot-ready demonstration

Completed for the presentation-focused vector scope:

* added a strict fixed demo definition and read-only readiness assessment;
* bound the dirty case, clean control, spatial contract and workflow dataset
  by deterministic identities and SHA-256;
* demonstrated expected invalid-geometry rejection and a clean contract pass;
* demonstrated constrained proposal, deterministic compilation, exact plan
  approval, isolated Executor/MCP execution and 12 passing PostGIS checks;
* recorded five validated correlation-scoped GIS operational events;
* persisted a separate Critic result without changing authoritative status;
* created and independently verified a six-component authoritative release;
* exported an approved vector conversion to Snakemake, statically validated
  it, completed an isolated dry-run without output and completed an approved
  replay with deterministic validation and durable evidence;
* added a clean-checkout readiness target and operator presentation
  walkthrough;
* passed 1,051 automated tests.

The fixed presentation scope intentionally uses the completed vector contract
benchmark. Controlled raster inspection exists, while raster contract fixtures
remain deferred. Generated approvals, execution evidence and releases remain
outside Git and must be recreated for each authoritative run.

### Checkpoint 15 — Expanded PostGIS workflows and controlled release

Completed for the governed candidate-to-current lifecycle:

* bounded PostGIS relation inspection;
* deterministic candidate-to-current comparison and change assessment;
* digest-bound promotion planning and exact approval;
* serializable promotion execution with locked state reverification;
* independent post-promotion state verification;
* digest-bound rollback planning and separate approval;
* serializable rollback execution with locked state reverification; and
* independent post-rollback state verification.

Controlled transformations, general spatial queries, export, publication and
generic recipe integration were not part of the completed 15A–15K scope and
remain possible future extensions rather than incomplete lifecycle gates.

### Previously proposed Checkpoint 16 — Restricted GeoServer publication

Planned:

* publication planning without mutation;
* restricted GeoServer credentials;
* approval-gated publication of promoted releases;
* allowlisted workspace, datastore, layer and style targets;
* publication and service verification;
* release-linked publication evidence and lineage.

### Checkpoint 17A — Read-only workflow interface foundation

Status: implemented for review. The isolated `interface/` application provides
a polished blueprint-style graph of the governed execution lifecycle. It
supports node selection, authority and evidence inspection, bounded zoom, a
minimap and an execution timeline using a schema-validated sanitized fixture.
Fit-to-viewport is calculated from the live canvas dimensions, the minimap
tracks and controls the visible region, and operators can switch between
horizontal and vertical graph layouts. Narrow screens default to vertical.
The minimap and viewport controls remain fixed to the canvas frame while graph
content pans underneath them.
The deliberately small stack is React, TypeScript, Vite, Zod, Lucide React and
plain CSS; it contains no hosting-provider or backend scaffold.
It has no approval, execution, secret, filesystem, database, arbitrary network
or package-installation authority.

Pandas and external-service connectivity are recorded as governed capability
expansion work in `context/CAPABILITY_EXPANSION.md`; neither is implemented by
Checkpoint 17A.

Remaining Checkpoint 17 work:

* guided request, contract, recipe and approval workflow;
* live bounded evidence projection and agent-history visualization;
* validation, Critic, release and report navigation;
* read-only default interface behavior;
* guided Snakemake export, validation, dry-run and replay;
* portfolio-ready GIS demonstrations.

### Checkpoint 17B — Bounded workflow evidence projection

Status: implemented for review. One exact validated workflow trace can be
projected into a browser-safe graph without exposing request text, tool
payloads, approval identity, artifact paths or secrets. The projector enforces
safe task identity, a fixed trace-root filename, symlink rejection, strict
schema validation and input/output size limits. The interface loads only a
same-origin fixed runtime path, validates it again and falls back safely to its
sanitized demonstration.

### Checkpoint 17C — Bounded workflow run selector

Status: implemented for review. A single operator command validates and exports
up to 50 workflow traces as ignored sanitized runtime projections plus a strict
catalog. The interface header lists those runs and switches the graph through
task-ID-bound same-origin paths. No source trace, approval or execution state is
modified.

### Checkpoint 17D — Evidence-backed node inspector

Status: implemented for review. Every projected workflow node now carries a
strict optional detail record containing a bounded summary, at most ten
aggregate observed facts, execution timing and at most ten safe findings. The
React inspector renders these records and clears stale node selection when a
different run is loaded. Python and browser schemas reject additional fields;
request text, tool inputs and outputs, approval identities, artifact paths,
secret values and private reasoning remain excluded.

### Checkpoint 17E — Safe evidence previews

Status: implemented for review. Planner, approval, validation and evidence
nodes expose expandable, schema-validated preview cards. The cards identify
trace, plan, approval, validation and up to four artifact records; show bounded
aggregate facts and plan integrity where available; and reduce artifact paths
to basenames. Approval identity, raw trace content, payloads, private paths,
secrets and unrestricted messages remain excluded. Older runtime projections
remain compatible and show a regeneration prompt.

### Checkpoint 17F — Trace-derived workflow topology

Status: implemented for review. Runtime projections replace the single generic
tool node with zero to twenty recorded operation nodes, preserving trace order
without exposing arguments or results. Safe controlled operation identifiers
become readable titles; unsafe identifiers receive neutral numbered labels.
Edges connect the Executor through the recorded operation sequence into
Validation. Horizontal and vertical canvas dimensions are calculated from the
actual projected nodes rather than an eight-node template.
Nodes are process-centric and label their performer. The minimap mirrors node
category, state and shape; wheel input controls zoom; Shift plus wheel retains
horizontal scrolling; and the corrected timeline spans its full width and
selects each projected process node.

The complete intended interface coverage is recorded in
`docs/INTERFACE_PRODUCT_SCOPE.md`. Checkpoint 17 remains the guided product
interface sequence; Checkpoint 18 remains pilot operations and bounded memory.

### Checkpoint 17G — Semantic node design system

Status: implemented for review. The projection now separates eight process
categories from five owner groups and explicit performer labels. The interface
renders restrained charcoal nodes with consistent geometry, category-colored
accent rails, matching icons and minimap symbols, selected-state glow and
semi-transparent ownership frames for intake, planning, governance, execution
and assurance. Legacy projections receive deterministic display fallbacks.
Human approval uses the same correctly clipped ten-pixel corner structure as
other nodes while remaining visually distinct through its orange category.
Category borders are two-pixel high-contrast strokes, action titles remain
near-white, performer identities use outlined badges and the timeline aligns
each status above its connected marker with the action below.
Group-specific frame padding prevents the Planner and Governance containers
from intersecting. Completed timeline events preserve category color through
moderate tinted capsules and glows instead of rendering every step bright green.
The theme now covers the complete application shell. Evidence uses an
off-white/slate identity, agent-owned planning and execution actions have a
distinct upper-right corner, and the graph supports non-passive wheel zoom and
empty-canvas pointer panning. Tablet and phone layouts retain the inspector
below the graph rather than removing it.

### Checkpoint 17H — Typed graph lanes and connections

Status: implemented for review. Projection edges now require a bounded label
and one of five meanings: control, governance, tool, data or evidence. User
Request and a separately sanitized Input Data node both enter the Planner.
Planner and Executor expose hollow triangular control sockets plus circular
data/tool sockets, while policy and human approval remain in Governance.
Executor connects only to the first recorded operation, operation nodes follow
recorded trace order, and only the last operation feeds validation. Optional
stages without corresponding trace evidence are omitted. Each connection has
a distinct color, line style, socket treatment,
label, legend entry and minimap representation. Run-specific input-reference
and tool counts plus correlation identity remain visible. Horizontal sockets
occupy left/right sides; vertical sockets occupy top/bottom sides. Every edge
uses matching hollow endpoint shapes. Catalog-selected runs no longer silently
fall back to the demonstration when their ignored runtime projection is stale
or invalid; the interface asks the operator to re-export it. Legacy browser
projections receive deterministic edge fallbacks. Completed traces remain
non-draggable; layout editing is reserved for future proposal mode.

The minimap uses outlines and thin edges. Ports sit inside node borders above
their lines, the graph cannot paint over the inspector, the redundant rounded
viewport border is removed, and the controls and legend can be moved through
dedicated drag handles. Snakemake appears only when explicitly present in trace
runtime or operation metadata; older replay records require a producer-level
execution-engine field rather than task-name inference.

### Checkpoint 17I — Proposal edit mode foundation

Status: implemented for review. The interface now exposes two explicit modes.
Evidence view preserves the immutable 17H projection behavior. Proposal edit
creates a separate browser-memory draft, disables run switching, and labels the
surface as uncommitted. Within that draft, nodes may be added from the bounded
type palette, selected, renamed, described, assigned a performer, repositioned
in either orientation or deleted with their incident draft edges.

The draft is discarded on exit. It cannot persist a proposal, reconnect typed
ports, invoke Planner, evaluate policy, record approval, call MCP, execute a
tool, access secrets or write evidence. Those capabilities require later
backend-integrated Checkpoint 17 slices. The product target remains complete
interface operation over the existing governed contracts, with the CLI retained
as a first-class automation, CI, debugging and expert surface.

### Checkpoint 17J — Typed proposal connection editing

Status: implemented for review. Proposal edit now exposes the existing block
field and deletion actions clearly in the Inspector and adds bounded directed
connection creation and deletion. The editor offers control, governance, tool,
data and evidence types, checks both endpoint socket families, rejects self
connections, exact duplicates and cycles, and immediately updates socket fill
and graph topology. Filled sockets are connected; hollow sockets are available.
Connections can be created either through the accessible Inspector controls or
by dragging an output socket onto a compatible unoccupied input socket. The
performer is selected from bounded project roles while preserving recorded
performers found in the current projection.

The graph remains an uncommitted browser-memory proposal. It cannot save,
compile, invoke Planner, evaluate backend policy, approve, execute, call MCP or
write evidence. The next slice must define a canonical proposal contract and a
safe persistence/compilation boundary before adding operational authority.

### Checkpoint 17K — Trusted template proposal bridge

Status: implemented for review. The interface now consumes a capped,
schema-validated runtime projection emitted by the existing
`recipe-template-catalog` command from `context/RECIPE_TEMPLATES.yaml`. It can
select one of the five trusted templates, collect required parameters, render
the declared steps and dependencies, and download a strict non-executable
`RecipeProposal` document compatible with the existing CLI compiler.

The generated browser catalog remains ignored. Missing request/parameter values
withhold download. Structural changes to a loaded template graph also withhold
download because the current recipe proposal contract cannot faithfully encode
arbitrary graph edits. No proposal is saved, compiled, approved or executed in
the browser. The next slice is a loopback-only typed service for deterministic
assessment and compilation of this exact shared contract.

Template selection now opens from a dedicated top-bar button into a focused
workspace above the graph. It is no longer mixed with selected-node details in
the Inspector. The workspace explains workflow, recipe and skill distinctions
and shows each recipe's steps, included skills and required inputs. Core concept
documentation also records CLI/interface equivalence testing with separate safe
identifiers and targets.

### Previously proposed Checkpoint 18 — Pilot operations and bounded memory

Planned:

* collect real pilot feedback before adding memory;
* retain only reviewed operational facts with provenance and scope;
* define version, retention and deletion controls;
* separate operational facts from run history;
* prohibit secrets, private reasoning and unreviewed conclusions.

## MVP status

The initial controlled GIS vertical slice is implemented:

```text
task-specific context
→ structured plan
→ deterministic policy
→ exact human approval
→ typed execution envelope
→ approval-gated MCP
→ controlled PostGIS write
→ deterministic validation
→ report and trace
→ independent evidence review
```

The reusable natural-language recipe extension is also implemented:

```text
natural-language request
→ constrained local-model proposal
→ deterministic assessment
→ trusted recipe compilation
→ operator review
→ explicit immutable save
→ human approval
→ approval-gated execution
→ deterministic QA
→ durable result, evidence and report
```

The declarative skill extension is now also implemented:

```text
versioned skill definition
→ deterministic permission policy
→ immutable contract bundle
→ isolated untrusted scaffold
→ trusted adapter materialization
→ network-disabled candidate tests
→ digest-bound test evidence
→ promotion assessment and exact plan
→ explicit transactional promotion
→ implemented registry entry
→ direct CLI and recipe-template availability
```

This pipeline reduces repetitive skill boilerplate while preserving the rule that declarative input and generated code cannot directly grant themselves execution authority.

The project currently demonstrates a secure and reproducible architecture for local-model-assisted geospatial automation. It does not yet provide a complete general-purpose GIS platform, but its main planning, approval, execution, validation and evidence boundaries are working.


### Checkpoint 14C vector presentation scope completed

The presentation-required vector portion of spatial-data contracts is now
implemented.

Completed controls:

* added strict versioned vector-contract schemas;
* added bounded JSON and YAML loading beneath a separate approved root;
* added canonical contract JSON and SHA-256 identity;
* added deterministic CRS, geometry, schema, nullability, uniqueness,
  feature-count, geometry-quality and extent checks;
* hashed each physical dataset before and after assessment;
* rejected path escapes, symlinks, ambiguous multilayer inputs and changed
  datasets;
* added typed checks and violations with validation-derived pass status;
* added operator CLI and read-only MCP access;
* kept all agent manifests unchanged and granted no new execution authority;
* added a generated dirty-vector benchmark with one clean and twelve failing
  cases;
* demonstrated a clean pass and isolated invalid-geometry failure;
* passed 969 automated tests.

Assessment performs no filesystem or database mutation and does not execute a
workflow. Raster contracts and raster dirty-data fixtures remain deferred by
the presentation scope of the product roadmap.

### Checkpoint 15A bounded PostGIS inspection

Checkpoint 15A adds a narrow read-only inspection surface for one exact
allowlisted PostGIS table. It reports bounded column, key, geometry, CRS,
count, geometry-quality and extent metadata through strict versioned schemas.
The service accepts no arbitrary SQL or query fragments, uses fixed queries,
a read-only connection and a statement timeout, and redacts connection
details from failures. The same operation is available through
`inspect-postgis-table` and the fixed MCP tool allowlist. It grants no write,
approval, export, staging, promotion or publication authority.

### Checkpoint 15B deterministic PostGIS comparison

Checkpoint 15B compares two distinct, exact PostGIS relations by composing
the bounded 15A inspector over one shared repeatable-read transaction. It
normalizes table-specific constraint names and returns typed differences for
columns, key structure, row count, geometry registration, CRS, observed
types, geometry-quality counts and extent. Matching and different outcomes
are deterministic results; missing evidence and policy failures fail closed.
The CLI and MCP surfaces accept no SQL or query fragments and grant no new
mutation authority.

### Checkpoint 15C deterministic PostGIS change assessment

Checkpoint 15C classifies validated comparison evidence as compatible,
review-required or incompatible using fixed policy. Schema, key, geometry
registration, CRS and type changes are incompatible; row-count, geometry
quality and extent drift require review when structure remains compatible.
Structural incompatibility dominates simultaneous observational drift and
unknown future changes fail closed. Assessment is model-free, read-only and
cannot create approval or authorize promotion.

### Checkpoint 15D digest-bound PostGIS promotion planning

Checkpoint 15D creates a canonical SHA-256-bound, non-executing promotion
plan only after fresh compatible comparison evidence and confirmation that
the exact archive relation is absent. The plan fixes the transaction,
rollback, lock, archive, promotion and post-validation choreography and marks
only the two future rename mutations as approval-required. Planning accepts
no SQL, creates no approval and performs no database mutation.

### Checkpoint 15E immutable PostGIS promotion approval

Checkpoint 15E loads a bounded 15D plan-result file, recomputes its canonical
plan digest and records a separate human decision in an immutable,
digest-addressed package. Approval is bound to the plan and assessment
digests and exactly the two planned rename mutations. Approved corrections
fail closed and require a replacement plan. This checkpoint writes approval
evidence only and performs no promotion or database mutation.

### Checkpoint 15F transactional PostGIS promotion

Checkpoint 15F consumes the exact 15D plan and 15E approval only after explicit
digest confirmation and write enablement. It locks and reverifies the relations,
proves archive absence, performs the two fixed renames in one serializable
transaction, validates before commit, rolls back every failure, and stores
canonical digest-addressed execution evidence.

### Checkpoint 15G independent promotion verification

Checkpoint 15G independently reloads the exact plan and execution package,
reinspects the promoted and archived relations in a new read-only transaction,
compares their normalized profiles with the approved snapshots, and persists
separate canonical digest-addressed verification evidence.

### Checkpoint 15H deterministic promotion rollback planning

Checkpoint 15H derives a canonical rollback plan only from an exact, successful
15D plan, 15F execution and 15G independent verification chain. Every source
digest and identity is revalidated. The six fixed steps reserve approval for
the two future rename mutations, require transactional execution and final
validation, and currently perform no database access or mutation.

### Checkpoints 15I and 15J rollback approval and execution

Checkpoint 15I records a redacted, immutable human decision bound to one exact
15H plan digest and exactly its two restoration mutations. Checkpoint 15J
executes only an unexpired approved decision after explicit digest confirmation
and write enablement. It locks and reverifies the relations, proves the original
candidate identity remains absent, performs the two fixed renames in one
serializable transaction, validates both restored relations before commit,
rolls back failures, and persists canonical execution evidence.

### Checkpoint 15K independent rollback verification

Checkpoint 15K independently reloads the exact rollback plan, approval and
execution package, recomputes their canonical SHA-256 identities, and verifies
their bindings and approved scope. It then inspects the restored PostGIS
relations through a separate read-only transaction, compares normalized state
with the approved snapshots, rejects missing or inconsistent evidence, and
persists a separate digest-addressed verification package.

The verifier does not trust the rollback executor's transaction or validation
claims. A rollback becomes verified only when the independently observed final
state matches the exact governed restoration plan. This closes the complete
15A–15K promotion and rollback lifecycle. The full regression after completion
passed 1,153 tests.
## Checkpoint 17L — CLI/interface parity baseline

Checkpoint 17L adds a committed, non-secret vector-conversion proposal under
`examples/interface-parity/` and regression coverage that compiles it through
the same trusted template and skill registry used by the CLI. The baseline
proves ordered inspection and conversion steps, deterministic policy validity,
and the exact steps requiring approval and validation while confirming that no
recipe is saved, no approval is issued and no execution occurs. Generated
catalog projections and compilation responses remain outside Git. The next
slice is a loopback-only typed interface assessment/compilation service over
this exact contract; persistence and execution remain later, separate gates.
## Checkpoint 17M — loopback proposal compilation

Checkpoint 17M adds a standard-library HTTP service bound only to
`127.0.0.1`. The service exposes health, trusted recipe-template catalog and
in-memory RecipeProposal compilation through strict typed routes, bounded JSON,
origin checks and redacted failures. It calls the existing catalog, registry
and compiler services directly and verifies that no recipe was saved, approved
or executed. Vite proxies `/api` to this service, and the Templates workspace
now provides a Compile proposal button with an ordered-step and gate summary.
The static runtime catalog remains an offline browsing fallback. Persistence,
approval, execution, validation and evidence actions remain unavailable.
## Checkpoint 17N — digest-bound reviewed recipe storage

Checkpoint 17N adds the first persistent interface operation after 17M's
non-mutating compilation. The Templates workspace displays the exact compiled
recipe SHA-256 and ordered steps, clears stale review state whenever the
request changes, and requires a separate operator confirmation and save action.
The loopback service validates the exact request, recompiles against the
trusted registry, verifies the displayed digest, and uses the existing
redacting write-once storage beneath `workflow-recipes/`. The browser cannot
select a path, duplicate recipes cannot overwrite existing state, generated
JSON remains ignored by Git, and saving performs no approval or execution.
## Checkpoint 17O — stored recipe inventory

Checkpoint 17O preserves the 17N save result until the operator explicitly
selects Done — view saved recipes, then transitions to a read-only inventory
also available from a persistent top-bar Recipes control. The loopback service
loads at most 200 canonical recipes beneath the fixed root and returns only safe
identity, digest, ordered skill and future approval/validation gate summaries.
It rejects symlinks, escaped or invalid artifacts and policy failures. Recipe
arguments and approval identities remain excluded, and inventory performs no
mutation, approval or execution.
## Checkpoint 17P — exact approval-request preparation

Checkpoint 17P adds a Prepare approval request action to each eligible stored
recipe. The loopback service accepts only the canonical filename and confirmed
recipe digest, reloads and rehashes the artifact beneath the fixed root, reruns
deterministic policy, and returns the complete required approval scope plus a
separate canonical request digest. The interface shows the exact steps and
skills in a prepared-only card. No approver, decision, reason, expiry or
correction is collected; no approval evidence is written and no execution is
possible.
## Checkpoint 17Q — append-only recipe approval decision

Checkpoint 17Q adds a distinct Human decision drawer after 17P preparation.
The operator may approve or deny, identify the approver, provide a required
reason and optional bounded expiry, then explicitly confirm the displayed
request digest and fixed step scope. The loopback service reprepares the
request, recomputes both digests, reruns policy and derives steps server-side
before using the existing redacting append-only approval service. The stored
result exposes a safe filename, decision, scope and expiry and explicitly
reports that nothing executed. Execution controls remain absent.

## Checkpoint 17U — durable live execution state

Checkpoint 17U projects real recipe-runner transitions into the active workflow
graph and a step-level execution panel. Progress is keyed by the confirmed
execution-preview SHA-256 and atomically persisted beneath the fixed
`workflow-state/interface-executions/` root. If the API restarts while a
snapshot still says `running`, the next inspection classifies the attempt as
`interrupted`, localizes the active step and presents fail-closed recovery
guidance. It never resumes or retries a write automatically. Approved, denied,
failed and interrupted remain distinct outcomes; denied and interrupted use a
red stop treatment in the interface. The authoritative execution result and
durable evidence remain the only source of a validated-success claim.

## Checkpoint 17V — durable execution attempt browser

Checkpoint 17V adds a bounded read-only inventory over the durable 17U progress
records and a visible Runs workspace in the main interface. New attempts retain
the immutable recipe identity and exact step dependencies needed to reconstruct
their run-specific graph. An operator can reopen completed, failed, interrupted
or active state after closing the browser or restarting the local API. Reopening
cannot approve, resume, retry or execute anything; legacy records without enough
identity remain listed but their graph action is disabled.
