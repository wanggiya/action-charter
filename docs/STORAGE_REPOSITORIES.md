# Workspace storage repositories

P0-5, [issue #62](https://github.com/wanggiya/action-charter/issues/62).
Users keep their workspace setting, launcher, chats, plans and execution history.
There is no new database/dependency to install or automatic record migration.

```text
API / CLI / terminal chat / existing MCP tools
                     |
               shared task actions
          policy, scope, revisions, validation
                     |
             storage.repositories(project)
                     |
          +----------+-------------------+
          |                              |
    metadata transaction          local document repositories
    SQLite tasks.sqlite3          durable-run JSON / saved plans
          |                              |
          +------ configured workspace --+
```

## Responsibilities

| Layer | Responsibility |
|---|---|
| `storage/contracts.py` | Metadata transactions, closed record collections/settings, JSON records and saved-plan interfaces |
| `storage/provider.py` | Trusted application composition point; default is local SQLite/files |
| `storage/metadata.py` | Shared transaction/error adapters and bounded planning-JSON identity/read/write mechanics |
| `storage/sqlite.py` | Existing table layouts, safe database opening, transactions, queries and monitoring/cache retention |
| `storage/files.py` | Bounded no-follow reads, exclusive plan creation, atomic run replacement and lookup |
| Task actions/domain services | Identity/provenance, revision checks, content/record budgets, hashes, approval and execution policy |

Operational metadata includes conversations/private memory, historical tasks,
submissions, chat-history blobs/entries, dataset views, methods, capability attempts
and diagnostics. Settings include model choice/reasoning, review budget and method
switches. The method-helper cache has a separate bounded adapter method for its
existing composite key and retention policy.

Production metadata clients now use `storage.metadata.transaction`, delegating to the
same provider and translating storage failures into the same shared error identity.
`planning_tasks.transaction` re-exports that exact function. It exposes repository
methods without a SQL connection. The old `database()` and raw-transaction private
helper support remain explicitly available to legacy consumers and fixture tests.
They are not model tools. Durable-run storage/lookups and saved-plan access use file
repositories; the original plan schema/version parser and explicit root overrides
remain. Legacy conversation-file reads also use bounded repositories.

## Boundaries and compatibility

R6b2 gives [verified installed-package metadata](TRUSTED_REGISTRY_BOUNDARY.md) a shared
storage owner. The existing bounded no-follow reader and directory helper preserve
installed record formats/digests; package testing/install/execution remain separate.
That earlier ownership move did not implement specialized ledger contracts; the
P0-5b follow-up now supplies them as described below.

- Conversation, private memory, history and an optional restored view commit together.
  Domain errors roll back their record/blob changes in the unit of work.
- Writes retain `BEGIN IMMEDIATE`, five-second locking, FULL synchronization and the
  64 MB database contract. Reads now share a coherent snapshot; absent-storage reads
  do not create a database. Revision comparisons remain inside write transactions.
- Submission claims commit before inference. Chat, receipt and filesystem run writes
  retain their existing separate boundaries. Uncertain receipts never cause automatic
  inference/execution replay.
- Existing table layouts, row order on update, IDs, encoded JSON, plan bytes and digest
  algorithms remain compatible. No old tables are rewritten or records relocated.
- Run replacement synchronizes the file and directory; plan creation is exclusive and
  cannot use replacement. JSON reads reject traversal, symlinks, hardlinks, oversized
  content and special files. FIFO opening is nonblocking.
- A data workflow is not one transaction across SQLite, files and PostgreSQL. Partial
  outputs and uncertain execution still require inspection. Cancellation, authority
  consumption and recovery proposals remain task-action responsibilities.

Storage never grants authority. Metadata collections exclude approvals/write policy.
Models cannot select a provider, supply SQL or register Python entrypoints. Existing
session, exact approval, source/target and deterministic validation checks still apply.

## Provider selection and limits

`repositories(project_root)` resolves the provider without caching a global project
root/connection. `using_repository_provider(...)` is a trusted application/test hook,
scoped by a context variable and restored after use. The existing background dispatcher
copies that context into its worker.

Only the SQLite/file implementation is delivered. No remote backend, server edition
or user-facing backend switch is added. Future profiles can implement these contracts
without SQL in task actions, but require their own failure/concurrency acceptance.
Local filesystem leases remain; this is not distributed coordination.

[P0-5b specialized contracts](LEDGER_CONTRACTS.md) now serve immutable approvals,
evidence and lifecycle records, attempt/event journals, write-policy SQLite records
and the successful-workflow index. They deliberately do not reuse the general metadata
replace/delete interface. Domain owner/session leases remain host-local; no distributed
backend is delivered. Legacy conversation JSON writing still retains its existing
implementation. This is not a universal rewrite or relocation of historic records.
The delivered P0-6 frontend split and R6 layer moves are documented separately.

## R3 transaction and plan contracts

R3, [issue #68](https://github.com/wanggiya/action-charter/issues/68), 2026-11-05.
`storage/metadata.py` owns shared transaction/raw-connection adapters, 32-hex planning
identity validation, bounded JSON reads and planning-record writes. Model preferences,
request telemetry, capability attempts, dataset views and role-mode bookkeeping no
longer import storage access from task actions. Other metadata formats still use the
existing closed repository methods; the 128-record planning limit is not a new limit
on telemetry, view or capability collections.

```text
model / telemetry / capability / data-view / coordinator clients
                              |
                  storage.metadata.transaction
                              |
               unchanged provider and SQLite/file adapters

task_actions planning-state validation
                 |
                 +--> same transaction / bounded JSON helpers
                      + trusted existing-record validator for updates
```

Task actions retain chat revision checks, memory/provenance/schema validation,
historical read projections and atomic transcript/memory/history changes. Their `_get`
first uses the shared bounded reader, then applies the original domain rules. Their
`_put` supplies this validated reader to the shared writer, preserving validation of
an existing memory record before replacement. This reader is an internal Python
composition port, not a callable name or argument exposed to models/MCP. Byte/count
checks, validation order, JSON encoding, rollback and exception chaining remain.

The unchanged `PlanStep`, `WorkflowPlan` and `PlannerResult` definitions now live in
`contracts/planning.py`; `planner.schemas` aliases that module. Shared action-error
identity lives in `contracts/errors.py` and is re-exported from `task_actions.common`.
Both historical error names still identify the same exception. Native imports use
neutral contracts; historical generated strings remain unchanged. Saved-plan loading
continues to use the original approvals parser, path/version checks and canonical
serialization. Storage does not grant execution authority.

No database/table/column migration, new backend, new model/agent, authority change or
real-record move was introduced by R3. P0-5b's specialized ledger/concurrency work is
now delivered separately in the [ledger contracts](LEDGER_CONTRACTS.md). R4's readers/projections and remaining higher-level dependencies are not
completed merely by moving these contract definitions.

The layer baseline drops **75 -> 65 pairs** and **87 -> 68 occurrences**. All ten
removed pairs disappeared from the graph; no new/increased upward import was accepted.
R3 completion graph: 424 application modules, 29 visible aliases and one unchanged reviewed
dynamic import. Strict mode still fails the remaining debt.

Focused storage/layer cases: **77 passed (3.73 s)**; existing task/model/diagnostic/mode
cases: **76 passed (16.96 s)**. Fixtures cover exact UTF-8 bytes, canonical plan hashes,
identity/error compatibility, absent reads, limits, rollback, provider error causes
and retained domain validation in default/relocated workspaces. Frontend validation
passed (6.10 s build, existing bundle-size warning); the isolated relocated-state
browser/API/CLI/PTY journey passed with zero page errors using a fixture model and
temporary inputs/outputs. Full `make test`: **2,555 passed**, 13 existing spatial
warnings, **708.70 s (11:48)**. Normal layer check passes; strict mode correctly
rejects remaining dependency/dynamic-import debt. The documentation audit checked
439 local links, including 152 Markdown fragments; the roadmap remains below 64 KB.
Owner manual validation is deferred to the combined frontend/CLI journey; these tests
must not be presented as owner acceptance or real-local-model/database evidence.

## Original P0-5 verification and manual check

`tests/test_storage_repositories.py` exercises real temporary SQLite/files in default
and relocated workspaces: rollback, old bytes/order, revision/submission races, read
snapshots during WAL commits, owner isolation, read-only/closed-name checks, interrupted
atomic replacement and unsafe files. Instrumented providers test metadata clients
without SQL methods and actual background plan/run persistence. These are fixtures,
not a second production backend or live-model/database acceptance.

Final verification: **2,480 tests passed**, 13 existing spatial warnings, **732.26 s**.
All 33 new repository cases passed (4.10 s), plus 215 focused checks (80.01 s).
Frontend validation and relocated fixture browser/API/CLI/PTY passed with zero page
errors. Initial focused checks corrected a method-memory indentation error and legacy
fixture access; no product code changed during the final full run. Logs and remaining
owner acceptance are recorded in WORK_RESUME. No real-record cutover or live model/
database verification was performed.

For manual verification, restart your usual launcher with existing options. Send
`Run a new read-only inspection of sample_orders.csv.` If Inspection on send is OFF,
click Execute once. Inspect Outcome, refresh and reopen the chat/run: its saved result
should remain. In `./actioncharter`, use `/chats`, `/open CHAT_ID`, `/history` and
`/run RUN_ID` to inspect the same saved work. No new folder setup is needed. Use
disposable local output files for an authorized write check; no live DB change is needed.
