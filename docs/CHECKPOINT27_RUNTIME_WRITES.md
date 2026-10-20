# Checkpoint 27.7 — runtime write controls

Implemented slice: 2026-10-19. [Original design](RUNTIME_WRITE_CONTROL_DESIGN.md).
No new model/agent, overwrite operation or execution authority from text is added.

## Behavior

Start with `bash scripts/start_actioncharter.sh`. Write availability starts OFF.
Settings → Allow write operations changes the running API's availability; the
header and information panel report it. Browser refresh keeps the same backend
state; API restart creates a new session. `--enable-write-tools` remains a
compatibility option for starting ON, not an approval. `--read-only-lock` or
`ACTIONCHARTER_READ_ONLY_LOCK=true` explicitly locks the API read-only. The latter
is allowlisted host configuration; default-disabled startup is not that lock.
Model/endpoint configuration changes still require a restart.

GET/POST /api/v1/write-policy read/update typed state. Updates compare expected
session/revision; stale updates reject. Existing JSON/local-origin protections
apply. This is a local single-operator control, not multi-user authentication.
No model tool receives permission-changing access. The UI confirms backend state
and polls while visible; an external CLI change may take up to three seconds to
appear. A failed status request is not displayed as permission to write.

A project-local SQLite store under workflow-state records session/revision,
policy transitions and approval-content digest bindings, separate from immutable
plan/approval JSON. A project lease prevents two API owners; another process can
read the current policy but cannot override OFF through a cached/explicit true
settings object. Symlinked policy paths reject. Store files remain runtime data.

Enabling writes does not approve or execute work. Exact workflow authorization,
expiry, targets and existing validators still apply. Managed-session approvals
bind both plan and recipe decisions to the current session/revision. Changing
availability invalidates pending decisions; toggling back ON cannot revive them.
An idempotent unchanged-state update does not revoke approval. Old decisions are
readable but require fresh authorization before entering a new managed session.

The execution engine checks availability and its authority ticket at each write
operation boundary. Once dispatched, an operation may complete and validate even
if availability turns OFF; later writes cannot start under the old ticket.
Failure records identify the blocked step and observed partial outputs. There is
no automatic replay, rollback or overwrite. Metadata/evidence persistence is not
subject to the data-write switch, so failures and approvals can still be recorded.

## Supported paths and limitations

Main Planner CSV, installed fixed CSV adapter and spatial recipe execution reuse
the policy service and independent checks. The existing direct main-workflow
Snakemake export uses fresh plan authority; it does not rerun source operations.
Approved recipe and fixed vector/PostGIS MCP paths use the same session checks.
Low-level CSV/vector/raster/PostGIS mutators reject managed direct-call bypasses,
even with cached true settings. No new live spatial/database/service acceptance
is claimed from these tests.

Specialized legacy GeoServer publication and PostGIS promotion/rollback paths
are fail-closed within a managed session until their separate authorization
formats have a supported session-binding integration. The switch does not grant
them a generic permit. Legacy direct Snakemake exports likewise cannot use a
managed generator without its execution authority; use the main workflow path.
These limitations must remain visible in capability documentation.

CLI `geoagent write-policy --project-root PATH` reads the running session.
Add `--enabled` or `--disabled` to change availability with the same compare-and-
update service. These commands neither authorize nor execute. Standalone legacy
CLI work without a running API retains its existing explicit startup permissions;
it does not change API state, and an ended API's bound approvals cannot be reused
as standalone authority. Historical JSON inspection remains independent of these
write permits. Cross-platform file-lease portability remains unverified beyond
the current Linux environment.

Overwrite is not implemented by this slice. Existing output collisions reject.
Keep original data and choose fresh output paths. Replacement needs its own typed
scope, target identity, publication/backup behavior and tests.

## Manual validation

1. Stop the old launcher once with Ctrl+C to load this updated backend/frontend.
   Start `bash scripts/start_actioncharter.sh`, keep the terminal running, and
   open http://127.0.0.1:5173. Confirm Writes: OFF.
2. In a new Planner chat request: “Inspect sample_orders.csv. Create a numeric
   column doubled equal to amount multiplied by 2. Preserve original columns and
   propagate missing values. Save to a fresh CSV. Do not execute yet.” Check that
   the actual plan contains inspection and Calculate table columns with the right
   formula. A model failure is a separate planning issue; do not execute an
   incomplete plan.
3. Open Authorize while OFF: writes must be unavailable. Go to Settings, enable
   Allow write operations, then close Settings. Confirm Writes: ON without
   restarting; enabling alone must create no data output.
4. Review and Authorize the exact workflow, but do not Execute. Turn availability
   OFF then ON in Settings. The old authorization/review must clear. Reopen the
   workflow, review and Authorize again. Old cached API requests must not execute.
5. Execute once. Check the saved preview and independent checks. For the six-row
   sample, doubled values are 20, 40, missing, 80, 10, 60. Refresh the browser:
   availability remains ON, chat/results restore, and nothing reruns.
6. Optional CLI check from another terminal: use `.venv/bin/geoagent write-policy
   --project-root /home/jay/projects/geoagent-skill-harness --disabled` as a single
   shell command. The interface should show OFF shortly. This is not cancellation
   of already completed work.
7. Restart the launcher without flags. Availability returns OFF and previous
   session approvals cannot execute. Existing chat/results must stay readable.
   Optionally start with --read-only-lock and confirm Settings cannot enable it.

Mid-run disabling is covered by a deterministic held-validation browser fixture;
small real operations may finish before a manual click. Do not use live database
writes to manufacture a cancellation test. Retrying a completed create-only write
can legitimately reject an existing output: prepare fresh targets and authority.

## Automated verification

`make test`: 1,783 passed. `make interface-validate`: frontend type checking and
production build passed, with the existing bundle-size advisory. The 14 runtime
policy tests cover actual temporary CSV execution, direct/cached/cross-process
bypass rejection, stale/legacy/session authority, concurrent updates, locks,
symlinks, nested export paths and stopping later writes after validation.

Browser scripts passed 23 fixture cases: `browser:test:27-writes` (5),
`browser:test:27-calculations` (12) and `browser:test:26-recipes` (6). These use the
actual shared API, temporary files, fixture model replies and project-local
browser binaries/profiles; they do not exercise live databases or establish
actual-model quality. Launcher syntax, new documentation links and the status
file's 128,000-byte cap also passed. No Git/publication or live-data action.

## Delivery gate revision

The operator now requires generated capabilities (28.1), learning/RL (28.2) and
advanced private memory (29) to be implemented and validated before demo or
real-data testing. This supersedes the earlier minimum-demo proposal. Checkpoint
27 continues on synthetic fixtures: evidence feedback, bounded visualization and
full evaluation. Cross-chat sharing remains deferred to 30+ with a fresh decision.
These requirements are not delivered by a write switch, and no improvement claim
or model-weight training is implied. Demo/publication/Git/live-service permission
remains separate.
