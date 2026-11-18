# M1 provider profiles over the existing gateway

Context: B4/B5 merged in PR #92. Existing model discovery/pinning/gateway and Settings
already provide the shared path. Owner authorized M1 (#93), with M2 still pending.

Decision: add one L0 profile contract, one L1 configuration/credential module and one
L5 shared action module; reuse existing CLI/settings/catalogue/client. Persist a
bounded model-providers.json through existing atomic JSON storage and metadata
transaction locking, rather than introducing a YAML writer or database schema.
Only references to environment/project secret files are stored. Pin configuration
for active requests; resolve referenced credential values privately at send time.

New explicit profiles are loopback-only. Unclassified ordinary requests count as
raw for a coarse allowance guard. This is not M2's context-part egress gate;
legacy environment endpoint semantics remain compatible. Synthetic checks alone
can negotiate schema/object/text formats under one bounded deadline. Generation
never auto-downgrades or retries, and typed output/authorization validation remains.

Consequences: no new agent roles or execution authority; existing model/ref manifests
and budgets remain valid. Local proxy auth is testable without publishing data.
M2 must cover all context paths and legacy endpoints before enabling nonlocal data;
M3c/B6 qualify providers and compare outcomes. Key rotation can affect later sends
without changing the pinned credential reference. No authenticated multi-user/server
configuration or unrestricted provider adapters are claimed.
