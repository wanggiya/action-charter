# Data Cards — recorded facts for planning and inspection

P2-D1 [#98](https://github.com/wanggiya/action-charter/issues/98), P2-D2 [#101](https://github.com/wanggiya/action-charter/issues/101).

A Data Card projects facts collected by the existing bounded readers. It does not
scan again, infer domain definitions, authorize execution or install capabilities.
Existing CSV/TSV inspection, table profiling (including qualified XLSX/JSON readers)
and bounded spatial discovery return the same `data-card-v1` contract. CLI and MCP
reuse those services. The result Overview renders it without another network call.

Cards include the normalized input source, recorded full-file or package digest
when available, selection/population scope, counts, field storage/observed types,
candidate roles and available quality/numerical facts. Unknown counts remain null.
Identifiers and age bands do not acquire numerical means merely because they contain
digits. Row counts do not establish a patient/entity grain or clinical meaning.

The projection contains at most 32 fields and 8 KB; omitted-field counts remain
explicit. It excludes preview rows and category examples. Explicit selection/filter
and missing-token parameters can contain user-supplied literals; this is not an
anonymization boundary or permission to lower model data-egress classification.
Metadata missingness keeps its empty-cell/native-null semantics; distinct and numeric
counts retain their recorded missing-token and valid-value policies.

| Scope / identity | Meaning |
|---|---|
| Preliminary sample, digest pending | Existing opt-in discovery read a bounded sample/header; full counts and quality are unknown |
| Complete parsed file | Facts cover the complete bounded parsed source, not preview rows |
| Complete selected table | Facts cover the selected workbook sheet/range or record collection; the digest identifies the original file |
| Filtered rows | Profile counts cover matching rows; source and profile denominators remain separate |
| Spatial driver metadata | Driver dimensions/layers/CRS only; a package hash does not validate pixels or every geometry |
| Recorded read | A digest identifies that version; viewing a saved card does not check current file freshness |

The Planner receives same-turn cards only from existing explicit discovery, matched
to the supplied source paths. Recorded result context carries historical cards with
their recorded-freshness label. Source/worksheet/filter matching requires an
independently obtained digest and exact selection; the helper never reads files.
P2-D2 supplies request-level checks and bounded reuse for supported positive
inspection-planning requests. The existing Inspect-on-send switch must permit new
reads; records/workbooks and analytical selections keep reviewed Execute. No card
is silently certified fresh merely because its filename or timestamps match.

The workflow's original evidence is stored once. A normal/latest run response derives
its card from that evidence; the projection does not rewrite the run, reread inputs
or call a model. Existing interrupted-run reconciliation remains separate and never
restarts an operation. Old results without qualified identity/shape remain readable and may
have no card. Supplied card dictionaries never replace the trusted projection.
Comprehensive profile artifacts also store original evidence without the derived
card; the response adds it afterward so the existing artifact budget is preserved.

```text
Existing explicit reader -> original evidence
                                  |
                         shared pure projection
                                  |
                       typed bounded Data Card
                         /        |         \
                   Planner    CLI / MCP    Overview
```

No new agent role, container, arbitrary tool or operation registry entry is added.
`contracts/data_cards.py` owns L0 types; `data/discovery/cards.py` owns the L2 pure
projection. Existing services/adapters share it. Models still propose and interpret;
policy authorizes, Executor performs operations and Critic assesses recorded evidence.

## Source selection and lifecycle (P2-D2)

```text
Explicit Send / CLI / MCP request
             |
Resolve named input or unique current-workflow input
             |
Read policy + exact selection + reader/runtime contract
             |
Full current file/package digest -> matching cache -> verified reuse
             |                         |
Existing bounded reader on miss        |
             +---------- Data Card + request receipt
                                  |
                      Planner / context disclosure / CLI / MCP
```

The card remains recorded facts; a separate `data-card-use-v1` receipt says what
was checked **at that request**, not that the file stays fresh afterward. States:
`prepared`, `verified_reused`, `historical`, `read_not_permitted`, `review_required`
and `unavailable`. Reuse checks full content/package SHA-256, normalized source,
exact selection/read scope, projection/reader revision and runtime dependency
versions. Size/mtime checks only detect races; they are not proof of unchanged bytes.
Hashing large sources still has I/O cost. Checks describe the observed source at
that request, not an immutable snapshot or a guarantee against later modification.
Execute retains its own source/operation validation. No workflow result is replayed.

The cache is an additive `data_cards_v1` collection in the existing workspace
repository, bounded to256 cards/16KB per entry. Reconstructible cache eviction never
prunes chats, runs, claims or approvals. Conversation IDs isolate chats; explicit
CLI/MCP discovery uses its own scope and cannot populate another chat's memory.
Source-state ownership and egress checks remain unchanged. Cards exclude preview
rows, but user-supplied selection literals are not anonymized. A corrupt entry is a
cache miss; unavailable/unsafe storage cannot certify freshness. New source formats,
reader/projection semantics and dependency changes must update the reader contract.

In the interface, Inspect-on-send ON permits preliminary context for supported
positive inspection-planning requests. The current registry must classify the
inspector as read-only without an approval requirement. A known missing input in a
batch prevents even probing its valid prefix. A unique workflow source can resolve
“Analyze this dataset”; ambiguous/missing sources ask one concrete question; unsafe paths are refused.
Explicit new sources do not inherit a prior worksheet/filter. Workbook/record
sources, typed selections and analytical profiles retain reviewed Execute; vague
filter changes never certify the previous/default population. The Inspector must be
among selected compatible capabilities. Metadata context alone does not authorize
workflow execution. Exact eligible inspection-on-send retains its original rules.

Chat history & context -> Context sent to Planner -> Dataset context shows last-send receipts and bounded
facts, including check time and sample/full-table scope. OFF does not read current
source bytes; any matching retained card is explicitly historical. Opening a chat,
reading a submission, refreshing or expanding the disclosure never scans or calls
a model. Outcome cards remain recorded-result views, not live file monitors.

Explicit CLI/MCP users opt into the same shared lifecycle:

```bash
.venv/bin/geoagent discover-dataset sample_orders.csv --project-root . --card-context
```

Repeat to see `verified_reused`; editing the source yields `prepared` with a new
digest. Default discovery output remains unchanged. `--context-options FILE` accepts
bounded JSON with only `source_options`, `filters`, `missing_values` and requires
`--card-context`; delimiters retain their existing flag. MCP `discover_dataset`
exposes `card_context`, typed `source_options`/filters and missing tokens. Explicit
qualified CSV filters produce population-bound cards; non-CSV filtered context is
refused for reviewed handling rather than borrowing another selection's facts.
No arbitrary pandas kwargs, code, SQL, operation installation or write authority.

### Validate planning context in the interface

1. Open a new chat. In its gear menu, turn **Inspect on send ON**; close the menu.
2. Send: `Inspect sample_orders.csv and suggest a useful next analysis. Prepare only.`
3. Expand **Chat history & context -> Context sent to Planner -> Dataset context**. Expect prepared metadata
   and the correct source/field names. This is preliminary context, so full row
   counts/statistics may remain unknown. No workflow should execute for this broader
   planning request; a proposal or concrete goal question is valid.
4. Send the same message again in this chat. Expect **Reused after full content
   check**, with the same source digest. This skips metadata reconstruction, not
   the full digest check and not the requested Planner response.
5. Refresh or reopen this chat. Its last receipt/time stays; no new check or run is
   triggered. Other chats have separate caches.
6. Turn Inspect-on-send OFF and send that message again. Expect historical facts
   with source-not-checked wording. Do not interpret those as current file facts.
7. For full inspection results, send an ordinary inspection and use Execute as
   required. Outcome remains separate from the planning-context receipt.

Changed-byte, unchanged-size/mtime, worksheet/collection/filter, dependency-contract,
unsafe-path, cache-corruption, external-workspace restart, bounded-eviction and
no-replay checks use temporary fixtures in `tests/test_data_card_lifecycle.py`.
Complete regression/browser evidence is retained in the [D2 validation record](../benchmarks/results/2026-11-19-p2d2-validation.json).

### D2 verification record (2026-11-19)

All **3,200 final-source offline tests passed** through four disjoint `make test`
groups:842/729/841/788 tests, command times225.538/251.616/330.809/396.006s. Groups ran
with isolated fixtures and no exclusions; these durations are per command, not a
summed wall time. Passing IDs exactly match the complete collection (zero missing
or unexpected); all975 Python source/test files match the verified source export.
This is complete batched coverage, not one uninterrupted final-source invocation.
Earlier regression attempts exposed stale batch expectations and prompt overhead;
both were corrected without changing CI exclusions or prompt limits. A separate
interrupted run supplies no completion claim.

`make interface-validate` passed (Vite build7.12s; existing chunk warning). The isolated
actual-API/fake-model browser journey passed preparation, verified reuse, changed
source rebuild, historical-OFF and refresh without new reads/model calls, with zero
page errors or workflow dispatch/authorization. It used a fresh temporary profile,
not a personal browser cache. Strict layers pass633 modules/3175 imports with zero
debt; compatibility remains516 native/117 retained/290 retired. Prior-session browser
temporary logs/screenshots were cleared on reset; their inspected results are
recorded in the conversation, handoff and durable validation summary. No private
diabetes-data test, live database write or production-efficiency result is claimed.

### Bounded real local-model observation

[Capture](../benchmarks/results/2026-11-18-p2d2-context-lifecycle.json): installed
qwen3:4b-instruct, reasoning none,60s/512 output tokens, one model call per condition.
Pre-D2 Python from f237372 and candidate Python used identical current guidance
and the same three-row synthetic CSV/request. Both produced a valid inspection
proposal; neither dispatched a workflow or approved anything. Before23.041s with
2087 input/166 output tokens; after22.693s with2709 input/214 output tokens. Candidate
subsequent context check reused the card without another inspection in0.054s.
One before-then-after observation with uncontrolled load/warmup proves no speed or
reliability improvement. D2 added context/tokens; focused reduction is D3. Final
runtime/source-routing/prompt/read-gate hardening followed the capture and is fixture-tested;
no final-source model repetition is claimed. Reusable bounded harness:
`scripts/data_card_context_evaluation.py`. It does not install/start models or change
owner settings. Earlier D1 observations below remain separate evidence.

## Validate in the interface

1. In your usual launcher terminal run `.venv/bin/geoagent project-identity --project-root .`.
   Current owner status is stable without recovery. If a future device-number
   mismatch blocks status, use the [reviewed recovery guide](PROJECT_IDENTITY.md);
   do not initialize/reset history. Start with `bash scripts/start_actioncharter.sh`
   and refresh. Writes can remain off.
2. In a new chat send `Inspect sample_orders.csv. Return row count and column names. No writes.`
3. Click Execute if inspection-on-send is off. Open Outcome → Overview.
4. Find **Data Card · Recorded inspection**. Expand **Field facts**. Compare source
   rows, field count, missing/distinct values and available numerical summaries
   against Columns and the recorded result. IDs should remain identifier candidates.
5. Expand identity/selection. A completed inspection has a recorded digest; this is
   not a current-file recheck. Close and reopen the chat or historical run: the same
   card should return without another execution. Expanding it makes no analysis call.
6. For an existing comprehensive analytical chat, Outcome → Overview and terminal
   `/overview` show its recorded card. Older stored profiles can omit the UI card;
   a new explicit inspection obtains the current contract without modifying history.

CLI JSON inspection uses the same service:

```bash
.venv/bin/geoagent inspect-csv data/input/sample_orders.csv --project-root .
```

Use the installed CLI's existing help if running from another directory. MCP
`discover_dataset`/`profile_table` return `data_card` through their existing qualified
reader paths; no separate installation is needed. Full-data inference, database
transfer, automatic freshness and efficiency gains are separate acceptance gates.

## Verification record

All3,120 collected offline tests have passing coverage: full source-export run3,114
passed in1209.77s, then80 final affected checks passed22.50s (74 overlaps,0 missing).
The final checks cover narrow legacy/payload/artifact follow-ups; this is not one
uninterrupted final-source invocation. All970 Python source/test files match the
verified export. Interface validation passed12.06s; isolated actual-API/fake-model
browser and CLI/PTY checks passed expansion and refresh/history with no page errors
or authorization calls. Personal browser profiles/caches were not used.
Final context/bounds/redaction checks passed15 tests in0.80s in that isolated copy
with the final documents. Direct checkout checks instead refused the mismatched
ownership marker (6 failed/9 passed); no guard, marker or owner state was changed.

[Real local4B synthetic context observations](../benchmarks/results/2026-11-18-p2d1-card-context.json)
retain a clarification without reader context and a validated inspection proposal
with a preliminary card. No workflow was dispatched. This is not a frozen pre-feature
comparison, statistical reliability result or efficiency win; deterministic follow-ups
were verified afterward. [Current handoff](../context/WORK_RESUME.md).
