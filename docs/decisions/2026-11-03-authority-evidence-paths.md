# Authority and evidence paths during P0-2

Context: relocating plans/history alone leaves recipes, approvals and evidence at the
project root. Consumers that infer source identity from artifact parents break write
session binding; absolute physical references also break portable evidence verification.

Decision: adopt approvals, workflow-recipes, recipe-runs, recipe-evidence,
workflow-state/interface-executions and inspection-runs as one connected slice. Retain
logical artifact references and resolve them through the source project's configured
workspace at each reader. Pass source identity explicitly to approval issuance, but
bind its live write session only for that project's configured approval store. Unrelated
explicit directories preserve the old rejection behavior. Low-level explicit roots stay
explicit. PostgreSQL one-attempt receipts move with recipe-runs and cannot be reset by
relocation. Missing destination stores with legacy records fail closed.

Consequences: historical JSON, digests, data paths and approval expiry remain unchanged;
new launcher sessions revoke previous authority. This does not introduce a storage
daemon, new agent, dependency, UI or data-processing operation. Remaining lifecycle
stores, ownership binding, offline inventory/copy/verification/rollback and the source-only
repository exit check are still required before P0-2 is complete. No real migration
is performed by this change. See [storage guide](../WORKSPACE_STORAGE.md) for evidence.
