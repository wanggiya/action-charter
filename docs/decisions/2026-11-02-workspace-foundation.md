# Project-bound workspace paths, incremental adoption

Context: P0-2 must separate local state from source without losing chats, exact approval
identity or verifier references. Callers currently mix explicit roots and project-relative
paths; conversation JSON readers even infer project identity from a file's parents.

Decision: introduce a side-effect-free WorkspaceLayout with explicit project/state roots
and a strict project-local configuration. Preserve legacy defaults. Adopt the shared
planning SQLite helper first, refusing an absent migrated DB when legacy state exists.
No global environment override, automatic moves, approval reuse or digest rewriting.

Consequences: this is a working foundation, not P0-2 completion. Other stores remain
project-relative. Next migrate coupled paths and add offline verified copy/rollback before
moving real projects. Shared task-actions (P0-4) and repository interfaces (P0-5) follow.
