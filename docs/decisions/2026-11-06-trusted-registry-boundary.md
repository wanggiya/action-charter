# R6b2: trusted registry contracts and installed-package metadata

Context: approvals/history/release imported the capability-owned registry, whose loader
imported package execution code to read installed metadata. Table validation/execution
also imported that package module for arguments and read-only identity checks.

Decision: move unchanged registry/source/text/package contracts into neutral contracts,
the current registry reader into platform and verified installed metadata into storage.
Keep testing, installation and execution in their existing owner; preserve public
exports, two exact module aliases, fixed entrypoint strings and canonical formats.

Consequences: seven dependencies disappear, 33 -> 26, without new debt or layer
reclassification. Metadata loads need no agent/operation/scientific runtime and do not
test/install/execute packages. Approval still freshly loads metadata and runs the full
existing policy chain; exact authority, package pins and all validators remain. No new
agent, operation, UI, cache, dependency installation or real-record migration.
Planner-policy and recipe-ledger ownership remain R6b follow-up, with broader data work
still R6c; this does not complete either slice or P0-5b. See
[scope and validation](../TRUSTED_REGISTRY_BOUNDARY.md).
