# Server autonomy — authorization and structure

Recorded 2026-11-05 from an owner discussion. **Design direction, not implemented.**
Decision: [2026-11-05 server autonomy direction](../decisions/2026-11-05-server-autonomy-direction.md).
Extends [AUTONOMOUS_PLATFORM_DESIGN.md](AUTONOMOUS_PLATFORM_DESIGN.md) (autonomy levels,
control/data plane, ledger) and the [model-provider plan](MODEL_PROVIDERS_PLAN.md).

## Goal and scope

The owner's long-term goal: the platform runs as a backend service and handles data
processing, data engineering and administrative work **automatically, in real time, as
situations change**, with as little human work as governance allows.

Scope order: **on-site / self-managed server first.** Public cloud (AWS and others) later,
through the same interfaces; an AWS mapping is kept at the end for reference.

## Is full autonomy practical? (assessment)

Partly, and increasingly — as a direction, not a promise of "everything, no humans".

A task type can run without humans only when **all five** hold:
1. **Clear goal** — there is a right answer.
2. **Checkable result** — deterministic software can tell whether it worked.
3. **Reversible or contained** — rollback exists, or the work stays in staging.
4. **Bounded impact** — budgets and scope stop it from going wrong at scale.
5. **Track record** — this task type has succeeded many times under supervision.

Only what can be **verified** can be automated safely; the verification-first design is
the foundation for this.

| Practical now or soon (with governance) | Keeps a human (possibly permanently) |
|---|---|
| Ingest a file → validate → load to staging → quality checks → report | Irreversible actions: deleting data, breaking production schema changes |
| Schema drift → adapt transform in staging → verify → promote with rollback | **Granting permissions or access** (an agent that can grant itself access defeats every control) |
| Scheduled data-quality monitoring, anomaly alerts, routine refreshes | Security configuration changes |
| Backup checks, index/storage maintenance, retention clean-up | New incidents with unknown cause |
| Known-incident runbooks (restart, retry, fail over on a recognised pattern) | Legal, financial or ethical decisions |

Further constraints:
- **Accountability:** every automation has a named human owner, even when no human is in the loop.
- **Speed:** LLM decisions take seconds to minutes. Fine for data/admin work; millisecond
  reactions use deterministic rules, with the LLM only planning new responses.
- **Model capability:** a 9B model is not enough for unsupervised engineering decisions;
  server autonomy needs larger on-site models (allowed by the model-provider plan).

**Target:** humans *out of* the loop for routine work, humans *on* the loop for
exceptions; autonomy per task type is **earned by measured track record**. Over time the
share of work needing a person shrinks. L4 (administration, permissions) stays human.

## Core concept: registered automation

A human approves an **automation** once. That approval is the standing authority; runs
inside it proceed automatically; anything outside it escalates.

```yaml
id: nightly-admissions-load
owner: team:data-engineering          # accountable humans
trigger: { type: file_arrived, location: inbox/admissions/*.csv }
operations: [inspect_csv, validate_schema, clean_table, load_staging, quality_report]
targets: { read: [inbox/admissions], write: [staging.admissions] }
autonomy: L2                          # L3 requires a prepared rollback
budgets: { wall_clock_min: 30, rows_written: 5000000, model_calls: 20 }
on_failure: escalate                  # after bounded retries
expires: 2027-05-01                   # re-approval required
```

Existing **approved recipes** are the starting point for automations.

## Structure (server first)

```
Triggers: file arrives · table changes (DB change stream) · schedule · API / ticket
   → Event intake → job queue (PostgreSQL-backed first)
   → Control plane (API + orchestrator; run state in PostgreSQL)
        → match a registered automation (no match → nothing runs / ask a human)
        → agent plans (model via model gateway)
        → POLICY DECISION: allow | deny (reason recorded) | escalate
   → Credential broker: short-lived credentials scoped to this run
   → Sandboxed worker (no internet; Docker now, MicroVM on KVM hosts later)
        writes only to its process area → snapshot → deterministic verification
   → pass: promote to outcome (staging, or production with rollback) → ledger → notify
     fail: diagnose → bounded retry → escalate
```

## Authorization — three separate questions

| Question | Answer |
|---|---|
| **For whom is this run?** | Every run records an **owner** (who registered the automation) and an **initiator** (user acted for, or `system` for events). |
| **Is it allowed?** | **Our policy engine** decides from: owner, role manifest, autonomy level for task type × data source × environment, data classification, budget, time window. Candidates: Cedar or OPA. The model's plan is only an input. |
| **With which credentials?** | Only after "allow", a **credential broker** issues 15–60-minute credentials scoped to exactly this run (e.g. read one source path, write one staging schema). Databases: per-run roles or dynamic credentials (e.g. Vault). **The agent/model process never sees credentials**; only the worker executing the typed operation does. |

### Two enforcement layers

1. **Our policy** (application layer).
2. **Infrastructure permissions** as backstop — even if our policy has a bug:

| Level | Infrastructure role | Allowed |
|---|---|---|
| L1 | read-only role | read, profile, report |
| L2 | staging-write role | write staging only |
| L3 | production-write role | only with prepared rollback |
| L4 | **not assumable by automation** | human with MFA, each time |

### Other required controls

- **Human approvals:** signed by an authenticated person (OIDC/LDAP), bound to the exact
  plan digest (as Authorize is today), with expiry.
- **Limits:** per-run budgets; rate limits; **kill switch** per automation and global;
  circuit breaker after repeated failures; a lock per target so two runs cannot write the
  same table at once; **idempotency key** per event so retries never run twice.
- **Untrusted input:** an event or data content only selects *which registered automation*
  runs; it never grants authority. Prompt injection inside data is expected.
- **Audit:** append-only, hash-chained ledger; every model call, policy decision,
  credential issue and promotion linked by run id. Export for auditors.

## Model participation in authorization

Owner decision 2026-11-06 ([note](../decisions/2026-11-06-model-participation-in-authorization.md)):
**models participate in most of the process and seldom grant authority; the option for
a model to approve is kept, as an experimental feature first.**

### Default: models participate, policy grants

| Model role | Default |
|---|---|
| Plan, choose operations, write transforms in the sandbox | Yes |
| Review plans and results (Critic); flag semantic risks rules cannot see (identifiable patients in a report, quotes out of context, suspicious queries) | Yes |
| Make a decision stricter: deny, escalate, lower budget, add a check | Yes, always allowed |
| Classify data sensitivity | Yes; when uncertain the stricter class applies |
| Draft new policy rules from repeated escalations | Yes; active only after human approval, then deterministic |
| Approve an action | **Only via the experimental model approver below** |

Policy results are `allow`, `deny` or `escalate`. A model reviewer can turn `allow` into
`escalate`/`deny`. `escalate` normally goes to a human.

### Experimental: model approver

A model may resolve an `escalate` to `allow` only when **all** of these hold:

| Guard | Rule |
|---|---|
| Off by default | Enabled by a human per registered automation (or per task type in Personal), with expiry. Shown as **experimental** in UI and reports |
| Only the grey zone | Only actions the policy marks `escalate`. A policy `deny` is final |
| Hard limits (never model-approvable) | L4 work; granting permissions, roles or credentials; security configuration; irreversible actions (deleting data, breaking production schema); raising data-egress class; raising budgets above the human-set ceiling; changing any automation's or its own autonomy level |
| Ceiling | The human who enables it sets the maximum scope (targets, row counts, budget). The model approves only inside it |
| Contained | Approved work must be reversible or stay in staging (rollback prepared for L3) |
| Independent | Approver is separate from the planner: different prompt/role, preferably a different model; it sees the structured plan and evidence, not raw untrusted data where avoidable |
| Recorded | Ledger marks the decision **model-approved**, with model id/version, input digest, rationale and confidence; reports separate model-approved from human-approved work |
| Earned | Starts in **shadow mode**: the model decides, a human still decides, agreement is measured. Becomes active only after meeting an agreement threshold on the benchmark and on real escalations |
| Watched | Humans audit a sample of model approvals; disagreement or failure trips a circuit breaker back to human approval |

Why keep the option: fewer human escalations and more autonomy for routine grey-zone
cases. Known risks (prompt injection through data, non-reproducible decisions, weaker
audit explanation, shared blind spots between planner and approver) are why the guards
above are required and why it starts experimental.

Timing: shadow-mode data collection can start once escalations exist on the Platform
edition (Phase 7); activation is Phase 8. Nothing is built in Phase 0.

## What to build now vs later

| When | What |
|---|---|
| **Phase 0 (R12, now)** | Seams with local implementations: every task action takes an **actor** and a **run context** (run id, trigger, budget, idempotency key); interfaces for **policy decision**, **credential broker**, **job queue** and **clock**. Cheap now, expensive later. See [RESTRUCTURE_PLAN.md](RESTRUCTURE_PLAN.md). |
| Phase 0 (P0-5b) | Authority, evidence, lifecycle and ledger stores behind the storage contracts, with a concurrency contract |
| Phase 3 | Run workspaces (process/outcome, verified promotion) — the basis of safe unattended writes |
| Phase 7 | Server profile: PostgreSQL storage and queue, login, event intake, scheduler, credential broker, worker pool |
| Phase 8 | Registered automations, autonomy levels L1→L3 per task type based on track record, admin console; experimental model approver (shadow mode from Phase 7) |

## Reference: AWS mapping (later)

| Piece | AWS option |
|---|---|
| Event intake / queue | S3 events, EventBridge (incl. Scheduler), SQS |
| Control plane | ECS or EKS; RDS PostgreSQL |
| Policy | Cedar (self-hosted or Amazon Verified Permissions) or OPA |
| Credentials | STS AssumeRole with session policies and tags; RDS IAM auth or Vault |
| Workers | ECS tasks / EKS pods in a private VPC with endpoints, no internet; Firecracker needs bare-metal or nested-virtualization instances. Lambda's 15-minute limit is a poor fit for long jobs |
| Models | vLLM on GPU instances, Bedrock or a gateway (per model-provider plan) |
| Audit | Our ledger + CloudTrail (run id in the session name); ledger export to S3 Object Lock |
