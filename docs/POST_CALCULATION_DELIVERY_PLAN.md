# Delivery after bounded calculations

Recorded 2026-10-18. **Ordered delivery plan; 27.4a recorded-result slice implemented.**
See [delivered behavior and acceptance](CHECKPOINT27_RECORDED_RESULTS.md). Subsequent gates remain open.
The current checkpoint 27 snapshot adds successful-workflow retention/discovery,
bounded calculations and Planner reliability checks. It is not a claim that the
full interface, learning system or prototype is ready. Preserve the original
[checkpoint 27 plan](CHECKPOINT27_PLAN.md), [roadmap](../context/PRODUCT_ROADMAP.md)
and [calculation design](BOUNDED_CALCULATION_DESIGN.md).

## Updated delivery order and demo gate

Updated 2026-10-19. [27.4a recorded results](CHECKPOINT27_RECORDED_RESULTS.md) and
[27.7 runtime controls](CHECKPOINT27_RUNTIME_WRITES.md) are implemented slices.
Next: 27.3 evidence feedback, remaining 27.4 visualization and synthetic 27.5
evaluation; then implement/validate 28.1 generated capabilities, 28.2 learning/RL
and 29 advanced private memory before demo or real-data testing. Preparation
materials may be drafted earlier; 27.6 demo acceptance/packaging follow the gates.

This operator revision supersedes the earlier minimum-demo proposal. Learning
can remain OFF by default at runtime; its implementation/evaluation is now a
required pre-demo delivery. No improvement claim is assumed. Cross-chat sharing
remains deferred. [Runtime design](RUNTIME_WRITE_CONTROL_DESIGN.md) keeps
availability separate from exact authorization and execution. Overwrite remains
an operation-specific follow-up; the switch does not permit replacement.

## Optional acquisition clarification — 2026-10-19

[Checkpoint 28.1 design](OPTIONAL_CAPABILITY_ACQUISITION_PLAN.md): acquisition is
OFF by default and explicitly enabled per task. Existing operations and recipes
come first; a concrete capability gap, not workflow size alone, triggers bounded
candidate preparation/testing. No new candidate work when existing capabilities
suffice. Successful explicitly installed versions persist for reuse. Budgets cover
model/tool calls, attempts, elapsed time and isolated test resources; installation,
write availability, exact authorization and execution remain separate decisions.
The user does not write adapter definitions. This is planned behavior, not a
feature delivered by this documentation update. Optional use retains the existing
28.1 implementation/validation requirement before demo/real-data acceptance.

## Ordered work and acceptance gates

| Placement | Work and why | Measurable acceptance |
| --- | --- | --- |
| **27.4a — understandable recorded results** | Use existing evidence to show selected-operation purpose, formula, input → output, execution identity/status, bounded rows and readable validation checks. Keep raw/audit details collapsed. Users should not need folders or JSON to verify normal work. | The CSV calculation journey exposes the correct six rows and missing value, recorded calculation check and output path in the information panel. Inspection/calculation, history selection, chat changes and refresh cannot mix runs or require reexecution. Proposed data is visibly distinct from executed/validated results; stale or missing evidence is labelled. Write availability is visible and startup guidance includes --enable-write-tools for write workflows. |
| **27.7 — runtime write availability (implemented slice)** | Shared backend policy/session service, Settings switch and status remove routine restarts without granting authority. Preserve explicit locks and CLI parity. | OFF blocks writes; enabling creates no output/approval; exact authorization binds session/revision; disable/re-enable/restart cannot revive authority; mid-run disable respects operation boundaries; temporary-file API/CLI/browser tests pass. Replacement remains a separate contract. |
| **27.3/27.5 — evidence feedback and evaluation** | Clarify existing Planner/Critic/helper interfaces and expose provenance; reuse the deterministic execution engine. Add optional, bounded Critic applicability/limitations derived from recorded runs. Establish evidence before learning from it. | Planner adapts explicit workflows; Critic never overrides deterministic success/failure. Baseline retention survives helper/model failure. Spatial inspection, tabular calculation and a compatible combined journey have expected outputs plus documented failure/cancel/refresh behavior. Report correctness, elapsed time, calls/tokens, failures and user interventions; fixture tests are separate from actual-model acceptance. |
| **28.1 — optional governed capability-acquisition pilot** | OFF by default, explicit task opt-in, only after an actual gap in existing operations/recipes. Extend the existing registry, adapter/package and candidate lifecycle, initially for one bounded calculation/data-transform adapter family. Planner proposes a candidate and tests; services isolate/evaluate it; Critic assesses evidence. Repeated tasks can gain tested executable capability rather than only a remembered recipe. | A candidate runs only with temporary fixtures inside an established isolation boundary with fixed filesystem/network/resource limits. Independent held-out checks and negative/effect tests pass before explicit installation/promotion. Broken or unsafe candidates never become discoverable executable operations. Dependency installation and operation authorization remain separate. No separate Builder reasoning agent is required. This general generated-code path is not implemented today. |
| **28.2 — learning-policy experiment (opt-in runtime; required pre-demo delivery)** | After 28.1 and operational measurement, compare a small reward-based selector, potentially a contextual bandit, against fixed eligible-recipe/operation ranking. This is an experiment, not a claim of improved planning or general RL. | OFF by default. Frozen held-out tasks, versioned outcomes and reward definitions, bounded exploration, rollback and a fixed baseline exist. Report quality, failure rate, latency/call cost and interventions; retain the policy only if a stated evaluation threshold is met. It cannot install/promote code, expand allowed operations, change validation, reuse expired approvals or dispatch writes. It does not train Ollama model weights or prove general workflow learning. |
| **29 — same-conversation domain knowledge and corrections** | Extend private transcript/workflow memory with source-linked procedures, applicability, versions, corrections and expiry. Reuse local indexed storage before adding infrastructure. Retrieval from SQLite/files is still retrieval augmentation; it does not require a large vector service. | Domain fixtures check relevant retrieval, source visibility, conflict/expiry handling and no fabricated facts. A procedure is distinguished from a verified result and from authority. Corrections preserve provenance. Other chats are not searched. |
| **30 or later — cross-chat decision gate** | Keep the existing multi-checkpoint deferral. Consider explicit scoped sharing only after intervening operational/privacy work and a fresh operator decision. | See the existing deferred-memory acceptance and privacy gates. No sharing or cross-chat learning is enabled by this plan. |

27.6 demo/packaging preparation remains after data/evaluation acceptance. The
operator now requires generated capabilities, learning/RL and advanced private
memory before demo/real-data testing. Checkpoint 27 fixture evaluation can finish
before those later gates; demo acceptance cannot. Prepare installable/release materials only within their documented
scope; publication is a separate operator action. Do not rename historical
checkpoint numbers or claim checkpoint 27 completion from one passing calculation.

This serial delivery order limits simultaneous unknowns on a small laptop. A
selection-learning experiment can technically use existing operations without
generated-code acquisition; new capabilities are not a requirement for RL. Any
future MCP exposure remains a typed interface to registered operations, not a
general Python execution channel.

## Responsibilities and boundaries

- **Planner:** interpret scope; discover/compose/adapt operations and recipes;
  optionally propose bounded adapter candidates. Its proposals are untrusted.
- **Critic:** interpret recorded outcomes, suggest applicability/limitations and
  assess candidate evidence. It cannot certify its own narrative as a passed test.
- **Optional method-memory helper:** a separately maintained, OFF-by-default
  inference role for bounded advice. Extend its existing contract rather than
  introducing another container or mandatory reasoning agent. Domain correction
  and curation are future work, not delivered behavior.
- **Deterministic services:** registry contracts, isolation, budgets, fixture and
  held-out checks, provenance, persistence, installation/promotion gates, exact
  authorization, execution and independent validation.
- **Learning policy:** an optional bounded choice mechanism over already eligible
  options, not an authority-bearing agent or a new executable capability.
- **Operator:** intent, genuinely missing scope, consequential authorization and
  real-world suitability. Routine saving/indexing, source retrieval and technical
  repair should not require repeated manual bookkeeping.

The existing Planner budgets remain the starting point: four model calls and two
read-only discovery calls per turn, including one correction. New candidate work
needs separately measured test/runtime/resource caps before activation. Do not
invent autonomy percentages or improve scores by excluding failures. Preserve
full failure reporting and never automatically repeat writes.


## 2026-10-20 delivery update

[27.3/27.4d](CHECKPOINT27_ANALYSIS_AND_LAYOUT.md) implements advisory Critic note
indexing from existing assessments, ten chart views, explicit complete verified
CSV summaries, bounded WGS84 boundaries/attributes, collision-aware persistent
layout and the shared warning write switch. Broader visualization is now an
explicit 28.3 expansion after 28.1/28.2 pilots. 29 private memory and the 30+
cross-chat decision gate remain unchanged. Fixture acceptance and actual-model
measurements are reported separately; no release or parity claim follows.
