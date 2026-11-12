# Model participation in authorization; experimental model approver

Date: 2026-11-06. Direction set by the project owner; design only.

Context: comparing with platforms where a model approves tool requests, the owner asked
why authority is deterministic-only. Strict "models only propose" was judged too narrow.

Decision:
- Models participate in most of the process: planning, review, risk flags, making
  decisions stricter, sensitivity classification (stricter on uncertainty), drafting
  rules for human approval.
- Deterministic policy still grants by default (`allow` / `deny` / `escalate`).
  Conversation or data text never grants authority.
- Models seldom grant authority. The option is kept as an **experimental model
  approver**: off by default, enabled by a human per automation with expiry, only for
  `escalate` cases inside a human-set ceiling, never for hard-limit actions (L4,
  permissions/credentials, security, irreversible actions, egress or budget increases,
  autonomy changes), independent of the planner, recorded as model-approved, shadow mode
  before activation, sampled audit and circuit breaker.

Consequences: principle wording updated in `AGENTS.md`, the product-direction README,
the working method and the architecture note. Shadow mode from Phase 7, activation
Phase 8. Design: [SERVER_AUTONOMY_DESIGN.md](../product-direction/SERVER_AUTONOMY_DESIGN.md#model-participation-in-authorization).
