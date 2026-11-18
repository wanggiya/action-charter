# Phase 1 baseline evidence

## P2-D1 synthetic context observations — 2026-11-18

[Recorded observations](2026-11-18-p2d1-card-context.json) use installed
qwen3:4b-instruct with current code, one call per context, reasoning none,90s/768
tokens. Without discovery context: clarification,23.167s,2081 input/58 output tokens.
With same-turn preliminary Data Card: validated inspect_csv proposal,34.515s,2505
input/214 output tokens. Both actual readers verified3 source rows/3 fields/digest;
no workflow dispatch or authority, owner data/settings, database or dependency change.

This contrasts absent versus fresh reader context, not frozen pre-feature code.
One observation, cache/load/order uncontrolled; no efficiency/reliability improvement
claim. D1 adds source facts; prompt reduction is D3. Wide-card serialization budgeting and malformed-legacy handling
were tightened afterward; duplicate analytical metadata was removed. These follow-ups
are tested deterministically; no final-source model repetition
is claimed. Phase 1 baseline/history below is preserved.

## B6 broader saved-profile comparison — 2026-11-17

[Summary](2026-11-17-b6-broader-matrix.md),
[sanitized reports and comparisons](2026-11-17-b6-broader-matrix.json).
All27 shipped declarations were accounted for on each installed model, sequentially:
54 observations and27 pairs with matching recorded source/settings/inputs. Each
model recorded **4 passed, 7 failed, 10 timed out, 3 skipped, 3 unsupported**; three
pairs passed on both. Same counts do not mean the same tasks/outcomes.

The21 eligible cases per model used synthetic data and normal governed execution;
fresh fixture file outputs were explicitly enabled. Two database cases and optional
owner data were skipped; three declared gaps remained unsupported. No live database,
owner data/configuration, package/model installation or automatic replay was used.
Generation: reasoningnone/120s/1024 tokens, explicit TEMPORARY60s Critic budget,
existing task limits. No fixture tests ran concurrently; source stayed unchanged.
All54 reports are complete records, not claims that all tasks succeeded.

Seven task deadlines retain completed execution with an unfinished Critic call;
other execution/usage unknowns remain unknown. Quality9B rejected after correction
with a response-level field-rule finding; quality4B timed out during planning.
The bounded finding does not identify an exact policy cause. Two provider-unavailable
failures are retained without diagnosing RAM/context overflow from them. A missing
proposal does not establish a verified refusal; conservative refusal scoring remains.
No performance winner: single observations, model order9B then4B, uncontrolled host
load/thermals/cache. Earlier B5 and B6 pilots below remain separate history.

## B6 saved-profile observations — 2026-11-17

[Sanitized capture](2026-11-17-b6-profile-observations.json),
[descriptive-statistics comparison](2026-11-17-b6-h-describe-001.md),
[quality-case comparison](2026-11-17-b6-h-quality-001.md).
Four sequential real local-model runs use TWO shipped synthetic read-only tasks and
explicit temporary saved profiles, uniform120s/1024-token/None generation settings
and60s Critic budget (normal default15 unchanged). No fixture tests overlapped these
observations; model order9B then4B and uncontrolled hardware/cache/load preclude a
performance winner. All four recorded unchanged source and matching pair conditions.

| Task | qwen3.5:9b | qwen3:4b-instruct |
|---|---|---|
| Descriptive statistics | Passed all4 checks; Critic complete;106.94s;2 calls;6561 input/528 output | Passed all4 checks; Critic complete;103.28s;2 calls;6556 input/942 output |
| Quality checks | Plan policy rejected after one correction;70.16s;2 Planner calls;7260 input/379 output; no operation executed | Task deadline during correction;120.07s;2 recorded Planner calls; usage incomplete/unknown and execution observation unknown |

These are scoped functional observations, not the full27-task profile comparison,
repeated performance evidence or real private-data acceptance. Quality failures were
retained without automatic timeout retry or reinterpretation as success. Parent
reports distinguish completed run accounting from successful task outcomes. No write
operations, owner configuration, live database or model installation was enabled.
Broader measurements are now retained above; Phase1 closeout remains separate.
[Commands/limits](../../docs/BENCHMARKS.md).

## B6 failed-first-chat functional follow-up — 2026-11-16

[Sanitized observations](2026-11-16-b6-first-chat.json) retain two separate real
local qwen3.5:9b proposal-only calls using the shipped sample_orders.csv. Corrected
routing supplies inspect_csv and a11,439-byte prompt. Provider-default reasoning
still timed out121.128s; an explicit temporary reasoning-none test passed39.008s
with2,466 reported input/225 output tokens and one inspection proposal. Neither
approved or executed a workflow or changed owner settings. These are functional
observations with uncontrolled cache/load and overlapping fixture tests, not a
controlled B6 speed comparison. [Fix and retest](../../docs/REQUEST_DIAGNOSTICS.md).

## M3c managed local providers — 2026-11-16

[Acceptance manifest](2026-11-16-m3c-acceptance.json) verifies six passing modes
across **two captures with matching runner, worker, controller and runtime-source
hashes**. This is not a claimed single green matrix invocation. Both captures used
fresh synthetic projects, unchanged source during each run and explicit temporary
90-second review budgets. The product default remains15s. Offline fixture regression
overlapped the exercise; timing observations are not B6 performance comparisons.

| Capture | Evidence | Observation |
|---|---|---|
| Real LiteLLM pilot | [Pilot](2026-11-16-m3c-gateway-status-pilot.json) | Correct-key Planner/execution/Critic passed. Initial auth scorer expected401/403 and rejected the native wrong-key400 result; retained as not qualified |
| Managed matrix | [Matrix](2026-11-16-m3c-managed-matrix.json) | Direct, compatible relay, auth relay, isolated worker and real LiteLLM all passed. Initial secondary cache was empty; no operation executed in that mode |
| Explicit corrected-cache secondary run | [Secondary](2026-11-16-m3c-secondary-corrected-cache.json) | Separate owned Windows Ollama0.32.4 passed with qwen3:4b-instruct; cache inventory unchanged and process stopped |

The real gateway is LiteLLM1.109.1 installed in a separate optional environment,
with its dependency lock hash recorded. Missing key401/auth_error and wrong
key400/no_db_connection both produced **zero upstream calls**. The latter passes
only the narrow pinned-managed-gateway check with valid bodies, zero counted dispatch
and successful correct-key connectivity/workflow. Arbitrary400 is not accepted.
Gateway process-group shutdown and private state/log key scanning passed.

Every accepted mode has actual Planner and Critic calls, one executed inspect_csv,
three-row/column deterministic checks and zero data outputs. Gateway workflow:
83.560s; Planner35.145s/3112prompt/215completion and Critic45.619s/1176prompt/
303completion. Secondary workflow42.722s; Planner17.237s/3108prompt/176completion
and Critic21.037s/1171prompt/399completion. Different models/cache conditions are
explicit. Secondary uses the same installed Ollama binary/vendor and existing cached
weights, not vLLM/LM Studio or another physical host. Binary SHA-256 is recorded;
cache inventory binds blob sizes/mtimes and exact manifests rather than rereading
every weight cryptographically. No new model download, owner settings change or live
DB operation was performed. Earlier15s/invalid-advice failures below remain intact.

M3c local qualification is verified within this scope. Public API/data-card redaction,
remote-host/vendor coverage, gateway filesystem/network sandboxing and production
multi-user deployment are not established. B6 controlled comparison remains next.

## M3c local-provider qualification — 2026-11-15

[Protocol and commands](../../docs/MODEL_PROVIDER_QUALIFICATION.md),
[issue #95](https://github.com/wanggiya/action-charter/issues/95).
These are synthetic read-only CSV tasks against **real installed models**. They
are separate from the frozen B5 baseline below and are not a B6 speed comparison.
Times use UTC in JSON; filenames use the owner's local date. Fixture regressions
ran during parts of this development exercise; host load/warmth are uncontrolled.

| Observation | Recorded evidence | Result |
|---|---|---|
| Direct qwen3:4b-instruct, default 15-second Critic | [Initial direct](2026-11-15-m3c-local-4b-15s.json) | Planner 18.60 s, 3,108/180 tokens; correct execution; Critic timeout |
| qwen3.5:9b, compatible and authenticated relays plus network namespace | [Initial paths](2026-11-15-m3c-relays-15s.json) | All three plans/executions passed; no data writes. Auth gate returned 401 for missing/wrong keys with zero upstream calls; missing reference and egress refused pre-send. Critic timed out at 15 s |
| Explicit temporary Critic preference 60 s, qwen3.5:9b | [Follow-up](2026-11-15-m3c-followup-60s.json) | Direct/compatible/authenticated/isolated inspections passed; Critic responses returned but assessments were rejected. No automatic retry/default change |
| Content-free diagnosis, same model and isolated workflow | [Final diagnostic](2026-11-15-m3c-isolated-diagnostics.json) | Planner 45.50 s, 3,112/215 tokens; Critic 49.43 s, 1,164/389 tokens. Assessment schema/status valid; reusable method named three unknown operations, so deterministic validation rejected it |
| Observed-operation response schema, explicit temporary 60 s review | [Contract-fixed follow-up](2026-11-15-m3c-critic-contract-fixed.json) | Isolated workflow and Critic passed. Planner 64.65 s, 3,112/215 tokens; Critic 53.39 s, 1,176/262 tokens; accepted method uses `inspect_csv`. Two model calls, no correction/retry, one operation, no data output files |

In the final run, Ollama was **0.32.4**, Python **3.12.3**, httpx **0.28.1**.
Planner was actually called; expected answers were not supplied to it. Every
executed task inspected the three-row CSV, matched row/column checks and created
zero data outputs. Both network runs had a different namespace, only `lo`, a
successful allowed-model path over the fixed Unix broker and external
`ENETUNREACH`. The broker/model outside the namespace and host filesystem were
not sandboxed by this check. Initial root mapping was replaced with current-user
mapping to preserve the caller UID in the final runner.

The final follow-up constrains the generation schema to successful observed IDs;
the existing final validator remains. Source fingerprint is retained and unchanged
during that run. The explicit 60-second preference lives only in temporary state;
the production default remains 15 seconds. This is one accepted real Critic
assessment, not a general reliability or latency improvement claim.

**Not qualified:** no independent second runtime or
host, no installed/configured LiteLLM gateway, no public API/data-card check. Both
relay endpoints share Ollama; the auth relay is test infrastructure, not LiteLLM.
Explicit nonloopback profiles remain blocked. All reports intentionally retain
`complete: false` because all five real provider modes have not passed. Timeouts
and invalid advice are preserved. Longer time alone did not fix the Critic output;
the evidence-bound schema was verified in the final isolated follow-up.

Runner/worker/task hashes identify development versions where present. The first
captures precede the diagnostic fields; the runner/worker evolved during preparation
of the 60-second follow-up. Only the final isolated diagnostic used the final
instrumented source throughout. Do not infer an unchanged-source comparison across
these captures. The contract-fixed follow-up additionally binds the runtime source
fingerprint and uses the final source throughout. The original B5 baseline is untouched; no learning, performance
improvement, release readiness or model/RAM diagnosis is claimed.

## B5 frozen baseline — 2026-11-13

B5, [#91](https://github.com/wanggiya/action-charter/issues/91). Filenames use the
owner's local date (America/New_York, 2026-11-13); recorded start times use UTC.
These reports contain metadata/checks/metrics only, not private run folders.
[Definitions and scoring limits](../README.md), [runner/report commands](../../docs/BENCHMARKS.md).

## Frozen measurement protocol

- Suite v1, all 27 definitions, fresh project/state and no conversation history.
  Synthetic fixture writes and disposable PostgreSQL/PostGIS explicitly enabled;
  local/private data excluded. Missing local diabetes data and three declared gaps
  are retained in counts and never counted as capability successes.
- Fixed-proposal fixture control runs first. Real model: installed qwen3.5:9b via
  loopback Ollama, 120-second model timeout, 1,024 output tokens, reasoning none,
  JSON schema; task limits remain as declared (120 seconds / 3 calls for added tasks;
  the original CSV task retains its shorter deadline and own call limit). The corrected baseline follows the retained selector pilot; Ollama may already
  have the model loaded. No additional warmup or prompt tuning. Existing bounded schema correction
  is counted. The owner's selected qwen3:4b-instruct and .env were not changed.
- Expected answers/hashes are withheld from model input. Normal typed policy,
  authorization, runtime validation and Critic review still apply. Safety passes
  can come from deterministic rejection before a model call; they do not establish
  that the model itself recognized the attack or invalid request.
- No tests/builds run concurrently with the real-model measurement. Other host/service
  activity is uncontrolled. Wall time is an observation on this machine, not a
  cross-machine performance comparison. No model/GPU RAM or peak-memory claim.
- Public reports retain source revision/dirty state, a runtime source fingerprint,
  task hashes, generation settings and package versions. Pending B4/B5 code is dirty;
  this is a provisional development baseline, not a released revision. The source
  fingerprint covers runtime/fixtures and confirms unchanged bytes across the run;
  UI/CI scripts and final documentation are outside that digest.
- Unknown measurements stay null. Partial reported token sums show coverage; do not
  interpret fixture logical calls as measured model tokens. Critic assessment is
  advisory and separate from deterministic correctness.

## Retained selector pilot

The [initial fixture](2026-11-13-fixture-selector-pilot.json) passed 23 cases. The
[initial real-model pilot](2026-11-13-local-selector-pilot.json) was interrupted after
five recorded tasks: 1 passed, 2 failed, 1 cancelled/error, 1 unsupported. It is
incomplete and is not the final baseline. The conversion completed and validated,
but its check wrongly assumed step_1 rather than selecting convert_vector after
preinspection. The pipeline rejection is retained as a genuine policy failure.
Expected values/tolerances/output hashes, user requests, operation schemas and
generation settings are unchanged; normal architecture context reflects the fix. Selectors now bind operation
identity, not numbering, and still reject ambiguous evidence. Both controls are
rerun on the corrected frozen source; this is an explicit harness correction,
not a hidden model retry. Cancellation retains uncertain state and cleans only
owned temporary targets; no writes/approvals are reused.

## Recorded runs

Fixture control: [JSON](2026-11-13-fixture.json), [Markdown](2026-11-13-fixture.md).
Result: **23 passed, 0 failed/error/timeout, 1 skipped, 3 unsupported**.

Real model: [JSON](2026-11-13-local-qwen3.5-9b.json),
[Markdown](2026-11-13-local-qwen3.5-9b.md).
Result: **8 passed, 11 failed, 0 errors, 4 timeouts, 1 skipped, 3 unsupported**.
The 23 attempted cases are not a representative accuracy estimate; no comparison
against another model/platform or claim of improvement is made. `complete: true`
means the suite finished recording all tasks, not that every task succeeded.

40 recorded model-call attempts, 7 observed schema corrections and 1,564.88 seconds of summed
task time (about 26 minutes). Reported partial sums: 124,317 prompt / 2,643 completion
tokens across 11 tasks with complete usage fields; 23 tasks had calls. Missing usage
is not zero. There are 13 timeout observations including advisory calls, distinct
from four whole-task deadline statuses. CPU totals are unknown because skipped/gap
records have no process measurement; per-task CPU/sampled RSS remain available.

### What the measurement establishes

- Eight cases passed declared deterministic checks: vector attributes, conversion,
  raster/Shapefile/vector inspection, correlation, descriptive statistics and OLS.
- CSV pipeline, quality and column selection failed policy validation; missingness
  and PostgreSQL import/export returned no validated proposal. This is failure of
  the current harness/model interaction, not proof that only the model is at fault.
- Join values/columns and content hash were correct, but the model omitted the
  requested destination: an automatic filename was used instead of joined.csv.
  The required-file check correctly failed.
- PostGIS executed/validated three operations before the deadline interrupted
  Critic review. The task remains timeout with observed_outcome=completed. Grouping,
  data-cell injection and the original CSV case also reached task deadlines; read
  each record's observed_outcome/execution count rather than assuming failed math.
- Five negative requests returned no validated proposal, zero observed operations
  and no output files. They fail the explicit deterministic-refusal protocol; this
  is not evidence that a forbidden action executed. Plain model prose is not scored
  as verified refusal.
- Critic: 9 unavailable, 1 unknown/pending at deadline, 17 not requested; **none
  complete**. Fresh workspace review budget is the existing 15-second default,
  independently limiting review below the 120-second model ceiling. No completed
  real Critic assessment is claimed. Pure execution and whole-task completion are
  separate measurements.

The runtime source fingerprint matches between control/model runs and stayed
unchanged throughout both. Base Git revision is 48cc101832dfc161a714812de1fc65cf92a63378,
with dirty pending B4/B5 source; treat this as a development baseline. Model memory,
GPU peaks, context overflow and host load were not diagnosed by these timeouts.
The baseline exposes reliability and latency limits; do not use it as a readiness
claim for unattended/private-data workflows.

Raw task states for this measurement remain outside source in a private temporary
workspace and may be cleared at reboot; the sanitized exports here are retained.
Ordinary benchmark CLI runs use the configured persistent workspace. Model/service
catalogue metadata identifies the installed tag at preflight; it does not prove
immutable served weights throughout the run. No dependency/image download or live
owner-database operation was performed. Provider comparison and optimization are
later tasks; no learning improvement or mature-platform parity is inferred.

Preflight reference tag: `qwen3.5:9b`; artifact digest: `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`;
size: 6594474711 bytes. Native tool versions at measurement:
- `ogrinfo`: GDAL 3.8.4, released 2024/02/08
- `gdalinfo`: GDAL 3.8.4, released 2024/02/08


## Verification

Full source-only CI/GitHub/frontend-required `make test`: **2,928 passed**,
13 existing spatial warnings, 906.58 seconds. Final report tests: 11 passed;
four-task standalone CI gate: 4 passed/no skips. Strict layer/compatibility,
15 context checks, 400 local documentation links and whitespace checks passed.
Both final exports reproduce from stored records, source bytes match the measured
fingerprint, and public exports omit private fields. All 27 task values/requests
remain unchanged by the selector correction. No fixture containers remain.
[Maintainer handoff and logs](../../context/WORK_RESUME.md).
