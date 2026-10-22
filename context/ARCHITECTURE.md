# Architecture

## Core principle

> Models propose; deterministic software authorizes, executes, validates, and
> records evidence.

Generated text is untrusted input. It cannot grant permissions, approve a
mutation, select arbitrary executable entrypoints, or declare its own work
successful.

## Core components

- **Model:** one shared local Ollama/Qwen endpoint. Model connectivity does not
  imply tool authority.
- **Planner Agent:** receives a bounded context pack and creates a structured,
  non-executing proposal.
- **Executor Agent:** accepts only an exact authorized artifact and dispatches
  fixed approval-gated operations.
- **Critic Agent:** reads bounded deterministic evidence, identifies unresolved
  risks, and produces a schema-constrained assessment without changing status.
- **Optional capability preparation:** Planner proposes closed data-only CSV adapter candidates; fixed backend workers test them, Critic assesses applicability, and the operator explicitly installs eligible exact versions. The historical Builder lifecycle remains a separate compatibility/experimental path, not an extra agent in this pilot.
- **Human Operator:** approves or denies an exact digest and consequential step
  scope. A changed artifact requires a new decision.
- **Harness:** owns schemas, policy, state, digests, approvals, redaction,
  timeouts, failures, traces, and artifact rules.
- **GIS/MCP boundary:** owns professional-tool dependencies and credentials and
  exposes only typed, allowlisted operations.
- **Verifier:** independently reloads authoritative artifacts and inspects
  resulting state. It is deterministic software, not an LLM agent.
- **Evidence and release:** preserve digest-addressed execution, verification,
  history, and release artifacts.

## Authority structure

```mermaid
flowchart TD
    U["User / Operator"] --> P["Planner"]
    P --> G["Deterministic governance layer"]
    U --> A["Exact human approval"]
    A --> G
    G --> E["Executor"]
    E --> T["Allowlisted adapters / MCP"]
    T --> S["Professional tools"]
    S --> V["Independent verifier"]
    V --> R["Evidence and release"]
    S --> C["Critic"]
    C --> R
    M["Shared local model"] --> P
    M --> C
```

The Planner and Critic use distinct manifests, contexts, and permissions even
when they share a model runtime. The Executor has no model access. Tool and
database credentials remain inside the professional-tool boundary.

## Governed artifact chain

```mermaid
flowchart TD
    A["Request"] --> B["Typed proposal"]
    B --> C["Policy-valid plan"]
    C --> D["Plan SHA-256"]
    D --> E["Exact approval"]
    E --> F["Execution evidence"]
    F --> G["Independent verification"]
    G --> H["Authoritative evidence / release"]
```

Each downstream artifact identifies the exact upstream artifacts it depends
on. Digests are recomputed at trust boundaries. Missing, changed, expired, or
inconsistently scoped evidence fails closed.

## Runtime topology

- Planner and Critic can reach only the shared model network required by their
  roles.
- Executor can reach only the fixed internal MCP control boundary.
- GIS/MCP owns controlled data mounts, GIS dependencies, and approved PostGIS
  connectivity.
- Planner, Executor, and Critic do not receive PostGIS credentials.
- Trusted plans, recipes, approvals, contexts, and registries are read-only at
  execution boundaries.
- Runtime artifacts can be written only beneath their dedicated bounded roots.

See [runtime boundaries](RUNTIME_BOUNDARIES.md) for the mount and access matrix.

## PostGIS reference lifecycle

Checkpoints 15A–15K demonstrate the complete governed lifecycle for a
consequential mutation:

```text
bounded inspection
-> deterministic comparison
-> deterministic change assessment
-> digest-bound promotion plan
-> exact promotion approval
-> serializable promotion execution
-> independent promotion verification
-> digest-bound rollback plan
-> separate rollback approval
-> serializable rollback execution
-> independent rollback verification
```

Inspection, comparison, and assessment accept no arbitrary SQL. Promotion and
rollback execute only fixed identifier-safe mutations. Both verifiers reload
and rehash the artifact chain and inspect PostGIS through separate read-only
transactions rather than trusting executor claims.

## Historical Builder generated-extension lifecycle

The current optional data-only path is documented in [checkpoint 28.1](../docs/CHECKPOINT28_1.md); arbitrary generated Python is not enabled by it. The historical Builder cannot promote its own output. Generated candidates pass through:

```text
bounded request
-> candidate generation
-> path and content inspection
-> isolated materialization
-> network-disabled tests
-> deterministic review
-> exact human approval
-> transactional promotion
-> activation
-> post-activation verification
```

This preserves the same separation between intelligence and authority when the
system proposes extensions to itself.

28.2 adds `planner.outcome_recommendations`: bounded dispatch-contract-bound check metadata in existing SQLite, chat-private ranking supplied to Planner, and relevance-first recipe tie-breaking. No new agent/container; Critic assessments remain distinct. See [scope and limits](../docs/CHECKPOINT28_2.md).

28.2 paired evaluation reuses conversation/review/write-policy/durable-run services in disposable projects, with independent CSV/spatial result checks. The toolbar uses registered access for presentation and freshly prepares authoritative scope before direct read-only execution; writes still require exact approval. Recommendation receipts expose policy and supplied ordering, never inferred model adoption.

## Explicit inspection submission — 28.2

The [CSV-first submit coordinator](../docs/CHECKPOINT28_2_INSPECTION_SUBMIT.md)
wraps existing conversation validation, immutable plan storage and durable runs.
A deterministic policy plus fixed bounded reader enforces explicit user intent,
exact source content, chat revision, contract and no-approval read scope. Additive
submission receipts prevent replay and permit read-only reconciliation. Existing
conversation reads and plan-only commands do not dispatch. No extra LLM agent or
container is added. [Non-RL learning direction](../docs/LEARNING_WITHOUT_RL.md) is
separate proposed work, not execution authority.

## Typed result exploration — 28.3

[Result exploration](../docs/CHECKPOINT28_3_RESULTS.md) shares the existing verified
artifact reader between preview and typed full-bounded-file queries. Closed
filter/sort/page/aggregate contracts produce stable source-row IDs, bounded
profiles and explicit source/matching scopes. Planner proposes result_view from
recorded own-chat metadata; the coordinator checks scope/fields and preserves the
workflow. UI applies one explicit request, never replays it on restoration, and
uses existing tabs/charts/maps. No separate execution engine, extra agent or
model-derived plotted values are introduced.
