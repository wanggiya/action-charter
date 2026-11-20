# Stable project identity and offline ownership

P0-2b, [issue #79](https://github.com/wanggiya/action-charter/issues/79).
This is opt-in local ownership infrastructure, not execution permission. Projects
without an identity marker retain path-based behavior. Reading status does not
initialize an identity, create a database or migrate anything.

## What changes

`platform/project_identity.py` resolves a UUID stored in the private, Git-ignored
`.actioncharter-project.json`. It binds the UUID to the source and state directories'
filesystem identities and their reviewed locations. Version 2 records bind each
directory's inode to the kernel filesystem ID (`statvfs.f_fsid`), retaining device
numbers as observations. A later mount device-number change alone does not break
that binding. Unsupported/zero filesystem IDs retain strict version-1 device/inode
checks. Existing version-1 records are never upgraded silently. The workspace
resolver, write-owner lease, action audit and trusted task boundaries share it.
Code can be installed elsewhere; callers still supply the actual project root.
No agent, model or additional model call participates in identity decisions.

Before adoption:

```text
project path -> path digest -> workspace owner / write-owner lease / audit scope
```

After explicit adoption:

```text
project location -> verified directory bindings -> stable project UUID
                                               -> workspace owner
                                               -> write-owner lease
                                               -> audit scope
```

Paths still locate files and constrain individual requests. A stale RunContext
cannot silently follow a moved directory. New requests use its verified new root.
Identity never replaces exact plan hashes, approval scope, expiry, session checks,
safe data paths or consumed event claims.

## Operator commands

Stop launchers, CLI writers and workers, then back up source configuration and
runtime state before any transition. The owner adopted the real checkout before
Phase 0 closeout; transitions below are explicit operator actions. Existing legacy
projects require no action.

Read-only status, using installed code from any working directory:

```bash
geoagent project-identity --project-root /absolute/project
```

Explicit adoption, only after that backup and shutdown:

```bash
geoagent project-identity --project-root /absolute/project --initialize --offline
```

The state directory must already exist. Both the legacy path lease and new UUID
lease are held during adoption; existing artifact leases and local/MCP audit scopes
are checked. A foreign audit scope is rejected. External state ownership advances
from the path-digest record to a UUID record. The command creates no write session
and neither renews nor issues approval. Existing payloads and SQLite bytes remain
unchanged during adoption; the original audit-scope row remains provenance.

For a same-filesystem rename, move the directory while all processes are stopped.
At the new location, reads deliberately fail until this explicit verification:

```bash
geoagent project-identity --project-root /absolute/new-project --rebind --offline
```

The previous source location must be absent, source/state filesystem bindings must
match, ownership must match, and no managed owner or artifact lease may be active.
If an absolute workspace path moved with the project, first update the offline
workspace location to its actual directory. Relative workspace paths keep working.
External state can stay at its original location. The next launch creates a new
write-policy session; previous authority is not renewed by the move.

Use [workspace migration](WORKSPACE_STORAGE.md) for a verified state-root copy.
It retains the project UUID, writes a UUID owner and updates the state object
binding after copy verification. New receipts retain previous identity for guarded
rollback. Automatic rollback refuses historical source locations after a project
move, or a receipt created before identity adoption. Make a new verified backup
instead of forcing an old rollback.

## Device-number recovery after a WSL restart (P2-0, issue #100)

A version-1 identity can reject an unchanged project after a WSL restart because
Linux assigned a new `st_dev`. **Do not initialize fresh state, edit the marker or
use rename/rebind for this case.** Recovery requires the exact recorded source and
state paths, unchanged directory inodes, matching external owner UUID, valid audit
scopes and usable kernel filesystem IDs. A copied directory or substituted state
is refused. Legacy records have no enrolled filesystem ID: these checks cannot
prove that a whole volume was not cloned/restored with preserved inodes. The owner
must confirm this is the original workspace; ambiguous cases remain blocked.

First run ordinary read-only `project-identity` status. If it reports `stable`,
no recovery is needed; start the launcher normally. Device numbering may return to
its original value after another restart without any metadata change.

Stop the launcher and all CLI/worker processes. Choose a **new** backup directory
outside both project and state trees, with an existing owner-controlled parent
that is not group/world writable. The following example uses the state parent from
the owner's current layout; other projects must use their own locations:

```bash
.venv/bin/geoagent project-identity --project-root . --preview-recovery \
  --backup-root "$HOME/.local/share/actioncharter/workspaces/geoagent-skill-harness/recovery-p20"
```

Preview is read-only: it hashes active runtime stores and SQLite WAL/journal bytes,
and reports matching paths/inodes, old/current device numbers, backup size and
`preview_sha256`. Review those facts and the original-workspace limitation. Copy
that exact digest into the explicit recovery command:

```bash
.venv/bin/geoagent project-identity --project-root . --recover-device --offline \
  --backup-root "$HOME/.local/share/actioncharter/workspaces/geoagent-skill-harness/recovery-p20" \
  --expected-digest PASTE_THE_REVIEWED_PREVIEW_SHA256
```

The command takes stable UUID, legacy path and existing artifact leases, verifies
the preview again, and makes a private backup before the sole atomic cutover: a
version-2 identity marker with the **same UUID and legacy scope**. Config, state
owner, serialized history and action-ledger rows are not rewritten. SQLite backups
are verified by integrity/logical checks; non-SQLite payloads by exact hashes.
The backup contains active registered runtime stores, original identity/config/
owner metadata and any migration receipt. It excludes source/input/output data,
secrets, unrelated files and older `.legacy-source` archives; keep their existing
backups. Limits are 200,000 entries / 64 GiB of active state plus bounded metadata.
This is a private recovery copy, not a shareable export or automatic restore tool.

A stale digest, different inode/path/owner/filesystem, unsafe link, active managed
lease or failed backup stops recovery. Partial backups stay for inspection and
are never overwritten. Before marker publication the old binding remains; after
publication the version-2 binding is complete even if writing the final receipt
fails. In that case inspect read-only status and `recovery.json` (which may still
say `verified_before_publication`) instead of rerunning or restoring old authority.
An offline flag is operator confirmation, not proof that arbitrary unmanaged
processes stopped. Locks and final hashes detect managed activity/observed changes;
they cannot exclude a malicious filesystem owner or every external race.

After successful recovery:

```bash
.venv/bin/geoagent project-identity --project-root .
bash scripts/start_actioncharter.sh
```

Expect `mode: stable`, the same project UUID and `execution_authority: false`.
In the interface reopen an existing chat/run and its saved outcome. History must
remain present without regeneration. Writes start disabled; recovery never issues,
extends or renews approvals. If writes are needed later, use the ordinary exact
authorization and Execute flow. Keep the backup until this acceptance is complete.

## Copies, deployments and limits

- An independent project starts with fresh source and separate state, then initializes
  a new UUID. Copying a marker or runtime state does not provision a new project.
  There is no automatic fork/import of approvals or consumed claims.
- This first rebind supports filesystem renames, not cross-filesystem source copies,
  backup restoration with new inodes, unstable network filesystem object IDs or
  unverified host/container aliases. It refuses those rather than treating a UUID
  string as proof of ownership. Directory object IDs are local ownership checks,
  not content checksums, authentication or defense against a malicious filesystem
  owner. A cloned volume preserving filesystem IDs/inodes can defeat local object
  identity; this is not anti-cloning protection. Missing/changed filesystem IDs
  fail closed; do not fall back to inode-only matching.
- Existing legacy container profiles, read-only roots, MCP schemas and writable
  mounts are unchanged. `/workspace` is not assumed to identify a host project.
  Copying the marker into an image or mounting it at an unregistered alias fails
  closed. A previously separate MCP audit with a different source scope also blocks
  adoption; do not edit its scope row. Explicit provisioning for such mappings
  remains future work.
- Publication uses atomic individual file replacement, not a transaction across
  files. A crash between identity, owner and config publication can leave a blocked
  transition. Keep the backup and migration manifest, stop processes, compare the
  previous/verified bindings and restore a coherent metadata set offline. No
  automatic repair, new ID, state merge or authority is inferred.
- Local file ownership, symlink/hardlink checks, bounded records and private writes
  protect configuration handling. This is not multi-user authentication, remote
  delegation, portable filesystem identity or standing server authority.

## Verification

P2-0 fixture coverage: `tests/test_project_recovery.py` exercises pure preview,
same-path device changes, subsequent version-2 device renumbering, real source/
state copies, changed filesystem IDs, foreign owner/audit scopes, active leases,
stale previews including WAL changes, unsafe metadata/backup paths, corrupted and
interrupted backups/publication, exact metadata preservation, CLI confirmation and
stale write approvals. `tests/test_project_identity.py` retains adoption/rename/
migration/rollback regression coverage. No model or live database participates in
this platform-only task. Current owner status is stable again without recovery;
normal owner startup/history acceptance remains pending.

Automated P2-0 evidence: full `make test` **3,160 passed / 13 existing spatial
warnings / 935.56s**, final **145 affected checks passed / 59.09s**. The final
backup-parent fsync guard and added failure case followed the full export; 144 of
those focused cases overlap. All **3,161 final collected IDs** have passing coverage,
not a single uninterrupted final-source invocation. Interface typecheck/build passed
(build4.64s, existing bundle warning), strict layer and compatibility audits passed.
An isolated actual-API/synthetic-CSV browser restored graph/outcome after simulated
recovery and refresh, retained the same run, and made zero planning/dispatch/
authorization calls with zero page errors. This is fixture verification, not a real
filesystem remount experiment or a real local-model performance measurement.

### Earlier Phase 0 verification (historical)

`tests/test_project_identity.py` covers pure legacy reads; byte-preserving adoption of
both audit namespaces; source moves; external state and migration receipts; stable-ID
state cutover/rollback; copied sources/markers/state; independent projects; managed
and unmanaged active leases; invalid markers; foreign audit scope; and installed CLI
use from another working directory. Existing workspace, authority, R12 context, CLI
snapshot and container policy tests remain regression gates. Evidence is temporary
fixtures, not live-model or live-database acceptance.

Owner manual validation remains deferred until the R series is complete. Then use a
disposable project to exercise status, offline adoption, restart, read-only execution,
explicit write approval, rename/rebind and duplicate-event rejection. Do not begin
that acceptance by migrating the owner's only copy.

Automated interface acceptance runs with project-local browser storage. The existing
relocated legacy journey passes, and a second run enables stable identity before
starting the fixture API:

```bash
ACTIONCHARTER_TEST_RELOCATED_STATE=1 ACTIONCHARTER_TEST_STABLE_IDENTITY=1 \
  node scripts/analytical_workflow_browser_check.mjs
```

Both journeys use fake-model fixtures, include frontend/API/CLI/terminal continuity
and one explicitly authorized temporary write, and report zero page errors. A
separate disposable check verifies a relative state directory moving with its source.

Final automated gate: `make test` **2,796 passed, 13 existing spatial warnings,
816.47 s (13:36)**. Frontend typecheck/build passed (4.59 s build; existing bundle
warning). Strict imports: 903 modules, 3,305 internal import occurrences, zero upward
or dynamic debt. Focused groups passed 208 existing/new cases and 37 identity/CLI/
container cases (overlap); there are 25 new identity cases. The owner checkout's
read-only status reports `legacy_path`, no project UUID and no execution authority;
identity/config/action-audit files remain absent. Real owner cutover is unperformed.
