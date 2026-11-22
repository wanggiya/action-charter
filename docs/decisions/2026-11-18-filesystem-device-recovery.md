# Reviewed local recovery after filesystem device renumbering

Task P2-0, [issue #100](https://github.com/wanggiya/action-charter/issues/100).

## Context

The owner confirmed that the launcher rejected the adopted workspace after a WSL
restart. Read-only diagnosis found unchanged source/state paths, directory inodes
and external owner UUID, but changed device numbers. Version-1 device/inode binding
cannot distinguish a remount from a copy. Initializing fresh state would lose the
existing ownership/history relationship; rename rebind is the wrong transition.

## Decision

Keep strict v1 checks until explicit offline recovery. A read-only preview binds a
digest to paths, inodes, metadata, observed filesystem IDs, active-state inventory,
SQLite WAL/journal bytes and a new private backup destination. Recovery acquires
existing ownership/artifact leases, checks audit scope and verifies the backup
before atomically replacing only the identity marker. Preserve UUID, legacy scope,
configuration, state owner, payloads and consumed claims. V2 uses filesystem ID and
inode; device number is observed metadata. New initialization uses v2 where a usable
kernel filesystem ID exists, otherwise strict v1. Migration/rebind retain bindings.

## Consequences and limits

This is platform enforcement with a thin CLI, not model guidance or an agent tool.
No model call, new role, processing operation or execution permission is introduced.
Legacy v1 has no prior filesystem ID: owner review must confirm original storage.
Cloned volumes preserving IDs/inodes, malicious filesystem owners and unverified
network/container aliases are outside this local ownership guarantee. Unsupported
or changed IDs fail closed. Interrupted backups remain private and are never
overwritten; marker publication is the only cutover. Backup parent/content syncing
precedes it. Recovery never renews an approval or write session. Actual owner
recovery and launcher/history acceptance remain separate from fixture verification.

Commands, backup coverage, failure handling and acceptance:
[project identity guide](../PROJECT_IDENTITY.md#device-number-recovery-after-a-wsl-restart-p2-0-issue-100).
