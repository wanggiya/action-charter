# Focused Planner context and reviewed agent know-how

P2-D3/K, [issue #102](https://github.com/wanggiya/action-charter/issues/102).

The Planner receives a few relevant instruction files alongside existing Data Card
facts and typed operation contracts. Instructions describe methods, question choice
and reporting; deterministic services continue to enforce permission and results.
No new agent, processing operation, general code generator or memory store is added.

```text
Request + bounded Data Card facts + available operations
                         |
Existing schema focus + reviewed instruction selection
                         |
Planner proposes -> existing schema/policy/reuse validation
                         |
Normal reviewed execution -> recorded evidence -> Critic
```

The seed files cover table analysis, health-table analysis, readable reporting,
clear refusals, CSV-to-PostgreSQL and vector-to-PostGIS planning. They do not add new
statistical methods, clinical knowledge or automatic database writes. PostgreSQL
and PostGIS files require their referenced operations in the focused capability
scope; merely mentioning an excluded database does not enable those operations.

Ordinary table inspection-planning requests now omit unrelated transformation
schemas. Matching Data Card kind can help resolve a source-free follow-up. Current
workflow operations, requested transformations and mixed spatial work keep their
broader context. The full operation allowlist remains intact; missing deferred
schemas can still be supplied in the existing bounded correction. This is context
selection, not permission or a replacement for final validation. Existing recipe
discovery, inspected-source provenance and parameter validation remain in place.

For clearly inspection-only table preparation, with no existing non-inspection
workflow to preserve, the reply schema and post-parse/recipe-composition check now
bind the proposal to `inspect_csv`. This prevents an unrequested database reader or
writer from being introduced merely because it is globally registered. Supported
typed analysis remains available. Explicit broader requests and current workflows
containing other operations retain their scope. The interface, interactive CLI and
MCP conversation paths share this check; the standalone legacy Planner keeps its
separate plan-only contract and shared instruction loader.

The validated loader and selector live in one L3 capabilities module. Reviewed
Markdown files contain the know-how. A content pin binds the exact version read;
unlisted project files cannot add instructions, tools or data-egress permission.
Selection is deterministic and makes no additional model call. Existing exact
inspection fast paths remain separate. See [authoring and limits](../agent-skills/README.md).

In chat, expand **Chat history & context → Context sent to Planner** after a broader
planning request. **Agent know-how** shows the selected IDs and versions. Saved
receipts retain digests and omission reasons; refresh displays those recorded facts
without running the loader or model. Files can be omitted when irrelevant, unavailable
or over budget. Standalone Planner proposals retain provenance in generated warnings;
interactive CLI/MCP conversation paths use the same chat receipt as the interface.

To validate manually after restarting the launcher, send:

```text
Profile sample_orders.csv and suggest useful analysis. Prepare only.
```

Expect `table-analysis v1.0.0` in that disclosure after a completed model request,
and a proposed inspection or concrete objective question. No execution is expected
for this broader preparation request. For health guidance, use a supported source
you explicitly choose and state a health-analysis objective; unknown definitions
must remain unknown. This manual check is not the diabetes hero acceptance.

Automated trust, focus, legacy-contract and transport checks use synthetic fixtures.
The bounded local-model comparison changes instruction context and schema focus
together, so it does not isolate each file's benefit. Per-method qualification,
broader model reliability, routing and the real-data hero journey remain separate
Phase 2 gates. Wheel-layout resolution is fixture-tested; an actual wheel/image
build is not claimed when the optional build tooling is unavailable.

## Retained real local-model observations

Installed `qwen3:4b-instruct`, reasoning none, 60 seconds per call, 512 output tokens;
synthetic three-row source, no execution or authority. Eight provider calls across
the initial restricted/automatic captures. Subsequent normal-runtime failures and
the later scope-repair pair are separate observations retained below.

The [initial restricted-scope capture](../benchmarks/results/2026-11-19-focused-planning.json)
used an inspect-only allowlist inherited from the earlier harness. Quality planning
produced valid proposals on both sides, but candidate health advice timed out.
This capture cannot assess schema-focus reduction. The overlapping method guidance
was compacted afterward; the timeout is retained.

The [automatic-selection capture](../benchmarks/results/2026-11-19-focused-planning-automatic.json)
reduced the quality-planning request from eight supplied schemas/32,298 prompt bytes
(7,181 input tokens) to one schema/16,143 bytes (3,582 input tokens). Both versions
requested a correction that the one-call comparison cap blocked. Health advice
returned a clarification before and requested a correction afterward. These are
first-attempt observations, **not completed normal-runtime comparisons**: the actual
Planner permits one correction. No correctness, latency or reliability improvement
is established, and method-quality acceptance remains open. Do not present shorter
failed calls as a performance win. The reusable harness now defaults to the normal
two-call bound for a future explicitly chosen qualification; no such rerun is claimed.

The initial engineering slice supplies usable files, selection and receipts. It does
not complete D3/K's measured-improvement goal or qualify every seed method. The later scope-repair pair below resolves one normal-runtime failure. Continue
representative per-method qualification before expanding this into model routing
or the diabetes hero acceptance.

## Engineering verification

[Durable final-source record](../benchmarks/results/2026-11-19-p2d3-validation.json):
all3,222 collected IDs passed across four disjoint `make test` groups823/812/746/841;
command times334.433/197.590/210.890/252.527s. These are individual command durations,
not summed wall time. Zero missing or unexpected IDs; source, tests and instruction
assets match the verified export. This is complete batched coverage, not a single
uninterrupted invocation. [Initial partial inventory](../benchmarks/results/2026-11-19-p2d3-validation-initial.json)
retains six prompt-bound regressions and two obsolete schema-focus assertions.
Repairs did not raise size limits or introduce test/CI exclusions.

Frontend typecheck/build passed (Vite4.70s, existing chunk warning); the isolated
actual-API/fake-model browser passed specific-method selection display and refresh
with zero new calls/submissions/authorization/execution/page errors. It used fresh
browser state, not personal caches. Strict layers pass634 modules/3178 imports/zero
debt; compatibility is517 native/117 retained/290 retired. Wheel-layout resolution is
fixture-tested; an actual wheel/image build remains unverified. These engineering
checks do not establish model reliability or the diabetes hero acceptance.

## Inspection-scope repair (2026-11-20)

The earlier diagnostic established schema errors, but initially omitted enough detail
to identify the operation mismatch. A private, temporary synthetic-response capture
confirmed that the pre-scope model chose `inspect_postgres_table` with CSV arguments
(`path`, `delimiter`, `preview_rows`, `analysis`). The backend correctly rejected it.
Narrowing descriptive schemas alone had not narrowed the generated operation enum.

[Retained paired observation](../benchmarks/results/2026-11-20-inspection-scope.json):
reconstructed pre-scope native source matches the prior diagnostic SHA exactly.
Both sides used identical common guidance and the same synthetic three-row source,
installed `qwen3:4b-instruct`, reasoning none,60s per call/512 output tokens, at most
one correction. Before: two calls, invalid proposal,92.965s. After: one call, validated
read-only `inspect_csv` proposal,22.572s. Neither dispatched a workflow or recorded
authority. This fixes the demonstrated routing case; one pair does not establish
broad reliability, clinical analysis capability or a statistical speed improvement.
Older failed comparisons and timeouts remain evidence, not superseded successes.

The new scope binding first added redundant prose that exceeded an existing12KB
prompt check. Its removal preserves structured-schema and backend enforcement;
no prompt limit was raised. Regression cases cover both unrelated writers and the
actual wrong database-reader class. [Final-source offline verification](../benchmarks/results/2026-11-20-p2d3-validation.json)
passed all3,224 collected IDs in four disjoint make test groups823/812/748/841;
command times329.039/191.256/226.591/236.838s, not summed wall time. There were no
missing/unexpected cases or source/asset changes during validation. Frontend
validation passed (Vite4.34s, existing chunk warning); fresh-profile actual-API/
fake-model browser verified the valid plan, visible know-how and refresh with
zero new calls/submissions/authorization/execution/page errors. Strict layers and
compatibility remain634 modules/3178 imports/zero debt and517 native/117 retained/
290 retired. Final documentation context/bounds checks are recorded in the same
verification file. An actual wheel/image build and broader model quality remain
unverified.
Private synthetic reply logging is optional developer tooling, creates a new0600
file only under the temporary directory, and is never included in public reports.
