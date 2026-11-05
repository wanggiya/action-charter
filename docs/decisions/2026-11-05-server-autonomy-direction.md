# Server autonomy through registered automations, server first

Date: 2026-11-05. Direction set by the project owner; design only.

Context: the owner's long-term goal is that the platform, running as a backend service,
handles data processing, engineering and administrative work automatically and in real
time as situations change, with minimal human work. Public cloud (AWS) was raised; the
owner chose to consider self-managed servers first.

Decision:
- Long-term goal recorded as: humans out of the loop for routine work, on the loop for
  exceptions; autonomy per task type earned by measured track record. Not "everything,
  no humans": L4 (administration, permissions) stays human; every automation has a named
  human owner.
- Authority for unattended runs comes from **registered automations** approved by a
  human (trigger, operations, targets, autonomy level, budgets, expiry), starting from
  approved recipes. Events and data never grant authority.
- Three-part authorization: run owner/initiator recorded; our policy engine decides
  allow/deny/escalate; a credential broker issues short-lived per-run credentials only
  after "allow"; the agent/model never holds credentials. Infrastructure permissions per
  autonomy level act as a second enforcement layer.
- Server first; cloud later through the same interfaces.

Consequences: Phase 0 gains R12 (actor, run context, idempotency key; policy, credential
broker, queue and clock interfaces with local implementations) and P0-5b (authority,
evidence and ledger stores behind storage contracts with a concurrency contract). Full
design: [SERVER_AUTONOMY_DESIGN.md](../product-direction/SERVER_AUTONOMY_DESIGN.md).
