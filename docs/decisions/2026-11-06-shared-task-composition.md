# R5: shared domain functions with action-owned coordination

Context: ten remaining dependencies made planning, reuse, registry, data and role
code import task controllers. Legacy CLI service imports also bypassed a shared
composition owner, while the command signatures and services already worked.

Decision: extract non-executing validation/save, closed schemas, snapshot/archive and
observation helpers; give coordination explicit trusted conversation access; share
fixed spatial functions. Keep approval/execution/recovery in task actions. Route CLI
service imports through explicit lazy exports returning the original current functions.
Keep schema and compatibility identities; no model-specified callbacks or generic tool.

Consequences: all ten direct R5 pairs disappear with no new/increased debt. Completed
method reads become non-recovering; recovery remains an explicit run-action concern.
CLI options/control/output AST is unchanged; optional runtimes and test hooks remain.
Existing R6 ownership debt and R7/R8 file splits stay visible, as do P0-2b/P0-5b/R12.
Owner manual write acceptance remains pending. See [scope and evidence](../TASK_ACTIONS.md#r5-shared-composition-and-evidence-boundaries).
