# Product direction (2026-11)

Recorded 2026-11-01 from a strategy discussion with the project owner.
**Design and direction only — nothing in this folder is implemented yet.**
Implementation status remains in [context/CURRENT_STATUS.md](../../context/CURRENT_STATUS.md).

Read in this order:

| # | Document | Answers |
|---|---|---|
| 1 | [Vision and assessment](VISION_AND_ASSESSMENT.md) | What the product is for, where it stands (2026-11-01), top priorities, structural problems, competitors |
| 2 | [Editions and interfaces](EDITIONS_AND_INTERFACES.md) | Laptop vs server: one product or two? Professional vs non-professional interface |
| 3 | [Autonomous server platform design](AUTONOMOUS_PLATFORM_DESIGN.md) | Target architecture for a policy-governed autonomous agent platform, new code structure, migration phases |

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

1. Model/conversation/data text never grants execution authority.
2. Every consequential action is checked by policy, verified deterministically, and recorded in an append-only audit trail.
3. Raw sensitive data never has to leave the user's machine or site.
4. Learning/self-evolution changes nothing in production without passing evaluation, and it can always roll back.
5. One shared core; transports and UIs are thin adapters.
