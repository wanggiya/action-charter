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

* Raster processing is not implemented.
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

## Next milestones

### Checkpoint 11 — Skill scaffolding and contracts

Planned:

* generate a standard skill package;
* generate strict schema templates;
* generate policy and verifier placeholders;
* generate registry metadata;
* generate contract tests;
* test universal security requirements;
* require review before a generated skill becomes implemented.

### Checkpoint 12 — Snakemake export and replay

Planned:

* export validated recipes into deterministic Snakemake workflows;
* invoke stable GIS implementations directly;
* preserve artifact identity and lineage;
* avoid model invocation during deterministic replay.

### Checkpoint 13 — Raster foundation

Planned:

* raster metadata inspection;
* controlled raster conversion;
* CRS and resolution policy;
* nodata and band metadata;
* deterministic raster validation.

### Checkpoint 14 — Expanded PostGIS workflows

Planned:

* controlled spatial transformations;
* read-only spatial queries;
* validated PostGIS export;
* generic recipe-dispatch integration.

### Checkpoint 15 — GeoServer publication

Planned:

* restricted GeoServer credentials;
* approval-gated layer publication;
* validated workspace and datastore selection;
* publication verification;
* service evidence and lineage.

### Checkpoint 16 — Demonstration interface

Planned:

* guided workflow interface;
* clear approval review;
* workflow visualization;
* evidence navigation;
* portfolio-ready GIS demonstrations.

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

The project currently demonstrates a secure and reproducible architecture for local-model-assisted geospatial automation. It does not yet provide a complete general-purpose GIS platform, but its main planning, approval, execution, validation and evidence boundaries are working.
