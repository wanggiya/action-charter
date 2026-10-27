# Governed tabular PostgreSQL workflow — 2026-10-26

2026-10-26: [real diabetes frontend test flow](DIABETES_REAL_TEST_FLOW.md) now records
actual files, measured expectations, sectioned-codebook decoding and temporary database
round-trip acceptance. Earlier proposed/unverified statuses below remain historical.

Implementation follows the [real-data acceptance sequence](REAL_DATA_NEXT_TARGETS.md).
Preserve the existing PostGIS inspection/load/validation/promotion services and their
contracts. Add ordinary tabular capabilities through the shared operation registry,
Planner schemas, graph, CLI/MCP and exact recipe authorization/validation paths.

The dependency order is: source/readiness evidence → explicit mapping/preparation →
codebook-join reconciliation → authorized fresh-table import → database inspection →
authorized selected-column CSV export → deterministic semantic reconciliation.
Soft delete/restore is a separately reviewed branch over explicit keys and a matching
snapshot, never a side effect of import or export. Later incremental ingestion, schema
drift, append/replace and broader statistics require their own measured acceptance.

## Boundaries and delivery contract

- One environment-configured connection profile; models never supply credentials/URLs.
- Discover only allowed schemas; inspect bounded table metadata, row count, nulls,
  key candidates and rows. Database reads use read-only transactions and timeouts.
- Import requires explicit source identity, column mapping/types/null policy and a new
  table. Creation and all inserts share one transaction; no append, replace or DROP.
- Export binds to a reviewed table snapshot or a validated ancestor result and creates
  a new CSV. Record column types, null encoding, file hash and semantic row digest.
- Soft delete/restore changes an existing non-null boolean marker for exact unique
  keys, with a table-snapshot precondition and affected-row assertion. It does not add
  columns or delete rows. Fresh-table import may explicitly include soft_delete_marker
  to create a new NOT NULL boolean default-false column as part of the reviewed schema. Restore cannot prove whether an unrelated system changed
  a row before the snapshot; operators must review the current evidence.
- Scope summary belongs beside the graph, not in per-step blocking popups. Allow
  writes enables availability only; Authorize binds exact steps; Execute checks again.
- Snapshot or destination changes reject rather than silently revise approved work.
  A snapshot precondition is not continuing permission to perform future writes.
- Cancellation checkpoints before commit roll back the active transaction. Once commit
  succeeds, retain its receipt; later verification failure is reported as partial work.
  Do not automatically retry database writes. Cooperative cancellation is not instant
  termination of a running database statement; statement timeouts bound that wait.

## Validation and status

Use known-answer CSV fixtures and a dedicated disposable PostgreSQL container with no
production volumes. Exercise import/inspect/export, identifier/null preservation,
soft delete/restore, changed-source/snapshot rejection, target collision, failed casts,
rollback, cancellation and retry. No user database changes are authorized by this task.

This document is the implementation handoff. Update delivered checks and limitations
below after actual execution; it does not assert unrestricted PostgreSQL/PostGIS support.

## Delivered operation slice

| Operation | Effect | Binding and checks |
| --- | --- | --- |
| `discover_postgres_tables` | Read-only | Configured profile, allowed schema, ≤200 ordinary tables |
| `inspect_postgres_table` | Read-only | Full bounded row multiset hash, types/nulls/counts, bounded preview; includes marked records |
| `import_csv_to_postgres` | Database write | Source hash or validated CSV ancestor; configured connection hash; explicit type/null/key mapping; new table only |
| `export_postgres_to_csv` | File write | Exact table hash or validated database ancestor; selected columns; fresh output path; collision-safe null token |
| `soft_delete_postgres_rows` | Database write | Exact table hash, explicit unique keys/count; existing NOT NULL boolean marker becomes true |
| `restore_postgres_rows` | Database write | Fresh exact snapshot/keys/count; existing marker becomes false |

These are registered and available to Planner/graph/recipe execution, not arbitrary
SQL functions. MCP exposes the two read operations directly; writes use the existing
`run_approved_recipe` envelope, not newly exposed unapproved mutators. The frontend
review card shows effect summaries and expandable exact arguments. Operation Outcome
shows the receipt, row counts, commit status and verification. CLI `postgres discover`,
`postgres inspect`, and `postgres effects` use the same contracts; chat/recipe execution
retains the normal authorization process.

Import source digests may be filled from an exact same-chat saved analytical profile;
the configured connection identity is bound mechanically when omitted by the Planner.
No cross-chat retrieval, new file read, model call or permission grant is implied. If
there is no matching source identity, inspect first rather than invent a digest.
Table snapshots bind host/port/database/user plus schema/table/columns and all bounded
rows. They are content identities, not historical version counters. Every approved
database step also records a durable one-attempt claim, preventing replay of the same
approval even if a later restore makes the table content match an earlier snapshot.

Evidence now has explicit database snapshot references alongside physical file
artifacts. Database-only operations persist run/evidence/report records without
inventing filesystem artifacts. Legacy evidence omits the new field when empty, keeping
its serialized bytes/digests. Failed or unconfirmed attempts retain their authority
claim; a deliberate retry needs a fresh approval. Generic recovery does not rename
soft-delete/restore targets; it directs the operator back to target-specific review.

## Practical validation in the frontend

Restart the usual launcher to load the new backend, then refresh the frontend. Keep
ordinary read inspection available with writes OFF. Use a disposable sandbox schema
and a small CSV whose expected values you can independently check before any real-data
write. Database connection/allowed-schema settings come from the existing launcher
`.env`/secret-file configuration; this work does not change those files or start services.

1. Complete the existing full-file readiness inspection on the chosen CSV. Review
   field roles, null markers, encounter keys and codebook meanings. Sampling and any
   clinical exclusions remain explicit decisions, not defaults.
2. Ask: “List ordinary PostgreSQL tables in agent_sandbox. Prepare the workflow only.”
   Click Execute. This is read-only; verify the listed tables and recorded history.
3. In the inspected CSV chat, ask: “Prepare importing this CSV into a new PostgreSQL
   table agent_sandbox.my_fresh_table. Preserve identifiers as text, map the declared
   numeric fields explicitly, include a new soft_delete_marker named is_deleted, and treat only the supplied markers as null. Then export
   the validated table to a new CSV. Do not execute.” Supply actual field/mapping choices;
   do not copy invented names into the real dataset. Existing table names must reject.
4. Review graph parameters and database effect card: profile, schema/table, create-only
   behavior, mapping/null policy, source identity, selected export columns and file path.
   Use the normal Allow writes → Authorize → Execute flow. Authorize alone must change
   no database/file data. The review remains beside the graph rather than per-step popups.
5. Inspect the result/Execution History: every writer must have passing validation.
   Reopen the CSV, compare counts/IDs/nulls/values, and confirm database inspection
   agrees. File exports use an explicit null token; preserve its documented meaning.
6. Only on an appropriate test table with an existing NOT NULL boolean marker: inspect
   it, ask for soft deletion of explicit unique keys, review exact count/marker/snapshot,
   authorize and execute. Inspect again before preparing restore; authorize restore
   separately. Both keep total rows unchanged; neither permanently removes records.
7. Reusing an already attempted approval, an old table snapshot, a changed source hash
   or an existing output destination must reject. On failure, inspect committed/partial
   outputs before recovery; do not repeat writes merely because a response was lost.

Read-only CLI examples (no Python-module invocation is needed if `geoagent` is installed):

```sh
geoagent postgres discover --schema agent_sandbox
geoagent postgres inspect my_fresh_table --schema agent_sandbox
```

The existing terminal workspace remains `./actioncharter` with the launcher running.
Database writes are proposed/reviewed/executed through its shared workflow services;
there is no standalone bypassing `postgres import` command.

## Automated acceptance and limits

`tests/test_postgres_operations.py` covers closed schemas, path/hash/profile rejection,
source contracts, semantic types, file verification, read-only workflow execution,
authority claims and Planner scope. `scripts/postgres_workflow_acceptance.py` starts a
new UUID-named postgres:17 container from the locally available image, with temporary
storage and loopback port, exercises real authorization/transactions, and removes only
that container. It verifies readiness/duplicate inspection, a many-to-one codebook join,
validated intermediate import/export, leading zeros, null encoding, stale snapshots,
marker delete/restore, collision rejection, failed-cast rollback and pre-commit cancellation.
`scripts/postgres_authorization_browser_check.mjs` uses a temporary real API and model
fixture, checks import/marker effect cards and exact authorization, and confirms no
execution/database request happens merely from approval.

This is verified small-fixture functionality, not a benchmark for maximum row limits
or proof of small-model planning reliability on clinical data. Import/export/snapshot
bounds are 200,000 rows, 100 columns and 64 MiB; CSV cells ≤4,096 characters. Existing
pandas transformations/joins still use 10,000 rows and 8 MiB, so use the supplied 5,000-row
sample for the entire preparation round trip first. Larger direct imports can use the
new limits, but full-source preprocessing needs its own resource-strategy extension.
Per-statement timeout is 15s, lock timeout 3s; cooperative cancellation is bounded by
active database statements, not instant interruption. Existing schemas must already
exist; no schema creation or implicit marker creation on existing tables, implicit alterations of existing tables, append, replacement, hard deletion, arbitrary
SQL, filtered export, scheduling/incremental ingestion, or unrestricted PostGIS coverage
is claimed. Codebook join checks enforce cardinality and row reconciliation; clinical
meaning, unmatched-code interpretation and a polished combined findings report still
require the recorded next-task acceptance, not model invention.

An explicit `soft_delete_marker` on import provides the practical marker test without
manual SQL. It appears in the reviewed schema/effect card and is included in semantic
verification. It never alters an existing table. Existing-table soft delete/restore
still requires the marker to be present and NOT NULL.

Final verification: `make test` passed **2,120 tests** with 13 existing raster warnings;
`make interface-validate` passed with the existing bundle-size warning. The final
marker-option change also passed the 9 focused database tests and the real disposable
PostgreSQL acceptance. Database authorization browser checks and the complete existing
frontend/CLI/real-PTY inspection/execution/history journey passed, with no page errors.
No credentials/configuration files were edited, dependencies downloaded, user database
changed, or Git staging/commit/push/merge/publication performed.
