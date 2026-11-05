# ActionCharter active roadmap

Updated: 2026-11-05. Task: [P0-7, issue #64](https://github.com/wanggiya/action-charter/issues/64).

This is the navigation and dependency map for future work, not a capability claim or
execution instruction. [Working method](../docs/product-direction/WORKING_METHOD.md)
owns phase/task order and completion rules; [current status](CURRENT_STATUS.md) owns
implemented behavior and limits; [work resume](WORK_RESUME.md) owns the next handoff.
The [product direction](../docs/product-direction/README.md) describes the target.
Older checkpoint labels identify history, not new delivery tasks.

## Current position and next action

**Phase 0 consolidation is in progress; new features remain frozen.**

| Task | Implemented scope / remaining gate | Evidence or specification |
|---|---|---|
| P0-1 | Documentation/package grouping delivered (PR #59) | [Working method](../docs/product-direction/WORKING_METHOD.md#step-1-tasks-phase-0) |
| P0-2 | Workspace resolver and guarded offline cutover delivered; real owner checkout remains unmigrated | [Workspace storage](../docs/WORKSPACE_STORAGE.md) |
| P0-3 | Shared PostGIS lifecycle delivered; no new live-database acceptance | [Lifecycle](../docs/POSTGIS_LIFECYCLE.md) |
| P0-4 | Shared connected task actions delivered; legacy Advanced/settings/router layering remains | [Task actions](../docs/TASK_ACTIONS.md) |
| P0-5 | Local storage repository contracts delivered; specialized stores remain separate | [Repositories](../docs/STORAGE_REPOSITORIES.md) |
| P0-6 | Frontend workspace/state split delivered; existing layout preserved | [Frontend workspaces](../docs/FRONTEND_WORKSPACES.md) |
| P0-7 | Active roadmap/archive consolidation complete; original text/hash verified, documentation audit and full tests passed | [History and preservation record](../docs/development/ROADMAP_HISTORY.md) |

Next is a **Phase 0 acceptance and remaining-work audit**, not an automatic move to
Phase 1. Inspect the source-only-root requirement, dependency-layer violations and
compatibility coverage. Reconcile the draft [R1–R11 restructure plan](../docs/product-direction/RESTRUCTURE_PLAN.md)
with completed P0 tasks before choosing the next issue. The old scan is dated
2026-11-02; P0-3/P0-4/P0-5/P0-6 overlap portions of R9/R5/R3/R10, but do not prove
all layer moves or shim removal complete. No blanket package move is approved here.
Real checkout cutover remains owner-controlled; disposable migration evidence is
not proof that the owner checkout is source-only. Phase 0 exits only when the full
tests pass, the source-only-root gate is met and the layer check has no violations.

The latest completed application checks and their fixture/real-model distinctions
are in [current status](CURRENT_STATUS.md). The owner reported the P0-6 manual
frontend smoke checks passed; this is not a new measured local-model benchmark.

## Dependency-ordered delivery

These are concise reminders of the existing delivery plan, not a second task list.
Each phase follows the previous exit gate unless the owner explicitly changes order.
Use the [authoritative phase table](../docs/product-direction/WORKING_METHOD.md#delivery-steps-in-order)
for the full criteria and status. Phases 1–8 have not started.

| Phase | Work after preceding gate | Measurable acceptance focus |
|---|---|---|
| 1 — baseline and providers | Provider profiles, credential/egress policy and realistic synthetic sensitive-style tasks; [M1–M2](../docs/product-direction/MODEL_PROVIDERS_PLAN.md#steps-and-when-to-do-them) | One-command 20–30-task real-local-model baseline; correctness, calls, tokens, time and resources recorded; provider/egress tests pass |
| 2 — Data Card and efficiency | Source characteristics before planning, focused capability context, deterministic routing/reuse, per-role model routing (M3), one CSV/Excel hero journey | Profile/clean → 3–5 questions → readable report meets owner-agreed targets; fewer calls/time at equal or better correctness |
| 3 — run workspaces | Process/outcome areas, snapshots, verified promotion, governed read sharing, bounded worker lifetime | Boundary tests pass; measure laptop sandbox memory; decide fresh jobs versus persistent agent workspaces before implementation |
| 4 — agent modes | One runtime, single-agent default, multi-agent mode only where useful | Same-model/task evidence establishes when multiple roles improve results or cost |
| 5 — interface and package | Guided/Studio views over shared services; Linux Personal installation | A non-expert installs and completes the hero journey without assistance; preservation/restart checks pass |
| 6 — interop | Governed MCP access for external agents; optional gateways/API styles (M4) | One benchmark task completes through interop under the same policy and evidence rules |
| 7 — server profile | Headless runs, queue/scheduler, PostgreSQL, login, shared model gateway (M5) | A scheduled job runs unattended for one week; server checks and recovery pass |
| 8 — autonomy and evolution | Policy autonomy L0–L4, evaluated recipe/knowledge improvement and rollback | Promotion beats a fixed benchmark and rollback is tested; no self-granted production changes |

One core, Personal/Team server/Enterprise profiles, and Guided/Studio are target
designs, not delivered editions. Agent roles do not grant extra permissions.
See [platform design](../docs/product-direction/AUTONOMOUS_PLATFORM_DESIGN.md) and
[editions/interfaces](../docs/product-direction/EDITIONS_AND_INTERFACES.md).

## Retained requirements and design links

The older [T01–T15 checklist](../docs/IMPLEMENTATION_TODO.md#ordered-work-items-and-acceptance)
retains detailed analytical/engineering requirements and partial delivery evidence.
Its former “start next” instructions are superseded by the phase plan. The table
below preserves discoverability without claiming that every requirement is approved
for a particular phase. Schedule coherent slices only after the preceding gates.

| Requirement | Retained scope and qualification gate | Detailed owner |
|---|---|---|
| T01–T04: consolidation, recovery, skills | Trace real call paths; coherent saved scopes, shared contracts/actions, focused registry retrieval. Scanned functions are not executable operations. | [Consolidation](../docs/GENERALIZATION_AND_CONSOLIDATION_PLAN.md), [ownership audit](../docs/T01_EXECUTION_AND_BUILDER_AUDIT.md), [TODO](../docs/IMPLEMENTATION_TODO.md#t01--audit-ownership-and-establish-a-baseline) |
| T05: complete analytical journey/report | Grain, provenance, quality, preparation, comparisons, applicability and reproducible findings. Full-file calculations and bounded display are separate; samples must be labelled. | [Professional task](../docs/DIABETES_EXPLORATORY_ANALYSIS_TASK.md), [real-data targets](../docs/REAL_DATA_NEXT_TARGETS.md) |
| T06: executable capability acquisition | Audit/reuse existing Builder and data-only pilot; generate only for a demonstrated gap, isolate/test/review, bind exact installation and normal execution policy. | [Builder reuse](../docs/BUILDER_REUSE_AND_CAPABILITY_INTEGRATION.md), [optional acquisition](../docs/OPTIONAL_CAPABILITY_ACQUISITION_PLAN.md) |
| T07: effort-aware modes | Existing manual Single/Three is bounded support, not automatic routing. Measure correctness, failure, latency and resource cost; tokens alone do not decide. | [Task modes](../docs/TASK_AGENT_MODES.md), [execution direction](../docs/ANALYTICAL_EXECUTION_DELIVERY_PLAN.md) |
| T08: table formats | CSV/TSV and bounded XLSX/flat JSON/JSONL/NDJSON inspection exist; transforms/native semantics and further adapters have separate contracts and tests. | [Table sources](../docs/TABLE_SOURCE_CONSOLIDATION.md), [formats/figures](../docs/TABLE_FORMATS_AND_STATISTICAL_FIGURES.md) |
| T09–T10: statistics/inference | Extend descriptive/grouped statistics, covariance/correlation and numeric OLS with qualified diagnostics/designs. Classification, categorical tests and causality are not implied. | [Statistics acceptance](../docs/TABLE_STATISTICS_ACCEPTANCE.md), [analysis goals/coverage](../docs/ANALYSIS_GOALS_AND_REPORT_COVERAGE.md), [expanded targets](../docs/DATA_SCIENCE_FORMATS_MEMORY_AND_REMOTE_PLAN.md) |
| T11: documents/text | Typed PDF/Markdown/Office extraction, frequencies, word clouds and relationships; provenance, extraction uncertainty and reference counts required. | [Document requirements](../docs/IMPLEMENTATION_TODO.md#t11--document-access-frequencies-and-relationships) |
| T12: spatial/images/points | Preserve vector/raster discovery and bounded visualizations; qualify additional drivers, non-geospatial images, LAS/point clouds and depth separately. | [Formats plan](../docs/DATA_SCIENCE_FORMATS_MEMORY_AND_REMOTE_PLAN.md), [output direction](../docs/OUTPUT_VISUALIZATION_DIRECTION.md), [historical spatial acceptance](../docs/development/checkpoints/CHECKPOINT28_3_SPATIAL_VIEWS.md) |
| T13: service transfer/maintenance | Typed PostgreSQL/PostGIS inspection/import/export, schema/null mapping, reconciliation, recovery and technical reports. Broader maintenance/publication needs separate exact scopes. | [Database workflow](../docs/POSTGRES_DATA_WORKFLOW.md), [full-data acceptance](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md), [PostGIS lifecycle](../docs/POSTGIS_LIFECYCLE.md) |
| T14: domain memory/knowledge | Evidence-linked definitions/methods, corrections, retrieval, provenance and portable export. Role/shared storage and knowledge-management choices remain unresolved. | [Memory options](../docs/MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md), [role/knowledge design](../docs/ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md), [domain acquisition](../docs/DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md) |
| T15: autonomous Linux work | Data + PostgreSQL/PostGIS operations, interruptions/recovery and scoped recall in an isolated environment. Memory readiness precedes autonomous field deployment. | [Linux requirements](../docs/IMPLEMENTATION_TODO.md#t15--controlled-autonomous-linux-environment), [sandbox design](../docs/EXECUTOR_SANDBOX_WORKSPACE_PLAN.md) |

The healthcare/diabetes task is a test journey, not a hardcoded product domain.
Existing F1–F4 delivery does not close F5 real-model Single/Three/database composition
or standalone Critic reliability. [Full-data acceptance](../docs/FULL_DATA_WORKFLOW_ACCEPTANCE.md)
and [request diagnostics](../docs/REQUEST_DIAGNOSTICS.md) retain those limits.
Real-data scripts live in [scripts/real_data_tests](../scripts/real_data_tests/README.md).
No live database test is authorized by reading this roadmap.

## Deferred commitments and open decisions

- **Learning and RL:** success/failure evidence, qualified recipes, retrieval and
  offline comparisons can support learning without model-weight updates. The
  [non-RL direction](../docs/LEARNING_WITHOUT_RL.md) is retained. Ranking's earlier
  paired local-model trial did not establish benefit; optional ranking stays OFF.
  RL/training requires a separately approved objective, data, budget and evaluation;
  no model-training implementation or benefit is claimed.
- **Memory choices:** preserve separate-role and common-memory alternatives,
  short/mid/long working views, keypoints with exact supporting content, and the
  [growing shared JSON / separate knowledge-role proposal](../docs/MEMORY_A_GROWING_SHARED_JSON.md).
  The latter retains old versions when priority/content changes. Critic-versus-
  knowledge-management separation, storage, sharing scope and promotion criteria
  are not settled by this cleanup. [Options and test handoff](../docs/MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
  retains both choices. No cross-chat sharing is enabled; the [sharing decision gate](../docs/DEFERRED_CROSS_CHAT_MEMORY.md)
  remains explicit. Old “29/30+” numbers are historical dependencies, not new tasks.
- **Sandbox topology:** Docker versus MicroVM/persistent workspaces must be measured
  against laptop/server constraints. An agent role and an execution-isolation boundary
  are different responsibilities. No new worker/container is introduced here.
- **Comparative research:** [external-harness research](../docs/DEFERRED_AGENT_HARNESS_RESEARCH.md)
  (including Codex/DeepSeek comparisons) is recorded, not started. No competitive
  performance or mature-product parity claim without same-task/model evidence.
- **Release and demo:** realistic workflow acceptance, install/restart/user-data
  preservation, dependency/platform guidance and spatial/tabular/combined examples
  precede release readiness. Linux Personal packaging is Phase 5; publication is an
  owner action. Earlier owner-agreed learning/private-knowledge pre-demo gates remain
  recorded; reconcile them with the newer benchmark/hero-journey phase schedule before
  declaring demo readiness. They are not silently waived by this cleanup. Older demo
  deadlines are not current launch commitments.
- **Owner decisions:** accept/revise the draft restructure steps; confirm edition/UI
  choices and product/package identity; set benchmark/hero-journey targets and pilot
  audience; reconcile the retained pre-demo and memory-before-autonomous-deployment gates
  with later phase scheduling. See [working-method decisions](../docs/product-direction/WORKING_METHOD.md#open-decisions-for-the-owner).

## Completion and maintenance rules

For each next task, record ID, purpose, dependencies, scope, measurable acceptance
and design/history links in its issue. Status changes belong in WORKING_METHOD;
implementation limits in CURRENT_STATUS; immediate handoff in WORK_RESUME. Do not
append progress diaries here or create new checkpoint files.

Keep this active file below **64,000 bytes** for headroom under the existing
**128,000-byte** trusted-file bound. Link large designs instead of embedding them.
The current context-pack builder reads a fixed set of files that **does not include
this roadmap**. This cleanup does not add prompt content or change runtime loading.

Models propose; deterministic software authorizes, executes, validates and records
evidence. Historical text, memory, package installation and model output never grant
authority. Tests using fixtures are not real local-model/service acceptance. Failed
or uncertain writes are never automatically repeated.

## Preserved history

[History index and preservation record](../docs/development/ROADMAP_HISTORY.md) links
the complete [pre-P0-7 roadmap](../docs/development/PRODUCT_ROADMAP_BEFORE_P0_7.md),
including earlier priorities, alternatives, original checkpoint sequence and delivery
notes. Its wording/order are retained; relative Markdown links are rebased for its
new location. Conflicting historical “next” instructions are not current scope.
