# HTTP routing ownership and R8 acceptance

R8, [issue #76](https://github.com/wanggiya/action-charter/issues/76), 2026-11-08 local date.
Implementation and required automated checks are complete. The owner defers manual validation until all R-series work
is complete. Automated gates still run for each task; Git integration remains pending.

R11 follow-up: maintained callers and the launcher now use `apps.http.server`.
The public `interface_api` facade and server alias remain; obsolete internal leaf
aliases are retired. [Partition and compatibility rules](R11_COMPATIBILITY.md).
Use the [combined manual acceptance](R_SERIES_ACCEPTANCE.md) after R11 gates.

## Structure

```text
historical interface_api.server import
                  |
apps/http/server.py            startup, public service exports, composition
                  |
apps/http/transport.py         origin, JSON/body bounds, selected-model scope
                  |
apps/http/dispatch.py          fixed paths and original matching order
                  |
apps/http/routers/             typed parsing and existing service calls
                  |
task_actions / shared owners   policy, coordination, execution and records

apps/http/errors.py            original ordered exception-to-response mapping
contracts/interface_*         unchanged requests and finite limits
```

The former 2,365-line server is replaced by a 172-line composition owner, 84-line
transport, 103-line dispatcher and 133-line error translator. Ten router areas own
settings, history/context/intent, runs, operations, assurance, plans, recipes, results,
workflows and conversations. The largest router is 198 lines; every HTTP implementation
module is below 500 lines. The standard-library server and public entrypoints remain.

The server supplies an immutable context containing the four existing roots and its
trusted service-binding namespace. Routers do not import the server or one another.
This preserves current public service hooks without reverse imports or model-selected
entrypoints. Context carries no new permission, actor, credential or server-autonomy
policy; R12's actor/run/queue/clock work remains separate.

Six task-action modules own 24 existing coordinator/helpers previously embedded in
the server: resource inventories, Critic review, release review, legacy planning and
recipe catalogs, static export, and task context. Their function bodies/signatures
remain unchanged. Six legacy aliases preserve task-action parity. The 16 request
schemas and existing finite constants have neutral contract owners, with identical
JSON schemas. Existing public imports remain available through the server alias.

Two inline responsibilities move into the existing execution action: progress-cache
hydration and execution-result/task-reference linking. The same lock/cache objects,
load checks, partial-link findings and artifact references remain. A typed internal
load error preserves the old distinction between handled recorded-progress failures
and uncaught cache-serialization failures. It is not a new policy or authority gate.

## Preserved boundaries

- Same 21 GET matching branches and 50 allowed POST paths. Exact, regex and operation
  prefix matching retain their order and spelling. Unknown POST paths are rejected
  before JSON parsing; there is no fallback from an unknown path to execution.
- Same loopback startup, origin allowlist, configured-origin validation and both POST
  origin checks. Unsupported methods retain standard-library behavior.
- Same JSON content-type requirement, 65,536-byte body limit and length/error handling.
- Same compact JSON serializer, status codes, response headers, logging suppression
  and endpoint-specific error payloads. This server has JSON responses; frontend
  Markdown/PDF downloads retain their existing implementation.
- Same selected-model context around each POST, including restoration on failure.
  Unexpected exceptions still escape without being translated into success.
- Same typed action/endpoint checks, exact approvals, write sessions, revisions,
  cancellation/progress, durable history and independent verification services.

No agent, processing operation, framework, dependency, UI feature, execution engine
or model-approver path is added. Conversation and model text grant no authority.

## Evidence and limitations

Before editing, the snapshot captured 16 public request schemas, 24 coordinator ASTs,
the serializer/origin/logging/model-scope method ASTs, route matching descriptors and
104 request/error responses. The durable baseline is
`tests/architecture/r8_http_contract.json`; a bounded in-memory probe uses temporary
projects and fixed model/catalog fixtures. All 104 responses match after extraction.
Schema digests and coordinator/method ASTs match independently of end-to-end tests.

Focused existing API/workspace/action/model/layer checks: **146 passed**. Boundary/
workspace/action/layer group: **76 passed**, including ten new cases. Five Critic
fixture bindings and the monotonic clock fixture now target their actual shared
owners; all original assertion ASTs remain unchanged. Public route-level binding
hooks remain functional through explicit context. No guard was weakened.

The first focused HTTP run failed because the sandbox denied loopback sockets;
the permitted rerun passed. The first response probe caught a missing ValidationError
import in the extracted error translator. A new cache-failure test caught an incorrectly
placed exception clause; both extraction errors were fixed before final testing.
Final `make test`: **2,709 passed (713.38 s; 13 existing spatial warnings)**. Frontend validation passed (6.06 s build; existing
bundle-size warning). The isolated relocated browser/API/CLI/terminal journey passed
with zero page errors and one authorized temporary write. These are fixture checks,
not new real-local-model quality, live-database or multi-user readiness evidence.
Final documentation audit: 545 local links / 171 fragments across 39 changed Markdown
files pass; roadmap is 15,963 bytes (below 64,000); whitespace checks pass.

Strict graph: **893 modules / 3,209 internal imports; zero upward or dynamic debt**.
There are 407 audited compatibility adapters (61 package roots), 486 native modules.
R6/R7 guide counts remain their historical completion snapshots; R11 owns retirement.

## Combined manual acceptance after the R series

No owner manual test is required now. Keep the following for the combined pass:

1. Restart the existing launcher with normal settings and ports 5173/8765; previous
   chats, plans, runs and model/write settings remain available.
2. Send `Run a new read-only inspection of sample_orders.csv`. With Inspection on send
   ON, wait for its outcome; otherwise Execute once. Expect six rows/five columns.
3. Reopen the recorded outcome through Execution History, refresh/switch chats and
   inspect the same record through `./actioncharter` history. Browsing must not rerun it.
4. Prepare a fresh disposable CSV output, inspect its exact arguments, enable writes and wait for “Writes: ON”,
   then Authorize and Execute. Edit a separately authorized draft and confirm its old
   decision cannot execute the changed scope. Use the [existing disposable-write guide](R6_COMPLETION_AND_ACCEPTANCE.md#manual-validation-after-r6).
5. Check model selection/reasoning, diagnostics, saved records, operation catalogs,
   result views and downloads. Record actual errors/run IDs, not inferred success.

Live database writes, real workspace cutover and model benchmarks need their own
explicit scope; these structural checks do not authorize them.

## Next handoff

Reuse delivered R9/PostGIS lifecycle and R10/frontend split. Remaining Phase 0 work is
P0-2b stable project identity/owner cutover, P0-5b specialized append-only/concurrency
contracts, R12 server seams and final R11 compatibility retirement. Trace actor/run/
idempotency and ledger ownership together before choosing the next bounded task; do
not rebuild services, enable server autonomy or remove supported stored references.
Keep manual validation deferred until the R series is complete, as the owner requested.

The [P0-5b ledger follow-up](LEDGER_CONTRACTS.md) preserves this same combined journey.
Its storage conformance tests add duplicate-claim, concurrency, rollback and uncertain
publication checks using temporary fixtures; no owner live-database test is required now.
R9/R10 criteria are reconciled there against delivered P0-3/P0-6, with R12 and final
R11 still separate.

The [R12 integration](EXECUTION_CONTEXT.md) wraps dispatch with trusted action context
and buffers early responses until its separate audit acknowledges completion. Existing
route/response contracts stay intact; optional event keys gain explicit duplicate and
storage-uncertainty responses. The combined manual pass remains deferred.

## Environment-independent response probe (PR #82, 2026-11-12)

The historical operation-catalog response contains installed package versions. Those
versions describe the environment, rather than router behavior: for example, the
snapshot's psycopg 3.3.4 can legitimately become 3.3.8 on a fresh CI install. The
in-memory probe now supplies the snapshot's runtime metadata only within its own
scoped registry patch. All 104 complete responses and original snapshot bytes remain
checked. A regression fixture changes host versions, verifies production inventory
stays live, then confirms the probe restores that environment. It does not normalize
away fields, replace the catalog, hide availability or alter production behavior.
