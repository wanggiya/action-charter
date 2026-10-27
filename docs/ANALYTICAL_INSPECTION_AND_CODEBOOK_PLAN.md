# Analytical inspection with codebooks — proposed delivery

## Implemented analytical slice — 2026-10-24

Operator authorized implementation after the recorded proposal. See
[delivery and exact real-data retest](ANALYTICAL_INSPECTION_ACCEPTANCE.md).
Ollama Settings selection, hash-bound source queries, sectioned codebooks, complete-file
profiles/group export, shared MCP/CLI services and compact Results views are implemented.
Optional bounded post-run execution assistance is implemented; automatic mid-run
adaptation and a general lazy dataframe engine remain open. The actual diabetes inputs
passed independent full-file comparisons and normal authorized execution in a temporary
project. Earlier proposal-only statements below are preserved discussion history.
Memory/role-flexibility decisions remain parked; no checkpoint-29 completion claim.


Recorded 2026-10-23. Documentation only. The user reached step 4 on the downloaded
UCI diabetes data and requested a proposal before runtime/frontend changes. The
latest request authorizes recording that proposal and explaining MCP/backend duties;
no implementation, dataset processing, model call or frontend changes are authorized
by this documentation update. Memory alternatives remain parked.

## Expanded delivery and orchestration assessment

[Five-stage analytical execution plan](ANALYTICAL_EXECUTION_DELIVERY_PLAN.md) records
Ollama selection, typed intermediate tables, full-data operations, bounded execution
reasoning and frontend/task acceptance. It also compares selective roles with a single
loop and dynamic delegation. All are proposals; no runtime work is delivered.

## Operator findings and target

Reported: test/diabetic_data.csv was not recognized without moving it to data/input;
standalone inspection does not incorporate IDS_mapping.csv; first-five-row previews
and 20-row/32-column presentation limits do not provide a useful analytical inspection.
User stopped before sample aggregation. Do not call those observations independently
reproduced bugs or claim the age/codebook interpretation has been verified.

Target: inspect the complete supported CSV with its supplied code definitions,
produce explicit full-file profiles and requested aggregates, and explore bounded
relevant table pages. Separate full-file analytical coverage from display limits.
Do not substitute a 5,000-row sample for full-file result correctness acceptance.
A small fixture may aid debugging, but must not be reported as full-data analysis.

## Proposed dependency order

1. Audit path resolution, worker limits, result contracts and actual codebook structure.
   test/file.csv beneath data/input should resolve within that permitted root. A project
   root test/ folder is different and needs explicit additional read-only root policy.
   Model text never grants arbitrary filesystem access. Explain resolved/rejected paths.
2. Add main-table + supporting-codebook/document bindings. Inspect actual IDS_mapping.csv
   before choosing a parser: do not assume it is one flat join table. Match declared
   mappings to fields, detect duplicate/unknown codes and retain source/revision identity
   for both table and mapping. Labelling must not silently multiply/drop observations.
3. Add analytical profiles: parsed count, field/type evidence, documented missing-code
   counts, suitable numeric summaries, categorical counts/proportions, identifier
   uniqueness/repeat information and mapping coverage. Preserve supplied versus inferred
   meanings and per-claim uncertainty. Age intervals remain categories unless a reviewed
   method justifies another representation. Clinical definitions are not guessed.
4. Extend full-file processing through bounded worker services. Consider chunked pandas
   for count/sum/mean and bounded groups, with NumPy for appropriate numeric operations.
   Exact distinct counts/quantiles/high-cardinality groups/joins need explicit memory or
   disk strategies and limits. Never silently sample or approximate an exact request.
   Preserve no-follow access/source checks, hashing, cancellation, partial-status and
   changed-source detection. Raising 8 MiB/10,000-row limits blindly is not acceptance.
5. Expose reviewed typed operations through shared API/CLI/Planner graph and selected
   MCP tools; add deterministic checks before declaring an operation successful.
6. Audit and propose frontend layout before edits, then implement only after agreement.
   Validate full-file results against independent reference calculations and exercise
   source/codebook mismatches, restart and safe over-limit/failure behavior.

Current state: streaming inspection already covers counts/identity beyond the display
preview; it is narrower than the proposed analytical profile. Current transformations
are still bounded to 8 MiB/10,000 rows. This plan does not claim the new analysis exists.

## Proposed analytical result contract

Return separately: source and codebook bindings, complete/provisional/failed status,
metrics with coverage (full-file / sampled / unavailable), typed column profiles,
category/mapping coverage, requested group summaries, bounded table view identifiers,
checks and limitations. Each count/proportion carries its denominator. IDs are not
numeric measurements merely because their strings are digits. Do not merge a valid
unperformed-test category into missing without a supplied interpretation.

A bounded table page is a view of recorded/explicitly read data, not the full statistics
input. Table filters should disclose whether they affect the loaded page or the complete
verified source. Opening saved results should not silently rescan or rerun; larger
on-demand reads need source identity checks and explicit status. Retained snapshots,
read indexes and paging/cache lifecycle remain to be designed.

## Execution assistance — proposed, not delivered

User requests reasoning during execution for mappings/processing ambiguities. Proposed
boundary: bounded LLM-backed execution assistance receives metadata/codebook/error,
returns a typed interpretation or revised operation; backend validates scope/contracts.
No LLM call per chunk, arbitrary Python, invented domain facts, silent operation change
or automatic repeat of writes. Material changes produce a revised proposal with normal
fresh validation/authority. Existing executor remains deterministic until this separate
extension is explicitly agreed and tested. An LLM helper is not another required agent
or permission to send entire health records to a model.

## Frontend inspection promise

Before changing frontend: read ResultsWorkspace/table/profile/result contracts, reproduce
this journey with isolated browser tooling if available, inspect actual returned data,
scrolling/layout/paging and empty/error states, and present findings plus proposed layout.
Initial proposal only: Overview | Data table | Columns | Codes & definitions | Checks.
Display distributions, meaningful selected records and code meanings rather than an
unqualified first-five-row sample. No navigation redesign or frontend edits yet.

## MCP versus backend: current wiring and proposed ownership

Code inspected during this documentation turn:

- mcp_server/server.py uses FastMCP and stateless_http=True; registers explicit tools.
- mcp_server/tools.py contains TOOL_ALLOWLIST and thin calls to service functions.
  discover_dataset delegates to discovery.service.discover_dataset, requires the
  configured project data/input root, and keeps its bounded read-only contract.
- discovery/service.py uses the bounded inspection policy/worker; existing discovery
  readers implement source access and CSV/spatial inspection. tabular/service.py and
  its typed schemas implement current bounded table processing separately.
- mcp_client/client.py has its own read-only tool allowlist. Adding a server tool does
  not automatically expose it to the Planner/client, graph, registry or CLI.
- mcp_server/approved_recipe.py validates recipe/approval artifacts and delegates to
  shared runner/persistence services. MCP calls can therefore produce durable project
  evidence; stateless transport does not mean every called operation lacks state.

New data-reading/profiling/mapping/aggregation logic belongs in a reusable backend
service with typed contracts and effects, not duplicated inside a protocol handler.
Frontend API and CLI can call that service directly. MCP exposes selected capabilities
as named callable tools to compatible agent clients using the same service and policy.
MCP is not the database containing all functions, datasets, memory or model weights.

    Planner / workflow ----+
    Interface API ---------+--> typed backend service --> bounded workers/readers
    CLI -------------------+             |
    MCP tool adapter ------+             +--> results/evidence in project storage

What the MCP layer defines: tool names/descriptions, argument schemas, result/error
serialization, transport and tool policy, and calls into backend services. Actual
packages/data/codebooks and durable run/approval evidence remain in configured project
storage or external services. No ingestion/installation of every pandas/NumPy function.
Not every existing operation is a standalone MCP tool: approved recipes can compose
registered operations. Tool exposure and operation-registry registration are distinct.

Proposed exposure: preserve existing discover_dataset/inspect_csv compatibility; add
versioned richer contracts or a distinct profile/codebook tool when their semantics and
budgets are settled. Full processing should use registered closed operations and the
normal workflow runner. Final names/count of tools remain unresolved. Update server
and client allowlists, catalog/argument/result schemas and meaningful contract tests
where relevant. MCP parity means equivalent shared behavior, not mandatory network
round-trips for all local requests. Read-only profiles need no invented write approval;
actual exported files/transformations keep their declared write gates.

## Acceptance for the first coherent delivery

- Resolve/reject nested paths clearly without widening filesystem scope implicitly.
- Read actual diabetes CSV and mapping format; document semantic unknowns.
- Full-file profiles and at least one supported full-file grouped result match an
  independent oracle over the same defined dataset, not the preview/sample.
- Mapping cannot inflate rows; unknown/duplicate codes and missing definitions visible.
- Bounded table views and coverage labels agree with backend evidence; preserve run
  reopening without regeneration. Keep huge-data claims separate from ~18 MB testing.
- Capture elapsed time/worker memory, cancellation, incomplete work and source changes.
- Meaningful backend tests, make test, make interface-validate and isolated browser
  journeys for any implemented relevant changes. No tests were run in this doc-only turn.
- No private dataset commits, arbitrary execution, live DB changes or silent write
  retries. No clinical inference or medical-image processing claim.

Next step is implementation agreement, then audit/reproduce first. Do not resume the
old step-5 sample instructions as if they validate the requested complete-file analysis.
