# R11 retires obsolete adapters while preserving supported contracts

## Context

R6–R8 retained 407 adapters during native ownership moves. The original R11 sketch
said “no shims”; subsequent owner-approved planning explicitly preserves required
public and saved/generated references. Some old names are operation/replay identifiers
or reserved candidate-loader namespaces, not merely internal imports.

## Decision

Move maintained callers to native owners, retire 290 obsolete adapters and retain
117 explicit public/schema/SDK boundaries with evidence. Preserve the original R6
inventory and frozen contracts; a separate exhaustive partition records each decision.
Reject new implementation under old supported package roots, reintroduced retired
adapters, unclassified aliases and ordinary caller regressions.

Do not rewrite stored artifacts, registry IDs, generated SDK templates or approval
hashes. The isolated candidate overlay keeps its reserved namespaces. Worker packaging
uses native source and is verified independently of an installed development package.

## Consequences

The project has 613 modules, including the unchanged 496 native implementations.
The literal historical zero-shim target is not claimed; remaining boundaries are
supported compatibility with one implementation and tested identity. A breaking
removal requires a separate migration decision. No new agent, policy authority,
model call, data operation or live-service change. See [R11 evidence](../R11_COMPATIBILITY.md)
and [combined manual acceptance](../R_SERIES_ACCEPTANCE.md).
