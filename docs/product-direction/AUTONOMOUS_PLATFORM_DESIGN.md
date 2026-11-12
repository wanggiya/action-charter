# Autonomous agent platform — target design

Recorded 2026-11-01. Target architecture; **not implemented**. It extends, and does not
replace, the core principle in [context/ARCHITECTURE.md](../../context/ARCHITECTURE.md):
*models propose; deterministic software authorizes, executes, validates and records evidence.*
Model participation and the experimental model approver (2026-11-06):
[SERVER_AUTONOMY_DESIGN.md](SERVER_AUTONOMY_DESIGN.md#model-participation-in-authorization).

## Revision 2026-11-02 — read first

The owner decided to build this platform ourselves ([decision note](../decisions/2026-11-02-own-platform-direction.md)). Compared with
the original 2026-11-01 design below:

| Area | Original (2026-11-01) | Revised (2026-11-02) |
|---|---|---|
| Scope | General autonomous platform for processing, science, engineering and administration | Same long-term goal, but **verified data work first** |
| Sandbox | Sandboxed executors (Docker → gVisor/Firecracker) for isolation | **Run workspaces**: process vs outcome areas, snapshots, promotion by verification, governed sharing between agents; Docker per job now, MicroVM later |
| Data access | Connectors | **Data Card** first (header, schema, profile, quality, hash) for agents and people |
| Efficiency | Budgets and observability | **Measured efficiency** as a main differentiator (calls, tokens, time, resources; routing; recipe reuse) |
| Agents | Supervisor + about nine roles, multi-agent central | **Single-agent mode by default**, multi-agent mode optional and benchmark-justified |
| Interop | MCP as one front end | **Two-way, opt-in**: external agents use our tools; our agents can hand work to Claude Code, Codex or other agents |
| Technology | Temporal, OPA/Cedar, gVisor/Firecracker, Helm named | **Thin platform layer**: reuse proven tools; choose specific ones when the phase needs them |
| Order | Server first (headless → policy/sandbox → Supervisor → evolution) | Differentiators first; phases 0–8 in [WORKING_METHOD.md](WORKING_METHOD.md) |

Server-side unattended operation (registered automations, authorization, what stays human): [SERVER_AUTONOMY_DESIGN.md](SERVER_AUTONOMY_DESIGN.md) (2026-11-05).

Unchanged: core principle, policy, ledger, verification, autonomy levels L0–L4, agent
manifests, model gateway, editions, governed evolution. Code moves: [RESTRUCTURE_PLAN.md](RESTRUCTURE_PLAN.md).
The original design follows unchanged as the reference for those parts.

## Goal

An agent platform that runs on a laptop, an on-site server or a private cloud. It handles
data processing, data science, data engineering and (gated) administration autonomously,
with role-separated agents that improve over time. Raw sensitive data stays inside the
customer's site.

## Core idea: autonomy within policy

The desktop product today: a **human** grants permission (Authorize → Execute).
The server platform: a **policy** grants permission, and humans handle exceptions and escalations.

### Autonomy levels

Assign a level to each task type, data source and role. Raise a level only after benchmark evidence supports it.

| Level | Agent may do autonomously | Example |
|---|---|---|
| L0 Propose | Plan only | New or unknown data source |
| L1 Read | Read, profile, analyse, report | Nightly data-quality report |
| L2 Sandbox writes | Create new outputs in staging/scratch | Build a cleaned table in `staging` |
| L3 Production writes | Promote with automatic verification and a prepared rollback | Nightly ETL into `prod` |
| L4 Administration | Users, schema, infrastructure | Human approval, possibly permanently |

The existing PostGIS promotion/rollback plan → approval → execution → verification packages are the L3 prototype. Generalize them.

## Autonomous run lifecycle

```
Trigger (schedule | file arrives | table changed | goal | chat | ticket)
  → Supervisor: interpret goal, split into tasks, assign roles
  → Planner: typed plan (existing contracts)
  → Policy engine: allow | deny (record reason) | escalate (human approval queue)
  → Sandboxed worker with scoped short-lived credentials, resource limits, no internet
  → Deterministic verification (counts, schema, hashes, statistical checks)
       fail → diagnose → bounded retry → escalate
       pass → promote/commit → Critic review → report to user
  → Experience store (input to the evolution loop)
```

Invariant: model output never grants authority; only policy plus verification does.
Data content is untrusted. Treat prompt injection inside cells/documents as an expected attack.

## Architecture: control plane / data plane

```
CONTROL PLANE (decides)
  Front ends: Web UI (Guided/Studio/Admin) · CLI · REST/gRPC · MCP · chat connectors
  Goal & task service · Scheduler / event triggers
  Orchestrator: durable workflows (restart-safe, retries, timeouts, budgets)
  Agent runtime: Supervisor, Planner, Data Engineer, Data Scientist, Analyst/Reporter,
                 Ops/Admin, Critic, Builder, Librarian (memory curator)
  Policy engine · Model gateway · Capability registry · Memory/knowledge service
  Audit ledger (append-only, hash-chained) · Observability (traces, cost, latency)

DATA PLANE (touches data; can live only on-site)
  Worker pools per site / tenant / data zone
  Sandboxed executors (containers; gVisor/Firecracker for generated code)
  Connectors: PostgreSQL/PostGIS, files, S3/MinIO, SQL Server, APIs …
  Compute: DuckDB/pandas/Polars, GDAL, scikit-learn, optional Spark
  Secrets from a vault; no internet egress
```

Deployment options: both planes on-site (air-gapped), or control plane in a private
cloud with the data plane on-site, where only plans and aggregates cross the boundary.

## Agents are configuration

Each role is a manifest. This extends the existing `agents/*/manifest.yaml`. A new role
means a manifest plus tools, not a new subsystem.

```yaml
id: data_engineer
model: { route: large-reasoning, fallback: small-fast }
tools: [inspect_table, transform_table, load_postgres, profile_schema]
autonomy: { default: L2, max: L3 }
budgets: { model_calls: 20, wall_clock_min: 30, rows_written: 5000000 }
memory: { read: [recipes, schema_facts], write: [cases] }
escalate_to: human:data-team
```

Roles may share one model with separate contexts, or use different models through the gateway.

## Self-evolution loop (governed)

```
Experience store (plan, result, verification, user feedback for every run)
  → Miner: repeated successes, repeated failures, slow steps
  → Candidate, cheapest first:
       1. recipe (verified workflow template)
       2. skill/tool (Builder-generated code, sandbox-tested)
       3. prompt or routing change
       4. LoRA adapter fine-tuned on-site on own traces
  → Offline evaluation on the benchmark suite (must beat current version)
  → Canary / shadow mode on limited scope
  → Promote (versioned), or automatic rollback if metrics drop
```

No candidate promotes itself. Server editions require a human to approve promotion; the Admin console shows the evaluation report.

## Technology choices (proposed)

| Need | Choice |
|---|---|
| State, queue, audit, vectors | PostgreSQL + pgvector (server); SQLite (Personal) |
| Durable workflows | Temporal, or an in-house engine on PostgreSQL |
| Policy | OPA or Cedar (declarative, auditable) |
| Models | vLLM on server GPUs; Ollama for Personal/small sites |
| Artifacts | S3 / MinIO |
| Sandbox | Hardened Docker (exists) → gVisor/Firecracker for generated code |
| Secrets | Vault / Kubernetes secrets; agents never hold long-lived credentials |
| Identity | OIDC / LDAP / AD |
| Deploy | Desktop bundle, docker compose, Helm, offline bundle |
| Observability | OpenTelemetry + Grafana |

## Target code structure

One core shared by every edition. Arrows (←) show where the current modules move.

```
actioncharter/
├── core/
│   ├── contracts/        ← schemas.py, spatial_contracts, schema_registry
│   ├── policy/           ← write_policy.py, approvals (+ autonomy levels)
│   ├── ledger/           ← trace.py, releases, evidence persistence
│   └── verification/     ← verifier, *_verification
├── capabilities/
│   ├── registry/         ← operations, capabilities, skill_registry, discovery, skill_definitions
│   ├── tabular/          ← tabular, reporting.py
│   ├── spatial/          ← geoserver_*, vector/raster tools
│   ├── databases/        ← postgres + the 11 postgis_* packages merged into one lifecycle
│   ├── ml/               (new: training/evaluation)
│   └── admin/            (new: L4-gated)
├── agents/
│   ├── runtime/          ← orchestrator, planner, critic, builder, agent_manifest.py
│   ├── roles/            ← agents/*/manifest.yaml
│   └── memory/           ← context_retrieval, context_pack, task_history, recipes, method_memory
├── evolution/            ← builder lifecycle, skill_scaffolding, benchmarks
├── platform/
│   ├── orchestrator/     (durable workflows, scheduler, triggers)
│   ├── model_gateway/    ← model
│   ├── workers/          ← executor, sandbox
│   ├── connectors/
│   ├── identity/
│   └── storage/          (repositories; replaces the root artifact directories)
├── apps/
│   ├── server/           ← interface_api
│   ├── web/              ← interface/
│   ├── cli/              ← cli.py, chat
│   ├── mcp/              ← mcp_server
│   └── desktop/          (launcher: server + web + local model)
├── deploy/               ← docker/, compose.yaml (+ helm, offline bundle)
├── benchmarks/
├── tests/
└── docs/                 (README, architecture, user/ops guides; development/checkpoints/ for history)
```

Do not move everything at once. Follow the consolidation method in
[GENERALIZATION_AND_CONSOLIDATION_PLAN.md](../GENERALIZATION_AND_CONSOLIDATION_PLAN.md):
trace callers, move one responsibility at a time, and keep external contracts and
historical digests compatible.

## Migration phases

| Phase | Goal | Exit criterion |
|---|---|---|
| 0 Consolidate | Workspace state root (no root artifact directories), merge `postgis_*`, shared task-actions layer, storage repository interface | Full test suite passes; repo root has source only |
| 1 Headless, read-only | Server app + job queue + scheduler; L1 autonomy | A scheduled report runs unattended for a week |
| 2 Policy + sandbox writes | Policy engine, control/data plane split, vault, L2 staging writes | Every autonomous write verified and in the ledger |
| 3 Supervisor + memory | Supervisor, role manifests, case/recipe memory, vLLM gateway | Benchmark success ≥ target (e.g. 80%) |
| 4 Evolution | Miner → candidate → eval → canary → promote/rollback | Measured improvement on repeat tasks; rollback tested |
| 5 Production + admin + multi-tenant | L3 with rollback, OIDC/RBAC, Helm, air-gapped bundle; L4 behind approval | First pilot site |

## Risks

- **Model capability:** full autonomy needs much stronger models than 9B. Plan for on-site GPUs.
- **Silent wrong answers** matter more as human review shrinks. Invest in verification and Critic checks.
- **Prompt injection through data:** keep "data never grants authority".
- **Scope:** "all processing, science, engineering and administration" is too broad. Ship Phases 1–2 for one domain first (health data or GIS).
- **Compliance:** HIPAA/GDPR, audit retention, data residency. The ledger is a selling point; design export for auditors.
