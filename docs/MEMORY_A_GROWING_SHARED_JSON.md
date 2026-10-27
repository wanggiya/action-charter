# Memory A revision — growing shared JSON and a separate knowledge agent

## Latest clarification — alternatives parked, data testing next

[Current retention, role options and data-test handoff](MEMORY_OPTIONS_AND_DATA_TEST_HANDOFF.md)
clarifies mutable content/priority with old versions recoverable by default, not
absolute irreversible retention. Both separate/common memories and combined/separate
Critic-curator roles remain recorded and undecided. Earlier “requires separate agent”
wording describes the preceding A proposal, not a final selected architecture.
Prepare controlled data testing next; no runtime work is authorized by this note.

Recorded 2026-10-23. Design/documentation only; no runtime implementation.
This is the latest operator direction for A. Preserve earlier designs as history,
but do not treat their conflicting defaults as current requirements for A.
The user has not selected A over B or approved an implementation protocol.

## Operator requirements for A

- Planner and Critic retain their separate short/mid/long-term memories.
- A's shared memory does not forget. It is a growing JSON collection.
- Shared-record content and priority can be updated; low priority does not delete
  a record. Age or recall frequency cannot remove shared content.
- A separate knowledge-management agent performs the knowledge function and works
  in/with the shared memory. Do not substitute an optional Critic function for it.
- Keep domain knowledge and graph relationships explicit, with source references.
- Compare with earlier proposals and leave B unchanged unless separately requested.

Private-memory retention mechanics, JSON schema/write protocol, exact knowledge-agent
schedule, scope of its own memory and storage growth policy remain to be designed.
This instruction does not expand chat/project access or authorize model training.

## Revised A flow

    USER / DATA / DOCUMENTS
                 |
          HISTORY / SOURCES
                 |
          -------+-------
          |             |
       PLANNER        CRITIC
          |             |
       private        private
       short/mid/     short/mid/
       long memory    long memory
          |             |
          --- selected contributions ---
                         |
              validated memory operations
                         |
                         v
             SHARED JSON — NO FORGETTING
             contributions, content, priority,
             sources, revisions and status
                         ^
                         | scoped reads / proposed updates
                         v
             KNOWLEDGE-MANAGEMENT AGENT
             extract, compare, qualify, revise,
             propose methods and relationships
                         |
                validated knowledge updates
                         |
                         v
             DOMAIN KNOWLEDGE + GRAPH LINKS
             conditional claims and methods;
             supported_by / requires / tested_on /
             contradicts / supersedes / applies_to
                         |
                  relevant retrieval
                         v
                   PLANNER / CRITIC

Domain knowledge is a distinct logical collection; its physical location (inside the
shared JSON or separately materialized with references) is still open. History is
not a synonym for shared memory, and a graph is the relationship representation,
not a replacement for explanations/evidence. The knowledge agent can write its own
source-linked proposals and assessments into shared memory; it has a distinct role,
instructions, input/output contract and evaluation from Critic. Separate logical
agent need not mean another container or simultaneously loaded model; runtime topology
and call limits remain undecided. Do not add per-tier memory subagents by assumption.

## Responsibilities

| Component | Duty |
| --- | --- |
| Planner | Solve/adapt tasks; retain private planning context; submit selected facts/decisions/method candidates with sources. |
| Critic | Assess task results, checks, failures and limitations; retain private assessment context; contribute findings. |
| Knowledge-management agent | Interpret contributions, extract conditional domain knowledge, identify duplicates/conflicts, propose corrections/priority and graph edges, and assess reusable lessons against evidence. |
| Memory/knowledge services | Enforce scope/schema, expected versions, safe serialization, source binding, reliable persistence, indices, export/recovery and dependency invalidation. |

The knowledge agent supplies semantic judgment; services reliably apply permitted
updates. Neither model agreement nor the new role proves a domain claim. Memory,
history and knowledge never grant execution authority. Reassessment/practice uses
independently defined checks when available, and normal execution authorization.

## No forgetting versus updates — proposed representation to evaluate

The requirement is retained shared memory with editable content/priority. Proposed
implementation: stable record IDs plus versioned updates; retain previous content,
new content, authorship, sources and reasons. Mark a wrong claim superseded/invalid,
not erased; reduce priority without removing its detail. A materialized current view
may be rebuilt from revisions. This is a proposal, not an approved JSON schema.

A growing shared collection does not mean loading its entire JSON into each prompt.
Services can maintain rebuildable indices; retrieval selects current relevant records
and expands keypoints on demand. Storage retention and prompt selection are separate.
Not loading a retained item is not deleting or forgetting it. Old erroneous versions
remain inspectable but excluded from ordinary advice. Archived retrieval must clearly
label them to prevent accidental reuse.

A correction can update a record and explicitly link affected knowledge/methods and
private notes. Services flag dependencies; the knowledge agent assesses what needs
revision. Invalidate stale cached context; preserve task history and exact execution
records. Revalidate affected plans before later execution without modifying approvals
or automatically repeating writes. Require expected-version checks for concurrent
updates rather than silent overwrite.

JSON serialization, atomic writes/recovery and multi-writer coordination need design.
Rewriting a single ever-growing document can become expensive. Do not silently replace
the requested authoritative JSON with SQLite or JSONL; explain any alternative and its
tradeoffs first. Do not prune shared records to satisfy a cap. If storage capacity is
exhausted, stop new memory writes visibly and preserve the last complete state; storage
forecasting, optional explicit archival and recovery exports need separate design.
User-directed erasure, sensitive-data retention and deletion from backups need an
explicit policy; no automatic forgetting does not settle those questions.

## Earlier structures and differences

### Earlier proposal 1 — role views over one store

    Planner / Critic -> common service -> one transactional record store
                                      -> role/tier views
    Optional Critic extraction -> knowledge records + graph relationships

This simplified storage; it did not implement two distinct memory organizations.
The operator challenged using storage backends alone as the A/B comparison.

### Earlier proposal 2 — A/B memory organization

    A: Planner private memory + Critic private memory
                    -> selected shared memory
                    -> Critic curation -> domain knowledge / graph

    B: Planner + Critic -> common tiered memory
                        -> Critic curation -> domain knowledge / graph

These differ in ownership, retrieval and private-to-shared contribution behavior,
not just file versus SQLite. Their common downstream curation was acknowledged.

### Rejected simplification for A — forgetting shared working board

    Private role memories -> temporary shared board
                          -> resolve/remove from active board
                          -> knowledge/history

The latest operator correction rejects treating A's shared memory as a forgetting
working board. Do not carry its automatic retirement/removal policy into revised A.

### Latest A — retained shared JSON with distinct knowledge agent

    Private role memories -> growing shared JSON <-> knowledge agent
                                              -> domain knowledge / graph

| Area | Earlier proposal | Latest A requirement / remaining choice |
| --- | --- | --- |
| Shared retention | Temporary board or policy-based retention/pruning | No automatic forgetting/deletion; growing JSON. |
| Content/priority | Working-note updates | Updates remain allowed; version-preserving mechanism proposed. |
| Agent responsibility | Critic optionally performs curation | Separate knowledge-management agent operates on shared memory. |
| Storage | Files versus SQLite treated as the experimental axis | A specifically requests JSON; A/B differ in memory organization. |
| Domain knowledge | Sometimes blurred into common memory | Distinct logical knowledge with sources and graph links; physical layout open. |
| Synchronization | Role copies or filtered views | Private memories reference shared revisions; dependent knowledge/notes reassessed through knowledge-agent proposals. |
| Context | Risk of conflating retained memory with loaded context | Bounded relevant reads even though shared records are retained. |
| B baseline | Common tiered memory plus earlier Critic curation | Unchanged by this A-specific direction; knowledge-agent symmetry is a future decision. |

## A/B comparison implication

A now differs from the earlier B in both memory organization and curation role/retention.
An end-to-end comparison tests the whole configuration, not the isolated effect of
private versus common memory. Do not attribute any benefit to one factor without a
controlled follow-up. First verify each mode faithfully follows its own rules.
No automatic migration/shared experiment state, production switch or Git branch work
is authorized. Both may be prototyped later in one branch with isolated state.

## Next design questions and acceptance targets

Define the knowledge-agent contract/schedule and JSON update protocol with a worked
example before code. Demonstrate: contributions retained across restart; priority and
content correction without loss of prior source/version; low-priority old item still
readable; two simultaneous updates recover safely; knowledge-agent failure preserves
shared records; corrected claims supersede old advice and flag dependents; graph links
and provenance round-trip through export. A clean compatible installation must validate
imported knowledge, not assume it is executable or trained into the model. Cross-chat
and cross-user transfer remain separately gated. Latest work is documentation only.
