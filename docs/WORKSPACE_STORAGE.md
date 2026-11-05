# Workspace storage (P0-2)

P0-2 implementation and automated acceptance completed 2026-11-03.
It consolidates internal runtime state beneath one configurable, project-bound
workspace. Source, datasets, generated user data and credentials retain their separate
contracts. It changes storage, not agent roles or execution authority.

Existing projects keep their historical locations until the owner explicitly migrates.
No real project state has been moved during development. The source-only exit check is
performed on disposable migrated projects; this checkout's existing records are retained.
Earlier implementation evidence is preserved in the
[foundation record](development/storage/WORKSPACE_STORAGE_FOUNDATION.md).

## What belongs where

| Content | Workspace location / behavior |
| --- | --- |
| Conversations, settings, telemetry, task state | `planner-workspace/tasks.sqlite3`, legacy `planner-conversations/` |
| Plans and decisions | `plans/`, `approvals/`, `workflow-recipes/` |
| Runs, progress, write policy, successful-method index, analytical profile artifacts | `workflow-state/`, including existing session locks, SQLite stores and durable receipts |
| Execution and verification evidence | `recipe-runs/`, `recipe-evidence/`, `inspection-runs/`, `traces/`, `reports/` |
| Task events and reviewed reasoning | `task-history/`, `reviewed-contexts/`, `reviewed-intents/` |
| Critic, operational history, local release-evidence packages | `critic-results/`, `operational-history/`, `releases/` |
| Discovery and installed/registered catalogs | `library-discovery/`, `operation-packages/`, `reusable-recipes/` |
| Historical Builder lifecycle | All existing `builder-*` stores; unchanged candidate/review/promotion/activation schemas |
| Skill definitions, candidates, tests and scaffolds | Existing `skill-*` stores, `spatial-contracts/` |
| Database lifecycle artifacts | Existing `postgis-promotion-*`, `postgis-rollback-*`, `geoserver-publication-evidence/` |
| Proposals, replay exports and local development state | `recipe-proposals/`, `recipe-proposals.local/`, `recipe-reviews/`, `snakemake-exports/`, `.local/` |
| Optional old derived inventory | `approved-recipes.local.json` is included in offline copies; its explicit file-based CLI usage is unchanged |
| Source / shipped recipes / agent manifests | Stay in the source project; never treated as runtime state |
| Raw input and generated user files | `data/input/`, `data/output/` stay in the source project and retain safe path and write-approval checks |
| Credentials and environment | `.secrets/`, `.env` stay in place; never copied by workspace migration |

`workspace.py` contains the closed store list. Shared API/CLI/Planner/execution services
resolve it using source project identity. File references remain logical, for example
`reports/report.md`; immutable JSON bytes, artifact digests and operation fingerprints
are not rewritten. Historical Builder bundles are still untrusted candidates until
their existing checks and exact decisions pass. Moving a package does not install it.

Canonical source copies of the old Builder request and raster skill definitions live
under [examples/extension-lifecycle](../examples/extension-lifecycle/README.md). Tests and
the Builder Compose mount use those source copies. Legacy top-level copies remain
compatible and are included in migration; archiving them does not remove shipped examples.

CLI artifact **defaults** use the workspace. Explicit `--*-root` values retain their
literal meaning, including project-local custom directories. Commands without
`--project-root` use the working directory as source identity. Explicit artifact files
are not silently relocated: pass the file's actual path or the supported filename.
Default MCP authority/evidence/state/contract settings use the same resolver; explicit
`GEOAGENT_*_ROOT` settings remain explicit. Low-level Python storage functions accepting
an explicit root continue to accept that root.

## Configuration and ownership

An ordinary private directory on the laptop's existing disk is sufficient. No new
PostgreSQL server, Docker container or dependency is needed for workspace storage.
Give each source project a dedicated directory. New migrated roots must be outside
the source project; this keeps runtime folders out of its top-level directory.

The untracked `actioncharter.workspace.json` records the owner-selected location:

```json
{"version": 1, "state_root": "/absolute/private/path/actioncharter-state"}
```

The resolver also supports normalized project-relative locations for compatibility
with earlier development configurations. Resolving/reading absent state creates
nothing. Source/data/secrets/Git overlap, nesting inside an existing runtime-store name,
parent traversal and symlink components reject. This prevents recursive state copies.
A missing relocated store with existing legacy records fails instead of hiding history
behind a new empty store. This presence check alone cannot certify a manual partial copy.
Use the migration tool for a complete copy/ownership certificate.

Migration binds its private owner record to the canonical source-project path. Another
project cannot adopt that certified workspace. Older manually configured development
roots without this record remain compatible; they are not certified migrations or
multi-tenant stores. Moving the source checkout itself needs an explicit future identity
migration; do not edit the owner record to bypass this check.

The launcher's host-local project ownership lock is independent of state location.
Changing storage during an active session rejects access and second-owner startup.
Restart issues a new write-session identity; copied approvals do not revive stale
session authority. PostgreSQL one-attempt receipts move with the state, preventing
an automatic repeat. These are local POSIX coordination guarantees, not distributed
locks or proof of shared ownership across isolated container namespaces.

## Offline migration

Stop **all** launcher, CLI, worker and container processes that can write this project's
state. The tool blocks the active launcher and held artifact locks, and checks that the
source/configuration remain unchanged during the copy. It cannot detect every unrelated
process using a custom root; `--offline` is an explicit operator assertion.

Run from the source project, using a new dedicated destination that does not exist:

```bash
# Preview only: no configuration change, copy, approval or workflow execution.
.venv/bin/geoagent workspace-migrate /absolute/private/path/actioncharter-state

# Copy, verify and switch; retain old roots in place.
.venv/bin/geoagent workspace-migrate /absolute/private/path/actioncharter-state --apply --offline
```

For a source-only top-level exit, instead use the following second command **after
reviewing the preview**. It archives the old roots under the verified workspace; it does
not delete them. Archive requires the same filesystem so each directory move is atomic.
Do not run both apply commands against the same destination.

```bash
.venv/bin/geoagent workspace-migrate /absolute/private/path/actioncharter-state --apply --offline --archive-legacy
.venv/bin/geoagent workspace-verify
```

Migration:

1. Inventories only the closed runtime stores (at most 200,000 entries / 64 GiB).
   Symlinks, hard-linked files, sockets and special files reject; credentials/data are excluded.
2. Holds host-local project ownership and existing artifact locks. Copies into a private
   staging directory; ordinary files retain exact bytes, hashes and modification times.
3. Uses SQLite backup for committed database state, including WAL content; checks database
   integrity and logical SQL identity. SQLite file headers may differ; serialized evidence
   is not rewritten. Transient SQLite sidecars are not copied as independent databases.
4. Checks copied entry counts, file hashes and logical internal-file references against
   the source, preserving pre-existing unavailable references rather than inventing results.
5. Publishes a private ownership/inventory manifest and atomically changes the config.
   If requested, archives old roots under `.legacy-source/`. Raw inputs/outputs are untouched.

Immediately after cutover, `workspace-verify` should report `status: verified`,
`exact_copy: true`. With archival it should also report `source_only: true` and an empty
`legacy_entries`. The source-only check concerns known internal runtime stores; dependencies,
inputs and ordinary source assets are not required to disappear. Existing tracked
`.gitkeep` markers move with their old folders; review their Git deletions yourself.
Legacy tracked example copies may move too; the canonical copies under `examples/`
remain source assets. The tool never stages or commits those changes.

Normal subsequent work changes state. Verification then reports
`changed_since_migration`; this is not proof of corruption or invalid outcomes. Existing
artifact verifiers still check each record's contracts/hashes. A new consistent backup
is needed before another storage move.

## Rollback and interruption

Before using the migrated workspace, test rollback while all processes remain stopped:

```bash
.venv/bin/geoagent workspace-rollback --offline --confirm-rollback
```

Rollback restores the previous config and archived roots only when both current and
legacy state still match the cutover inventories. New records, a new write session or
changed old explicit-root artifacts block automatic rollback, avoiding silent data loss.
The destination copy and manifest remain available; nothing is deleted.

A failure before configuration cutover leaves the old configuration in force and may
leave a private `*.migrating-*` staging directory. A failure after cutover leaves the
verified destination active; its manifest records archival progress so unchanged-state
rollback can restore archived entries. Inspect the printed path and manifest before
cleanup. Do not merge partial copies or remove a live lock inode. There is no automatic
cleanup of interrupted staging areas and no automatic retry of workflow writes.

Developer `.local/interface-acceptance` sessions may contain dependency symlinks. Such
legacy trees intentionally fail the migration preflight; review/archive those disposable
sessions separately rather than disabling link checks or copying linked dependencies.

## Launcher, Docker and development tools

The existing launcher reports the resolved workspace path and continues to stream API/
frontend logs to the terminal. It does not persist new `.local/run` or `.local/logs` files.
The isolated acceptance-session helper uses the configured `.local/` workspace store.

Compose keeps the existing container destinations, mount permissions, networks and
credential boundaries. Host runtime mounts use `ACTIONCHARTER_STATE_ROOT`, defaulting to
`.` for old direct Compose commands. Make targets resolve this variable from workspace
configuration automatically. When running Compose directly after migration, set it to the
same absolute location shown by the launcher:

```bash
ACTIONCHARTER_STATE_ROOT=/absolute/private/path/actioncharter-state docker compose --profile agents --profile tools config --quiet
```

This validates configuration only; it starts no containers. Do not mount the entire
workspace into every agent. Container runtime project paths remain explicit; host-local
write-session ownership is not a distributed permission bridge to containers. No image
or live service changes are needed to migrate local host state.

## Verification record

| Check | Result |
| --- | --- |
| `make test` (stop on first failure; all tests completed) | **2,388 passed**, 13 existing spatial warnings, **666.49 s** |
| `make interface-validate` | Typecheck and production build passed; existing chunk-size warnings remain |
| `make config` and launcher shell syntax | Passed; no service was started |
| Relocated fixture browser/API/CLI/PTY journey | Passed, zero page errors; core runtime stores absent from source root |
| Temporary offline migration exit | `exact_copy: true`, `source_only: true`, 7 files copied; saved chat and completed run restored |
| Additional source-example checks | 34 passed |
| Final focused completion/compatibility checks | 55 passed |

The temporary exit's source directory contained only `actioncharter.workspace.json`,
`agents/`, `context/` and `data/`. Broader lifecycle fixtures verify catalogs, reports,
Critic/release evidence and Builder artifacts. The owner's checkout was not migrated.

Initial runs exposed default CLI spelling and unsafe-folder diagnostic regressions;
both were corrected. A report lifecycle fixture encountered a 115 ms backward host
clock step and correctly failed strict evidence validation. That fixture now supplies
ordered API timestamps; production timestamp validation was not relaxed. Invalid
historical execution timing still prevents trace adaptation.

Completion status is recorded in `context/WORK_RESUME.md` and `context/CURRENT_STATUS.md`.
New temporary tests cover offline copy/cutover, source-only
exit, chat/run restoration, WAL backup, ownership conflicts, unsafe files, stale authority,
rollback before/after new writes, reviewed-context revalidation and Builder CLI defaults.
The broader suite covers existing explicit roots and approval/evidence chains. Browser
acceptance uses a disposable configured workspace and fixture model/database responses;
it is not a live-model or live-PostgreSQL quality claim.
