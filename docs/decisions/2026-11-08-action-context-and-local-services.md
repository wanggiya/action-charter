# Trusted action context and local service seams

R12, [issue #78](https://github.com/wanggiya/action-charter/issues/78).

Use a shared task-entry boundary with frozen actor/run/budget contracts and scoped
local service providers. Local identity remains the owner; an admission policy can
stop a call but cannot bypass exact domain approval. Do not add actor fields to model,
HTTP JSON or MCP schemas. Preserve existing function bodies/public signatures through
explicit first-party wrappers rather than moving role or operation logic into transports.

Persist action claims and hash-chained audit events beside workspace state. Keep them
separate from historic canonical approval/evidence records. Explicit event keys bind
the exact action/request and survive failure/restart; duplicate requests report their
earlier attempt rather than redispatch or refresh authority. Buffer early HTTP responses
until the audit acknowledges completion. Lost acknowledgement is uncertainty, not a
claim that no operation executed.

Provide local clock, policy, credential-broker and context-copying queue implementations.
The broker issues nothing; existing credentials stay in typed workers. In-process
context propagation does not imply authenticated delegation across subprocesses or
networks. Default manual invocations remain distinct; durable keys are optional
trusted-context metadata or an HTTP event header, never authority.

Consequences: internal durable audit writes accompany accepted processing/mutations,
including read-only data processing, and explicitly keyed events. Designated history/
catalog queries retain pure reads through a bounded, non-authoritative transient audit
buffer; they cannot create or rewrite project state. HTTP server composition must
bind the trusted service profile in its request threads. Static metadata CLI commands
need no writable workspace. Backups
must retain that SQLite state; incomplete hand-copies fail closed. No UI, agent, data
operation, autonomous authorization or distributed backend is added. Stable project IDs,
real owner cutover and compatibility retirement remain separate. Owner manual validation
is deferred until the R series is complete. [Contracts and evidence](../EXECUTION_CONTEXT.md).

Preserve deployment permissions: proposal-only role CLI calls use transient context;
MCP durable audit uses its existing writable trace mount under `.action-audit`. The
local/controller ledger remains in workflow-state. Namespaces are deliberately distinct
while source-path identities differ across runtimes; no cross-process authority is
inferred. No Compose permission or mount is broadened.
