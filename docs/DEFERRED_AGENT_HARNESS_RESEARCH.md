# Deferred research — data specialization and agent harnesses

Recorded 2026-10-21. Documentation only. Do not start benchmarking, source-code
review, integration, installation, migration or model changes from this note.
The operator asked to record the direction and defer work on these comparisons.

## Product hypothesis

ActionCharter should specialize in data science and engineering: correct,
repeatable spatial/tabular workflows with fewer user interventions and shorter
completion time using the same small open-source model and comparable resources.
Local isolation alone is not sufficient differentiation. Typed operations,
editable workflows, source lineage, verified outputs, recovery and usable
visualizations must produce a measurable practical advantage.

A general coding agent can implement similar data transformations. No unique
capability, speed advantage or superiority over Codex has been established.
Codex is a product reference; do not assume it can run an arbitrary open-source
model. For a controlled same-model comparison, use a harness that actually
supports the identical model. Separately label comparisons against Codex's own
supported model/runtime configuration; they do not isolate harness effects.

## Deferred comparison protocol

- Freeze representative CSV, spatial and combined task definitions and expected
  results, including replacement inputs, follow-up edits and failure recovery.
- Use equivalent libraries, data access and machine limits. Fix model/version,
  quantization, generation settings and context budget where controllable.
- Measure verified completion, end-to-end time, model versus processing time,
  calls/corrections, tokens, human interventions and peak memory.
- Repeat trials; report cold/warm behavior and failures. A fast incorrect workflow
  is not success. Keep comparison fixtures separate from development examples.
- Establish baseline results before claiming that retrieval, compilation,
  recipes, memory or an adaptive policy improves outcomes.

## DeepSeek and other open-source harnesses

Sources identified in discussion, not an architecture audit:

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness): its public
  README describes a plugin-oriented agent harness and warns about developer
  preview compatibility changes. Review current code/license before any reuse.
- [DeepInfer](https://github.com/deepseek-ai/DeepInfer): an inference-serving
  project, a different layer from ActionCharter's data workflow execution.

Future review should examine session state, context/tool selection, event flow,
plugin contracts, cancellation, recovery and bounded retries. Evaluate one useful
pattern/component behind existing interfaces before considering runtime migration.
Review licensing, dependencies, privacy/effect boundaries and maintenance cost.
Do not equate open-source inference code or an agent harness with a transferable
reasoning capability or with model training. Other harnesses can be evaluated
under the same criteria; no dependency or preferred replacement is selected.

## Constraints and relationship to delivery

Preserve the existing Planner, operation contracts, deterministic validation and
exact execution authority unless a separately reviewed change justifies replacing
them. No additional LLM agent is implied. Training, MCP expansion and arbitrary
code execution are not prerequisites for this research proposal.

This note does not implement or complete checkpoint 28.2, change the 28.3/29 order,
remove the operator's pre-demo learning/private-memory gates, or authorize Git,
publication, external data transfer or live-service mutation. Current work remains
inspection-on-send design/implementation and checkpoint acceptance as separately
authorized. Research is deferred until the operator resumes it.
