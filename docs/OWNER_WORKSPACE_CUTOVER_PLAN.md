# Owner workspace cutover: reviewed preparation

P0-2b follow-up, [issue #79](https://github.com/wanggiya/action-charter/issues/79).
Observed 2026-11-09. **Preparation only: no real backup, archival, identity adoption,
configuration change or migration has been performed. Actual cutover needs owner
approval of this plan.** Manual R-series interface acceptance is also still pending.

## Observed layout and readiness

| Item | Read-only observation |
|---|---|
| Source and current state root | `/home/jay/projects/geoagent-skill-harness` |
| Identity | `legacy_path`; no UUID marker or workspace configuration |
| Existing runtime roots | 44 entries: 43 directories and `approved-recipes.local.json` |
| Regular files / directories | 2,129 files / 526 directories; dependency links not followed |
| Regular-file bytes | 27,742,154 bytes = 26.46 MiB |
| Symlinks / hardlinks / special files | Six symlinks; zero hardlinks, special or unreadable entries |
| SQLite | Three databases; each read-only `quick_check` returned `ok`; no SQLite sidecars observed |
| Managed writer lease | No project lease found; eight existing artifact/session locks not held |
| Launcher ports | No listener on 5173 or 8765 in the inspected environment |
| Compose containers | None returned for this checkout's Compose working-directory label |
| Actual migration preview | Blocked, correctly: symbolic links are not allowed |

The database paths are `planner-workspace/tasks.sqlite3`,
`workflow-state/write-policy.sqlite3` and
`workflow-state/successful-workflows.sqlite3`. Checks used immutable read-only SQLite
connections only after checking sidecars and leases, and compared file metadata
before/after. They establish structural integrity at inspection time, not semantic
validation of every saved record or proof that all possible external writers stopped.
Ports, leases, file counts and free space must be checked again immediately before
cutover. Processes with explicit custom roots and separately launched containers need
operator confirmation; matching project labels alone cannot discover them all.

Most bytes are `.local/` (11,127,381) and `library-discovery/` (11,659,019).
Chats/settings, plans, approvals, workflows, task history, outcomes, reports, catalogs,
and existing Builder/skill/database-lifecycle evidence are in the migration's closed
runtime-store list. Data files, source, `.git`, `.env`, `.secrets`, `.aws`, `.venv` and
frontend dependencies are outside this copy. No secret values or chat contents were
printed or included in this report.

The `.env` defines `GEOAGENT_PROJECT_ROOT`, `GEOAGENT_RECIPE_ROOT` and
`GEOAGENT_STATE_ROOT`; values were not disclosed or changed. The host launcher's
allowlist does not load these keys from `.env`. No inherited root overrides were
present in this inspection. Actual launcher-terminal exports must still be checked:
explicit roots retain their meaning instead of automatically following the workspace.
Container mappings remain a separate deployment concern; this plan changes no services.

## Blockers and preservation

These three old development sessions each contain two dependency symlinks:

```text
.local/interface-acceptance/20261005T174714Z-7330e5bf/
.local/interface-acceptance/20261005T235717Z-bb7882a9/
.local/interface-acceptance/20261006T022502Z-4dfd6a45/
```

The links are `workspace/.venv` and `workspace/interface/node_modules`, pointing at
the checkout's existing dependency directories. The migration must keep rejecting
them. The proposed solution is to preserve the **entire three session directories**
in the private development-session archive below, moving them only after a verified
backup. Preserve links as links; never follow them or copy their dependency targets.
No session contents, dependency trees or operational records are deleted. The current
source-only migration cannot proceed until this preparation is approved and completed.
A bounded byte screening of all 740 regular runtime files outside those sessions
found no occurrences of their three session IDs. This supports separate archival;
it is not a general proof about every possible compressed or constructed reference.
Keep the complete backup and record each original-to-archive path mapping.

## Proposed locations and storage budget

| Purpose | Proposed location; not created |
|---|---|
| Active state | `/home/jay/.local/share/actioncharter/workspaces/geoagent-skill-harness/state` |
| Independent pre-cutover backup | `/home/jay/.local/share/actioncharter/backups/geoagent-skill-harness/<unique-cutover-id>/` |
| Three preserved development sessions | `<backup>/development-sessions/` |
| Preserved old operational roots | `<active-state>/.legacy-source/`, created by the migration tool |

Both proposed parents currently resolve to the source filesystem; the active
destination does not exist. About 35.34 GiB was available. Reserve at least **256 MiB
for this measured snapshot**, then recalculate before applying. This covers a complete
runtime backup, the new verified state copy, metadata/manifests and headroom. Archived
original roots move on the same filesystem rather than being duplicated again.
It excludes copying user datasets and installed dependencies. A same-disk backup
protects against a mistaken cutover, not disk loss; an additional external backup is
an owner choice. Use new private directories (0700) and files (0600), never merge
with an existing destination.

## Execution sequence after approval only

1. Confirm all project writers are stopped. Recheck inventory, locks, free space,
   destination absence and effective roots. Do not stop or modify live databases.
2. Create an independent backup of the closed runtime roots, SQLite files/sidecars
   and existing identity/config metadata, recording explicitly absent metadata.
   Do not include secrets, source dependencies or input/output datasets. Preserve
   symlink text without dereferencing. Verify every backed-up regular file's bytes,
   link text, paths and entry counts against an offline no-follow manifest before
   altering the source. Any mismatch stops the procedure.
3. Move only the three identified development-session directories into
   `<backup>/development-sessions/`; preserve their files and six links. Verify the
   archive and then rerun the migration preview. No links/special files may remain
   in the migratable roots. If the preview still rejects, stop and preserve both sides.
4. Adopt a stable UUID on the stopped source project, then separately save the
   post-adoption identity metadata in the backup. Adoption precedes migration so
   the migration receipt records `previous_identity` for guarded rollback.
5. Run the existing verified migration with archival, using the exact active-state
   destination above. This copies state, verifies hashes/SQLite logical contents and
   logical references, changes location metadata and archives old runtime roots.
6. **Before launching anything**, require `workspace-verify` to report `verified`,
   `exact_copy: true`, `source_only: true` and no legacy entries. Identity status
   must show the same UUID with the new state root. Source/data/secret locations
   and private backup remain intact. No workflow or database operation is executed.
7. Restart the normal launcher with writes OFF. Confirm the state-root message,
   saved chat/workflow/history restoration and read-only execution using the
   [combined acceptance guide](R_SERIES_ACCEPTANCE.md). A new session does not renew
   old write approval. Owner manual results must be recorded separately from fixtures.

Existing CLI commands for steps 3–6, **not instructions to execute before approval**:

```bash
.venv/bin/geoagent workspace-migrate /home/jay/.local/share/actioncharter/workspaces/geoagent-skill-harness/state --project-root /home/jay/projects/geoagent-skill-harness
.venv/bin/geoagent project-identity --project-root /home/jay/projects/geoagent-skill-harness --initialize --offline
.venv/bin/geoagent workspace-migrate /home/jay/.local/share/actioncharter/workspaces/geoagent-skill-harness/state --project-root /home/jay/projects/geoagent-skill-harness --apply --offline --archive-legacy
.venv/bin/geoagent workspace-verify --project-root /home/jay/projects/geoagent-skill-harness
.venv/bin/geoagent project-identity --project-root /home/jay/projects/geoagent-skill-harness
```

The preview currently fails for the known links; backup/session preservation comes
first. Identity adoption alone is not approval to execute a workflow. Twelve tracked
runtime files/markers will also move with archival; canonical shipped examples stay
under `examples/extension-lifecycle/`. Git status changes are left to the owner;
there is no staging, commit, push or repository cleanup in this procedure.

## Rollback and interruption

Immediately after a complete cutover, while inventories still match and **before
starting the launcher**, the existing guarded rollback can restore prior config and
original runtime roots. It retains the UUID adopted in step 4 and preserves the
destination copy. Preserve the separate development-session archive too.

```bash
.venv/bin/geoagent workspace-rollback --project-root /home/jay/projects/geoagent-skill-harness --offline --confirm-rollback
```

Starting a write-policy session or recording new work changes state and normally
blocks this automatic rollback. Then stop writers, preserve a new complete backup
of current state and review recovery; never discard newer records or force an old
snapshot over them. Returning all the way to pre-adoption metadata is a separate
reviewed recovery, not an automatic deletion of the UUID file.

An interrupted identity/config/owner publication can fail closed before the normal
CLI resolver works. Inspect the preserved migration manifest and both pre-adoption
and post-adoption metadata backups offline. Restore a coherent verified metadata set
only after checking which copy/config was published. Do not invent a UUID, edit owner
records to bypass checks, merge partial state or retry workflow writes.

## Verification already performed

Real owner records: metadata-only inventory, no-follow link inspection, existing
read-only lease probes, three immutable read-only SQLite checks and the blocked
migration preview. No owner files were copied, moved or repaired.

A **synthetic structural fixture**, using the same 44 runtime-root names and three
fake SQLite stores, passed: initial link rejection; preserving three fake development
sessions with six links; clean preview; stable-ID adoption; copy/verify/archive;
`exact_copy`/`source_only`; and immediate guarded rollback with stable UUID and fixture
evidence preserved. No model, workflow, live database, real record copy or Docker
service was involved. This does not certify the real cutover or manual interface test.

Application code and tests were unchanged in this preparation. R11's completed
2,808-test/frontend/browser gates remain the preceding implementation evidence;
they were not rerun for this read-only investigation and documentation-only update.
