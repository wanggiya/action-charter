# Opt-in stable project identity

## Context

Path digests coupled workspace ownership and write/audit scope to a source checkout.
Installed code must serve explicit projects without making a path or copied UUID
file an execution credential. Existing history, claims and legacy setups must survive.

## Decision

Use one private project UUID with explicit source/state filesystem-object bindings.
Absent markers preserve legacy behavior. Adoption and same-filesystem rename rebind
are trusted offline operator actions guarded by ownership and artifact leases.
Copied or substituted directories fail closed. Workspace state migration retains the
UUID after verifying its copy and records prior identity for guarded rollback.

Keep original audit scope as provenance: a verified identity accepts its one original
path scope or UUID scope. Do not rewrite claim/event rows or canonical approvals.
RunContext path checks remain strict; moves do not renew sessions or authority.

## Consequences

One shared resolver serves workspace, policy, audit and task boundaries. No new
agent, role, UI or dependency. Identity survives reviewed local renames and verified
state cutovers. Cross-filesystem source transfers and host/container aliases need
future explicit provisioning; matching UUIDs are insufficient. Metadata crash
recovery remains an offline backup/manifest operation, not automatic repair.
See [commands, limits and evidence](../PROJECT_IDENTITY.md). The owner's real cutover
remains separate, unperformed work.
