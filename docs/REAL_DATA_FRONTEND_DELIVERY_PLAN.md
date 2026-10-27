# Next real-data frontend delivery — integrated scope

**Implementation update — 2026-10-25:** the CSV/TSV profiling, shared typed tool,
Docker job pilot, recorded graph and interactive Outcome portions are implemented.
See [delivered scope and acceptance](COMPREHENSIVE_INSPECTION_DELIVERY.md) for tested
boundaries and remaining limitations. The original design below is preserved history;
it is not evidence that every planned operation or future sandbox adapter is complete.

## Docker versus MicroVM clarification — 2026-10-25

Docker is the initial worker backend. MicroVM is a later isolation option, not a claim
of smaller size than a container: containers share the host kernel; MicroVMs add a
guest kernel and virtualization lifecycle. Image size depends on packaged dependencies.
“Micro” compares with traditional VMs. Evaluate stronger containment against resource
and deployment costs; neither runtime proves security without boundary tests.


Recorded 2026-10-25. **Agreed next scope, not implemented by this document update.**
This is the latest ordering clarification: deliver a useful agent-assisted real-data
inspection journey, including an Executor-managed Docker calculation worker. Neither
sandbox infrastructure alone nor frontend-only profiling constitutes completion.
Earlier sandbox-first and analysis-only summaries are preserved history; this document
coordinates their scope rather than replacing their technical details.

Related designs: [typed comprehensive inspection](COMPREHENSIVE_DATASET_INSPECTION_PLAN.md),
[Executor sandbox/workspace](EXECUTOR_SANDBOX_WORKSPACE_PLAN.md),
[full diabetes task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md),
[current analytical loop](BOUNDED_ANALYTICAL_LOOP.md) and
[current graph/inspector](ANALYTICAL_GRAPH_AND_INSPECTOR.md).

## Delivery objective

From one frontend conversation, the agent discovers relevant files, understands their
available structure, assesses feasible processing, obtains comprehensive appropriately
typed profiles, explains recorded findings and supports interactive exploration. The
graph shows the actual process primarily left to right; clicking Outcome opens useful
data views. Users can reopen evidence without regenerating the analysis.

The supported calculation path also runs in a demonstrably isolated Executor-managed
Docker worker with private scratch and recorded runtime evidence. Users should not
manually manage jobs or choose mounts. A Docker pilot is a dependency slice of this
same delivery, not a substitute for analytical usefulness.

## Included — all parts required for the integrated acceptance

| Part | Intended functionality | Completion evidence |
| --- | --- | --- |
| Agent behaviour | Discover, assess operation-specific feasibility, select supported reads, calculate, explain and suggest useful follow-ups | Natural-language real-data journey grounded in tool evidence, with measured model calls/failures |
| Comprehensive inspection | Cover all fields with observed types/analytical roles and suitable quality/statistical summaries | Independent complete-source comparisons, explicit coverage/algorithms and no sampled totals presented as full totals |
| MCP/shared services | Typed capabilities available to agents, API, frontend and CLI | Equivalent analytical facts for equivalent queries; no unrestricted library namespaces |
| Executor runtime | Governed job dispatch into a restricted Docker calculation worker | Actual sandbox launch, negative isolation tests and parity with shared service results |
| Workspace/artifacts | Private bounded scratch, scoped intermediates/cache and validated result manifests | Ownership, quotas, source-change invalidation, cleanup and restart tests |
| Graph | Mostly left-to-right inputs/actions/results, honest failure and scope states | Complete/partial browser journeys; no invented approval/Critic/execution steps |
| Outcome | Interactive overview, column profiles, distributions, table/group exploration and checks | Clicking Outcome opens real recorded results; selections and restore work without needless model calls/scans |
| User validation | Source and existing sample tested through the actual frontend path | Clear repeatable instructions, independent numerical checks, runtime evidence and accurate limitations |

## What “Executor container included” means

Sandbox-worker lifecycle is part of the Executor responsibility. Reuse existing
execution/permission/validation services and define a runtime adapter; do not add a
second competing Executor or another worker agent.

The initial target is one controlled Docker worker path for CSV profiling, extended to
the comprehensive profiling operation used in the delivered frontend journey. This
includes validated job inputs, image/runtime selection from approved templates, selected
read-only input mounts, private scratch, resource limits, cancellation/cleanup behaviour,
output validation and runtime provenance. Workers receive no credentials, management
socket or general network access. Agents cannot supply arbitrary Docker commands or mounts.

Existing Compose role/tool containers are not proof of this boundary: the local analytical
path currently launches bounded subprocesses; the Compose executor command alone is
agent-info. Audit/reuse appropriate existing images and contracts. Do not claim every
spatial/database operation has migrated to per-job workers in this first delivery.

Reusable services can run separately from workers; the enforced container boundary must
surround calculation. Initially reuse images/code, not live worker state across jobs.
MicroVM support is a later adapter. A separate long-lived LLM Executor container is not
required to implement this responsibility.

If the required sandbox is unavailable, report that fact. Do not silently run a host
subprocess while labelling the result sandboxed. Any explicit compatibility mode must
identify itself and cannot satisfy the Docker isolation acceptance gate.

## Inspection and calculation requirements

- Profile every field without the user naming each numerical column or the model making
  one tool call per field. Preserve bounded summaries and paged result/artifact access
  rather than sending an entire dataset/profile dump into model context.
- Report storage/observed form and analytical role: numerical measurement, count,
  categorical code, ordered band, identifier, free text or uncertain/mixed. Preserve
  original strings and leading zeros; type compatibility does not establish semantics.
- Numerical fields: valid/missing/invalid counts, mean, min/max, spread, median/quantiles
  and useful distributions. Specify exact/approximate methods and resource limits.
- Categorical/band fields: frequencies/proportions, rare or unexpected levels, ordering
  where supported, missingness and supplied codebook coverage. No arithmetic on ID codes
  or invented exact ages/weights from bands.
- Identifier fields: distinct/once-only/repeated values, key constraints and duplicates;
  distinguish recurring patients from duplicate encounters.
- Distinguish raw empty cells, candidate missing markers and interpreted missing values.
  Report evidence and proposed policy compactly; do not silently recode Unknown/None or
  demand repetitive classification of every field before showing useful information.
- Distinguish not applicable, not calculated, unavailable due to limits and failed.
  Classification uncertainty needs a readable explanation and correction path.
- Prefer complete-source streaming when feasible. Sampling is operation-dependent;
  neighbouring filenames and matching headers do not prove sample provenance.

## Dependency-ordered work slices

1. **Audit and contracts.** Inspect actual profiling coverage, worker protocol, container
   images/runtime support and Results components. Define typed dataset/profile, job,
   artifact and runtime-evidence contracts. Present the frontend layout before edits.
   Acceptance: a concrete gap map and compatible contracts covering every included part.
2. **Comprehensive shared profiling and minimal Docker pilot.** Implement appropriate
   type/role classification and calculation primitives while wiring one supported CSV
   profile job through Executor-owned sandbox/workspace services. Extend that path to
   the complete profiler rather than create two unrelated calculation engines.
   Acceptance: correct synthetic results, clear unavailable/type states and a real worker
   path with bounded artifacts. Do not stop after a standalone container demonstration.
3. **Isolation and shared-tool integration.** Prove input immutability, denied host/other-job
   access, absent secrets/socket, blocked network, enforced quotas, cancellation/crash
   cleanup and no automatic write replay. Expose shared capabilities through typed MCP,
   API and CLI. Acceptance: negative boundary tests plus numerical/result parity.
4. **Agent analytical loop.** Give the existing reasoning role compact schema/profile
   evidence and supported tool choices. It chooses a strategy, obtains calculations,
   explains results and handles limits/partial failures honestly. Keep validation outside
   model judgment and preserve current workflow/authority. Acceptance: matched direct
   and conversational queries, recorded budgets/interventions and calibrated explanations.
5. **Graph and interactive Outcome.** Correct predominantly left-to-right layout and open
   the proper Results workspace on Outcome selection. Reuse current style, resizing and
   existing table/chart interaction where useful. Surface types, source/sample coverage,
   denominators, calculations and actual worker/runtime evidence. Acceptance: complete,
   partial, refresh, source-switch and new-chat browser journeys without authority leakage.
6. **Real-data frontend acceptance.** Use the existing diabetes source, 5,000-row sample
   and codebook in temporary automated fixtures, then provide exact user-facing steps
   for data/input/test. Compare independent full-file figures, classifications and
   appropriate summaries. Record performance/limits/model failures separately. The
   delivery closes only when analytical usefulness, frontend interaction and Docker
   boundary evidence pass together; report unavailable gates rather than claiming completion.

Implementation within each slice may batch independent work, but scope/validation
contracts precede runtime and frontend assumptions. Use meaningful tests, make test and
make interface-validate, and actual interface journeys when browser tooling is available.
Docker builds/launches are future implementation work, not performed by documenting this plan.

## Deferred from this delivery, without losing the larger task

- MicroVM backend and live-worker pooling.
- Migration of every existing operation, unrestricted generated code or shell access.
- Statistical relationship inference, confidence intervals and adjusted modelling; these
  follow this inspection/exploration foundation in the full health-data assignment.
- Retained sample creation/export adapters if not yet registered: the agent must report
  the missing capability. Any implemented retained write uses Allow writes → Authorize →
  Execute and explicit provenance; scratch does not bypass this gate.
- Flexible multi-agent scheduling/role reassignment, group communication and simulated
  Linux-server evaluation after one successful complete data journey. Roles are
  responsibilities and may be assigned across compatible actors without changing authority.
- Memory architecture choices, RL and release/publication.

## Resume rule

Read this integrated plan first. Preserve user data, existing changes and checkpoint
history. Do not replace the goal with sandbox infrastructure alone, selective metadata
inspection alone or a visual redesign alone. Do not stage, commit, push, merge or publish.
The operator requested recording scope in this turn; no runtime or data work is authorized
merely by this document update. Begin implementation when requested in a later turn.
