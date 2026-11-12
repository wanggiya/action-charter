# R6a: shared controls and neutral graph/evidence types

Context: data engines imported recipe coordination for cancellation, graph consumers
imported planner-owned helpers and core history imported role-owned result schemas.
One Executor schema file also includes a recipe result with domain-dependent validators.

Decision: move unchanged cancellation/progress controls to platform and pure graph/
Critic/four Executor contracts to neutral contracts. Use exact module aliases or class
exports at legacy paths. Retain the recipe-specific result and validators in their
domain owner. Update native imports; preserve generated/stored references.

Consequences: eight dependencies disappear without new debt, reclassification or
behavior changes. One context/exception identity, legacy graph hashes and all 12
public schemas remain. R6a is a bounded slice; evidence-building/core/data/role ownership
and later package moves remain open. No agent, tool, UI or authority is added.
See [scope and verification](../SHARED_EXECUTION_PRIMITIVES.md).
