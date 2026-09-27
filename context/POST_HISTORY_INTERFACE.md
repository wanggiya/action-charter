# Post-history interface: one task, one decision, visible outcome

## Why this is needed

The Checkpoint 19 operator completed the full Planner → PostGIS → validation → evidence → Critic → release → Snakemake path, but reported that repeated plan, recipe, approval, preview, storage, and history screens took more effort than doing the data task manually. Functional parity alone is not a usable default experience.

## Default journey after governed task history and context exist

1. **Describe and plan.** The user states the goal and selects inputs. The Intent Agent can ask a necessary clarification using bounded, cited task context; the Planner maps the reviewed intent to implemented skills. Skill selection is optional for the user, but the exact capability set and policy effects remain visible before a decision.
2. **Review beside the graph.** A context/task pane sits beside the proposed flow. The graph shows inputs, key operations, affected resources, approval gates and expected outputs. Individual steps, arguments, recipe identities, scopes, digests and evidence expand on selection. The user can request a revision or edit permitted parameters; any change to consequential scope requires a new decision.
3. **Decide once.** The default surface offers an explicit **Approve and run** or **Deny** decision for one exact consequential scope, including target resources and side effects. Optional Snakemake preview is available before the decision. The backend may compile, persist and verify separate plan/recipe records, but performs those deterministic bookkeeping steps without asking the user to shepherd each artifact. Approval is not inferred from chat, graph viewing or a previous decision. A denied task remains denied.
4. **Run and check outcome.** After valid approval, a separate deliberate Run action starts the exact approved work, with live node status and a prominent final success, failure, denial or interruption. The default outcome shows the current task's output and validation first. A log and **Execution attempts** button reveal durable history; routine internal artifacts stay collapsed. Failures surface the responsible step, findings, evidence and safe next action.

The precise implementation may combine the decision and Run into one clearly labelled action only if the user sees the complete scope and the backend still verifies the immutable approval before execution. The current two-step version is acceptable as an intermediate safety boundary.

## Non-negotiable backend behavior

- Derive plan, recipe and execution identity server-side; compare hashes and exact scope automatically. Preserve immutable records and independent validation.
- Store the human decision once against the full consequential scope. Do not reuse it if the scope, target, recipe, or policy changes or if it expires.
- Keep the CLI and Advanced screens for artifact audit, troubleshooting, expert editing, Critic/release administration and run history.
- Do not claim a task is successful until deterministic post-write validation passes. A failed or interrupted attempt must remain in the log and must not trigger an automatic write retry.
- Make optional model guidance and skill recommendations advisory. Only implemented, approved capabilities can enter execution.

## Acceptance measures

For the same fresh PostGIS task used in Checkpoint 19, measure user actions, time to validated output, scope comprehension, failure recovery and evidence traceability. The default path should require one review of consequential scope and one decision, not repeated manual hash checks, recipe selection and approval screens. Compare it against the current interface and a manual GIS/database workflow before calling the simplification complete.
