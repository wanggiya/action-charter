# Any model source, with policy-controlled data egress

Date: 2026-11-03. Decided by the project owner.

Context: users such as labs and companies may use a local model, an on-site or
private-cloud deployment, an organisation AI gateway, or a public API, depending on their
rules. The client today supports one OpenAI-compatible endpoint without authentication.

Decision:
- Support all four sources through **provider profiles** in trusted configuration.
- Each profile has a `data_allowed` class (`none`, `metadata`, `data_card`, `aggregates`,
  `raw`). The model gateway refuses a request carrying a higher class **before any
  network call**. Model output or chat text can never raise it.
- Local-first default: a fresh install sends nothing off the machine; non-local profiles
  start at `none`.
- Credentials are referenced, read from environment/secret store, and never appear in
  prompts, logs, diagnostics, exports or evidence.
- Every model call records provider, model and highest data class sent.
- Per-role routing (different models for different roles) is allowed and benchmarked.

Consequences: implementation steps M0–M5, timing and verification are in
[MODEL_PROVIDERS_PLAN.md](../product-direction/MODEL_PROVIDERS_PLAN.md). Until M2 (egress
gate) passes, non-local profiles are limited to `none`. Positioning: "works with any model
you are allowed to use; local-first by default; outside models only where your policy permits."
