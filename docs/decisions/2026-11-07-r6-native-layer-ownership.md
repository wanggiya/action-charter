# R6 native ownership and compatibility

Date: 2026-11-07. [Issue #74](https://github.com/wanggiya/action-charter/issues/74).

## Context

R1–R6b2 reduced upward dependency debt from 109 pairs / 128 occurrences to 26 / 26.
The remaining mixed policy, ledger, calculation and role ownership prevented safe
physical moves. The owner requested finishing R6 together, with manual validation
afterward and an immediate R7 handoff. Existing Git work remains owner-managed.

## Decision

Separate existing pure contracts and deterministic policy/record readers from role
generation and coordination, then move implementations to their native layers.
Contracts are L0; core/platform L1; data/workspaces L2; capabilities L3; agents/evolution
L4; task actions L5; application adapters L6. Same-layer/downward imports are allowed.
The fixed internal MCP client is platform infrastructure, not an external-agent connector.
Recipe action coordination belongs in task actions; pure recipe definitions stay below it.

Preserve old leaf imports as exact module aliases and package roots as export facades.
Audit these adapters through an explicit owner/source-SHA manifest, prohibit business
definitions in them, and keep ordinary layer rules for native imports of old paths.
Do not rewrite stored/generated entrypoint strings or change schema, digest, approval,
execution, evidence or tool-allowlist contracts. Keep the main CLI/HTTP split for R7/R8.

## Consequences

The strict graph has no upward or dynamic-import debt. Core policy/record imports no
longer require roles or data execution. Compatibility preserves identity of classes,
exceptions, locks and contexts, but temporarily increases Python file count and adds
about 151 KB of source; R11 owns retirement after supported references are accounted for.
This is static dependency enforcement, not a stronger sandbox, distributed ledger,
new agent, processing capability or model-authorization path.

Native public service ports retain established late-bound CLI behavior. Tests move
their imports/mock binding sites without weakening existing assertion ASTs. Validation,
initial failures and repairs, manual checks and R7 handoff are recorded in the
[R6 guide](../R6_COMPLETION_AND_ACCEPTANCE.md). Automated fixtures are distinct from
real-local-model/live-database acceptance. P0-2b real cutover, P0-5b and R12 remain open.
