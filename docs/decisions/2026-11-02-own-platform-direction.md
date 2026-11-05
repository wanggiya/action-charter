# Own agent platform with interop, focused on verified data work

Date: 2026-11-02. Decided by the project owner. Supersedes the "do not build the server
platform / use another platform" recommendation in
[MARKET_POSITION_AND_STRATEGY.md](../product-direction/MARKET_POSITION_AND_STRATEGY.md)
and the "blocked on validation" gate in
[WORKING_METHOD.md](../product-direction/WORKING_METHOD.md).

Context: the owner attended a competitor's lecture on an agent platform (sandboxed
containers, isolation, working-content snapshots) that overlaps with this project's plans.
Building on another vendor's platform was considered and rejected: their pace cannot be
matched, and depending on them would make this project a follower. The owner observed in
the lecture (owner's notes, not independently verified):
- performance and efficiency were not addressed;
- isolation was presented, but not a container/workspace model that separates an agent's
  working process from its outcome while making both accessible to other agents;
- the competitor's frontend is clearly better than ours;
- they show agents a header/preview of data before processing so people can confirm it is
  correct (this project already has header-only and comprehensive inspection).

Decision:
1. **Build our own agent server platform**, as one core shared by laptop (Personal) and
   server editions. Do not build on, or imitate, a competitor's platform.
2. **Interop, opt-in:** users may connect external agents/harnesses (Claude Code, Codex,
   others) — external agents can use our governed tools via MCP, and our agents can hand
   work to external agents or models through the model gateway when the user allows it.
3. **Our own agents, two modes:** an easy **single-agent mode** (default for individual
   use) and a **multi-agent mode** (for complex tasks and server use), on the same runtime.
4. **Differentiators to build first:**
   - measured **efficiency** (model calls, tokens, time, resources per task; deterministic
     routing and recipe reuse);
   - **run workspaces** that separate *process* (scratch, code, logs, snapshots) from
     *outcome* (verified results); promotion from process to outcome only by
     deterministic verification; governed read access to both for other agents;
   - a first-class **Data Card** (header, schema, profile, sample, quality flags, hash)
     shown to agents and people before work starts;
   - a much better **frontend** (Guided and Studio modes).
5. **Keep the platform layer thin**: reuse proven infrastructure (PostgreSQL, Docker,
   existing libraries) for queues, scheduling and storage; spend effort on the
   differentiators. Sandbox: per-job hardened Docker now, MicroVM adapter as a later option
   ([sandbox plan](../EXECUTOR_SANDBOX_WORKSPACE_PLAN.md)). Do not claim stronger isolation
   than boundary tests prove.
6. Core principle unchanged: models propose; deterministic software authorizes, executes,
   validates and records evidence.

Consequences:
- The delivery order in [WORKING_METHOD.md](../product-direction/WORKING_METHOD.md) is
  replaced by phases 0–8: consolidate → baseline benchmark → Data Card + efficiency → run
  workspaces → agent modes → frontend → interop → server profile → autonomy/evolution.
- [AUTONOMOUS_PLATFORM_DESIGN.md](../product-direction/AUTONOMOUS_PLATFORM_DESIGN.md)
  remains the reference for policy, ledger, autonomy levels and editions; its scope and
  order are revised as above. The code moves follow
  [RESTRUCTURE_PLAN.md](../product-direction/RESTRUCTURE_PLAN.md) (draft).
- Customer validation (talking to users in one domain) is still recommended, but it is no
  longer a blocker for platform work.
- Multi-agent mode stays optional until the benchmark shows it helps; on one shared small
  model it multiplies latency.
