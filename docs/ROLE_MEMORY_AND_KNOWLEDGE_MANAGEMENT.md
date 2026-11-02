# Role memory, shared knowledge and portable recovery — proposed design

## Latest clarification — alternatives parked, data testing next

[Current retention, role options and data-test handoff](MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
clarifies mutable content/priority with old versions recoverable by default, not
absolute irreversible retention. Both separate/common memories and combined/separate
Critic-curator roles remain recorded and undecided. Earlier “requires separate agent”
wording describes the preceding A proposal, not a final selected architecture.
Prepare controlled data testing next; no runtime work is authorized by this note.

Recorded 2026-10-23. Documentation only; none of the mechanisms below are delivered
by this update. Extends DOMAIN_KNOWLEDGE_ACQUISITION_DESIGN.md and checkpoint 29.
Preserve same-chat scope; project/cross-chat sharing remains separately gated at 30+.

## Latest A-specific operator revision — 2026-10-23

[Revised A and historical comparison](MEMORY_A_GROWING_SHARED_JSON.md): A now requires a growing shared JSON that does not forget, content/priority updates, and a separate knowledge-management agent. This supersedes conflicting Critic-only curation, automatic shared pruning and backend-only A/B assumptions below for A. B is not changed. Version/write protocols and full implementation remain unsettled; documentation only.

## Decision status — unresolved, 2026-10-23

The operator explicitly considers these parts unsettled. Preserve this document as
options and a working proposal, not an approved architecture or implementation order.
“Would”, “should” and numerical limits below describe recommendations to evaluate;
they are not acceptance of a specific mechanism. No runtime implementation is requested.

| Open decision | Options/questions to resolve | Evidence or example needed |
| --- | --- | --- |
| Agent versus service ownership | Which semantic decisions require model reasoning, and which explicit rules suffice? | Trace a duplicate, a contradiction and an unsupported domain claim through both paths. |
| Curator responsibility | Existing Critic duty, separate logical curator, or selective combination? How is self-review represented? | Compare failure handling, calls/latency and independent evidence; role agreement is insufficient. |
| Role-specific memory | Separate stores/files, shared records with role views, or a hybrid? | Show a private note, a common fact and a correction without divergent copies. |
| Tier policy | Who nominates and applies short/mid/long-term changes? Which items are pinned, inactive or removed? | Walk through new, old, frequently recalled, rarely used but critical, and contradicted records. |
| Keypoints and source fidelity | Which detail is retained, expanded on demand or omitted? | Recover exact original content, then show behavior when its source is changed/deleted. |
| Sharing policy | Which within-chat contributions can be shared automatically? Which require clarification? | Test private sources, linked evidence, conflicts and attempted scope broadening. Cross-chat remains separately gated. |
| Priorities and budgets | Explainable categories versus scored ranking; call/context/storage limits? | Measure correct recall, inappropriate reuse, latency and retained size before choosing weights or caps. |
| Domain classification | Small controlled labels, free keywords or a mixture? Who corrects classifications? | Test overlapping domains, synonyms, unknown labels and conflicting units. |
| Persistence and recovery | Which revision/checkpoint strategy, retention caps and backup destination behavior? | Interrupted-write and device-loss scenarios; do not confuse local history with an independent backup. |
| Export/import scope | What must be portable first, what evidence is included, and how are private backups distinguished? | Round-trip a corrected record and missing evidence without leaking unrelated content or granting authority. |
| Checkpoint boundaries | Which minimal functions belong in 29 versus later slices? | Review a worked end-to-end learning exercise and realistic laptop costs before fixing delivery scope. |

The user wants knowledge export capability; the schema, timing, UI and retention
policy are still proposals. Existing scope/authority restrictions remain in force.
Next discussion should resolve concrete scenarios and tradeoffs, not silently turn
this table into implementation instructions or another list of target capabilities.

## Purpose and learning method

Retain separate working memories for Planner, Critic and future specialist roles,
while referencing common scoped facts and methods. Explain, predict, practise,
check, diagnose, revise and test transfer; summarization alone is not learning.
Human learning is a design analogy, not an equivalence or proof of improvement.

## Structure and contribution ownership

    Planner memory       Critic memory       Future role memory
           \                  |                    /
            ------ structured change proposals -----
                              |
                     Curator reasoning role
                 interpret, compare, explain conflicts
                              |
                   Record-management service
                 validate, version, apply atomically
                              |
                    Shared scoped knowledge
                   keypoint -> content -> sources
                              |
                    Role/task-specific views
                    short / mid / long-term

Each role can select candidates and propose keypoints, detailed content, importance,
applicability and retention. Planner preferentially collects task constraints,
planning strategies, supplied definitions and unresolved assumptions. Critic collects
counterexamples, outcome limitations, checks and proposed corrections. Specialist
roles contribute their domain observations. Services supply structured measured facts.
Contributions use one contract: create, support, contradict, revise, invalidate or
request retention. Include author role, source references, reason and expected record
version. Agents do not independently rewrite a shared JSON document.

The curator is initially a bounded responsibility of the existing Critic, not a new
mandatory process/model/container. Keep originating and reviewing roles in provenance;
self-review or agreement between model roles is not independent verification. Split
curation into another logical role later only if workload/quality justify it.

## Agent/service combination: rules, not an arbitrary ratio

Do not assign a percentage of memory decisions to models. Route by decision type:

| Decision | Owner | Method / failure behavior |
| --- | --- | --- |
| IDs, required fields, access, version conflicts | Service | Typed validation, explicit scope filters, transactional expected-version updates; reject safely. |
| Exact repeated evidence | Service | Source ID/revision or digest deduplication; no new model call. |
| Semantic duplicates or contradictory explanations | Curator | Compare bounded candidates and cited sources; return a proposal with rationale and uncertainty. |
| Domain applicability or generalization | Planner / curator | State preconditions and exclusions; tentative if evidence cannot establish them. |
| Runtime outcome and numeric fixture checks | Service | Record actual observations; never infer domain correctness from process success. |
| Retention and availability | Service policy + agent suggestion | User instructions, active-task relevance, evidence state, usefulness and budgets. |
| Ambiguous consequential domain fact | User / trustworthy source | Focused question or abstention; do not resolve by agent voting. |

Call the curator only for new interpretive content or a material conflict; reuse its
cached result for unchanged sources. Initially reuse checkpoint-29 limits: at most one
optional extraction/curation call per changed evidence bundle, no automatic repair
loop, <=6 KB source, <=3.5 KB proposed content, <=14 KB prompt, 15-second timeout.
These are proposed starting limits, not proven optimal. Capture timing must not block
normal inspection or silently introduce model calls into zero-model execution.
On failure retain a tentative candidate and preserve the task; no silent promotion.
Measure calls, latency, accepted/rejected corrections, inappropriate reuse and held-out
transfer rather than targeting a human/agent or agent/service percentage.

## Memory tiers versus evidence and permissions

Record availability is distinct from validity, retention and scope. Short-term means
current task content directly available; mid-term means compact relevant candidates
and evaluated-in-progress methods; long-term means durably retained definitions,
procedures, limitations or important unresolved questions retrieved on demand.
No rule says that every old item becomes durable or that frequent retrieval proves it.
A documented critical definition can be retained immediately. An unsupported old guess
can become inactive. Retrieval can bring a durable record into working context without
moving/copying the authoritative record. Views may differ by role.

Preserve keypoint, detailed explanation, exact source references, assumptions and
exceptions separately. Never repeatedly compress the sole surviving source. A pointer
alone is not a preserved source: report unavailable/changed originals. Preserve originals
under the user's retention choices; record which details an export actually includes.
Track retrieved, used, independently supported, contradicted and user-corrected events
separately. Retrieval popularity cannot upgrade truth status or broaden permissions.

## Sharing definition and indices

Sharing is permission to read selected records or submit proposed changes, not permission
to overwrite, approve execution or access raw transcripts. Share records by reference,
not independent copies in each role memory. Maintain explicit dimensions:

- project_id and conversation_id: origin and tenancy boundary;
- visibility: role_private, chat_shared, or future project_shared;
- owner_role and allowed_reader_roles: private ownership or an explicit role group;
- applicability: dataset identity/version, fields, units, CRS and method preconditions;
- evidence_status and lifecycle_status: supplied/inferred/checked; candidate/current/
  superseded/invalid/stale;
- source_ids, source revisions/digests, record version and supersession links;
- domain labels and keywords: discovery metadata, never access permissions.

Eligibility must first satisfy project/chat/role permissions, lifecycle and relevant
applicability requirements. Only then rank candidates by exact source/task match,
explicit user retention, declared task relevance, supported successful use and recency.
Start with explainable priority categories and deterministic tie-breaking. Do not
introduce unvalidated numeric weights or a sharing percentage. Limit context to the
proposed five records / 6 KB inside the existing total prompt budget; expand a selected
source only on demand with a bounded read. Record why each item was included.

role_private -> chat_shared requires a structured, validated contribution. The curator
can recommend it under an enabled within-chat policy; services prevent accidental
inclusion of private material outside that scope. chat_shared -> project_shared is a
future separately enabled policy decision, never automatic ageing or promotion.
Source pointers and linked evidence must be access-checked too; access to a summary
does not grant access to its hidden sources. References to an unshareable source cannot
silently publish its content. Model redaction alone is not a privacy guarantee.
Corrections flag dependent role notes; keep common definitions referenced rather than
copied. Expected-version conflicts produce a fresh review, not last-writer-wins loss.

## Domains, keywords and stable identity

Use both structured labels and user-friendly keywords. Suggested extensible examples:
geography.hydrology, geography.crs, medicine.epidemiology, psychology.psychometrics,
statistics.missing_data. A method can carry several labels. Broad categories alone do
not establish validity: statistics + geography does not establish correct rainfall units.
Do not force all records into one domain or require users to classify every message.
Agents propose labels; services normalize aliases and preserve original labels. Keep
unknown/custom labels without inventing authoritative domain classification.

Unique record IDs and explicit namespace/version identify records; keywords need not
be globally unique. Similar labels are not sufficient for merging claims. Preserve
multiple conflicting claims with sources until resolved. A configurable small local
vocabulary is enough initially; no mandatory universal ontology, embeddings or vector
store. Index scope/status/source references and searchable keypoints/content separately.
Domain labels rank relevant material; typed field/unit/source compatibility constrains use.

## Storage, history, backup and export

Users should not need to supply Git, SQLite tools or a remote service. Prefer extending
the existing project-local SQLite state, with service-managed consistent writes and
versioned records. Human-readable JSON/Markdown views are inspectable exports, not a
second independently editable authoritative store.

Retain logical revisions and small append-only change events with source references;
deduplicate repeated content. Do not make a full repository/dataset copy per memory
change. Define configurable retention and caps for events, snapshots and attachments;
never claim unlimited history or silently prune pinned records without disclosure.
A same-disk history helps recover mistakes but cannot protect against device loss.

Proposed recovery/export functions, delivered incrementally:

1. Checkpoint 29: user-triggered versioned knowledge export and verified import into a
   temporary store, plus automatic recovery checkpoints around committed changes.
   Use a service-managed consistent snapshot, not a casual copy of a running database.
   Bound checkpoint counts/bytes and retain the prior complete copy if a write fails.
2. Offer a separate user-selected backup destination and a clear last-success status;
   no automatic upload, remote sync or Git commit. This can follow basic export/restore.
3. Export a manifest and versioned JSON records/events, optional readable Markdown and
   optional selected evidence attachments. Include record/source IDs, statuses,
   applicability, supersession, dependencies, schema versions and integrity hashes.
   List omitted/unavailable evidence. Reopen the export without needing a model.
4. Default export is a selected knowledge subset, excluding credentials, approvals,
   raw transcripts, datasets and private role notes. Export preview names included
   scopes and source types. Even selected knowledge may be sensitive: do not label
   automated selection/redaction as guaranteed anonymization. Full private backup is
   a distinct clearly labeled mode with explicit user choice.
5. Import is bounded, schema/path/hash checked and treated as untrusted data. Preview
   duplicates/conflicts, map source scope and preserve provenance; reject executable
   payloads and never grant authority. Missing evidence remains explicitly unavailable.
   Restoring a private backup preserves its chat boundaries; cross-project method
   promotion/generalization remains later, not silently enabled by import.
6. Restore tests compare IDs, versions, corrections, links and counts; incompatible or
   incomplete bundles reject safely. Export/import must not overwrite existing memory
   by default. User-editable imported content is a new version, not original evidence.

Git can optionally track selected sanitized text exports for users who already use it.
It is not required and is not the primary backup workflow. Do not recommend checking
in live SQLite files, credentials, personal data or private conversation history.
Deletion must address retained snapshots/exports and documented retention limitations;
logical deletion is not secure erasure. Local privacy and recovery controls precede
claims of hardened multi-user storage or portable cross-user knowledge packages.

## Acceptance and continuation

Use synthetic records to test role-private isolation, same-chat sharing, source access,
failed/outdated curator proposals, concurrent corrections, stale dependent notes,
keyword collisions, inappropriate transfer and curator timeout. No model call for
exact duplicate capture. Memory OFF injects no knowledge; no memory grants authority.
Round-trip an export into an isolated temporary store and verify corrected records,
provenance and scopes; simulate interruption and missing evidence. Demonstrate storage
caps and measure actual size/call/latency before any scale claim. Show one learning
exercise with explanation, practice, correction and held-out transfer.

This proposal clarifies how the agent and service cooperate; it does not authorize a
new runtime, cross-chat sharing, model training, Git actions or live-service changes.
Before implementation reconcile checkpoint-29 slices with the role/curator contracts,
minimal export/restore acceptance and the worked learning exercise. Keep broader
project sharing and portable cross-user packages as separately accepted later slices.


## Two deployment/storage scenarios — unresolved alternatives, 2026-10-23

The latest discussion simplifies contribution: add memory functions to the existing
Planner/Critic roles, not a required hierarchy of memory subagents. Both alternatives
below retain records, explicit graph relationships and history. Shared among roles
within an allowed chat is not cross-chat sharing. No architecture is selected here.

### Common logical modules and existing integration points

Proposed paths below do not exist as a delivered memory subsystem. Inspect existing
code before fixing names or adding a new package. A small shared module boundary
could contain schemas, retrieval, update/version policy, relationship traversal and
export/restore; keep persistent-backend differences behind that boundary.

    src/geoagent_harness/
      memory/                       PROPOSED, name/boundary undecided
        schemas.py                  record + contribution + relationship types
        service.py                  scoped read/update interface
        retrieval.py                eligibility, ranking, bounded expansion
        relationships.py            dependency links / stale propagation
        export.py                   snapshot/export/restore validation
        <chosen storage backend>    scenario A or B, not both by default
      interface_api/conversation.py existing Planner integration
      interface_api/method_helper.py and method_memory.py
                                    existing notes; inspect/reuse, do not duplicate
      interface_api/planning_tasks.py
                                    existing conversation/task SQLite persistence
      planner/successful_retrieval.py
                                    existing own-chat method retrieval to integrate
      critic/                       existing role extended with optional memory updates

Expose a common API/CLI boundary and compact UI source/correction disclosure rather
than separate role-specific applications. Existing TextPlanner and planner-conversation
client are potential frontend integration points. No new mandatory container, model
instance or continuously running memory agent is required. Reconcile migrations with
existing records, size caps, source binding and settings before code.

### Scenario A — separate authoritative role files plus shared files

    <private runtime state>/memory/       proposed layout, not source-controlled
      roles/planner/records/             Planner-owned notes
      roles/planner/index.json           tier/keypoint references
      roles/critic/records/              Critic-owned notes
      roles/critic/index.json            tier/keypoint references
      shared/records/                    common definitions/methods within scope
      shared/relationships.jsonl         source/dependency/correction edges
      history/events.jsonl               contributions, versions and corrections
      recovery/                          bounded checkpoints / update journal

Planner/Critic nominate changes through scoped service functions; they do not rewrite
large shared files directly. Common facts are referenced, not copied. A file backend
would need serialized writes, expected-version checks, durable journal entries,
recoverable multi-file commits, restart reconciliation and index rebuild. File names,
append/compaction strategy and journal protocol remain unresolved.

Effect on project structure: introduce a file-storage adapter and recovery/index
machinery; existing agent code gains calls/structured contribution outputs, not new
subagent trees. Existing conversation/task storage may remain SQLite, so references
between it and file memories need an explicit recoverable binding protocol. Export
must capture a consistent file generation, not a half-completed update.

Benefits: separately inspectable role areas, portable text, clear ownership.
Costs: more synchronization/recovery code, filesystem churn and potential duplicates.
Separate files alone do not provide privacy. Model call count is not inherently higher
or lower than scenario B; compare the actual curation policy and measurements.

### Scenario B — one authoritative transactional store with role views

    Existing private project SQLite state, extended after migration review
      memory_records / versions          owner, readers, scope, keypoint and content
      memory_sources                     evidence references and source identity
      memory_edges                       supported_by/requires/supersedes/tested_on
      memory_events                      update and usage history
      memory_view_state                  tier selections/pins, not content copies

These are conceptual proposed tables, not approved names/schema. Reuse existing
planning_tasks database infrastructure if its lifecycle/caps fit; do not add a second
persistent store by default. History may reference existing messages/runs instead of
copying their full contents. JSON/Markdown files become user-facing exports rather
than competing live stores. Role-private access remains explicit despite shared storage.

Effect on project structure: introduce additive migrations and a transactional storage
adapter; service/agent/frontend interfaces otherwise resemble scenario A. Record,
version, edge and event updates can commit together. Cached views are rebuildable;
exports use a consistent snapshot. Existing workflow digests and saved results remain
unchanged. Check actual migration/locking behavior rather than assuming it is free.

Benefits: less duplicated state, simpler consistent corrections, flexible indexed views.
Costs: careful schema/permission management, migration work and reliance on inspection/
export tools for readability. Same-store corruption/device loss still requires backups.

### Contribution and synchronization flow in both alternatives

1. Preserve the ordinary response/assessment in history. Do not equate everything an
   agent says with a new fact. Optional typed memory updates can accompany its normal
   output, subject to small-model schema evaluation; exact structured facts need no LLM.
2. Submit candidate/shared updates with source IDs, proposed meaning, evidence status,
   applicability, expected version and operation type. Role notes remain role-scoped.
3. Validate scope, deduplicate and commit consistently. On a concurrent edit, reject
   the stale expected version and reconcile against the current record; no silent
   last-writer-wins. Semantic conflict may need bounded Critic reasoning or clarification.
4. Preserve superseded history. A correction flags explicit dependents and cached
   summaries; it does not trigger a model reread of all transcripts. Missing usage links
   are a known limitation; require structured knowledge-used references where possible.
5. Retrieval excludes superseded records and surfaces stale essential methods with a
   warning. Reassess only affected needed records; a parameterized generic method may
   remain valid while a dataset-specific conversion changes. Do not auto-upgrade evidence.
6. Bind plans to knowledge versions used. Consequential changes require scope/plan
   revalidation before later execution; never silently mutate approved operations,
   reuse mismatched authority or rerun writes. Completed runs remain historical facts,
   with affected interpretations annotated rather than rewritten.

Tier state is independent from record ownership, evidence status and access scope.
Age/recall can affect availability, not silently publish private notes or certify truth.
An optional curator remains a duty of an existing role initially, not a required
third agent. A dedicated role can be considered later based on measured workload.

## Ratio discussion: clarification and unresolved choices

The explicit ratio question was the balance between agent reasoning and backend
services (and whether sharing should use a ratio). No numeric split such as 70/30
was agreed. Proposed response: decide by responsibility, not percentage. Semantic
interpretation belongs to an agent; permissions, versions and durable writes belong
to deterministic software. No “percentage shared” can replace explicit access scope.

Separate issues must not be conflated with that question:

- Context allocation across short/mid/long-term: a possible later tunable budget;
  no fixed percentage was selected. Use bounded relevant retrieval first, then compare
  recall/cost before proposing allocations. Reserved system/task space is separate.
- Ranking weights for recency, frequency, importance and usefulness: unresolved;
  no formula or decay coefficient approved. Retrieval frequency is not verification.
- Sharing scope: an explicit permission/applicability decision, not a ratio of records.
- Calls/time/bytes: initial proposed limits are experimental caps, not agent/service
  ratios or proof of acceptable laptop cost.

Next design comparison should use the same small learning/correction exercise in both
scenarios, including simultaneous updates, stale sources, restart and export/restore.
Choose based on correctness, maintenance burden and measured cost, not the number of
memory layers or agents. Documentation only; implementation remains unapproved.


## Knowledge-curation function and experimental comparison — 2026-10-23

Latest operator request: record the concrete Critic curation flow, consider two
separated experimental memory implementations selectable during testing, and explain
portability to a clean installation. Documentation only; no runtime switch, branch,
training or package installation is delivered or authorized by this note.
Interpret the two implementations as storage scenarios A/B above, not evidence that
one is better, and not two agent teams or model instances.

### Concrete curation flow

Eligible triggers: a supplied definition/procedure, assessed completed workflow,
meaningful correction or useful failure. Ordinary acknowledgments and unchanged
sources do not require extraction. Preserve the primary response/outcome first.
Backend assembles a bounded source-linked bundle of relevant excerpts, current
workflow/knowledge versions, actual checks, related records and unknowns. Structured
observations can be recorded directly without a model.

The existing Critic receives a dedicated optional extraction contract with actions
create/support/revise/contradict/no_change. Proposal fields: keypoint, detailed
conditional lesson, applicability/preconditions, source IDs, per-claim evidence state,
exceptions, related record/version and suggested practice cases. Prefer integrating
with an existing assessment when there is sufficient evidence; do not add an obligatory
call or make memory success a condition for returning the task result. Test whether
combined output complexity hurts small-model reliability before choosing the protocol.

Service validates references, permissions, duplicate/conflict/version state and
commits candidates; it does not certify scientific meaning. Unsupported generalization
remains tentative. A fixture can verify conversion arithmetic without verifying a
user-supplied unit definition. Preserve this distinction per claim.

Practice loop: worked example -> candidate -> predicted compatible/counterexample
results -> independent checks -> correction -> held-out transfer. No independent check
means advice with uncertainty, not manufactured verification. Missing executable
operations remain explicit capability gaps. Retrieval expands eligible keypoints with
details/sources on demand and records exact knowledge versions used. Corrections
supersede claims and flag dependent notes/methods; reassessment is selective and bounded,
never an automatic full-history scan or rerun of writes.

### Test-only backend selector

Proposed common interface: retrieve, read details, submit contribution, revise,
inspect history, export and restore. Implement a file backend and a transactional-store
backend behind the same semantic contract. Tests use explicit backend selection and
separate state roots. A developer/test configuration switch can select A or B; exact
name and UI remain undecided. No user-facing production switch is necessary.

A switch selects one backend for a test/session; it does not mix records or migrate
an active session automatically. Use isolated memory state, extraction caches, settings,
indices and evaluation outputs for each variant. Preserve stable source fixtures but
separate receipts/history as necessary to prevent duplicate execution or evidence
contamination. Never fall back to the other backend silently on failure. Do not dual
write by default or compare variants by live production writes.

A single feature branch can contain both adapters and a selector; two long-lived Git
branches are not required. Separate branches are optional for incompatible prototypes,
but introduce drift and make fair comparisons harder. No branch is created by this
request, and the user continues to own Git actions.

Keep model/settings, prompts, source fixtures, tier and eligibility policies, context
budgets and task cases equal when testing storage differences. First replay identical
structured contributions to isolate storage correctness/cost; then compare complete
agent journeys in isolated fresh states. If testing different memory policies rather
than just storage, declare that as another experimental factor. Run variants serially
on the laptop initially. Measure recall/incorrect transfer, correction propagation,
concurrent-update/restart safety, export fidelity, model calls, latency and storage.
Record failures and repeated trials; experience over time is useful but not a controlled
comparison by itself. Keep the production choice unresolved until these results exist;
retain only the chosen production backend if carrying both adds unnecessary burden.

### Portable domain knowledge: desired result and compatibility boundary

Goal: after repeated assessed use, export selected definitions, conditional methods,
examples, counterexamples and corrections, then import them into a clean compatible
installation without replaying the original conversations. This transfers external
knowledge, not a trained model's weights, automatic correctness or new executables.
It is possible only where the target supports the package schema or has an adapter.
Arbitrary other platforms will need an import/retrieval integration; readable JSON
and Markdown alone cannot make them automatically use the package.

Proposed package components:

- Manifest: package identity/version, schema version, provenance, intended domains,
  applicable conditions, limitations, dependencies and integrity hashes.
- Knowledge records and graph edges: definitions, conditional explanations, units,
  source/evidence status, supersession links and stable source/package identities.
- Parameterized methods using registered operations; dependencies/contracts are
  declared, not assumed present. Avoid retaining original private paths and targets.
- Synthetic worked examples, counterexamples and held-out checks where distributable;
  list evidence omitted/unavailable, rights/usage constraints and remaining uncertainty.

Export previews selected content and excludes credentials, authority records and raw
private transcripts by default. Domain explanations themselves may be sensitive;
redaction is not guaranteed anonymization. Generalizing a dataset-specific claim is a
reasoning/review task, not stripping its scope. Keep local dataset-specific records
local unless explicit export selection and evidence support the intended scope.

Import validates schema/size/paths/hashes, dependency contracts, source accessibility,
conflicts and scope mapping in a temporary store. Map package references to new local
record IDs where needed; keep original provenance. Imported claims retain their
original evidence status. Run available fixture checks before enabling executable
method reuse; unresolved prerequisites leave it discoverable but unavailable to run.
Import grants no write permission and installs no code/dependencies by implication.
A knowledge package and a governed executable-operation package remain separate.

Acceptance demonstration: installation A acquires/corrects a synthetic rainfall
method; export selected records; installation B starts empty and imports; B retrieves
the corrected method, passes a new compatible case and rejects an incompatible case
without original-chat access. Show missing-source and missing-operation behavior.
This is a future portability test/goal, not authorization to enable cross-chat recall,
install packages or share private knowledge now. Reconcile delivery timing with the
existing 30+ sharing gate and the unresolved checkpoint-29 export/restore scope.
