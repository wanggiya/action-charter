# Report and review lifecycle paths during P0-2

Context: authority/evidence and session/history paths support relocation, but report,
Critic and local release-evidence readers/writers still assume the project root.

Decision: adopt traces, reports, critic-results, operational-history and releases together.
Resolve logical references at API inventory/assessment/record/package boundaries, default
execution report settings and task-history byte verification. Preserve source bytes,
hashes, schemas, immutable record/package naming and explicit custom roots. Existing
low-level artifact CLI commands retain their root options.

Consequences: temporary offline copies can verify old source records and packaged copies
independently. Current-source links are invalidated by changed reports; immutable package
contents retain their own verification boundary. No additional model call, agent,
container, publication or live migration is introduced. Legacy fixture ownership must
be isolated along with policy paths to avoid reading an operator's live project session.
Remaining stores and verified migration/ownership/rollback are required before P0-2 is
complete. See [storage guide](../WORKSPACE_STORAGE.md) for acceptance and limits.
