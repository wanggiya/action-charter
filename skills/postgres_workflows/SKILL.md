# PostgreSQL/PostGIS workflow composition

Use registered operation schemas; this guide grants no execution authority. PostgreSQL
operations use the environment-configured connection only. Never request a password,
connection string, arbitrary SQL, package installation or shell execution from a model.

## Ordinary tabular data

1. Establish source identity and row grain using inspect_csv/comprehensive profile and
   supplied codebooks. Identify missing codes, repeated keys and incompatible types;
   do not invent clinical meanings or exclusion rules.
2. Propose typed preparation using existing select/filter/missing/join/calculation
   operations only when needed. Declare join cardinality; reconcile row counts.
   For select/filter/handle_csv_missing/decode/export_csv above 10,000 rows or 8 MiB,
   use streaming=true: bounded chunks, at most 200,000 rows / 64 MiB output, verified
   source identity and replay. It supports original inputs and validated CSV ancestors.
   This does not enlarge join or calculation limits. Streaming aggregate_csv also
   accepts validated CSV ancestors; keep output groups within its existing bounds.
3. discover_postgres_tables / inspect_postgres_table reads allowed ordinary tables,
   including soft-deleted records. Inspection returns exact bounded table_sha256 and
   connection_sha256, counts, nulls, column metadata and a bounded saved preview.
4. import_csv_to_postgres creates a fresh table, with explicit source/name/type/nullable
   mappings, null_values and optional key_columns. An explicit soft_delete_marker may
   add a new NOT NULL boolean default-false column during fresh-table creation. Text preserves leading zeros. Original
   input requires source_sha256 from same-chat inspection; validated CSV ancestors use
   source_step. Backend may bind configured connection identity and already recorded
   source identity, without a new read or any permission grant.
   First propose validate_postgres_import with the same mapping/source. It scans all
   values for casts, nullability and key violations without database mutation. Its
   proposed_ddl is not proof of target existence or permission. Import repeats the
   same checks before CREATE TABLE. Use each column's optional null_values to override
   the global policy only when explicitly justified; do not turn '?' into NULL in
   unrelated fields. Preserve entity IDs as text and distinguish a unique observation
   key from repeated entities. Unsupported types/DDL/constraints require another contract.
5. export_postgres_to_csv creates a fresh selected-column CSV from an exact snapshot,
   or a validated database-writing ancestor for the same table. Null token defaults
   to backslash-N; collisions reject. Export includes all rows, including deleted ones.
6. Soft delete/restore requires explicit unique keys, exact affected count, current
   table digest and an existing NOT NULL boolean marker. Do not add the marker column
   implicitly. Do not rename a target during recovery. Ask for a fresh inspection and
   new exact authorization; never replay an earlier write automatically.

All database and exported-file writes require Allow writes → Authorize → Execute.
Show the configured destination, action, mapping/keys and preconditions in the existing
review panel. A request to prepare or discuss an operation is not authorization. One
review can cover the complete workflow; each approved database step permits one attempt.

## Spatial data

Reuse inspect_vector → load_vector_to_postgis → validate_postgis_layer for compatible
spatial ingestion. Plain CSV import does not create geometry, infer a CRS, enable
PostGIS, transform coordinates or replace existing spatial tables. Existing bounded
PostGIS inspection/comparison/promotion/rollback services keep their own contracts.
Do not substitute new ordinary-table skills for spatial validation.

## Boundaries

Current database reads/import/export: at most 200,000 rows, 100 columns, 64 MiB encoded
snapshot/source/output. Previews: at most 20 rows and 4 KiB. Per-statement timeout 15s;
lock timeout 3s. Default pandas preparation remains bounded to 10,000 rows/8 MiB;
only the qualified streaming paths above have larger bounds. No arbitrary joins/SQL, append/replace, schema
creation, hard delete, automatic sampling or unvalidated model-generated code.

Results/evidence report what actually completed. If commit acknowledgement or later
validation fails, inspect history and the actual target. Cancellation rolls back before
commit; it cannot reverse completed earlier steps. Never treat an uncertain response as
proof of rollback. See docs/POSTGRES_DATA_WORKFLOW.md for acceptance and manual testing.

workflow_report reads source-linked analytical and technical Markdown from a saved run.
It distinguishes proposed DDL from observed column/key metadata, reports partial work,
and includes source/output digests and recovery guidance. No model call, source scan,
write retry or approval occurs. Full database defaults/indexes/grants are not a backup.
