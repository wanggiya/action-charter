# P0-5: local repository interfaces

Context: shared task actions still embedded SQLite statements and run-file mechanics.
Chat/memory/history/view atomicity and committed submission claims must survive a
storage abstraction; historical formats, IDs, hashes and authority must remain.

Decision: add closed metadata transaction/record/setting and file/plan contracts over
the existing local SQLite database and JSON files. Move SQL out of operational actions
and their model/settings/view/diagnostic clients. Retain raw-connection compatibility
explicitly for legacy/fixture consumers. Domain policy, provenance, revision checks
and recovery stay in services. Read snapshots become coherent; writes retain immediate
locking and rollback. Provider selection is a trusted application composition hook.

Consequences: those clients no longer embed SQL. No schema migration, new dependency,
remote backend, UI, agent or automatic retry. Specialized authority/evidence stores,
ranking and filesystem coordination remain separate. Fixture checks do not establish
server production readiness or local-model quality.
