# Stable project identity and offline ownership

P0-2b, [issue #79](https://github.com/wanggiya/action-charter/issues/79).
This is opt-in local ownership infrastructure, not execution permission. Projects
without an identity marker retain path-based behavior. Reading status does not
initialize an identity, create a database or migrate anything.

## What changes

`platform/project_identity.py` resolves a UUID stored in the private, Git-ignored
`.actioncharter-project.json`. It binds the UUID to the source and state directories'
filesystem device/inode identities and their reviewed locations. The workspace
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
runtime state before any transition. The owner's real checkout has not been adopted
or moved by this implementation. Existing legacy projects require no action.

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

The previous source location must be absent, source/state device and inode must
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

## Copies, deployments and limits

- An independent project starts with fresh source and separate state, then initializes
  a new UUID. Copying a marker or runtime state does not provision a new project.
  There is no automatic fork/import of approvals or consumed claims.
- This first rebind supports filesystem renames, not cross-filesystem source copies,
  backup restoration with new inodes, unstable network filesystem object IDs or
  unverified host/container aliases. It refuses those rather than treating a UUID
  string as proof of ownership. Directory object IDs are local ownership checks,
  not content checksums, authentication or defense against a malicious filesystem
  owner. Full-file inventories remain the migration tool's job.
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
