# Shared execution controls and neutral contracts

R6a, [issue #71](https://github.com/wanggiya/action-charter/issues/71), 2026-11-06.
This is the first bounded R6 ownership slice. Existing cancellation, workflow graph,
API/CLI commands, approvals and stored outcomes keep their behavior. No new setup,
model, dependency, operation or interface feature is introduced.

Subsequent native package moves and the remaining ownership work are implemented in
[R6 completion](R6_COMPLETION_AND_ACCEPTANCE.md). Paths/counts below describe this
earlier slice; historical imports remain supported.

## Owners and compatibility

| Shared owner | Existing responsibility | Compatibility path |
|---|---|---|
| `platform/execution_control.py` | The same observer ContextVar, cancellation exception and checkpoint/progress forwarding | `recipes.control` aliases the exact module |
| `contracts/graph.py` | Existing dependency fallback, stable topological ordering and ancestor traversal | `planner.topology` aliases the exact module |
| `contracts/critic.py` | Existing Critic evidence, assessment and immutable-record schemas/validators | `critic.schemas` aliases the exact module |
| `contracts/execution.py` | `WorkflowToolArguments`, `ExecutionEnvelope`, `WorkflowExecutionResult`, `ExecutorRunResult` | `executor.schemas` re-exports the exact four classes |

`ExecutorRecipeRunResult` remains in `executor.schemas`, with the original recipe-run
and recipe-evidence types/validators. Those domain contracts include runtime-dependent
checks, so moving the entire schema dependency tree into neutral contracts would
misrepresent its ownership. The partial export preserves class identity without
copying or stripping validators.

Native import statements in 25 files use the shared owners. Generated/stored Python
strings retain their old paths; compatibility modules still resolve them. Existing
agent packages can re-export the same schemas, while lower-level data/history code
uses contracts directly. The neutral owners load without the agent, recipe, model,
HTTP/MCP or GIS runtimes.

## Preserved behavior

- There is one observer ContextVar, with its original name/default and exception
  identity. Legacy/native callers, explicitly copied worker contexts and progress
  callbacks share it. Reset and failure isolation remain. The helper forwards existing
  checks; it does not grant authority, schedule work or change cancellation boundaries.
- Cancellation stays cooperative. An active write and its verification retain their
  existing finish/recovery rules; no automatic write retry or new interruption policy.
- Missing `depends_on` retains sequential fallback. Explicit disconnected/branching
  graphs keep deterministic ready order. Duplicate/unknown/self/cyclic dependencies
  still reject. Graph reads do not mutate the plan or introduce dependency fields
  into legacy serialization, preserving canonical bytes and approval digests.
- All 12 public JSON schemas are unchanged compared with the pre-R6a snapshot. All
  four extracted Executor classes and the retained recipe-result class keep identical
  bodies. The complete control/graph/Critic-schema moves are unchanged source copies.
  Literal permission flags, tool-name/argument restrictions, timestamp awareness and
  deterministic-result consistency checks remain.
- Typed results still require service/evidence verification. A schema, graph edge,
  progress message, Critic assessment or model text supplies no execution authority.
  Current source/target, registry, exact-decision, session and verification checks remain.

## Evidence and remaining scope

The layer baseline shrinks **43 -> 35 pairs and occurrences**, removing six R6 pairs
and two mixed R4/R6 schema dependencies. No new/increased upward dependency or
classification change is accepted. The graph has 447 modules, 40 aliases and the same
single reviewed dynamic import. Normal mode passes; strict mode still rejects debt.

Verified:

- **30 existing schema/evidence/history/import cases passed (3.30 s)**.
- **37 primitive/layer cases passed (1.48 s)**, including 19 new cases for shared
  context/exception identity, copied worker contexts, reset/isolation, graph guards,
  canonical payloads, permission flags and neutral imports.
- **82 existing cancellation/database-adapter/table/workflow/authorization cases
  passed (20.13 s)** using temporary data and fake database adapters.
- All 12 public JSON schemas match the pre-change snapshot; source/class comparisons
  confirm that the moved code and retained recipe-result validators are unchanged.
- Frontend validation passed (4.43 s build, existing bundle-size warning).

The isolated relocated browser/API/CLI/PTY journey passed with zero page errors,
including saved results/history, statistics, JSON/XLSX/PDF paths and one exact temporary
write authorization. Final full `make test`: **2,626 passed**, 13 existing spatial
warnings, **711.11 s (11:51)**. Normal layer check and 473 local links (160 Markdown
fragments) pass; the roadmap remains below 64 KB. Whitespace checks pass. Source was
frozen throughout the final full run; strict mode correctly rejects remaining debt. Fixtures are distinct from a new
real-local-model/database benchmark. The owner manual write check remains pending.
No live data, secret settings or real workspace records were changed.

R6 remains open. At R6a completion the history observer still depended on the Critic
evidence builder; the later [R6b evidence slice](SHARED_CRITIC_EVIDENCE.md) removes it.
Broader core policy/ledger, data/capability and agent/recipe/interop ownership need subsequent
slices before physical package moves. See the
[ordered R6 checklist](product-direction/RESTRUCTURE_PLAN.md#r6-reviewable-slices).
R7/R8 command/router decomposition, P0-2b/P0-5b, R12 and final R11 compatibility review
remain separate. This task does not claim a zero-debt Phase 0 exit.

For a later manual smoke check, restart the usual launcher with its existing options.
Inspect `sample_orders.csv`, check Outcome and reopen the saved run in frontend history
and `./actioncharter`. Existing explicit graph dependencies and Cancel should keep
their behavior. Use disposable outputs for any future write/cancellation check; the
owner's unperformed write test must not be counted as acceptance.
