# Specialized storage ports and R9/R10 reconciliation

P0-5b, [issue #77](https://github.com/wanggiya/action-charter/issues/77).

Keep immutable approval/evidence packages distinct from mutable diagnostic projections
and advisory ranking notes. Move filesystem persistence primitives and closed SQLite
units to platform storage; keep schemas, hashes, scopes and authorization decisions
with their domain owners. Use a separate trusted provider from general metadata
repositories so immutable records cannot accidentally acquire metadata replacement or
deletion methods. Preserve existing layouts and failure/recovery boundaries.

Local contracts require exclusive identity, locked validation/append, transactional
policy revisions and bindings, and no replay on uncertainty. Existing host-local
project/session leases stay in core policy. A distributed backend must provide its
own ownership/fencing implementation and conformance evidence; changing database
drivers alone is insufficient. No live workspace migration, server authority or
exactly-once remote execution is introduced.

R9 and R10 reuse P0-3 and P0-6 rather than restart their completed work. Refine the
original R9 core-location suggestion: the shared DB-dependent driver belongs in data,
while pure policy/ledger contracts belong below it. App already meets R10's size/store
criterion. [Scope, reconciliation and acceptance](../LEDGER_CONTRACTS.md).

Continue with R12 server seams, handle P0-2b stable identity/owner cutover separately,
and retire compatibility last in R11. Owner manual checks remain deferred until the
R series is complete; automated checks are required for each delivered task.
