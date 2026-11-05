# P0-2 workspace cutover

## Context

Runtime state accumulated at the source-project root. Redirecting individual environment
variables missed API readers, default CLI roots, indexes and write-session identity.
Historical evidence cannot be rewritten merely to move its storage.

## Decision

Use a closed, shared workspace resolver keyed by source-project identity. Keep legacy
locations until an explicit offline migration. Resolve artifact defaults across shared
services and CLI adapters; preserve explicit custom roots and container access boundaries.
Keep shipped definitions and user input/output data separate from internal state.

Provide preview, verified copy/cutover, source-only audit and guarded rollback. Back up
SQLite logically, including WAL commits; copy serialized artifacts without changing
bytes/digests. Bind migrated storage to the canonical project. Preserve old roots by
default, or explicitly archive them after cutover; delete no old records. Lock project
ownership, reject unsafe files and source changes, and never infer execution authority.

## Consequences

P0-2's source-only exit can be exercised without moving the owner's live records.
Existing projects remain compatible; their operator must stop all processes and choose
whether/when to cut over. A new session revokes previous session-bound approvals. New
state on either side blocks automatic rollback. Interrupted staging remains inspectable.

Host-local POSIX ownership is not distributed/container coordination. Docker host paths
can use the same state directory while preserving existing explicit container roots and
mount permissions. Changing source identity, Windows support, storage repositories and
multi-user operation remain separate work. See [workspace storage](../WORKSPACE_STORAGE.md)
for operator steps.
