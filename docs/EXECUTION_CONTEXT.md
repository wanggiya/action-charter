# Action context and local execution services

R12, [issue #78](https://github.com/wanggiya/action-charter/issues/78), 2026-11-08.
Started 2026-11-08; implementation and required automated gates completed 2026-11-09. Owner manual validation remains
deferred until all R-series work is complete. This is Phase 0 infrastructure, not
server autonomy, another agent or a change to data-operation approval.

```text
HTTP / ordinary CLI / terminal over API / existing MCP tools
                         |
                trusted Actor + RunContext
                         |
             task entrypoint / admission / claim
                  |                  |
          existing task actions       +--> separate append-only action audit
                  |
      unchanged exact approval + domain validation
                  |
            existing workflow services
                  |
       operations / validation / original evidence

Local service ports: policy / clock / credential broker / context-copying queue
```

## Ownership and compatibility

| Native module | Responsibility |
|---|---|
| `contracts/task_context.py` | Frozen actor, run, budget and admission-decision types; bounded context/error contracts |
| `platform/action_context.py` | Context-variable scope, parent action and shared thread-safe admission budget |
| `platform/execution_services.py` | Clock/policy/credential/queue/durable-and-query audit interfaces and trusted scoped local composition |
| `platform/storage/action_ledger.py` | Fixed SQLite claims/events/project binding and bounded verified reads; bounded transient query telemetry |
| `core/execution/actions.py` | Context validation, admission, claim-before-call, terminal audit and evidence references |
| Task/application adapters | Fixed entrypoint registration, HTTP event-header parsing, CLI defaults and response buffering |

The explicit inventory in `tests/architecture/r12_entrypoints.json` contains 70 shared
task entrypoints in 20 modules. Internal parsers, pure helpers and metadata repository
methods are not separate tasks. Fixed wrapper assignments preserve module aliases, external signatures and
monkeypatch bindings; coordination stays with its existing owner. Queue/default-clock
delegation and evidence-reference hooks are the intentional service integrations. This is not
library auto-discovery or model-selected Python execution.

HTTP dispatch records remaining application actions, including settings/catalog
requests. Ordinary CLI callbacks establish a context above their existing services.
Static agent/template metadata commands stay independent of a writable workspace.
Standalone proposal-only CLI planning/Builder/Critic calls use transient context too,
so the existing read-only agent containers do not need new writable mounts.
CLI startup and offline workspace migration/verification/rollback retain their own
lifetime: auditing them would mutate the state being checked or span a server lifetime.
Terminal requests use the same HTTP boundary. All 27 registered MCP ingress callbacks
also establish context and bind their server's service profile, including legacy aliases
that intentionally retain identity with fixed data services. All 27 tool definitions
match the captured pre-ingress schemas exactly. The public tools gain no actor/context
argument. MCP calls default to an `mcp` trigger when called independently. Subprocess/network boundaries establish their own
local context; this task does not introduce a cross-process authenticated delegation
protocol. In-process nested calls and queued workers share their parent context.

A server captures its trusted service profile when constructing the HTTP handler,
then installs that profile explicitly in request threads. A context variable in the
bootstrap thread alone would not propagate to those threads. Model selection remains
request-scoped as before; this is service composition, not a request-selected backend.

Local identity is `Actor(actor_id='owner', kind='owner')`. Agent roles describe work;
they are not authenticated principals. Other actor kinds are reserved contracts and
the local policy rejects them. No user/service authentication is implemented here.
Trusted Python callers may supply `actor=` and `run_context=`; those kwargs are not
added to HTTP JSON, CLI options or MCP tool schemas. Actor dictionaries/model text
cannot substitute for the trusted context objects. Nested calls cannot change actor,
run or project. Scoped service providers reset after use and do not cache project roots.

## Admission is not execution authority

The local policy returns `allow / local_owner_admission_only` for the local owner.
That means the function may proceed to its existing domain checks. It does not approve
a plan, enable writes or issue credentials. Policy `deny` and `escalate` stop the call;
there is no automatic human-escalation workflow or model approver in this implementation.

Existing exact hashes, session/revision binding, expiry, write availability, target
checks and deterministic verification remain mandatory. The injectable UTC clock now
provides default workflow/recipe approval times and action/run timestamps; explicit
domain time overrides remain. The local credential broker returns `None`; its request
hook runs inside the existing verified write-operation boundary. Existing worker
password-file access remains unchanged. No credential or raw argument enters the audit.

Optional budgets restrict nested action admission count and elapsed wall time at entry.
The count is wrapped boundary entries, including nested queries, rather than model
calls or dataset operations. They do not interrupt an active operation, replace worker
limits, or impose a new default
model/token budget. Their shared counter spans the current call tree/copied workers;
they are not durable account-wide quotas. Existing cooperative cancellation stays at
safe operation boundaries. The queue copies actor/run, service providers and existing
context variables into an in-process daemon thread; process restart does not replay jobs.

## Durable event identity and failure handling

Default manual invocations receive a fresh run UUID. Identical text alone is not an
event identity: users can intentionally repeat read-only work. A trusted caller can set
`RunContext.idempotency_key`, or an HTTP POST client can send `Idempotency-Key` (1–160
ASCII letters/digits or `_.:@-`). The header supplies no actor, permission or approval.

Designated history/catalog lookups and non-dispatch preparation retain their original
pure-read guarantees: they carry actor/run/admission facts through a bounded transient
query audit, without creating/changing workspace files. The process buffer retains at
most 512 events, each at most 4,096 bytes, filtered by project and run. It contains no
source rows/prompts and is not agent memory or durable recovery evidence. Accepted data
processing/mutations use the durable ledger, even when the processing is read-only.
An explicit event key also forces a durable claim for a query. Queries inside an already
durable processing call share its durable audit. Other query telemetry can expire and
disappears on process exit; a profile needing persistent query telemetry must supply its
own tested query sink. Query records cannot authorize or recover execution.

Claims are scoped to the application audit namespace, source project and actor.
They do not provide cross-process authenticated delegation or cross-namespace replay
coordination; existing exact-operation attempt guards remain mandatory. An explicit
key is consumed by the outer action; nested actions receive separate invocation IDs
under the same run. The claim binds the action name and a request fingerprint, before
calling any service. A changed action/request with that key conflicts. A matching key
returns HTTP 409 with `action_already_claimed`, the earlier action/run IDs and its last
audit phase; it never dispatches again or reissues an approval. It does not replay a
cached response. Normal browser requests and existing submission receipts keep their
existing behavior; no new frontend control is required.

| Failure point | Result |
|---|---|
| Context/policy invalid | No function dispatch; policy denials are audited when admitted to the ledger |
| Claim cannot be acknowledged | No dispatch from that invocation; inspect state before retrying |
| Function raises/cancels | Claim remains consumed; terminal failure is recorded when storage permits |
| Function returns but completion audit fails | Execution may already have happened; HTTP 503 reports `execution_status: unconfirmed`, never falsely says nothing executed |
| Retry after crash/uncertain completion | Existing durable claim blocks repetition, even without a terminal event |

GET and early POST responses are buffered until audit acknowledgement, preventing a
success followed by a second error response. Original route matching, origin/body
guards, response payloads and existing exception mapping remain. New duplicate/storage
errors have their own bounded responses. An audit action completing means its function
returned; for background dispatch this means queued, not that the workflow succeeded.
Existing durable workflow outcomes remain the authority for operation success.

## Stored evidence and limits

For processing/mutations/keyed events, the separate `workflow-state/action-ledger.sqlite3`
uses transactional claims and a
per-run hash chain of started/completed/failed/blocked/reference events. SQL is owned by
the backend; no model or task caller receives a connection. It binds the current source
project and refuses another project sharing the same database. The file limit is 64 MB,
each event is at most 4,096 bytes, and each run at most 100,000 events. MCP uses the
separate `traces/.action-audit/action-ledger.sqlite3` namespace, through its existing
writable trace mount. Its root filesystem, approval and data permissions are not
broadened. Host/controller and container source paths remain independently bound;
stable cross-runtime project identity is P0-2b, not delivered here. Custom MCP profiles
must provide writable canonical trace storage or a trusted ledger implementation.
Bounded reads
verify chain order/digests and do not create missing storage. There is no silent eviction.

Records contain owner/run/trigger/action/parent, admission facts, limits and time.
Arguments are fingerprinted, not stored. Model prompts/replies, exception messages,
source rows, credentials and returned previews are excluded. Reference events link
returned workflow/chat/plan IDs and newly recorded exact approvals to the action.
Existing approval/evidence/result files, schemas and hashes are not rewritten or given
new fields. Action run IDs are distinct from existing workflow run IDs; reference
events connect them. Audit evidence itself never grants authority.

The developer readers are `LocalActionLedger(project).events(action_run_id, limit=1000)`
for local durable evidence; pass `namespace="mcp"` for the MCP ledger in its own
runtime project identity. Use `execution_services().queries(project).events(action_run_id)`
for the bounded transient query buffer.
No new audit viewer is added to the interface. SQLite and data/approval/file writes
remain separate transactions; this is not exactly-once remote execution or a signed,
tamper-proof infrastructure ledger. No remote queue/backend, scheduler, identity provider
or credential issuer is delivered. Future implementations need their own concurrency,
ownership/fencing and failure acceptance.

Include this SQLite file in the existing offline workspace backup/cutover. The migration
tool already handles SQLite files generically. Partial hand-copies that omit an existing
ledger fail closed; do not delete the database to retry a write. Stable project-ID
ownership and the owner's real cutover remain P0-2b. R11 retires compatibility last.

## Verification and later manual acceptance

`tests/test_action_context.py` covers immutable context, nested scope, nonowner and
deny/escalate policy, budgets, injected clock/approval expiry, concurrent/process-restart
duplicates, uncertainty, privacy, project isolation, migration guards, HTTP event keys,
single-response failure handling, CLI lineage and unchanged write authority.
The initial API/CLI/workspace/workflow/conversation/MCP group passed 170 checks.
The final recovery/context/workspace/parity group passed 97 checks, including 31 R12
contract cases. A final MCP/context/security group passes 106 checks, including two
additional ingress/schema/profile cases. Read-only compatibility adds MCP trace-mount
and proposal-only CLI cases (35 R12 cases total); existing MCP/container/context group
passes 116 checks. All existing container mounts and permission tests stay intact. Original behavior assertions remain; fixtures now explicitly retain
new durable audit state in authority/history copies. Controlled evaluation clones
exclude private source-bound action claims when creating independent temporary projects;
no production migration drops them.
The first sandbox run could not open temporary loopback sockets; the permitted rerun
passed. Two older hand-copy fixtures now explicitly include audit state, preserving
their original assertions. New write-authority fixture settings were corrected to include
the required input/output roots.

The preliminary full suite found seven regressions (2,755 passed): query audit wrote
state during pure lookups, private source-bound claims were copied into independent
evaluation projects, and an unused timer read consumed a test clock tick. Those cases
now pass without relaxing their existing checks. The first browser run timed out at
authorization; a diagnostic rerun passed, and the final script explicitly waits for
Writes: ON before Authorize and retains response/screenshot diagnostics. Threaded test
servers also exposed missing service-profile propagation; handler composition now binds
it explicitly, and static metadata CLI calls stay read-only. The 21 test-only action
claims accidentally written in the checkout were preserved intact at
`/tmp/actioncharter-r12-test-audit-preserved.sqlite3` and removed from the checkout;
no existing ledger or data was replaced. New tests cover thread composition and purity.
The corrected suite passed 2,767 tests (801.52 s, 13 existing spatial warnings) before
the final MCP ingress gap was found. That gap is now covered at the MCP application
boundary, preserving fixed-operation identities. Its 2,769-test gate also passed before
the final read-only-container namespace correction; only the completed-source gate below
counts for task completion. Final completed-source `make test`: **2,771 passed (793.66 s / 13:13; 13 existing
spatial warnings)**. Frontend validation passed (4.36 s build; existing bundle warning).
Final relocated fixture browser/API/CLI/terminal passed, zero page errors and one
explicitly authorized temporary CSV write. Strict graph: 902 modules / 3,288 internal
imports, zero upward/dynamic debt; 407 compatibility adapters (61 package roots),
495 native modules. Both owner-checkout audit locations remain absent. No existing
assertion or permission guard was relaxed. No live database/service or secret changed;
Git integration remains owner-controlled. Final documentation audit passes: 43 changed Markdown files,
572 local links and 176 heading fragments; roadmap 16,143 bytes below 64,000;
whitespace clean.

These are temporary-fixture checks, not real-local-model or live-database evidence.
Owner manual tests remain deferred until all R-series work is complete; use the
[combined acceptance guide](HTTP_ROUTER_STRUCTURE.md#combined-manual-acceptance-after-the-r-series)
then. R12 requires no new launcher flag, model call, dependency or permission dialog.
