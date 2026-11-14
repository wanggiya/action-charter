# Phase 1 baseline evidence

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
