# HTTP routers over existing shared actions

Date: 2026-11-08 local. [R8, issue #76](https://github.com/wanggiya/action-charter/issues/76).

## Context

R6/R7 provide native service and CLI owners, but the HTTP server still mixes parsing,
routing, exception translation and older coordinators in 2,365 lines. The owner
authorized R8 and deferred manual acceptance until the R series is complete.

## Decision

Keep standard-library HTTP startup/composition in `apps/http/server`, common parsing
and origin/serialization in transport, fixed ordered routes in a dispatcher, and
small responsibility routers over existing task actions. Translate the original
exception chain separately while preserving unmatched exceptions and early responses.
Pass existing roots and trusted public service bindings explicitly; routers do not
import the server or one another. Preserve model-selection context and exact authority.

Move 24 existing non-HTTP coordinator/helpers into six task-action owners and 16
request schemas/finite limits into neutral contracts. Move inline cache hydration and
execution/task-reference linking into the existing execution owner. Preserve its
old failure scopes, lock/cache identity and service hooks. Keep exact legacy aliases.

Capture routes, schemas, bodies and response cases before editing. Keep existing test
assertions, retarget fixture hooks to actual shared owners, and require focused/full/
frontend/isolated cross-interface verification. No new features, agents, frameworks,
dependencies, live-service authority or experimental model approval.

## Consequences

Composition is 172 lines, transport 84, dispatcher 103, error mapping 133; largest
router 198. This clarifies ownership without changing URLs or execution semantics.
Seven new audited adapters preserve compatibility; R11 retains retirement ownership.
Static layer success does not establish a stronger sandbox, server-ready ledger or
model quality. [Evidence, limits and combined manual acceptance](../HTTP_ROUTER_STRUCTURE.md)
retain those distinctions. R12/P0-5b/P0-2b remain separate; Git remains owner-managed.
