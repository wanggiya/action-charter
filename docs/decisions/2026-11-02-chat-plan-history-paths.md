# Explicit project identity for relocated chat, plan and history stores

Context: deriving project identity from record parents breaks when state is outside the
source project, especially partial-output recovery, method lookup and scoped history.

Decision: production callers pass project_root explicitly. A shared resolver is adopted
for legacy chat JSON, saved plans and durable interface-run history, together with their
inventory/receipt/resume readers. Existing defaults, serialized bytes and digests remain
compatible; explicit low-level root overrides remain explicit. Private legacy reader
signatures retain a project-relative compatibility fallback, never used by production.

Consequences: approvals/recipes and execution evidence/progress remain at their existing
roots for the next coupled slice. Relocation remains opt-in for disposable developer
projects; existing real projects are not migrated. Missing destinations with legacy records
fail closed, but a presence check is not a verified migration. An offline ownership-bound
copy/verification/rollback operation is required before recommending real-project relocation.
