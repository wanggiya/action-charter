# Reviewed agent know-how and focused context

P2-D3/K, [#102](https://github.com/wanggiya/action-charter/issues/102).

## Context

Data Cards supply facts, not analysis methods. Large descriptive operation catalogs
cost small-model context, while embedding each method as backend branching creates
unnecessary coupling. Existing schema focus, recipe discovery and deterministic
validation already provide the execution boundary.

## Decision

Keep methods in reviewed `agent-skills/<id>/SKILL.md` files. One L3 loader validates
bounded strict-JSON headers and content pins, then selects relevant files within
the current capability scope. It cannot discover or enroll project-local additions.
At most three files/2,600 payload bytes are supplied. Optional reviewed method-family
and specificity metadata prevent redundant generic/domain instructions; field-name
hints establish relevance, not domain truth or permission.

Extend existing schema focus for ordinary table inspection, preserving requested
transformations, current workflows and the full operation allowlist. Uninspected
recipe summaries remain brief; existing discovery supplies details and existing
validation binds composition/reuse claims. Instruction IDs are not recipe sources.
Final policy, egress, exact authorization and runtime verification stay independent.

Conversation records selection provenance in its existing context receipt, and
standalone Planner proposals expose backend-generated provenance warnings. Refresh
is read-only. Wheels and the existing agent build include the same pinned assets.
No new agent, executable operation, code generator or private memory store.

## Consequences

Methods can change through source review without adding executable operations.
Missing/unsafe/changed files are omitted, not promoted into instructions. Repository
review establishes provenance; it does not establish that a small model follows a
method correctly. Retain failed/limited comparisons, including the early health
timeout. Fixture success, smaller requests and first-attempt results cannot replace
normal-runtime correctness or per-method qualification. [Scope and evidence](../AGENT_KNOWHOW.md).
