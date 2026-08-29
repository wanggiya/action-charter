# Current Status

Last updated: 2026-08-21

## Project summary

GeoAgent Skill Harness is a CLI-first, local-first, containerized system for planning, approving, executing, validating and auditing controlled geospatial workflows.

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
* natural-language recipe proposals;
* guided operator review and explicit recipe storage.

The model is used to interpret requests and produce constrained proposals. It does not determine execution success, approve writes, call GIS tools or directly modify artifacts.

Final success is derived only from deterministic validation.

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
* Critic assessments are not persisted as separate authoritative artifacts.
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

## Next milestones

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

Next Builder slice:

* define an explicit human review package for the exact inspected and tested candidate digest;
* include the Builder request, proposal, manifest, inspection and test assessment;
* prohibit automatic promotion from passing tests;
* define bounded destination planning for reviewed candidate files;
* reuse the existing transactional promotion boundary where appropriate.

Next Builder slice:

* run exact inspected candidates in the existing network-disabled skill-test container;
* mount the candidate read-only;
* bind test evidence to the inspected candidate-tree digest;
* reject candidates that change between inspection and testing;
* keep passing tests insufficient for trust or promotion.

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

Planned:

* assign stable role IDs and unique instance, run, task and correlation IDs;
* preserve parent-child relationships across workflow stages;
* write append-only typed operational events;
* record status transitions, versions, digests and redacted failures;
* exclude credentials, secrets and private model reasoning.

### Checkpoint 14E — Authoritative results and release packages

Planned:

* add candidate, validated, released and rejected lifecycle states;
* persist Critic output separately;
* build one immutable digest-addressed release package per authoritative run;
* include recipe, approval, results, validation, Critic evidence, artifacts, lineage and report;
* add read-only release inspection and verification;
* withhold release status when required evidence is incomplete.

### Checkpoint 14F — Pilot-ready demonstration

Planned:

* prepare fixed dirty-vector and controlled-raster scenarios;
* demonstrate contract assessment, proposal, compilation, approval, execution and validation;
* show correlated agent history and separate Critic evidence;
* create and inspect a release package;
* demonstrate Snakemake export, dry-run and approved replay;
* provide a repeatable clean-checkout presentation walkthrough.

### Checkpoint 15 — Expanded PostGIS workflows and controlled release

Planned:

* controlled spatial transformations;
* bounded read-only spatial queries;
* validated PostGIS export;
* versioned candidate staging;
* candidate-to-current comparison;
* exact approval before promotion;
* previous-version and rollback metadata;
* trusted-skill and declarative-recipe integration.

### Checkpoint 16 — Restricted GeoServer publication

Planned:

* publication planning without mutation;
* restricted GeoServer credentials;
* approval-gated publication of promoted releases;
* allowlisted workspace, datastore, layer and style targets;
* publication and service verification;
* release-linked publication evidence and lineage.

### Checkpoint 17 — Guided interface and Snakemake productization

Planned:

* guided request, contract, recipe and approval workflow;
* workflow and agent-history visualization;
* validation, Critic, release and report navigation;
* read-only default interface behavior;
* guided Snakemake export, validation, dry-run and replay;
* portfolio-ready GIS demonstrations.

### Checkpoint 18 — Pilot operations and bounded memory

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
