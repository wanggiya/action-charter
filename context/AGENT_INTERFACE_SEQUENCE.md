# Next sequence: one task, agent reasoning, then a usable workspace

The current interface proves governed execution, but exposes too much internal bookkeeping and treats the graph as the main application. The default product should let a user describe a goal, see a cited interpretation and proposed graph, make one explicit consequential decision, run, and inspect validated output. The existing CLI, recipes, approvals, Snakemake replay, Critic, and releases remain available in Advanced and automation paths.

| Checkpoint | Goal | Acceptance boundary |
| --- | --- | --- |
| **21 — task identity and history** | One recoverable task record links new requests, clarifications, selections, reviewed plans, exact approvals, recipe executions, failures and outputs. Build bounded, redacted context from verified original sources. | A failed Planner request is still visible under its task ID after restart. No silent history failure; older records remain unassigned unless their identity can be proved. A history decision is never approval. |
| **22 — context and intent reasoning** | Deterministic Context Curator assembles a cited context package; an Intent Agent proposes a goal-level approach and asks clarifying questions. The capability Planner maps reviewed intent to implemented typed skills. | The user sees the exact context and proposed intent before accepting it. The model cannot select unavailable skills, authorize tools, or silently broaden scope. Policy rejection is a visible finding with a bounded revision path. |
| **23 — task-centered agent interface** | Put task conversation/context and editable review graph side by side. Hide routine plan/recipe bookkeeping; review one exact consequential scope, record one explicit decision, deliberately run, then show current validated outcome and responsible failure node. | Complete a fresh PostGIS task through the default interface with fewer manual screens than Checkpoint 19. Denial, expiry, mismatch and interruption remain distinct. CLI and Advanced flows still work. |
| **24 — tabular data** | Add typed CSV/TSV and Pandas operations, deterministic validation and evidence through the same task journey. | A realistic non-spatial task completes end to end without arbitrary Python execution. |
| **25 — governed capability growth** | Discover installed library functions as candidates with fully qualified names, typed contracts, isolated tests and human promotion. | Unknown functions never become executable merely because a model names them. |
| **26 — comparative evaluation and release** | Benchmark correctness, interventions, elapsed time, recovery, reproducibility and comprehension against manual tools and a general coding agent. Prepare a laptop alpha from protected main once gates pass. | Demonstrate a measurable benefit, publish supported setup limits, and fix blockers before a wider release. |

## Immediate implementation order

1. Finish Checkpoint 21's task-link contract and fail clearly if the history service is unavailable. Verify the task-history endpoint and current source before running the Planner.
2. Store exact, independently checked artifact references; recover a task after browser and API restarts. A hash chain checks event changes but is not itself proof of a plan or execution claim.
3. Test the context and intent agent boundary using real planning failures, including an Ollama proposal that invents an unselected skill. Offer correction/replanning without relaxing deterministic policy.
4. Replace the default artifact-by-artifact path only after a single task can hold the exact reviewed scope and its evidence. Preserve separate backend validation even when the UI has one decision.

Do not add tool families merely to make the interface look more capable. The first product test is whether a user can express a data goal, understand and correct the agent's proposal, execute with bounded authority, and trust the result faster than manual coordination.
