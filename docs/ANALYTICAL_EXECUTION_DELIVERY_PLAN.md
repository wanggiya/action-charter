# Analytical execution delivery and agent-role assessment — proposed plan

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


Recorded 2026-10-23. Latest operator request: preserve the five-stage analytical
execution plan and assess role-based agents against single-loop/dynamic delegation.
Documentation and source review only. No runtime, frontend edits, model calls,
dataset processing, dependency changes or Git actions performed by this update.
Memory/knowledge architecture remains parked and unresolved.

## Delivery-order clarification — workflow first, flexible roles later

Recorded 2026-10-23 from the latest discussion. Preserve this order:

1. Complete the real diabetes analytical journey using current roles: codebook-aware
   full-data inspection, processing, intermediate exploration, verification and export.
   Model selection is the first coherent implementation slice in the five-stage plan.
   Fix demonstrated gaps rather than first building an agent orchestration framework.
2. Make role responsibilities independently callable with explicit input/output and
   failure contracts. Planner proposes; execution runs a validated existing workflow;
   Critic assesses an existing run without requiring regeneration. This is not a grant
   of autonomous permissions, extra processes or model calls on every path.
3. Add selective orchestration: exact inspection can remain deterministic; one
   coordinating agent with tools can handle simple exploration; execution reasoning
   and Critic are invoked when useful. Keep one user-facing conversation and one clear
   lifecycle owner. A role is not permission to bypass policy.
4. Compare combined versus separate responsibilities using the same data/task/model,
   measuring correctness, interventions, calls, latency and recovery. Retain separate
   roles where evidence justifies them. Do not start unrestricted automatic role
   switching; capabilities/authority remain explicit and changes are recorded.

“Work alone” means a role can perform its defined responsibility with supplied
artifacts, not that all services/validation are removed. The same model may fulfil
several logical roles. Role flexibility must not delay the first complete process.
Memory layout and separate knowledge-agent questions remain parked/unresolved.
Latest user instruction requests document updates and explanation of next work only;
no runtime or frontend implementation is performed by recording this direction.

## Immediate next implementation slice (proposed)

Audit the Settings model panel and shared model client/configuration. Present a minimal
available/loaded-model selector consistent with existing UI before edits. Then add
bounded Ollama discovery, persistent selection and request-pinned effective settings,
with provider-failure/schema tests and frontend checks. This is not a full Settings
redesign or permission to alter data/execute an analysis. After that coherent slice,
inspect actual table/codebook inputs and implement the analytical stages below.

## Target

Complete a real health-data analysis using full eligible source coverage, codebook
semantics, inspectable intermediate tables, deterministic calculations and bounded
execution-time reasoning. Current CSV inventory/preview is not that capability.
Finish coherent stages with measurements; no large-data/medical-image readiness claim.
Read ANALYTICAL_INSPECTION_AND_CODEBOOK_PLAN.md and HEALTH_DATA_SCIENCE_READMISSION_TASK.md.

## Proposed architecture

    Conversation -> Planner -> validated task/workflow scope
                                      |
                           Execution coordinator
                             ^               |
                   optional LLM              v
                   interpretation     typed table services
                                      ^ API / CLI / MCP
                                             |
                               intermediate refs / lineage /
                               outcomes and deterministic checks
                                             |
                                      Critic assessment

Agent roles are logical responsibilities, not necessarily separate models/processes.
Planner handles intent/approach; coordinator owns lifecycle, budgets/cancellation and
permitted dispatch; LLM assistance interprets bounded observations or proposes revisions;
Critic assesses evidence. Deterministic execution is not an LLM agent by itself.
One user-facing conversation remains the entry; avoid users orchestrating agent handoffs.
No compulsory LLM call for exact inspection, per chunk, or every trivial operation.

## Dependency-ordered stages and acceptance

### 1. Ollama discovery and runtime selection

Backend queries the configured provider's available-model and loaded-model lists.
A shared model-settings resolver supports Planner/Critic/execution assistance, retaining
existing endpoint configuration. Persist a selected model locally with explicit
configuration precedence; do not rewrite .env silently. Snapshot settings per request
so switching affects later requests, not an in-flight run. Inspect Settings styling
before proposing minimal changes. Listing/selecting does not download or invoke models.
Explicit structured-output compatibility testing is separate from discovery.

Acceptance: refresh retains selection; unavailable/provider errors visible; restart
preference behavior documented; actual model appears in request diagnostics; existing
launch configuration works; no silent fallback/authority change. Tests use stub Ollama
responses; explicitly requested live checks are distinguished from fixtures.

### 2. Typed table/intermediate references

Inspect existing operation/result contracts and worker boundaries. Add the smallest
shared table-reference contract needed: source+codebook identity, columns/types and
interpretation evidence, producing operation/parameters, lineage, row count/validation
state and temporary-storage lifetime. T1 -> filter -> T2 -> group -> T3 -> view/export.
A reference may identify lazy source operations or bounded materialized data; do not
assume all data fits RAM or every step needs a named user CSV.

Temporary scratch/cache writes, persistent artifacts and user-requested exports need
explicit effects/cleanup and authority semantics before use. Do not bypass current
write gates by calling output temporary. Session cleanup/restart behavior and stale
source detection are part of the contract.

Acceptance: intermediate inputs/outputs trace to exact sources/operations; stale or
cross-chat references reject; reopening never invents missing data or silently reruns;
no redundant private dataset copies or unexplained filesystem effects.

### 3. Codebook-aware analytical operations over full eligible data

Audit actual source paths and IDS_mapping.csv sections before selecting a parser.
Use explicit typed operations for table profiles, mapping inspection/application,
selection/filtering, derivation, joins, grouping and view/export. Reuse or extend existing
registered operations instead of a parallel dataframe engine. Column meanings and
missing codes retain sources; inferred types/semantics are labelled. IDs and age bands
are not continuous numeric measurements. Mapping cannot silently multiply/drop rows.

Chunk suitable counts/sums/means/groups; design separate resource strategies for exact
distinct counts, quantiles, joins and large groups. Preserve worker limits, changed-source
checks, cancellation, partial evidence and explicit coverage. No silent sampling or
unannounced approximation. Do not raise 8 MiB/10,000-row transformation caps blindly.
An independent reference computes the same defined full-data task. The real CSV/source
contract must be checked before declaring a specific operation supported.

Acceptance: profiles plus at least one full-file readmission grouping reconcile with
independent counts/rates on actual defined source data; mapping unknown/duplicate codes
visible; bounded paged display distinct from statistical population; elapsed time and
peak resources recorded; unsupported cases fail safely. ~18 MB is medium-sized, not
proof of huge-data support. No blanket replacement of ?/None or invented clinical codes.

### 4. Bounded execution-time LLM assistance

Extend the coordinator with permitted operation -> deterministic result/check -> bounded
observation -> continue/finish/propose revision. LLM receives schema/codebook/error and
selected relevant observations, not the entire CSV by default. Reuse the shared model
client/settings and existing effort-budget concepts. Define state transitions, allowed
read exploration, limits and authority semantics before enabling adaptive behavior.

Model/tool-call and wall-time caps, cancellation, durable progress, model/request
identity and error categories are explicit. No unrestricted Python, silent research
question/cohort change, automatic write replay or changes to approved operations.
A revision outside scope returns a fresh validated proposal and required authority.
Retrying a provider call is not permission to repeat a processing operation.

Acceptance: unknown code triggers source-backed investigation or uncertainty, not an
invented definition; helper timeout preserves workflow/results; out-of-scope requests
reject; deterministic exact reads remain usable without LLM availability. Actual-model
reliability is measured separately from mocked transition tests.

### 5. Frontend exploration and real assignment acceptance

Before frontend changes: inspect actual components/contracts, reproduce the current
browser journey in an isolated profile if tools are available, inspect layout/paging/
scroll/error behavior, then present the proposed change for agreement. Initial layout
proposal remains Overview / Data table / Columns / Codes & definitions / Checks.
Show intermediate results, full-data coverage and filter semantics; saved view reopening
must not silently scan/execute. Do not undertake unrelated navigation redesign.

Run the agreed health assignment end to end with independent reference checks; report
correctness, semantic gaps, time/peak memory, calls/interventions, cancellation, reopening
and recovery. Meaningful backend tests plus make test and make interface-validate for
implemented relevant changes; isolated browser journeys where available. No frontend
journey or implementation test was run by recording this plan.

## Is a role-based design appropriate?

Recommendation: keep small, explicit responsibilities but use demand-driven activation.
Routine path: one coordinating conversation plus typed operations. Invoke an execution
reasoning role for a specific ambiguity/adaptation and Critic for useful outcome review,
not as a mandatory ceremonial chain for every request. The separate knowledge-agent
question remains deferred with memory; do not add it to this analytical delivery.

| Arrangement | Potential benefits | Risks/tradeoffs |
| --- | --- | --- |
| One coordinating agent loop + tools | Few handoffs, unified context, simple debugging; plausible laptop baseline. | Overloaded context and self-review, less independent task decomposition, role switching can be inconsistent. |
| Explicit Planner/execution reasoning/Critic roles | Focused instructions and evidence packages; independently testable responsibilities; deterministic boundary remains clear. | Extra calls/latency and handoff schemas; lost context or stale assumptions; same-model correlated errors; rigid plans can obstruct exploration. |
| Dynamic specialists/subtasks | Adapt division of work to task; independent subproblems can be isolated/parallel. | Routing/context duplication, conflicting results and budget growth; shared data/state coordination; laptop parallelism may contend for resources. |

Roles do not themselves enforce permissions or prove independent verification. Capability
gains require operations, evidence, clear state and evaluation. A single agent can use
the same deterministic policy; role labels alone are not a security advantage. Likewise,
multiple roles sharing one model are not independent scientific judges. Parallelism is
not required for logical separation; start serially on the laptop.

Comparison plan: same source/task/model/settings and operation contracts, comparing one
coordinating loop against selective role separation. Measure reference correctness,
invalid transitions/authority attempts, intervention count, model calls, elapsed time,
peak resources and recovery. Keep failed trials. Retain a role only where measured
quality/clarity justifies cost; no claimed superiority over other platforms.

## External architecture facts checked 2026-10-23

Codex is not inherently single-agent: official documentation describes subagents and
custom role configurations. ZeroClaw is not inherently roleless: its official docs
support named agents with per-agent identities/configuration and distinguish same-
identity subagents from delegation to another configured specialist. Compare orchestration
patterns, not unsupported product labels. This source review is not a comparative test.

Sources:
- OpenAI official subagent documentation: https://learn.chatgpt.com/docs/agent-configuration/subagents
- ZeroClaw agent overview: https://github.com/zeroclaw-labs/zeroclaw/blob/master/docs/book/src/agents/overview.md
- ZeroClaw delegation: https://docs.zeroclaw.com/master/en/agents/delegation.html
- Ollama available models: https://docs.ollama.com/api/tags
- Ollama loaded models: https://docs.ollama.com/api/ps

## Resume

User asks to record/explain before runtime changes. Implementation order above is
proposed, not a claim of delivery. First inspect current Settings/model config and
present minimal UI changes; analytical storage/authority contracts precede adaptive
execution. Memory alternatives remain recorded. User controls Git/publication;
no live PostGIS/GeoServer changes. Context/model output never grants authority.
