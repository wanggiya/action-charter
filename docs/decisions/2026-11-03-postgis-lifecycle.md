# Share the fixed PostGIS relation lifecycle (P0-3)

## Context

Promotion and rollback implemented the same authority checks, relation profiling,
transaction cleanup and immutable package mechanics in separate modules. Public
artifacts and import paths already have consumers and historical hashes.

## Decision

Keep typed direction-specific plans, bindings, results and public compatibility facades.
Share decision fields, scope/time checks, fixed transactional choreography, independent
reader lifetime and immutable package storage. Preserve existing canonical bytes and
CLI contracts. Add workspace-bound one-attempt claims and append-only observed-stage
journals so an uncertain commit cannot automatically reuse the same exact decision.
Promotion and rollback always require separate decisions.

## Consequences

The lifecycle mechanics have one implementation without adding operations or agents.
A failed connection or confirmed rollback still consumes that decision's attempt;
recovery needs inspection and a fresh exact decision. Commit acknowledgement failure is
explicitly uncertain. Legacy records stay readable; ambiguous/future approval times
cannot authorize a new mutation. Existing session guards and professional-tool
credentials remain in place. Metadata profiles are not content checksums or proof of
production readiness. See [operator guide](../POSTGIS_LIFECYCLE.md).
