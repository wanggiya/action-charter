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
| `storage/sqlite.py` | Existing table layouts, safe database opening, transactions, queries and monitoring/cache retention |
| `storage/files.py` | Bounded no-follow reads, exclusive plan creation, atomic run replacement and lookup |
| Task actions/domain services | Identity/provenance, revision checks, content/record budgets, hashes, approval and execution policy |

Operational metadata includes conversations/private memory, historical tasks,
submissions, chat-history blobs/entries, dataset views, methods, capability attempts
and diagnostics. Settings include model choice/reasoning, review budget and method
switches. The method-helper cache has a separate bounded adapter method for its
existing composite key and retention policy.

Production clients use `planning_tasks.transaction`, delegating to the provider and
translating storage failures into existing service errors. It exposes repository
methods without a SQL connection. The old `database()` and raw-transaction private
helper support remain explicitly available to legacy consumers and fixture tests.
They are not model tools. Durable-run storage/lookups and saved-plan access use file
repositories; the original plan schema/version parser and explicit root overrides
remain. Legacy conversation-file reads also use bounded repositories.

## Boundaries and compatibility

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

Specialized immutable authority/evidence/lifecycle stores, the successful-workflow
ranking database, write-policy ownership storage and legacy conversation JSON writing
retain existing implementations. This is not a universal migration of every historic
store. P0-6 frontend separation and full import-layer restructuring remain separate.

## Verification and manual check

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
