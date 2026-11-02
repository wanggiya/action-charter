# Governed tabular PostgreSQL workflow — 2026-10-26

## Next implementation: full-data analytical and engineering handoff — 2026-10-29

**Historical implementation plan, now followed by delivered F1–F4 functionality.**
See [current contracts, limits and acceptance](FULL_DATA_WORKFLOW_ACCEPTANCE.md).
The seven-step full-source disposable round trip is qualified separately from local
model generation. F5 remains partial: Single/Three generated and executed a full-file
selection, but advisory model reviews were unavailable within their budgets. The full
seven-step workflow has not been certified as a one-shot model-generated proposal.
The future-tense detail below preserves the original plan, not an assertion that all
its broader acceptance gates are closed.
This continues T03/T04/T05/T13 in [IMPLEMENTATION_TODO](IMPLEMENTATION_TODO.md), rather
than creating another independent checkpoint or agent system. The target is the full
supplied dataset; a 5,000-row sample is a preliminary fixture, never a silent substitute.
Existing delivered capabilities and earlier acceptance below remain historical evidence.

### Target and known baseline

Complete one reusable journey:

```text
Question -> source/readiness inspection -> explicit preparation
         -> analytical calculations -> proposed database mapping + read-only preflight
         -> review exact write effects -> authorize -> execute fresh-table import
         -> inspect actual database schema/content -> export and reconcile
         -> analytical report + technical handoff + saved evidence
```

Full-file calculations/readiness have been independently reconciled for 101,766 rows,
50 fields and 71,518 patient identifiers. That does not certify local-model planning,
clinical interpretation, full-file preparation, database transfer or a final report.
The planning timeout follow-up is documented in
[readiness acceptance](READINESS_ASSESSMENT_AND_FULL_DATA_TEST.md).

Current PostgreSQL import/read/export limits are 200,000 rows / 100 columns / 64 MiB;
several pandas preparation paths still have 10,000-row / 8 MiB limits. The source is
19,159,383 bytes. Being eligible for database import does not make preparation eligible,
and expanded decoded outputs/snapshots must be measured separately. Do not merely raise
all limits or promise unrestricted processing.

### Agent skills and backend responsibilities

| Layer | Planned responsibility | Boundary |
| --- | --- | --- |
| Planner/statistical/PostgreSQL skills | Choose registered operations, use readiness/codebook evidence, propose preparation and table design, explain genuine ambiguities and supported findings | Reasoning/proposals only; no invented field meaning, values, credentials or permission |
| Execution role and shared services | Run the validated typed operations, enforce worker/resource/path boundaries, perform calculations and transactional database changes, record actual results | Models do not supply arbitrary Python/SQL; role labels do not grant authority |
| Critic skill | Review observation grain, repeated entities, mapping/cast coverage, denominators, analytical assumptions and handoff completeness against recorded evidence | Advisory assessment cannot change deterministic results, approve writes or certify missing checks |
| Registry/MCP/CLI/frontend | Expose the same typed arguments, effects, runtime limits, validation/result contracts and saved evidence | No separate implementation of calculations or direct unapproved MCP mutator |
| Report assembly | Deterministically assemble source-linked facts, actual schema/receipts and separately labelled model interpretation | No invented findings, generic success narrative or silent merging of unrelated runs |

Update existing `skills/table_statistics/SKILL.md`,
`skills/postgres_workflows/SKILL.md` and applicable Planner/Critic role guidance when
the corresponding services are qualified. Audit the existing `generate_report`
implementation/registration and its stale-looking skill documentation before deciding
whether to extend it or add an explicitly distinct report contract. Do not instruct
agents to invoke planned operations as though they already exist.

MCP exposes callable contracts, not the implementation of pandas/PostgreSQL itself.
The shared backend implements operations; skills teach agents when and how to compose
them. Register new contracts or compatible extensions with typed schemas, dependencies,
read/write effects, authorization and validation requirements. Reuse existing operation
IDs where compatible, and version materially changed behavior. No new permanent agent,
unrestricted library execution, automatic installation or general SQL console is needed.

### Dependency-ordered delivery slices

1. **F1 — full-file preparation (T03/T04/T13).** Audit/reuse source verification and
   existing selection, filtering, missing-value and sectioned-codebook decoding paths.
   Add bounded streaming only for needed row-local/verified-mapping operations, sharing
   CSV parsing, null semantics and result manifests. Retain bounded dataframe behavior
   for operations that cannot safely stream; joins require explicit cardinality/state
   contracts. Every transform records source identity, parameters, input/output counts,
   null/mapping coverage and fresh output identity. Preserve identifiers, row order
   where promised and original inputs. Check cancellation and publish outputs atomically.
   Acceptance: unrelated known-answer fixtures, all full-source rows for row-preserving
   transforms, declared filtering counts, changed-source rejection, output collisions,
   bounded memory/time and no partial output claimed as success. No silent sample or
   unrequested imputation. All generated dataset files require normal write authority.

2. **F2 — schema proposal and read-only mapping preflight (T04/T13), after F1's
   source/output contracts.** Planner proposes source-to-destination column names,
   supported PostgreSQL types, explicit null policies and observation keys from full
   evidence and supplied definitions. Backend checks every selected value for cast
   compatibility, nullability and key violations against exact source/selection and
   configured connection identity. Report totals and bounded safe findings; do not expose
   raw patient identifiers in model evidence. The current global `null_values` policy
   must not silently turn a meaningful token into NULL across unrelated columns. Audit
   whether an additive per-column policy or an explicit preparation step is needed;
   retain compatibility and bind any new semantics into review/approval identity.
   Acceptance: textual IDs/leading zeros preserved, unique/non-null key evidence, repeated
   patient IDs allowed, exact bad-cast/null/key counts, changed-binding invalidation and
   no database mutation or authority from preflight. A passed preflight is stale if its
   source, mapping or target identity changes; execution must check again.

3. **F3 — fresh PostgreSQL round trip (T13), after F1/F2.** Reuse create-only import,
   database inspection and snapshot-bound export. Use bounded bulk/streaming execution
   only after inspecting current implementation and testing its transaction/resource
   behavior. Verify the actual destination column types, nullability, keys and counts;
   reconcile exported values with the prepared source under a recorded normalization
   policy. CSV byte hashes alone are not semantic equality after type/null/order changes.
   Acceptance: full-file import/inspect/export in a disposable database, exact identifiers,
   numeric precision/null preservation, target collision, source/target drift, rollback,
   cancellation and one-attempt/recovery evidence. Distinguish committed writes from
   failed later verification. Never automatically repeat a write. Existing production
   tables/services and their data are outside this acceptance.

4. **F4 — analytical report and technical handoff (T05/T13).** Reuse source-bound
   statistical/readiness evidence and existing Markdown/PDF presentation. Assemble
   results from explicitly compatible workflow steps with source/transformation lineage;
   no implicit cross-chat or cross-source synthesis. Analytical report: question, scope,
   grain, methods, missingness/exclusions, measured tables/charts, interpretations and
   limitations. Technical handoff: source/codebook hashes, workflow/run/operation versions,
   preparation and mapping/null decisions, reviewed versus actually created table design,
   safely rendered DDL/data dictionary, constraints/indexes actually present, verification
   results, export encoding/digests, reproduction and recovery instructions. Before a run,
   label technical material as a draft; after execution derive actual claims from receipts
   and database introspection. Acceptance: reproducible source-linked numbers, actual
   schema agrees with document, explicit unavailable/omitted checks, no secrets or
   fabricated success. Browser downloads stay local; backend report-file creation follows
   normal write authorization. Report scope/budgets and complete-table access are explicit.

5. **F5 — real-model and role-mode acceptance, after F1–F4.** First use unrelated small
   fixtures, then preliminary sample checks, then the full supplied file. Stage planning
   around inspection/preparation/schema boundaries rather than one oversized prompt;
   retrieve relevant contracts and reuse the reviewed current plan. Run the same task
   separately in existing Single and Three modes with the same model and comparable
   settings. Record correctness, calls/tokens when available, prompt sizes, wall time,
   failures, corrections, tool/resource use and user interventions. Do not automatically
   choose modes by tokens alone. Acceptance: correct end-to-end evidence in both modes,
   frontend/CLI continuation, history after restart without execution replay, cancellation
   and clear recovery. A fixture pass or extra role alone is not proof of real-model
   competence. Any live user database write requires separate explicit permission.

### What “good schema” means for the first case

Start with a validated encounter-grain table in an existing allowed test namespace.
Preserve encounter/patient identifiers as text, test encounter uniqueness/non-nullness,
allow repeated patient identifiers, retain age bands as categories, and use numeric
types only for justified measurements/counts with verified range/precision. Declared
missing markers must be distinguished from genuine codes. Supplied codebook labels
are definitions to trace, not independent clinical verification. The full-source test
must not infer a cohort, units or exclusion policy from the filename.

Separate lookup tables, foreign keys, extra indexes, namespace creation and broader
relational normalization require justified contracts, verified mappings and their own
reviewed write effects; they are not silently added. Distinguish a PostgreSQL namespace
from table design. The first slice does not add arbitrary schema maintenance, append,
replace, destructive cleanup or ongoing autonomous production administration.

### Low-friction interaction and authority

User supplies the objective and resolves genuine domain/destination ambiguities.
Planner handles mechanical operation composition, parameter binding and explanations;
backend handles supported safe defaults, validation and evidence. Do not require users
to type SQL, intermediate JSON, mapping definitions that can already be derived from
evidence, or manually register a recipe. Ambiguous semantics cannot be invented to save
a click. Present one coherent review of exact file/database effects where supported.
Read-only operations remain directly executable; writes require Allow writes ->
Authorize -> Execute. Context, history, model text, recipes, a preflight or library
installation never grants or renews authority.

### Resume instruction

Start F1 by tracing the actual preparation reader/writer and verification paths and
existing tests. Then implement the smallest shared streaming preparation slice needed
for the full-data journey. Update skills/registry/interfaces alongside the qualified
backend behavior, run meaningful tests plus `make test`/`make interface-validate`, and
record browser/model evidence separately. Do not mark F1–F5 or the first real end-to-end
test complete from the earlier read-only numerical results. No implementation, database
action, package installation or Git/publication action is authorized by this planning
record alone.

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
