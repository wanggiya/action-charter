# Workspace storage foundation (P0-2, historical)

Frozen record of the incremental foundation before P0-2 completion. Current behavior
and operator instructions are in [workspace storage](../../WORKSPACE_STORAGE.md).

Status: partial implementation, 2026-11-03. Phase 0 feature freeze applies.
This is a storage refactor, not a new agent or a completed runtime migration.

## What storage does a laptop need?

An ordinary private folder on the existing disk is enough: one SQLite file for
chat/settings/task records, plus subfolders for plans, run evidence and reports.
No additional hardware, PostgreSQL server, cloud account or Docker container is needed
for this workspace. It is distinct from PostgreSQL used as an analysis destination.
Give each project its own dedicated state folder. A future default may be
`~/.local/share/actioncharter/<project>/`; it is not enabled by this foundation.
Existing users do not need to choose a directory or move records now.

## Current storage map

| Responsibility | Existing location | Owner / current consumer | Migration status |
| --- | --- | --- | --- |
| Task/chat snapshots, private task memory, model preferences, submission state and request telemetry | planner-workspace/tasks.sqlite3 | interface_api/planning_tasks.database; model catalog/telemetry and conversation services reuse it | Shared workspace resolver integrated |
| Legacy chat JSON | planner-conversations/ | interface_api/conversation: _path, _read, _write | Resolver integrated; production readers pass source project identity explicitly |
| Saved plans | plans/ | API save/review/approval preparation, workflow/resume and Snakemake plan readers | Resolver integrated; immutable bytes/digests preserved |
| Approvals and workflow recipes | approvals/, workflow-recipes/ | Existing authorization and recipe lifecycle | Resolver integrated for interface workflows and default MCP execution roots; explicit artifact roots remain explicit |
| Durable run history and leases | workflow-state/interface-runs/ | workflow_runs, submission receipts, chat_history and successful-method readers | Resolver integrated; source project passed explicitly for recovery |
| Execution progress and inspection evidence | workflow-state/interface-executions/, inspection-runs/ | Workflow executor and verifier | Resolver integrated; missing progress reads create no state |
| Recipe results, evidence and database attempt receipts | recipe-runs/, recipe-evidence/ (including postgres-attempts/) | Recipe executor, inventory, task history, Critic trace and release readers | Resolver integrated; logical references and one-attempt protection preserved |
| Governed task-event history | task-history/ | Task history, API/CLI, context retrieval and intent revalidation | Resolver integrated; event bytes, hash chains and references preserved; saved chat transcripts remain in the already-adopted planning SQLite store |
| Reports and review/evidence lifecycle | traces/, reports/, critic-results/, releases/, operational-history/ | Recipe/report writers, Critic, release and history lifecycle | Resolver integrated; logical references, immutable records/packages and content hashes preserved |
| Write-session policy and session lease | workflow-state/write-policy.sqlite3 and write-policy.lock | write_policy | Resolver integrated; source project identity and session revocation preserved; separate host-local project ownership prevents a second owner after a live storage change |
| Discovery, installed operations and reusable recipes | library-discovery/, operation-packages/, reusable-recipes/ | operations storage/packages and recipe_catalog | Resolver integrated; snapshot/package/recipe hashes and operation fingerprints retained; discovery grants no execution authority |
| Historical Builder lifecycle artifacts | builder-* directories | builder/*_storage and lifecycle services | Pending; separate storage conventions, not just one folder rename |
| Reviewed context/intent and workflow exports | reviewed-contexts/, reviewed-intents/, snakemake-exports/ and associated evidence | context/intent and Snakemake services | Pending; exact historical references must remain readable |
| Launcher process state and logs | .local/run/, .local/logs/ | scripts/start_actioncharter.sh and launcher | Pending audit of process leases/log paths before relocation |
| Raw data and generated user files | data/input/, data/output/ | MCP settings, source contracts, analytical workers | Separate from internal state; retain existing path contracts |
| Source and credentials | context/, agents/, skills/, src/, .secrets/ | context loader, role manifests, controlled settings | Never moved as runtime state |

The MCP settings already expose individual GEOAGENT_*_ROOT options. Several API paths
still construct project-relative roots directly. A global env redirect would not fix
those paths or callers that derive project identity from parent directories. The new
resolver is deliberately adopted one store at a time rather than pretending a global
switch has completed migration.

## Implemented behavior

`geoagent_harness.workspace.WorkspaceLayout` separates project identity and state root.
Loading/resolving it performs no file creation or data movement. Without configuration,
all locations retain their historical defaults. The shared planning SQLite store, legacy
chat JSON, saved plans, durable interface-run history, approvals, workflow recipes,
recipe results/evidence, execution progress, inspection records, write-policy state and
governed task-event history, reports, traces, Critic records, local release-evidence
packages, operational history and saved discovery/operation/recipe catalogs consume its state root.
API-backed CLI chat/workflow actions and MCP workflow reports use the same services.
Standalone artifact-level CLI commands retain their explicit root options; this does not
redirect every low-level command or GEOAGENT_* setting.

A project-local, untracked `actioncharter.workspace.json` may specify:

```json
{"version": 1, "state_root": ".actioncharter-state"}
```

A relative state root is relative to that project; an absolute external directory is
also supported. Use a dedicated directory per project; this is not a shared or multi-tenant store. No process-wide environment override is introduced, avoiding accidental
redirection of fixture projects or unrelated projects to a live database. Source, data,
secrets and Git subtrees, parent traversal and symlink components are rejected. Read-only
access to an absent database creates nothing. New state/database directories are private.
Existing SQLite bounds, no-follow checks and transaction behavior remain in force.
The configuration file is operator configuration, never model/context authority.

This is an opt-in developer foundation, not a complete relocation switch. Existing users
need no configuration change. Stop all application/CLI processes before changing storage
configuration. If a legacy planning database exists and the destination database is
absent, both read and write access fail with a migration message instead of inventing an
empty history. Adopted file stores similarly reject a missing/empty destination when
legacy records exist. A nonempty destination is not a complete migration manifest;
partial copies are not certified by this presence check. There is no automatic copy, merge, deletion, or migration command yet.
Presence of a destination is not proof of a complete or correct migration.

## Implemented chat/plan/history slice

Source project identity is passed explicitly through production conversation, method-memory,
coordinator, run-recovery and successful-method readers. Private helpers retain an optional
legacy project-relative fallback for old callers/tests; external-store callers must pass
`project_root`. No reverse lookup, global mapping or project identity in serialized evidence
was introduced. Old digests and record schemas are unchanged.

Plan API defaults (save/list/load/edit, review/approval preparation, workflow recovery,
Snakemake references) resolve the same store. Explicit API root overrides remain explicit.
History indexes, receipt reopening and exact chat/plan latest-run lookup use the configured
run directory. Interrupted-run reconciliation inspects partial outputs beneath the source
project's data/output, not beneath the relocated state directory. It never restarts a worker.
Existing run/critic leases move with the interface-runs directory. The subsequent
authority/evidence slice also adopts interface-executions progress and inspection records.

No configured store or real user record was moved during development. The new integration
checks create temporary projects from scratch or perform test-only offline copies.

## Next P0-2 slices

1. Migrate Builder, reviewed-context/intent, workflow export and launcher stores with
   their security contracts. Retain source
   identity, session revocation, history references and exact digests.
2. Audit remaining direct runtime paths in CLI/MCP/adapters and explicit-root compatibility.
3. Provide an offline migration operation: consistent SQLite backup and artifact copies,
   project ownership binding, inventory/count/hash/reference checks, exclusive destination,
   configuration switch last, old store retained for rollback. Do not copy active SQLite/WAL
   files as ordinary files. Do not rewrite historical digests to match new locations.
4. Verify restart/recovery across interfaces and demonstrate a source-only repository root.
   P0-2 is not complete before this exit check and full regression pass.

## Implemented authority/evidence slice

The shared resolver now serves plan/recipe approval and inventory, recipe preparation,
recipe execution, durable progress and inspection records. API-backed terminal workflows
reuse these services. Standalone MCP approved-plan/recipe entry points resolve their
default roots when workspace relocation is configured. Explicit root overrides and the
public load_settings contract remain unchanged; artifact-level CLI commands still use
their declared roots. This is not a completed migration of every CLI/MCP lifecycle.

Artifacts retain logical names such as `recipe-runs/<digest>.json` and
`workflow-state/interface-executions/<digest>.json`. Evidence persistence, task-history
byte checks, Critic trace preparation, Snakemake source checks and release component
assessment/storage resolve those names against adopted stores. Their directories may be
external without changing historical JSON, approvals, recipes or digests. The later
report/review slice below also adopts report and review lifecycle stores. Other unadopted
stores stay project-local; arbitrary external files remain invalid.

Approval issuance receives source project identity explicitly. It binds to that project's
live write session only when using its configured approval directory. An unrelated
explicit approval directory cannot acquire that authority just by naming the source
project. New launcher sessions still invalidate old bindings. Legacy low-level recipe
approval callers retain their optional project-relative fallback.

PostgreSQL's append-only one-attempt receipts follow recipe-runs. Copying them offline
preserves the block on reusing already-attempted authority; relocation does not permit a
database retry. No database connection is needed for the receipt tests. Input/output data
remain under the original project. Missing relocated legacy stores fail before dispatch.
Per-call result-root overrides do not redirect those authority receipts; they use the
project's configured recipe-runs so changing an evidence destination cannot reset them.

Tests use disposable external state, real temporary CSV export/verification and an active
write-policy session. They cover historical approval/review identity, copied attempt
receipts, expiry/session revocation, unchanged copied bytes, evidence inventory, task
history, Critic trace and release source paths. Browser/API/CLI/PTY use fixture models.
Final `make test`: **2,338 passed**, 13 existing spatial warnings, 650.45 seconds.
Interface validation and the relocated fixture browser/API/CLI/PTY journey passed with
zero page errors. The browser exercises authorized grouped export, outcomes/history,
cross-interface continuation and read-only restoration. An initial browser failure
exposed parent-derived approval session identity; the final code passes both active
configured-workspace sessions and the existing unrelated-directory rejection. New
workspace/authority plus write-policy coverage: 26 tests passed. The broader boundary
and release checks also passed before the full run. No live model/database acceptance
or real migration is claimed. The earlier counts below describe prior slices.

## Implemented write-session and task-history slice

The policy database and `write-policy.lock` now resolve beneath the workspace's
workflow-state. Existing default paths and API/CLI policy commands remain compatible.
Missing relocated policy state with an existing legacy database requires an offline
SQLite backup; it cannot silently become a new empty policy store. Restart writes a
new session identity, so copied or previously issued authority is not revived.

A project ownership lock is keyed by the canonical source project path, independently
of state_root. It lives in a private per-user host temporary directory named
`actioncharter-write-owners-<uid>` and records only a state-location hash. This is
coordination metadata, not an authorization store. Merely leaving a lock file behind
does not indicate a running owner: kernel flock ownership determines that. Do not remove
live lock inodes. Active storage changes reject policy access and cannot start a second
owner. Restore configuration and stop all processes before an offline migration. An
active legacy project lease also blocks relocated startup.

These ownership checks target local POSIX processes with the same canonical project
path and shared host coordination directory. This is not a distributed lock or proof
of isolated-container/multi-host ownership. Existing agent/container topology and mounts
are unchanged; external-state deployment/mount validation remains future work.

API task-event recording, inventory, artifact/relationship checks, recovery notes, CLI
history/retrieval/review and intent revalidation share the relocated task-history root.
Low-level explicit history roots remain explicit. This is the existing governed event
store, not a new chat-memory or cross-chat feature. Exact old events and reviewed-context
digests survive test-only offline copies; later appended events invalidate old context
reviews as before. Old source records are not rewritten.

New temporary tests exercise child-process policy visibility, competing owners, live
configuration changes, copied database state, stale approvals, crash/restart, legacy
lease rejection, read-only no-create behavior and API/CLI history parity. No model or
database service is called. The isolated browser/API/CLI/PTY journey also verifies the
policy database and session lock exist only under the temporary configured state root.
Final `make test`: **2,348 passed**, 13 existing spatial warnings, **672.94 seconds**.
All 52 focused session/history/authority/context checks passed, including ten new
relocation tests. Interface validation and the relocated fixture browser/API/CLI/PTY
journey passed with zero page errors. An additional intent HTTP test initially hit the
sandbox's socket restriction; its permitted retest passed. No live local-model or
database-service acceptance is claimed. No real configuration or storage was changed.

## Implemented report/Critic/release-evidence slice

Trace/report production, Critic evidence inventory/assessment/recording, operational
history preparation and local release-evidence package creation/readers resolve the
configured workspace. Recipe execution and fixed approved-workflow services also resolve
default report/trace settings. Explicit custom roots and the public load_settings
contract remain unchanged; low-level artifact CLI commands retain their root options.

API paths remain logical (`traces/...`, `reports/...`, `critic-results/...`,
`operational-history/...`, `releases/...`). Record/package directories and filenames,
Critic evidence references, component hashes and serialized source bytes are unchanged.
Task-history artifact checks now resolve relocated trace/report/Critic references too.
The source project still owns datasets, output data, operation definitions and authority.

Temporary acceptance runs a real CSV export/verification, records a supplied fixture
Critic assessment, prepares operational history and creates a disposable local evidence
package. It independently inspects that package through the existing CLI. Test-only
offline copies retain every artifact byte/hash and current verification link. Changing
the copied source report removes its current-source Critic/release links; the immutable
package remains independently valid against its own recorded copy. Missing relocated
stores with legacy records fail closed, and empty inventories create no state.

No real release package is created or published. Critic assessments in these tests are
fixtures, not live-model evidence. Legacy repository-based tests isolate project ownership
as well as policy paths, so an operator's running launcher cannot influence those fixtures.
Nine new lifecycle tests and 97 focused boundary checks pass. Final `make test`:
**2,357 passed**, 13 existing spatial warnings, **661.64 seconds**. Frontend validation
and the relocated fixture browser/API/CLI/PTY journey passed with zero page errors.
The browser also checks report files exist under the temporary configured state root
and no reports directory was created under its source project. No live local-model,
database-service, publication or real migration acceptance is claimed.

## Implemented discovery and reusable-catalog slice

Saved library inventories, installed operation manifests and registered reusable recipes
resolve the same project-bound workspace in their shared backend readers/writers. API,
CLI, Planner discovery and execution consume these services. The shipped builtin recipes
remain source assets. Raw input/output paths remain beneath the source project.

Snapshot IDs, package pins, recipe digests, fixture test reports and operation-contract
fingerprints are unchanged. Discovery still parses metadata without importing candidate
code; saving an inventory does not install an operation. Installing a closed adapter or
registering a recipe grants no execution authority or dependency installation. Approved
execution independently checks the existing plan/review scope. Explicit low-level roots
elsewhere are not redirected by this change.

Temporary tests cover searchable external snapshots, installed-adapter execution with
and without authority, recipe registration/composition, test-only offline copies with
unchanged bytes, altered records/fingerprints, symlink rejection, missing-copy errors and
side-effect-free empty inventories. All **91 focused backend tests passed** in 40.17 s,
including **11 new relocation tests**. The focused command covered workspace catalogs,
workspace layout, operation discovery, recipe discovery and reusable recipes/runs.
HTTP fixtures required permission for temporary loopback sockets after the sandbox
rejected those sockets. These are fixture checks, not real-model acceptance.
No user state/configuration is moved. Full-suite, frontend/browser and owner manual
acceptance for this slice are deferred to the next session at the owner's request; prior
full-suite results elsewhere in this guide describe earlier slices only.

## Validation

`tests/test_workspace_layout.py` uses temporary projects to cover legacy behavior,
side-effect-free reads, external-root persistence, unsafe config/path rejection,
refusal to hide an existing DB, offline test-only SQLite backup with unchanged legacy
bytes and plan identity, and real conversation coordination with a fixture model plus
shared telemetry. It does not call Ollama or live databases. Full test/interface results
are recorded in WORK_RESUME. Later chat/plan/history evidence is recorded below. Final `make test`: **2,269 passed**, 13 existing spatial
warnings, 537.38 seconds. Interface validation and isolated fixture browser/API/CLI/PTY
journey passed with zero page errors. An initial diagnostic wording incompatibility
was corrected without changing the symlink rejection. No real-model or live-DB
acceptance was performed for this structural slice.

Manual regression for the unchanged default: restart the usual launcher, open an existing
chat, confirm its current plan and outcome/history, and inspect Request diagnostics and
saved model settings. Opening them should not generate a workflow or execute operations.
Do not move your real project records to test this partial foundation.

## Chat/plan/history acceptance

Additional tests use an external temporary state root to exercise exact inspect-on-send,
chat inventory, legacy JSON recovery, plan identity, scoped latest-run lookup, run/history
reopening, no replay and partial-output recovery against the original project. Test-only
offline SQLite/artifact copies preserve every recorded JSON byte and the old source files.
Wrong-project readers and missing relocated stores fail closed. An unapproved CSV write is
rejected by the execution service; the durable runner records a failed, undispatched attempt
without creating the target file or authorization records.

The isolated browser/API/CLI/PTY journey has an `ACTIONCHARTER_TEST_RELOCATED_STATE=1`
test-only mode. It uses a temporary configured state directory while datasets/output stay
under the temporary project. Existing graph/history/result/settings tests run unchanged,
including restoration beyond the global 50-run inventory and frontend/CLI continuation.
Model responses and database failures in this test are fixtures, not live-model/service proof.
Final full-suite result: **2,295 passed**, 13 existing spatial warnings, 562.44 seconds.
Interface validation passed. The configured-workspace browser/API/CLI/PTY journey
passed with zero page errors (`relocatedState: true`), including authorized fixture
writes, history recovery, cross-interface continuation and terminal use. All data/model/
database interactions in this journey are isolated fixtures. No real user state moved.

Default-storage manual regression: restart the usual launcher, open an earlier chat, verify
its graph/outcome/history, then continue with a fresh read-only inspection. Refresh and
check the matching run remains available. Do not configure relocation or move real folders
until the complete offline migration is delivered. No new user setup is needed now.
