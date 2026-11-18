# M2 context classifications at the existing model gateway

Context: M1 (#93) added profiles and a coarse explicit-only guard. Owner authorized
M2 (#94); roles, authority and existing payloads must remain unchanged.

Decision: add one L1 egress module, extend existing L0 provider contracts with context
parts/decisions, and store private content-bound tags on internal ModelRequest.
Classify all product construction sites conservatively. Mixed free text, histories,
notes and evidence remain raw; unchanged static instructions may be none. Changed or
unclassified messages/schemas and serialized labels cannot lower risk. Copy and check
before credentials/HTTP for implicit as well as explicit settings. Reuse diagnostics
and existing storage; no new audit ledger, role, router or operation.

Nonloopback project-data use stays restricted pending provider qualification; preserve
the existing implicit Docker host bridge as trusted local runtime compatibility.
MODEL_DATA_ALLOWED permits restricting the implicit local path without editing chat
or execution policy. Do not auto-redact or send a silently truncated context to fit.

Consequences: M2 establishes a context allowance gate, not semantic de-identification,
Data Card generation, an OS firewall or proof of downstream relay isolation. Most
conversations require raw. Monitoring remains best effort and records uncertainty
honestly; the deterministic gate does not depend on logging availability. Per-role
routing and real gateway qualification remain later tasks. See [usage and limits](../MODEL_EGRESS.md).
