# Generalization and consolidation — recorded direction

Recorded 2026-10-27. Design and documentation only; no structural changes implemented
by this document. Preserve earlier checkpoint history and working capabilities.

Use the [consolidated implementation TODO](IMPLEMENTATION_TODO.md) for task order,
dependencies and acceptance; this document retains the architectural rationale.

[Expanded analytical/format requirements](DATA_SCIENCE_FORMATS_MEMORY_AND_REMOTE_PLAN.md)
include substantive statistics/model reports and memory before autonomous Linux deployment.

[Composition and whole-project structure](COMPOSITION_IMPLEMENTATION_AND_AGENT_STRUCTURE.md)
records the concrete operation locations, parameterized examples, current/proposed
graphs and single-versus-role-context tradeoffs from the follow-up discussion.

[Builder reuse plan](BUILDER_REUSE_AND_CAPABILITY_INTEGRATION.md) corrects the earlier
impression that implementation generation starts from zero: August/September Builder
already generates candidate source and has a lifecycle. Audit/reuse it before building
a task-driven code-to-skill path; do not automatically activate source from chat.

## What the user wants

- An agent-driven data-science/engineering platform, not an expanding collection of
  dataset-specific endpoints, prompt patches or a generic coding assistant with a graph.
- Agents discover relevant installed Python capabilities, choose methods and compose
  existing operations/skills. New packages do not automatically become executable tools.
- Keep useful typed operations, templates and recipes. They avoid repeatedly generating
  code for solved tasks; generated Python is an optional gap-filling capability.
- Common-format support, ordinary analytical reports, document frequencies/relationships
  and realistic PostgreSQL/PostGIS work should use shared contracts and execution services.
- Manual and automatic Single/Three-role selection, including conversation overrides;
  Planner can recommend help, coordinator enforces effort and authority boundaries.
- Test with real or simulated domain data without binding product logic to that dataset.
- Simplify accumulated implementation and acceptance scripts; demonstrate value with
  correctness, less operator effort and measured small-model performance.
- Explain restored proposals/history, disabled Execute and absent outcomes clearly.
- No application implementation is authorized by this documentation-only task. No Git,
  live-service changes, dependency installation, tests or execution experiments.

## Current versus proposed

The current model composes structured workflows from implemented operations. That is
different from generating their Python implementations. Existing backend code performs
actual reading, computation, persistence, authorization, dispatch and verification.
Those responsibilities remain necessary; their existence does not justify duplication.

Package discovery, typed operations, shared execution services, durable runs and manual
task modes already have implementations. General XLSX/nested-JSON support, automatic
mode routing and arbitrary bounded Python task execution are proposals, not delivered
capabilities. Existing typed expression calculations are not arbitrary Python execution.
Fixture success does not establish actual Ollama planning reliability or domain expertise.

```text
Desired user journey
  Conversation / frontend / terminal / MCP
                  |
  Shared task actions and current workspace state
                  |
  Planner + relevant skills/capability retrieval
                  |
  Coordinator: mode, effort, explicit role handoffs
                  |
  Operation registry: typed contracts and effects
                  |
  Execution services + source adapters + isolated worker
                  |
  Recorded results, deterministic checks, assessment and presentation

Optional generated Python enters through the worker boundary;
it does not bypass execution policy or receive database credentials by default.
```

## Consolidation approach

First trace ownership and call paths; do not declare a file redundant from its name or
size. Inventory real behavior, shared callers, storage ownership and existing tests.
Choose one representative inspection/preparation/database/report journey as a baseline.
Extract and redirect one responsibility at a time, preserving external contracts. Remove
old internal branches only after their callers use the shared implementation.

| Existing area | Intended responsibility and consolidation |
| --- | --- |
| `interface_api`, `chat`, `mcp_server`, CLI entry points | Thin transport/session adapters over shared task actions; no separate implementations of profiling, authorization or execution |
| `planner` | Intent interpretation, capability retrieval, contract-driven prompt construction and generic structured correction; avoid accumulating dataset/wording-specific repair branches |
| `orchestrator` | Mode selection, total effort accounting, role-context handoffs and shared coordination; one execution lifecycle rather than role-specific copies |
| `operations/registry` | Canonical references to argument/result models, effects, requirements and validation; generate discovery/prompt/help metadata from these references |
| `discovery`, `tabular`, `postgres`, spatial services | Source discovery and format/domain adapters around reusable analytical/engineering operations; preserve meaningful differences between tables, geometry and rasters |
| `recipes` and skills | Parameterized methods over stable operation contracts; applicability conditions and tested examples rather than repeated implementations |
| `sandbox` | Explicit worker boundary, resource controls and artifact manifests; reuse existing worker facilities where they actually provide the required isolation |
| Result/evidence services and frontend views | One versioned result contract for tables, column profiles, groups, checks, charts, lineage and omissions; transports render the same facts |
| `scripts` and `tests` | Shared temporary-project/API/browser/database fixtures with named scenarios; retain thin useful command wrappers, remove duplicate setup only after migration |

This is a responsibility map, not an instruction to create all-new packages or move
every file. Existing shared services should remain where practical. Separate modules
are appropriate for distinct boundaries; fewer files is not the acceptance criterion.

## Make operations more general without making them unrestricted

1. **Describe sources consistently.** Source reference, identity, schema, grain/keys,
   types, geometry/CRS when applicable, supported reads and declared limits. Discovery
   does not silently read everything or grant authority.
2. **Separate readers from analysis.** XLSX sheets, CSV batches, JSON record paths and
   PostgreSQL relations can feed compatible table operations. Do not force all formats
   into permanent CSVs or require a full in-memory DataFrame. Preserve code/date/decimal
   semantics and explicit formula, nested-record and missingness policies.
3. **Represent analytical intent explicitly.** Profile, summarize, group, join, compare
   and export receive typed specifications. Column roles and applicability come from
   source evidence and user definitions; identifiers are not automatically measurements.
4. **Compose useful methods.** Skills explain decisions; recipes compose known operations;
   templates provide tested structure. They remain useful independently of an LLM's
   ability to generate code. Retrieve relevant methods instead of sending the entire catalog.
5. **Use generic contract correction.** Return structured field/effect/dependency findings
   to the model within a bounded correction. Keep genuine domain adapters and narrowly
   justified guards; replace equivalent special cases with shared rules, not one giant regex.
6. **Keep a controlled escape hatch.** If supported operations cannot express a task,
   optionally propose bounded Python using relevant installed packages. Preserve code,
   inputs, versions, seeds, limits and checks. Candidate skill reuse needs applicability
   tests and evidence; one successful run does not justify automatic global registration.
7. **Generate reports from evidence.** Deterministic services supply measured facts;
   agents explain and assess them. Report source/scope, method, findings, plots, checks
   and limitations through a general contract rather than a spatial-only report path.

Package indexing should avoid executing/importing arbitrary modules during discovery.
Installation, discovered functions, registered supported operations and approved
execution are distinct states. MCP/frontend/CLI coverage must be checked explicitly.

## Mode routing and agent responsibility

One primary context is the preferred starting point for Auto, subject to evaluation.
Planner may request Executor/Critic assistance for a named question with bounded evidence,
expected output and effort. Coordinator validates the request and enforces total limits.
Keep explicit Single/Three selection for reproducible comparisons and user control.

Routing inputs: uncertainty, method novelty, separable subtasks, verification gaps,
observed failed checks, operation consequence and measured runtime/resource budget.
Tokens are consumption evidence, not a sufficient difficulty score. Workflow length
alone is insufficient. Do not invent calibrated weights or claim multiple roles are
faster/better before controlled comparisons establish that.

Conversation instructions such as “use one agent” or “get a separate review” select
coordination within supported limits. Ambiguous instructions need clarification. Record
decision, reason and applicable task scope. Initially route before planning; freeze an
active execution's mode. No silent write retry, expired authority reuse or mid-run
switch without a separately designed handoff. Automatic routing is not yet implemented.

## Dependency-ordered delivery within the existing roadmap

These are consolidation slices, not replacement checkpoint numbers or a broad rewrite.

1. **Baseline and state clarity.** Trace one journey through each entry point; distinguish
   current proposal, historical graph, analytical evidence and recorded run. Acceptance:
   refresh never suggests execution occurred; every disabled Execute has an accurate reason;
   saved state is preserved without replay or new model calls.
2. **Shared task actions and result contracts.** Move duplicated behavior behind common
   actions and evidence views. Acceptance: frontend/CLI/MCP equivalent actions exercise
   the same policy/service and return equivalent facts/errors; legacy saved artifacts open.
3. **Registry-driven composition.** Consolidate metadata, prompt selection and generic
   validation feedback. Acceptance: operation addition uses the documented registration
   path without separate Planner/CLI/MCP dispatch implementations; actual entry-point
   coverage and compatibility tests pass. Prompt overhead is measured.
4. **Manual/Auto coordinator.** Add conversational overrides and explainable initial routing
   using existing modes. Acceptance: frozen run scope, total budgets and verified outcomes
   hold for both; same-model same-task comparisons record failures, calls and latency.
5. **General source and report adapters.** XLSX and JSON first, then formats justified by
   tasks; ordinary reports and staging database extensions use shared services. Acceptance:
   equivalent data across formats reconcile by types/values, full-file scope is explicit,
   source identity is retained, writes remain authorized, and reports cite recorded facts.
6. **Optional bounded Python and reusable method candidates.** Extend the worker only
   after reviewing isolation requirements. Acceptance: filesystem/network/resource tests,
   retained provenance, independent result checks and no direct live-database access.

Consolidate acceptance harnesses alongside these slices, not in a detached test rewrite.
Test data includes unrelated fixtures plus health and simulated infrastructure scenarios;
product code must not hard-code diabetes fields, expected row counts or clinical meanings.
Do not claim operational electricity/oil/gas maintenance readiness from import/export alone.

## Invariants and measurement

- Preserve operation IDs, public arguments, historical digests, approvals, saved runs and
  fixtures. Version new contracts and provide explicit compatibility adapters as needed;
  do not silently reserialize old evidence or expand old authority.
- Preserve policy, cancellation, durable state and failure/partial-output evidence.
- Historical/model text never grants execution authority. More agents do not strengthen
  permissions by themselves. Database writes remain typed and separately authorized.
- Measure correctness, user actions, useful capability coverage, duplicated paths,
  prompt size, actual calls/latency and maintenance burden. Source-file count alone and
  fixture-model token counts do not demonstrate product advantage.
- Run meaningful backend/frontend/entry-point checks during later implementation;
  none are run for this documentation-only change. No library/product parity claims.
