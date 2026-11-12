# Product direction (2026-11)

Recorded 2026-11-01 from a strategy discussion with the project owner.
**Target design and direction, not a claim of delivered editions or autonomy.**
Phase 0 consolidation has implemented portions of this direction; current and remaining
work is navigable through the [active roadmap](../../context/PRODUCT_ROADMAP.md).
Implementation status remains in [context/CURRENT_STATUS.md](../../context/CURRENT_STATUS.md).

Read in this order:

| # | Document | Answers |
|---|---|---|
| 1 | [Vision and assessment](VISION_AND_ASSESSMENT.md) | What the product is for, where it stands (2026-11-01), top priorities, structural problems, competitors |
| 2 | [Editions and interfaces](EDITIONS_AND_INTERFACES.md) | Laptop vs server: one product or two? Professional vs non-professional interface |
| 3 | [Autonomous server platform design](AUTONOMOUS_PLATFORM_DESIGN.md) | Target architecture for a policy-governed autonomous agent platform, new code structure, migration phases |
| 4 | [Market position and strategy options](MARKET_POSITION_AND_STRATEGY.md) | Is it competitive? Portfolio vs niche product vs governance layer for other agents; validation gate; open decision on the owner's goal |
| 5 | [Working method and delivery plan](WORKING_METHOD.md) | How contributors and agents work now (replaces checkpoints), ordered steps with exit criteria and status, task rules |
| 6 | [Code restructure plan](RESTRUCTURE_PLAN.md) | R1–R6 automatically verified; R7 CLI extraction automatically verified; R8 HTTP extraction automatically verified; R9/R10 reconciled against P0 delivery; specialized contracts; R12 context/services, local stable identity and R11 retirement automatically verified; owner startup/read-only/recovery passed; two manual checks and separate owner cutover remain |
| 7 | [Model providers plan](MODEL_PROVIDERS_PLAN.md) | Local / on-site / gateway / public models: profiles, data-egress gate, steps M0–M5, verification |
| 8 | [Server autonomy design](SERVER_AUTONOMY_DESIGN.md) | Server-first unattended operation: registered automations, three-part authorization, what can and cannot be automated, build-now vs later |
| 9 | [Showcase workloads and editions](SHOWCASE_WORKLOADS.md) | Health, data engineering (SHP/DWG → PostGIS), 2026-midterm policy analysis demo, grid monitoring; Personal vs Platform editions; where each sits in the phases |

## Latest decision (2026-11-02)

Build **our own agent platform** (one core for laptop and server), with opt-in interop to
external agents (Claude Code, Codex, …) and our own single-agent (default) and
multi-agent modes. Differentiators first: measured efficiency, process/outcome run
workspaces, Data Card, better frontend. Any model source (local, on-site, gateway,
public API) with a policy-controlled data-egress gate ([decision](../decisions/2026-11-03-model-providers.md)).
Server autonomy through human-approved registered automations, server first
([decision](../decisions/2026-11-05-server-autonomy-direction.md)).
Showcase workloads and Personal/Platform editions
([decision](../decisions/2026-11-06-showcase-workloads-and-editions.md)).
See the [platform decision note](../decisions/2026-11-02-own-platform-direction.md).

## One-paragraph summary for the next AI

ActionCharter is a local-first AI data platform for people whose data is too sensitive
for external AI APIs. Agents (Planner, Executor, Critic, Builder, memory) help with data
science, data engineering and reporting so non-experts can use the results. The owner's
long-term target is an **autonomous agent platform** that runs on a laptop, on-site
server or private cloud, with role-separated agents that improve over time. The agreed
direction is: **one core codebase, several deployment profiles (Personal / Team server /
Enterprise), and two interface modes (Guided for non-experts, Studio for professionals)
over the same backend.** Autonomy is granted by **policy and verification, never by model
output**. This extends the existing core principle "models propose; deterministic software
authorizes, executes, validates and records evidence." Before building the server
platform, consolidate the current codebase (Phase 0) and set up a measured benchmark.
Self-improvement must pass offline evaluation before anything is promoted.

## Non-negotiable principles carried forward

1. Model/conversation/data text never grants execution authority. Models participate throughout the process; a model may approve only through the experimental, opt-in, bounded **model approver** ([design](SERVER_AUTONOMY_DESIGN.md#model-participation-in-authorization), 2026-11-06).
2. Every consequential action is checked by policy, verified deterministically, and recorded in an append-only audit trail.
3. Raw sensitive data never has to leave the user's machine or site.
4. Learning/self-evolution changes nothing in production without passing evaluation, and it can always roll back.
5. One shared core; transports and UIs are thin adapters.
