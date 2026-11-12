# R1: explicit dependency debt before further package moves

Context: P0 implementations removed several direct HTTP dependencies, but core code
still reaches transport-owned settings and higher-level task actions. Import-time
lightweight tests alone do not enforce the proposed layer direction.

Decision: statically inspect every application Python module, using an explicit
current-path-to-layer policy. Permit same/downward imports; list exact existing upward
dependencies as debt with counts, reasons and follow-ups. Fail new/increased and stale
baseline entries. Non-literal import reviews bind expression and normalized source text. Preserve
compatibility aliases visibly. Offer strict zero-debt mode for the Phase 0 exit gate.

Consequences: no package move, new dependency or runtime behavior change. Baseline
success prevents regressions; it does not establish clean layers or safe arbitrary
Python execution. Common imports are resolved without executing modules; general
reflection, same-layer cycles and semantic ownership remain review limits. P0-2b,
P0-5b and R12 stay separate follow-ups in the same Phase 0 backlog.
See [usage, evidence and limitations](../IMPORT_LAYERS.md).
