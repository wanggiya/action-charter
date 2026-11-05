# Shared PostGIS promotion and rollback lifecycle (P0-3)

Tracked in [issue #60](https://github.com/wanggiya/action-charter/issues/60).
Implementation and automated acceptance completed 2026-11-03.
This consolidates existing fixed relation-renaming operations. Models propose;
operator decisions, typed policy, transactional SQL and independent inspection govern
changes. Agent roles and the registered operation set are unchanged.

## Structure

```text
Existing promotion / rollback public entry points and CLI commands
    |
    +-- typed direction-specific plan and evidence binding
    |
    +-- postgis/lifecycle.py
    |     shared decision fields, exact scope/time checks, snapshot/profile helpers
    |     fixed SQL driver, lock/reinspect -> rename -> validate -> commit/cleanup
    |     independent read-only inspection lifetime
    |
    +-- postgis/attempts.py
    |     exclusive claim for this direction + plan hash + approval hash
    |     append-only observed-stage journal + refreshed diagnostic snapshot
    |
    +-- postgis/artifact_storage.py
          shared canonical JSON, immutable packages, hash/path/content validation
```

`postgis/promotion/*` and `postgis/rollback/*` remain compatibility facades. Their
schemas, public function arguments, CLI names/options and package filenames remain.
Existing approval, execution, rollback-plan and verification JSON keeps its sorted,
indented UTF-8 representation and trailing newline. Promotion-plan hashes retain the
existing compact representation. Seven packaged record types share one storage engine.
Explicit roots remain explicit; CLI defaults use the P0-2 workspace resolver.
Stored bytes, package names and returned metadata derive from a detached validated
snapshot, so later changes to the caller's object cannot mix their identities.

Promotion planning and rollback planning retain their distinct evidence requirements.
Promotion rechecks a compatible comparison and archive absence. Rollback planning
requires a matching independently verified promotion chain. A promotion decision cannot
authorize rollback. Separate rollback authority binds its exact plan and verification.
Execution rejects incorrect confirmations/bindings, denied/reordered scope, expired,
future-dated or timezone-ambiguous authority before claiming or opening a transaction.
Historical records are never rewritten to make their authority current.

## Fixed choreography

```text
inspect/compare -> promotion plan -> exact promotion decision
    -> claim attempt -> lock reference + candidate -> reinspect
    -> reference becomes archive -> candidate becomes reference
    -> validate -> commit -> independent promotion verification
    -> rollback plan -> separate exact rollback decision
    -> claim attempt -> lock reference + archive -> reinspect
    -> reference becomes candidate -> archive becomes reference
    -> validate -> commit -> independent rollback verification
```

The shared driver uses serializable transactions, the existing statement/lock timeouts,
and quoted identifiers for the same fixed SQL. Execution still enforces allowed schemas.
Post-validation completes before commit. Verifiers open/read independent state rather
than treating the executor's success declaration as proof. The closed lifecycle is an
internal backend implementation, not an additional arbitrary SQL/MCP dispatch surface.

## Durable attempts and failures

Attempt files resolve under `workflow-state/postgis-attempts/` in the source project's
configured workspace. Their key binds direction, exact plan hash and exact approval
hash. An exclusive, synced claim is recorded before connection creation. Concurrent
calls with the same decision cannot both dispatch. The claim is never automatically
removed, even after rollback, failed connection, process interruption or workspace copy.
A new exact operator decision is needed for a retry, followed by fresh database checks.

Each attempt has a private JSON diagnostic snapshot and a sibling `.events.jsonl`
append-only journal with sequence numbers, observed timestamps and the last requested
rename/validation step. These records do not grant authority or replace independently
verified success evidence. Preserve them with the other workspace records.

| Observed status | Meaning / recovery |
| --- | --- |
| `claimed` | Dispatch has been reserved; a crash may leave this status. Inspect targets before deciding how to recover. |
| `connection_failed` | No transaction was obtained. Correct configuration and make a fresh exact decision before retrying. |
| `mutating` / `validating` | Inspect the last requested step and actual relation names. An interrupted process is not proof of either commit or rollback. |
| `rolled_back` | The pre-commit failure was followed by an acknowledged transaction rollback. Reinspect before a new decision. |
| `rollback_unconfirmed` | Rollback itself failed. Inspect database state; do not assume the first rename was reverted. |
| `commit_requested` / `commit_unknown` | Commit may have reached the server. A later rollback response cannot establish that it did not commit. Inspect actual targets and retain the attempt. |
| `committed` | Commit was acknowledged; independent verification is still required. |
| `committed_receipt_failed` | Commit was acknowledged but final receipt storage failed; the last durable event/claim may show an earlier state. Inspect targets and storage. |
| `committed_close_unconfirmed` | Commit was acknowledged; connection cleanup was not confirmed. This is not recorded as a reverted mutation. |

No automatic retry runs in any of these cases. Error text identifies the affected
lifecycle/status without printing driver credentials. Constructor failures close a
connection already obtained. Invalid evidence and failed authority checks create no
attempt and open no database connection. Missing/unsafe receipt storage blocks dispatch.

## Existing entry points

The commands remain `plan-postgis-promotion`, `record-postgis-promotion-approval`,
`execute-postgis-promotion`, `verify-postgis-promotion`, `plan-postgis-rollback`,
`record-postgis-rollback-approval`, `execute-postgis-rollback` and
`verify-postgis-rollback`. Their help describes the required files, roots and hashes.
They call the same public backend functions as before; the implementation is shared.

Existing MCP promotion planning remains read-only. This work adds no promotion/rollback
mutation endpoint or graph action. PostgreSQL CSV import/export retains its existing
adapter services. Active write-session guards remain in force: a standalone legacy
low-level command does not acquire a running API session's authority. P0-4 is the
separate task-action consolidation; no new authorization bridge is implied here.

## Validation and limits

For an automated check that touches no database service:

```bash
.venv/bin/pytest -q tests/test_postgis_lifecycle.py
```

The stateful fixture executes the production plan, decision, execution-control,
verification and persistence services through a complete promotion/restoration round
trip. It checks default/relocated workspaces, unchanged legacy JSON bytes/hashes,
independent post-commit inspection, offline-copy replay rejection, concurrent claims,
changed/denied/expired/future authority, rename/validation/commit/rollback/cleanup
faults and unsafe storage. Fixed-driver tests check the SQL statements, quoting,
isolation, timeouts and cleanup using a connection fixture.

This is fixture evidence, not a live PostGIS or local-model acceptance claim. No real
service, data or credentials are changed. The existing relation-profile checks compare
schema, keys, geometry metadata and row counts; they are not row-content hashes and do
not prove unchanged values or dependency behavior. Autonomous database maintenance,
dependency-aware migrations and new SQL operations remain outside this consolidation.

| Completion check | Result |
| --- | --- |
| Full `make test` (all tests completed; stop on first failure enabled) | **2,419 passed**, 13 existing spatial warnings, **672.35 seconds** |
| Focused PostGIS/schema/write-policy/workspace checks | **193 passed**, 18.76 seconds; includes **31 new lifecycle/driver/snapshot tests** |
| `make interface-validate` | Typecheck/build passed; existing large-chunk warnings remain |
| `make config` | Passed; starts no containers |
| Relocated fixture browser/API/CLI/PTY journey | Passed, zero page errors |

The final full run includes the detached-snapshot regression. No real database, model
service, user records or workspace configuration was changed. The owner requested and
authorized creation of issue #60; no Git branch, staging, commit, push, merge or release
was performed. Existing checkpoint 15 records remain historical; this guide describes
the consolidated implementation. Current handoff: [WORK_RESUME](../context/WORK_RESUME.md).
