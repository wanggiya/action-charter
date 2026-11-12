# Specialized ledgers and concurrency contracts

P0-5b, [issue #77](https://github.com/wanggiya/action-charter/issues/77), 2026-11-08.
This completes the local specialized storage boundary alongside the
[operational metadata repositories](STORAGE_REPOSITORIES.md). It changes storage
ownership, not operation selection, approval policy or the interface. Existing
workspaces need no configuration change, new dependency or automatic migration.

```text
API / CLI / terminal / MCP
             |
       shared task actions
             |
domain: identity, schema, digest, scope, authority, validation
             |
 platform.storage.ledger_provider (trusted composition)
             |
 +-----------+----------------+---------------------+
 |                            |                     |
immutable records      attempts / event chains   closed SQLite units
create / read / publish claim / append / snapshot policy / success index
 |                            |                     |
 +-------------- existing local workspace ---------+
```

## Delivered scope

Native implementation lives in `src/geoagent_harness/platform/storage/`.

| Contract / implementation | Production clients | Preserved domain responsibilities |
|---|---|---|
| `ImmutableRecords` / `ledger_files.LocalImmutableRecords` | Workflow and recipe approvals; recipe results/evidence/definitions; Critic records; release packages; Builder review/decision/plan/verification packages; PostGIS lifecycle artifacts; JSON traces | Schema/version checks, redaction, exact hashes, trusted roots, package layout, authorization and result interpretation |
| `AttemptLedger` / `ledger_files.LocalAttemptLedger` | PostGIS one-attempt claims/events/status; task event chains; operational event batches | Attempt key derivation, state/sequence, complete chain verification, identity, event budgets and recovery decisions |
| `WritePolicyStore` / `ledger_sqlite.SQLiteWritePolicy` | Session-bound write policy and approval bindings | Project ownership checks, session leases, enabled/locked state, expected revision, ticket capture and exact approval verification |
| `SuccessfulMethods` / `ledger_sqlite.SQLiteSuccessfulMethods` | Successful-workflow catalog and advisory annotations | Eligibility from validated outcomes, deduplication, privacy, scope, source consistency and retention limits |

All 32 affected canonical/digest helper ASTs and the three existing table-DDL strings
match the pre-edit snapshot. Record encodings, filenames, schema versions, digest algorithms, SQL table layouts,
startup invalidation and explicit low-level roots are preserved. Stored/generated
references are not rewritten. Independent artifact hashing remains in domain readers;
it is not replaced by trusting an index. The old private success-index connection
helper delegates to its new owner for compatibility; production catalog functions
use the closed unit and receive no SQL connection.

## Immutable records and mutable projections

`ImmutableRecords` deliberately has no replacement/deletion method. Creation is
exclusive; successful writes flush and synchronize the file and containing directory.
Directory publication between cooperating local writers is serialized by a directory-inode lock. An existing name,
including an empty directory or dangling symlink, blocks publication. File publication
uses an exclusive hard link, retaining the existing staging/cleanup protocol.

Bounded binary reads reject symlinks, hardlinks, special files and oversized content;
FIFO opens are nonblocking. Existing text readers retain their callers' root, type,
size and schema checks. The backend does not infer a trusted root from model text.

Claims consume an exact attempt name before dispatch. Their existence remains a
duplicate guard even if a later write or database commit fails. PostGIS diagnostic
JSON may be replaced atomically; its append-only sibling event journal is retained.
Neither a status snapshot nor an advisory recipe annotation is authority. A failed
sync can leave a record present but durability uncertain: inspect it and actual targets,
never infer permission to repeat the operation.

Task histories retain their persistent per-task lock and exclusive canonical event
files. Operational batches validate the complete bounded history under the same lock
used for appending. Invalid sequence/identity/redaction fails before appending; partial
I/O can still leave an incomplete log, which existing independent readers reject.
This is not a transactional append guarantee across process failure or power loss.

## Transactions and concurrency requirements

These are conformance requirements for another implementation, including a future
PostgreSQL profile; this task does not deliver that profile.

| Boundary | Required behavior |
|---|---|
| Immutable identity | Concurrent creates/publications of the same identity have at most one winner. Existing bytes/packages cannot be replaced, even if empty. No last-writer-wins fallback. |
| Event validation + append | Lock the relevant scope while reading, verifying and appending. Preserve order, unique event IDs and existing byte/event limits. Never truncate/rewrite accepted history through this contract. |
| Dispatch claim | Atomically consume the exact authority/attempt key before dispatch. A crash, uncertain commit or missing completion record does not release the claim. |
| Policy change + binding | Serialize writes (`BEGIN IMMEDIATE` locally; an equivalent transaction/row lock elsewhere). Recheck session/revision inside the transaction; stale/disabled/locked decisions fail closed. Bindings cannot overwrite an existing digest. |
| Success index | Insert sources transactionally with immutable run identity and owner consistency. Roll back failed batches. Annotation updates remain separate advisory metadata; they cannot change source evidence. |
| Scope | Never share a cached root/connection across projects or chats. Enforce the same domain scope checks before returning records. |
| Failure | Roll back uncommitted database changes on close/failure; report uncertainty if commit acknowledgement is lost. A storage exception never triggers inference, operation execution or automatic write replay. |

SQLite and filesystem changes remain separate durability boundaries. For example,
an approval file can be published before its session binding fails. That file stays
inspectable but cannot enter the managed write session without a valid binding.
There is no cross-store transaction and no claim of exactly-once remote execution.

Current leases/locks are host-local POSIX coordination. Core policy retains project
ownership and session-lease checks, including the relocation guard; storage ports own
the SQLite records. A server backend must implement equivalent ownership/fencing and
failure tests rather than merely swapping the SQL queries. Stable project IDs and the
owner's real offline cutover remain P0-2b; actor/run/queue/credential/clock seams are delivered by the separate
[R12 integration](EXECUTION_CONTEXT.md), implementation and required automated gates complete. No distributed coordinator is delivered here.

## Composition and tests

`ledger_repositories()` supplies stateless local factories. The trusted
`using_ledger_provider(...)` hook scopes first-party composition/tests with a context
variable, resets after use and participates in the existing copied worker context.
It is not exposed as a model tool or request-selected backend. Installing a provider
would not grant execution authority.

`tests/test_specialized_ledgers.py` checks competing processes, exclusive identity,
unsafe/bounded reads, sync/short-write uncertainty, checked append concurrency, SQL
rollback/revision locking, immutable source/scoped annotation behavior, provider
isolation and the published-but-unbound approval failure. Existing domain tests retain
their assertions. Focused existing checks: initial integration 127 passed, record
readers 77 passed, history/lifecycle 63 passed (overlapping groups); 27 new ledger
contract cases and three existing frontend workspace cases pass. Final `make test`:
**2,736 passed (750.12 s / 12:30; 13 existing spatial warnings)**. Frontend validation
passed (5.16 s build; existing bundle-size warning). The relocated fixture browser/
API/CLI/terminal journey passed, zero page errors, one authorized temporary write.
Strict graph: 897 modules / 3,239 internal import occurrences, zero upward/dynamic
debt; 407 compatibility adapters (61 package roots), 490 native modules. No existing
assertion was edited or safety guard weakened for this task. An initial new contract
fixture used an incorrect schema import; the fixture was corrected before final gates.
Final documentation audit passes: 41 changed Markdown files, 561 local links,
175 heading fragments; roadmap 15,910 bytes (below 64,000), whitespace clean.
Fixtures use temporary files and local SQLite; they are not real-model/live-DB evidence.
Owner manual validation remains deferred until **all R-series work is complete**;
the combined [HTTP/CLI/browser acceptance guide](HTTP_ROUTER_STRUCTURE.md) remains
the entry point then. No action on live PostgreSQL is required for these tests.

## R9 and R10 reconciliation

The restructure numbers describe responsibilities, not ten new implementations after
R8. These two scopes reuse P0 work already delivered; no new issue or redesign is needed.

| Original criterion | Existing delivery and ownership | Verification / remaining boundary |
|---|---|---|
| R9: one plan → approve → execute → verify → rollback lifecycle, unchanged evidence | P0-3, [issue #60](https://github.com/wanggiya/action-charter/issues/60), [lifecycle guide](POSTGIS_LIFECYCLE.md); one shared driver in `data/databases/postgis/lifecycle.py`, common attempt/artifact services and thin promotion/rollback adapters | Existing `tests/test_postgis_lifecycle.py` exercises both paths, single attempts, partial/uncertain failures and exact authority. P0-5b routes persistence through the new contracts. No live-database acceptance implied. |
| R9 proposed placement in `core/` | Location refined by R6: DB-dependent transaction/inspection work stays in L2 `data`; pure authority, ledger and verification contracts stay in L1 `core`/`platform` | Moving the driver into core would introduce upward dependencies. The strict layer check verifies the delivered split. No second driver is added. |
| R10: workspace split/store, App under about 300 lines, browser checks | P0-6, [issue #63](https://github.com/wanggiya/action-charter/issues/63), [workspace guide](FRONTEND_WORKSPACES.md); App is 48 lines, provider-scoped store and separate workspace controllers/views | `tests/test_frontend_workspaces.py`, frontend type/build validation and isolated browser journeys. Existing UI remains; no Guided/Studio implementation or performance claim. |

R9/R10 implementation criteria are satisfied by that delivered work. Owner combined
manual acceptance/Git review remain pending. R12 now integrates local context/services (implementation/automated gates complete); retain P0-2b's separate
owner cutover, and retire compatibility last in R11 after accounting for public and
stored/generated references. Phase 0 is not complete.
