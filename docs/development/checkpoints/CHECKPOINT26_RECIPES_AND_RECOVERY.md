# Checkpoint 26: reusable recipes and governed recovery

**Historical initial delivery:** the current natural-language route and role assignment supersede the Builder/manual-form instructions below; see [checkpoint closeout](CHECKPOINT26_CLOSEOUT.md). Legacy advanced controls remain compatible.

This operational slice extends the existing recipe catalog, typed Planner plans,
recipe runner, authorization and durable progress. It does not finish every
checkpoint 26 memory/orchestration proposal. Historical recipe definitions,
digests, CLI commands and synchronous execution endpoints remain supported.

## Structure

```text
Request → Planner discovers operations and reusable recipes
        → typed recipe uses OR ordinary complete plan
        → deterministic expansion, argument/path/DAG/policy checks
        → saved explicit workflow graph
        → Authorize writes → Execute → durable run
                                 ↓
                 operation → independent validation → next operation
                                 ↓
                  bounded previews, results and evidence
```

Recipes are JSON data, never arbitrary Python/library functions. Versioned
definitions live in `recipe_catalog/reusable_recipes.json`; explicitly registered
definitions persist in project-local `reusable-recipes/` (ignored by Git).
Existing `context/RECIPE_TEMPLATES.yaml` and concrete `workflow-recipes/` keep
their historical purposes. The new composition adapter targets the same
`WorkflowPlan` → `planner_recipe_definition` → governed recipe services; it is
not a second operation executor.

Three builtins provide CSV inspection, GeoJSON inspection/attribute export and
column selection/missing-cell filling. Their readable names, parameter types,
operation sequence, output contract, version and SHA-256 are discoverable.
Planner receives up to five ranked recipe contracts within its existing prompt
budget; this is bounded lexical discovery, not semantic tool retrieval.

Each use supplies an exact hash, unique alias and all parameters. Declarative
`$parameter` and `$step` references are resolved without evaluation. CSV source
parameters accept an original input path or `{"recipe_output":"earlier_alias"}`.
The latter binds the actual CSV-producing step and adds its dependency.
Inspection metadata cannot substitute for a CSV artifact. Output contracts are
checked against registered operations; argument values still pass the shared
typed/policy/path validators. IDs are remapped, total expansion caps at 20
operations, write/validation gates come from the registry, and recipe hashes
are included in plan assumptions, binding the saved plan digest to its sources.

The interface offers a searchable Reusable recipes panel, typed parameter
forms, composition ordering and selection of preceding CSV recipe outputs.
Using recipes validates and saves a new explicit graph, binds the current chat
when its scope matches and clears stale authority/results. It does not run data.
The graph exposes individual editable operations; nested/collapsible canvas
recipe groups and automatic migration of customized instances are not delivered.
Planner can also append recipe uses to an existing validated plan. Complex
requests can continue to use ordinary operation steps.

## Builder, tests and Critic

Creating a recipe from a current supported CSV-producing workflow is an explicit
Prepare action. It runs these steps sequentially, with no extra container/model:

1. The existing proposal-only Builder role proposes typed JSON and 1–3 small
   synthetic fixtures. The operation sequence must match the source workflow.
2. Deterministic services validate and execute fixture workflows in temporary
   projects. Only the declarative skill index and generated fixtures enter them;
   original datasets, credentials and `.env` are not copied. Expected CSV bytes
   and independent operation validation must pass.
3. One bounded Builder correction is allowed on schema/fixture failure.
4. The existing tool-free Critic role reviews the candidate and test report,
   including limitations. Same-model review is not independent verification.
5. The user clicks Register tested recipe once. Registration binds the exact
   hash, fingerprints operation versions/argument contracts and reruns fixtures;
   changed contracts block reuse until explicit migration/retesting. Registration
   stores metadata and grants no authority.

This path supports built-in CSV operations and the GeoJSON attribute bridge.
Inspection-only builtins can be reused directly; generating new inspection-only,
database, raster, extension-code or arbitrary-code recipes is outside this first
fixture verifier. No background learning or automatic registration occurs.
Builder and Critic cannot call tools, install recipes or approve operations.

Model preparation has bounded prompts/responses, at most two Builder calls and
one Critic call, sequentially. Each configured client call is capped at 45 seconds
and at most 4096 output tokens (also subject to the existing lower configured
limit). If the configured output budget is too small for a definition and its fixtures, preparation can fail; inspect MODEL_MAX_TOKENS before retrying. This is not a total latency guarantee. Real local-model quality remains
operator acceptance; synthetic tests do not prove general dataset suitability.

## Durable runs and cancellation

Normal main-workflow Execute starts a durable background run and polls status.
Run records under `workflow-state/interface-runs/` are atomically persisted with
fsync. A project lease prevents multiple durable workers across API/CLI processes.
Execution still uses the existing review, exact authority, dispatcher, sequential
topological scheduling and independent verifiers. Authority is rechecked before
each approval-required operation; an earlier long operation cannot authorize a
later write after expiry.

Cancel is one explicit header action. Cancellation is cooperative at the next
operation boundary: an active tool call and its verification finish before
later operations are skipped. It does not kill a thread, abort a database
transaction or promise immediate interruption. A late request after the final
operation may leave a successfully completed run. Completed files are retained.

Run history provides per-step status, dependencies, parameters, bounded results
and validation disclosures. Matching current graphs reflect running/completed/
failed/skipped operations; mismatched chat/plan graphs do not inherit these states.
Opening history and refreshing a browser never dispatch work. An orphaned queued,
running or cancelling record becomes interrupted when no project worker owns the
lease. Restart never resumes a worker automatically.

Stopped runs identify failure location and observed local output paths, sizes and
bounded hashes. Presence is not proof the attempt created or validated a file.
Database/service targets require separate inspection; reading history performs
no database calls. Full successful results continue to use existing durable
evidence. Partial per-step previews are observations, not a fabricated completed
recipe evidence package.

Recovery requires one Prepare recovery action, followed by the normal review and
Execute flow:

- **Read-only inspection:** exclude completed operations and prepare the remaining
  read steps as a new validated proposal. No operation starts automatically.
- **Workflows containing writes:** prepare the full workflow with fresh output
  filenames/table names. Completed writes are not reused; nothing reruns until
  the new scope receives fresh authorization and Execute. This is a safe new
  attempt, not write-step resume or rollback.
- Report/Snakemake recovery requires target-specific Planner review. Source
  Snakemake export retains its existing synchronous execution path.

The same durable write request cannot be started twice, including after failure
or cancellation. Changing unrelated request text cannot bypass that guard.
Project-local API/CLI leases do not coordinate legacy synchronous calls or
arbitrary external programs. Output create-only checks and existing approval
boundaries remain active on those older paths.

Bounds: 200 retained run records before explicit archival is needed; latest 50
inventory summaries; 512 KB/run; intermediate result previews at most 6 KB;
validation previews at most 3 KB; full returned execution result up to 160 KB
in the run record, otherwise use existing durable evidence; stopped file hashing
at most 32 MB/file. Native Windows support is not claimed: this slice uses POSIX
file leases, consistent with the existing host environment.

## Shared API and CLI

Both interfaces call the same services:

| Endpoint / CLI | Actions |
| --- | --- |
| POST `/api/v1/reusable-recipes` / `geoagent reusable-recipes` | `list`, `compose`, `prepare`, `test`, `register` |
| POST `/api/v1/workflow/runs` / `geoagent workflow-runs` | `list`, `start`, `read`, `cancel`, `recover` |

CLI commands accept `--project-root PATH` and an optional `--request-file JSON`.
Without a request file they list metadata. CLI start waits in the invoking
process; a separate terminal may inspect/cancel it. Stopping that process does
not automatically undo outputs. Schema definitions are in
`recipe_catalog/composition.py` and `interface_api/workflow_runs.py`.
Registration and runtime execution are distinct typed requests. Historical
context, method notes, recipes and model messages never grant execution authority.

## Frontend acceptance

Start with the existing launcher and your configured model. Use
`bash scripts/start_actioncharter.sh --enable-write-tools` only for the local
CSV output tests below. No PostGIS/GeoServer access is needed.

1. Open a new chat, then Reusable recipes. Choose **Select columns and fill
   missing cells**. Set source `data/input/sample_orders.csv`, columns
   `["region","amount"]`, fill values `{"region":"Unknown"}`, selected path
   `data/output/recipe_selected_test.csv` and target path
   `data/output/recipe_cleaned_test.csv`. Choose fresh filenames for each attempt.
2. Click Use recipe · create workflow. Expect two operations and their dependency,
   a saved workflow in the current chat and no output files yet. Refresh: the
   chat should restore that workflow without a model call.
3. Open Reusable recipes → Create a reusable recipe from this workflow → Prepare
   recipe. Expect Builder/test/Critic progress, then a candidate or an actionable
   failure. No real output should appear. If supported, Register tested recipe
   once; refresh and search for its name. Local-model failure is not a passing
   acceptance result; retain the original workflow and report the error.
4. Close the panel. Authorize the exact local CSV writes, then Execute. Expect
   two verified results and expandable previews. Missing `region` becomes
   `Unknown`; missing `amount` remains missing because no amount replacement was
   requested. There is no implied numeric aggregation in this recipe.
5. Open Execution History → Workflow runs · cancellation and recovery. Expand
   each operation's parameters, intermediate result and validation. Refreshing
   must not create another attempt.
6. On a sufficiently long run, click Cancel. Expect cancelling until active
   verification finishes, then skipped later steps. Small CSV workflows may
   finish before a manual cancellation can be observed; the controlled browser
   fixture below tests this boundary deterministically.
7. For a cancelled/failed/interrupted run, Prepare recovery. Check changed targets
   and preserved original output. A write recovery needs fresh Authorize and
   Execute. A stopped read-only inspection resumes only remaining read work.
8. Compose GeoJSON attribute export followed by CSV cleaning using Add to
   composition and Connect previous recipe output. Retain actual source field
   names and explicit replacements. Expect four connected operations, no geometry
   in the CSV and rejection when inspection metadata is used as a CSV source.

## Automated acceptance and remaining limits

Verified on 2026-10-15: **1,600 tests passed** with `make test`; frontend typecheck/build passed (existing large-bundle advisory remains). All **22 production-browser fixture groups** passed: six CSV journey groups, ten conversation/memory groups and six recipe/run groups. The focused 27-case recipe/run suite additionally verifies actual spatial→CSV recipe execution, read-only cancellation/history and remaining-read recovery. Model responses are fixtures; real local-model quality/latency and live GIS services were not exercised.

`make test` and `make interface-validate` cover shared contracts and compatibility.
`corepack pnpm@10.17.1 --dir interface browser:test:26-recipes` exercises real
temporary API/storage/pandas/validation with fixture model replies, including
registration, cancellation during active verification and fresh-target recovery.
Browser engines/profiles remain separate from normal browser caches.

Remaining checkpoint work includes independently verified reuse of completed
write intermediates, transactional/operation-specific resume, broader recovery
targets, global model scheduling/resource evaluation, parallel execution and
broader memory lifecycle proposals. The initial sequential scheduling and safe
new-attempt path do not establish those capabilities or full checkpoint completion.
Checkpoint 27 still covers visualization/demo and laptop/PC release preparation.
No release or live-service change is part of this delivery.
