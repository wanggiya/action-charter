# Editions and interfaces

Recorded 2026-11-01. This is a recommendation; the owner has not formally accepted it yet. Not implemented.

## Question 1 — separate products for laptop and server?

**Recommendation: no. Build one product with one core codebase and several deployment
profiles.** The laptop edition is simply the server stack bundled for one user with a
local model and conservative autonomy.

Why not two products:
- Two codebases double the work on governance, operations, verification and tests. Those are the most valuable and most expensive parts of the project.
- Recipes, skills, memory and audit records should move between editions. A workflow built on a laptop should run unchanged on the team server.
- A small team cannot keep two products in sync. They would drift.

What differs is **configuration and packaging, not code paths**:

| | Personal (laptop) | Team server (on-site) | Enterprise / private cloud |
|---|---|---|---|
| Users | 1, no login | Many; LDAP/OIDC | Many tenants; SSO, RBAC |
| Install | Linux installer/AppImage; Windows later | `docker compose` single node | Helm chart, offline/air-gapped bundle |
| Model | Ollama, small models (4–14B) | vLLM/Ollama on site GPUs | vLLM model gateway, routing, quotas |
| State | SQLite + local files | PostgreSQL + object store (MinIO) | PostgreSQL HA + S3/MinIO |
| Default autonomy | L0–L1 (propose, read-only auto) | L1–L2 (staging writes) | L1–L3 per policy; L4 human-approved |
| Triggers | Chat | Chat, schedules, file/table events | Plus tickets, APIs, connectors |
| Workers | In process + one sandbox | Worker pool | Worker pools per site/data zone |
| Admin console | Hidden | Policy, agents, audit | Plus tenants, quotas, compliance export |

Implementation rules:
- Every platform service sits behind an interface with a "local" and a "server" implementation (repository, queue, model gateway, secrets, identity). Choose by config profile, not by `if desktop:` branches spread through the code.
- The desktop app is a launcher that starts the same API server and web UI on loopback.
- Feature flags/licensing (if commercial) gate profiles. Do not fork.
- Possible business model: Personal is free or open-core; Team and Enterprise are paid (support, SSO, multi-tenant, compliance).

## Question 2 — professional and non-professional interfaces

**Recommendation: one web application with two interface modes over the same backend,
sessions and results.** Not two apps. A user can switch at any time; their role sets the
default. The server edition adds a third surface, the Admin console.

| | **Guided** (non-professional) | **Studio** (professional) | **Admin console** (server) |
|---|---|---|---|
| For | Managers, clinicians, analysts without DS training | Data scientists, engineers, GIS specialists | IT, data owners, compliance |
| Main surface | Chat + results cards + report | Workflow graph, inspector, chat, results workspace | Policies, autonomy levels, agents, audit |
| Start | Templates: "Check my data quality", "Compare groups", "Make a monthly report", "Clean and combine files" | Blank plan, recipes, operations catalog | — |
| Language | Plain: "This will create a new table *Patients_clean* with 101,766 rows. Continue?" | Exact: operation IDs, arguments, digests, scope, lineage | Rules, roles, quotas |
| Approvals | One clear confirmation per consequential step; read-only work runs directly | Full Authorize → Execute, scope review | Defines what needs approval |
| Results | Key findings in sentences, simple charts, "what this means", caveats in plain words | Full statistics, tables, diagnostics, generated recipe/Snakemake, SQL view | Run history, cost, failures |
| Hidden | Graph, digests, recipes, diagnostics (one "Show details" link) | Nothing | — |
| Learning | "Save this as a reusable task" | Edit and publish recipes/skills | Approve promotion of learned capabilities |

Design rules:
- Both modes call the **same task actions and policy**. Guided mode must never have weaker safety; it only presents it more simply.
- Every Guided screen has "Open in Studio", so an expert can take over the exact same session.
- Agent output gets a plain-language layer: Reporter/Analyst roles write the Guided explanation from the same recorded facts. Never invent numbers; cite the evidence ID behind each statement.
- Guided caveats are mandatory: sample size, missing data, "association is not causation".
- Measure Guided mode with real non-expert users (task completion, time, misunderstanding rate). Fixture tests are not enough.

## Suggested order

1. Phase 0 consolidation (shared task actions, workspace state root). See [AUTONOMOUS_PLATFORM_DESIGN.md](AUTONOMOUS_PLATFORM_DESIGN.md).
2. Guided mode for the single hero journey on the Personal edition.
3. Package Personal for Linux.
4. Team-server profile (PostgreSQL, login, scheduler, worker pool).
5. Admin console and autonomy levels L2+.
6. Windows Personal, Enterprise profile.
