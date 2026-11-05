# Write-session ownership and task-history paths

Context: relocating approvals/evidence leaves policy and task-event history at the source
root. Moving the policy lock alone would give a second API a new lock inode if state_root
changed during a live session.

Decision: resolve the policy database/session lock and default task-history store through
the workspace. Keep an additional host-local project ownership flock keyed by canonical
source path in a private per-user temporary directory. Its state-location hash detects
live changes; the actual policy/session/approval checks remain in workspace state. New
sessions revoke old authority. Missing legacy database copies and active legacy leases
block relocation. Do not copy active databases/leases or infer authority from lock text.

History consumers in API/CLI/context/intent resolve the same event store. Event bytes,
hash chains, logical references and explicit low-level roots remain compatible. Saved
conversation memory remains in planning SQLite; no memory feature or agent is added.

Consequences: ownership survives state-location changes within the tested local POSIX
scope. This does not establish distributed or separate-container namespace locking.
Remaining lifecycle stores and verified offline migration/ownership/rollback are still
required before P0-2 completion. Tests use temporary projects, child processes and fixture
models. No real records, model settings, database services or Git state are changed.
