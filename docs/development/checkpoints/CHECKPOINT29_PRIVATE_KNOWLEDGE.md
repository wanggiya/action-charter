# Checkpoint 29 — private sourced knowledge and corrections

## Latest clarification — alternatives parked, data testing next

[Current retention, role options and data-test handoff](../../MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
clarifies mutable content/priority with old versions recoverable by default, not
absolute irreversible retention. Both separate/common memories and combined/separate
Critic-curator roles remain recorded and undecided. Earlier “requires separate agent”
wording describes the preceding A proposal, not a final selected architecture.
Prepare controlled data testing next; no runtime work is authorized by this note.

Recorded: 2026-10-22. Planned work, not implemented functionality.
Checkpoint 28 engineering acceptance is complete; retain its measurements and limits.
This plan extends the [domain knowledge design](../../DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md).

## Latest A revision — takes precedence over conflicting earlier proposals

[Growing shared JSON + separate knowledge agent](../../MEMORY_A_GROWING_SHARED_JSON.md) records the operator's latest A requirements. Earlier Critic-only curation and retention/expiry proposals do not govern A's shared JSON. Private memory and domain-knowledge validity remain distinct from shared retention. B is unchanged. Reconcile the slices below before implementation; no runtime work is requested.

## Open design decisions — 2026-10-23

The operator considers the memory architecture unsettled. The slices below are a
working plan, not approval of the agent/service split, curator ownership, tier
policy, sharing rules, indexing, budgets or export/storage mechanisms. Review the
[open-decision register](../../ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md#decision-status--unresolved-2026-10-23)
with concrete scenarios before implementation. Latest instruction: documentation only.

## Learning method clarification

The [learning-process clarification](../../DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md#learning-process-clarification--2026-10-22) adds explanation, prediction, controlled practice, error diagnosis, revision and held-out transfer. Storage and summaries support this loop; they are not sufficient evidence of learning. Map the slices below to that loop before runtime implementation. Cross-chat scope is unchanged.

## Target and user experience

Within one conversation, retain supplied dataset definitions, domain assumptions,
processing preferences and evidence-backed methods so later compatible requests need
less explanation. Changing from spatial data to CSV in that chat must not apply
unrelated definitions. A successful run proves only its recorded checks, not domain
correctness. No automatic cross-chat retrieval, transcript pooling or sharing UI.

Normal work stays conversational. Reuse existing Chat memory and conversation
settings rather than adding another mandatory switch or knowledge-entry form.
Memory OFF excludes knowledge from Planner context; persisted records remain available
for later explicit re-enablement. Opening a chat restores saved state without a model
call. Ordinary conversation corrections should suffice; show compact expandable
“Knowledge used” references and correction/invalidation controls where needed.
Memory errors preserve the transcript and current workflow.

## Responsibility and structure

Reuse the existing conversation/planning_tasks SQLite persistence, method_helper and
method_memory integration boundaries, successful-method retrieval and Critic evidence
services. Inspect their actual schemas and settings before adding migrations. Existing
workflow-only helper notes remain unvalidated advice; do not silently relabel them as
source-backed domain knowledge. Prefer small focused modules and additive migrations
over another coordinator or parallel storage system.

Plain-text flow:

    Message / completed run and recorded checks
        -> scoped source references
        -> optional bounded Critic extraction
        -> typed candidate validation and versioned SQLite records
        -> deterministic applicability filtering and bounded retrieval
        -> Planner context with source IDs and uncertainty
        -> existing validated workflow and execution services

Planner interprets the request, uses applicable knowledge and proposes registered
operations. Critic is the existing logical assessment role, proposing lessons and
limitations from supplied evidence; no new mandatory agent, model or container.
Backend services own storage, indexing, scope enforcement, budgets, correction
transactions and authority checks. The UI explains what was used. Critic output never
verifies itself, installs operations, approves writes or changes model weights.
Docker deployment and execution topology remain unchanged.

## Dependency-ordered delivery and measurable acceptance

### 29.1 — typed records and private storage

Add versioned records for dataset definitions, domain assumptions, preferences and
method advice. Include record ID/type, conversation ID, source message/run/check IDs,
source revision/hash where available, dataset identity, applicability, confidence
category, timestamps, status and supersession links. Distinguish user-supplied claims,
model inferences and deterministically observed facts; “supplied” is not “verified”.

Acceptance: old chats and workflows reopen unchanged; records persist after restart;
queries require explicit chat scope; duplicate capture is idempotent. Same filenames
with changed contents do not inherit exact-dataset claims. No approval material is
stored as reusable knowledge. Unbound claims remain unbound, not dataset-wide defaults.

### 29.2 — bounded capture through the existing agent roles

Automatically retain source-linked candidates from eligible discussion and completed
outcomes when memory is enabled. Use deterministic capture for known structured facts;
use Critic for interpretations only when needed. Failed/partial runs retain their
failure evidence and cannot become successful method examples. Cache extraction by
source revision/evidence digest. No repeated extraction on opening or refreshing a chat.

Initial proposed limits: one optional serial extraction call per changed source bundle,
no automatic correction/retry call, source text <=6 KB, extracted document <=3.5 KB,
request <=14 KB and 15-second timeout, following existing helper limits. Bound output
tokens through the model client after checking compatibility. Record call count,
elapsed time, cache use and truncation; measure and revise limits before claiming
laptop suitability. Do not extract an entire transcript on every send or add a
mandatory model call to the exact inspection route. Acquisition should be a separate
optional job after the primary result; establish its lifecycle before implementation.

Acceptance: repeated sources generate zero additional extraction calls; timeout or
malformed notes preserve the workflow and result; no model claim becomes a verified
fact without independent evidence. Normal inspection remains usable with no model.

### 29.3 — retrieval, corrections and expiry

Start with SQLite indexes/keyword search and typed filters, without embeddings or a
vector database. Filter by chat, status, source identity, applicability and current
operation contracts before ranking. Proposed initial context budget: at most five
records and 6 KB combined, inside the existing overall prompt cap. Explicitly supplied
current instructions take precedence. Conflicts trigger a narrow clarification when
material; the model must not guess authoritative units or industrial rules.

Corrections create a new version and supersede the old record atomically. Source or
contract changes mark dependent claims stale; unrelated records remain intact. Preserve
an audit trail while excluding superseded/stale/invalid records from normal retrieval.
Implement explicit deletion with dependent-note invalidation; distinguish logical
removal from secure erasure of SQLite files/backups and document retention limitations.

Acceptance: compatible follow-up recalls the sourced definition without restating it;
unrelated CSV/spatial sources and another chat retrieve zero private records; corrected
units replace old units; changed-source claims are excluded; memory OFF contributes
zero records; retrieval failures preserve the workflow. Injection text in records never
changes skill allowlists, write settings or authorization.

### 29.4 — shared interface/CLI integration

Use the same query, inspection, correction and invalidation services in API and CLI;
keep low-level memory internals out of the ordinary user journey. Show only a compact
knowledge-used disclosure by default, with expandable sources, applicability and status.
Let users correct via chat and inspect or invalidate the affected record. Do not
redesign graph/results navigation or require manually managing recipes after each run.

Acceptance: saved chat preferences retain their existing behavior, latest workflow
restoration still works, provenance displayed matches actual Planner inclusion, and
all supplied UI corrections affect the next retrieval. CLI and API fixtures return
matching eligible records and enforce identical isolation rules.

### 29.5 — synthetic acceptance and learning evaluation

Build temporary fixtures for CSV units/missing codes, spatial CRS/measurement
assumptions, changed-source versions, contradictory corrections, topic changes and
other-chat isolation. Include misleading model notes, partial runs and failures.
Run meaningful backend tests, make test and make interface-validate; exercise complete
isolated browser journeys when available. Do not use live databases or private data.

Compare memory OFF/ON with the same model/settings and held-out follow-ups. Report
correct recall, inappropriate recall, task correctness, model calls, elapsed time and
human clarifications separately. Declare cases and benefit criteria before trials;
minimum functional gate: all deterministic isolation/correction cases pass, no authority
bypass, and sourced compatible recall passes held-out examples. Model-based improvement
requires its own predeclared paired threshold and measured result; a fixture pass is
not evidence of learned benefit. Retain failures and do not combine different versions
into one success rate. If benefit is absent, report it and keep optional enrichment
experimental rather than claiming the pre-demo learning gate passed.

## Boundaries and following checkpoints

This is source-backed memory and retrieval, not RL or Ollama weight training. It does
not acquire arbitrary executable capabilities, expose unrestricted Python or create MCP
servers. Existing bounded capability and recipe contracts remain authoritative.
No historical statement or memory can grant execution authority. Writes continue
through Allow writes, exact Authorize and Execute; read eligibility remains unchanged.

Checkpoint 30 or later may reconsider project-scoped cross-chat knowledge only after a
fresh operator decision and privacy/isolation acceptance. Portable sanitized knowledge
packages, broader code generation, training and desktop packaging remain separate work.
Controlled realistic-data and demo preparation follow evaluated private-knowledge and
learning acceptance; checkpoint completion alone must not be presented as proof of
industrial correctness, laptop scale or superiority to other platforms.

## Resume instruction

Next implementation starts at 29.1 after inspecting current storage and agent contracts.
Finish each coherent slice and document actual verification before advancing. This
update authorizes documentation only: no runtime change, Git mutation, publication,
dependency installation or live-service modification was performed.


## Handoff after learning-process discussion

Before runtime work, refine this plan with one complete worked learning exercise:
for each function specify inputs, outputs, feedback/checks, failure/stop conditions
and responsible role. Demonstrate a tentative lesson, a counterexample, correction
and held-out transfer. This addresses the operator's concern that capability lists
and memory infrastructure alone do not explain how learning will happen. Current
request records the discussion only; it does not authorize implementation or
cross-chat/RL scope changes. Resume details: [WORK_RESUME](../../../context/WORK_RESUME.md).

## Role memory and recovery design — 2026-10-23

[Role memory/curation specification](../../ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md) clarifies contribution contracts, scopes, domain labels and service/agent duties. Add minimal scoped export, safe temporary-store restore and interrupted-write recovery acceptance to 29.1/29.4/29.5 before implementation. This is private knowledge recovery, not authorization for cross-chat retrieval or portable cross-user promotion. No new runtime behavior is delivered.

## Storage alternatives and contribution simplification — 2026-10-23

[Two scenarios and ratio clarification](../../ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md#two-deploymentstorage-scenarios--unresolved-alternatives-2026-10-23) compare separate role/shared files with one transactional store and role views. Existing Planner/Critic may emit memory contributions without additional memory agents. Domain graph links and version-aware reassessment remain in both. No scenario, percentage or schema has been approved.

## Experimental selector and portable knowledge goal — 2026-10-23

[Latest design clarification](../../ROLE_MEMORY_AND_KNOWLEDGE_MANAGEMENT.md#knowledge-curation-function-and-experimental-comparison--2026-10-23) specifies source-linked Critic proposals, per-claim status, independent practice checks and no-change/caching behavior. Consider both storage adapters behind one test-only selector with isolated state; no second branch or extra agent is required. Selected package reuse on a clean installation remains a design goal with compatibility/privacy/operation checks, not a delivered feature or cross-chat authorization.
