# Shared evidence collection and Critic record storage

R6b evidence/storage slice, [issue #72](https://github.com/wanggiya/action-charter/issues/72),
2026-11-06. This evidence/storage slice is complete and verified. Subsequent native
moves and broader policy/ledger ownership are implemented in
[R6 completion](R6_COMPLETION_AND_ACCEPTANCE.md); Phase 0 remains open. Paths/counts
below describe this earlier slice, with historical imports supported.

## Responsibilities

| Owner | Responsibility | Legacy path |
|---|---|---|
| `platform/evidence.py` | Read bounded trace/report artifacts, check schema and status consistency, redact context and construct evidence references | `critic.evidence` aliases the exact module |
| `storage/critic_records.py` | Construct the existing Critic record and canonical result digest | `critic.records` aliases the exact module |
| `storage/critic_record_storage.py` | Persist/load the existing canonical digest-addressed record package | `critic.record_storage` aliases the exact module |
| `critic/agent.py` and `critic/service.py` | Request and constrain the model's interpretation of the evidence | Existing role entry points remain |

History observers and release assessment now use the shared services directly rather
than importing Critic behavior. Eight native caller files use the new owners, including
the Critic compatibility exports, API and lazy CLI action catalog. Legacy modules share
function, exception and module identity; there is no second implementation. Native
caller imports were updated during development, not by a runtime agent rewriting code.

The separation is:

```text
recorded trace + report
          |
          v
deterministic evidence collection ---> history / release consistency checks
          |
          v
Critic model interpretation
          |
          v
validated assessment ---> canonical record construction ---> immutable package storage
```

An observed row count and a statement that a transformation is appropriate are
different claims. The collector checks recorded observations and consistency; the
Critic interprets their support and limitations. Neither a digest nor an LLM opinion
independently proves scientific correctness. Existing operation validators establish
their own checks; this move adds no new validation method.

## Preserved contracts and boundaries

- Evidence collection makes no model call and does not modify its trace/report inputs.
  Existing approved-root, suffix, size, UTF-8, schema, status-consistency, redaction,
  excerpt and missing-evidence behavior stays intact. Recorded references retain their
  original path/digest semantics; this is not a new immutable-source snapshot mechanism.
- Record construction retains task/status/conclusion consistency, aware timestamps,
  secret rejection and false authority flags. A Critic assessment cannot change
  deterministic outcome status, approve execution or confer database access.
- Storage retains canonical JSON bytes, file/directory names, result/package digests,
  root/path checks, staged persistence, duplicate rejection and load-time verification.
  Existing packages remain readable; no migration or new database is introduced.
- Old direct-module patches see the actual shared owner. One CLI fixture's storage
  mock now targets that owner; the existing failure/exit-code assertions are unchanged.
  The Critic role's public exports remain available.
- Fresh shared-service and operational-history imports do not load agent roles,
  model clients, application transports or scientific data runtimes.
- The static layer checker rejects new/increased dependencies and requires removed
  debt to leave the baseline. Runtime authority remains enforced by the existing
  policy/execution services; the development checker supplies no permission.

The evidence collector and record builder are complete unchanged source copies.
Record-storage definitions and six caller control-flow ASTs are unchanged apart from
imports. All 12 public schemas match the pre-change snapshot. Dependency debt shrinks
**35 -> 33 pairs and occurrences**, removing observer -> Critic evidence and release
assessment -> Critic dependencies. Layer classifications are unchanged. The graph has
450 modules, 43 visible compatibility aliases and one unchanged dynamic-import review.

## Verification and remaining work

The initial 45 existing checks passed. Final focused checks: **120 passed (7.30 s)**,
including 18 new cases for compatibility, shared callers, clean imports, unsafe/missing
evidence, shared limits, redaction, unchanged source bytes, model-status override
rejection, canonical/immutable packages and task/status/secret guards.

Frontend validation passed (5.86 s build, existing bundle-size warning). The isolated
relocated browser/API/CLI/PTY journey passed with zero page errors, including saved-run
restoration, results/statistics, JSON/XLSX/PDF paths and one authorized temporary write.
Documentation audit: 481 local links (161 fragments) across 27 changed Markdown files;
roadmap 15,890 bytes, below its 64 KB target. Working-method changes are Status-only.
Final full `make test`: **2,644 passed**, 13 existing spatial warnings,
**724.88 s (12:04)**. Source was frozen throughout that run. Normal layer and
whitespace checks pass; strict mode correctly rejects remaining debt. These fixtures
are not real-local-model or live-database acceptance. The owner's
manual write check remains pending. No real records, secrets or live services changed.

This completes only the evidence/storage responsibility within R6b. Approval policy,
fresh registry/version checks and recipe-ledger ownership remain for a separately
traced bounded part. It does not implement the P0-5b append-only/concurrency interfaces,
finish the remaining 33 dependencies or remove compatibility paths. See the
[R6 checklist](product-direction/RESTRUCTURE_PLAN.md#r6-reviewable-slices).

For a later manual smoke check, restart the usual launcher with its existing options.
Send `Run a new read-only inspection of sample_orders.csv`, check Outcome, and reopen
the same saved run through workflow history and `./actioncharter`. Results should
remain available without regeneration or execution. If optional Critic review is
unavailable, its status must remain separate from successful execution. This check
does not exercise every record/release path; the automated fixture cases cover those.
