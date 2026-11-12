# R3: shared metadata mechanics and neutral plan contracts

Context: five lower-layer modules still reached metadata storage through task actions,
and the storage interface referenced a Planner-owned type. Some callers also depended
on bounded conversation JSON helpers; moving transactions alone would leave that edge.

Decision: extract transaction/identity/bounded JSON mechanics to storage. Preserve the
same provider and SQLite implementation. Keep memory/provenance/revision rules in task
actions, supplying their existing-record validator to the writer. Move self-contained
plan DTOs unchanged to neutral contracts, preserve `planner.schemas` module identity,
and share the existing error class through neutral contracts and compatibility names.

Consequences: lower-level clients no longer import the task storage wrapper, and the
storage type contract no longer points upward. JSON bytes, canonical hashes, limits,
locking, parser behavior and exact authority remain compatible. No SQL rewrite, data
migration, new adapter or model-call behavior. P0-5b and broader R4 work remain separate.
Owner manual acceptance is pending; label automated fixture evidence distinctly.
See [implementation and verification](../STORAGE_REPOSITORIES.md#r3-transaction-and-plan-contracts).
