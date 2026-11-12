# R6b: share evidence collection and Critic record storage

Context: core history and release assessment imported a role package for deterministic
artifact collection and record reads. That coupled observations and persistence to
model interpretation even when no Critic request was needed.

Decision: move unchanged evidence collection to platform and existing Critic record
construction/storage to storage. Update native callers; preserve three exact legacy
module aliases and public role exports. Keep model interpretation in the Critic role.

Consequences: two upward dependencies disappear, 35 -> 33, without new debt or layer
reclassification. Paths, limits, formats, schemas, canonical hashes and authority checks
remain. No new agent, operation, model call, UI or record migration. Evidence integrity
and consistency do not imply semantic or scientific truth. Broader policy/registry/
ledger ownership remains R6b follow-up; P0-5b and overall R6 are not complete.
See [scope and verification](../SHARED_CRITIC_EVIDENCE.md).
