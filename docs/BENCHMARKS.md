# Benchmark definitions and evidence

P1-B1, 2026-11-13, [#86](https://github.com/wanggiya/action-charter/issues/86).
B1 contracts/loading and B2/B3 runner/CLI/deterministic checks are implemented.
Tracking: [B2 #87](https://github.com/wanggiya/action-charter/issues/87),
[B3 #88](https://github.com/wanggiya/action-charter/issues/88). Provider profiles,
20–30-task suite and real-model baseline remain future P1 work. [Phase 1 plan](product-direction/PHASE_1_PLAN.md).

## Structure and responsibilities

```text
benchmarks/tasks/<id>/task.yaml + synthetic input/
                    |
        apps/benchmark/loader.py (L6)
                    |
        contracts/benchmark.py (L0)
                    |
        validated definitions + availability + definition SHA-256

Runner -> existing task actions / agent runtime -> observed evidence
                                                     -> deterministic checks
                                                     -> benchmark result
```

Loading neither calls models nor invokes workflows. It reads only the definition;
input and gold-label files are checked with filesystem metadata, not opened. It
does not create workspace records, install dependencies or grant authority.

P1-B2 owns dispatch/result persistence; P1-B3 owns scorer implementations.
Planner continues proposing, Executor continues governed deterministic execution,
and Critic continues assessment. No new role or permission is introduced. Model
provider/gateway changes are P1-M1/M2, not part of this loader.

## Definition format

See the complete synthetic example in
[task.yaml](../benchmarks/tasks/s-csv-profile-001/task.yaml). Each task directory's
name must exactly equal its stable `id`. Required fields:

| Field | Contract |
|---|---|
| `id`, `workload`, `title`, `request` | Stable bounded ID; workload H/E/PA/G/S; nonempty title/request |
| `inputs` | At most 32 unique normalized relative locators |
| `requires_local_data` | Explicit boolean, default false |
| `data_class` | none, metadata, data_card, aggregates or raw; descriptive until M2 enforces egress |
| `expected` | One of the four typed expectations below |
| `limits` | Positive wall-clock seconds, at most 86,400; 0–1,000 model calls; defaults 600/20 |
| `schema_version` | 1.0, defaulted when absent |

Unknown fields reject at every schema level. Validated collections are immutable
tuples. The loader does not execute. The runner admits model calls against the declared
limit and stops the worker process group at the task deadline; setup/scoring are
bounded local work, not a kernel-level wall-time sandbox.

Fixture locators start with `input/` and resolve inside that task directory.
Optional local locators start with `data/input/`, resolve inside the supplied project
root and require `requires_local_data: true`. Missing local data is recorded in
`missing_local_inputs`, with `available: false`; The runner skips it explicitly. Missing
synthetic fixtures or gold labels are definition errors. No missing file is created.

The runner stages fixtures in an isolated project's `data/input/`, maps locators
to supported workflow paths and rejects destination collisions. Task-relative
locators are not direct dispatcher arguments. Local data is not committed, and its
presence here does not authorize reading it through an agent or sending it to a model.

| Expected kind | Typed content | Meaning |
|---|---|---|
| `deterministic` | 1–64 checks: `report_contains_columns`, `value_close`, `row_count`, `file_exists`, `table_exists` | Scorers evaluate actual evidence; check declarations are not Python/SQL callbacks |
| `gold_set` | Required existing `expected/...` label file | Reference scoring is not yet implemented; a run records gold_scorer_unavailable |
| `refusal` | `nothing_executed: true` | A response saying no is insufficient without zero-execution evidence |
| `unsupported` | Bounded `reason_code` | Baseline capability gap; never counted as a passing capability |

`value_close` requires finite expected/tolerance numbers and nonnegative tolerance.
`file_exists` names a normalized `data/output/...` path. `table_exists` names schema
and table identifiers only, not a connection string or SQL. These checks never
approve file/database writes; execution retains the normal exact authorization.

## Read-only validation

From the repository root:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from geoagent_harness.apps.benchmark.loader import load_suite

for item in load_suite(Path('.')):
    print(item.task.id, 'available' if item.available else 'missing local data')
    print('definition SHA-256:', item.task_sha256)
    print('checks:', item.task.expected.kind)
PY
```

Expect the synthetic example to be available. This is validation only, not a
benchmark run; executable CLI usage follows below. No UI step or model
configuration is needed. Definitions are loaded in stable directory-name order.

The loader rejects duplicate YAML keys, aliases, non-string keys, custom unsafe tags,
unsafe paths, symbolic/hard links, non-regular resources and directory/ID mismatches.
It caps each definition at 65,536 bytes, YAML at 4,096 nodes/24 levels, and a suite at
256 tasks/8 MiB of definitions. Empty suites and malformed definitions fail explicitly;
they are not silently skipped or presented as a successful empty benchmark. Error
messages omit raw YAML/request/data values. This is validation under a trusted local
checkout, not a sandbox for executing third-party benchmark code.

## Result contract

`BenchmarkResult` records task/run IDs, the exact definition-byte digest, source Git
revision/dirty flag (null when unavailable in an unversioned install/export), fixture versus real-model evidence, model/profile attribution,
egress class, expected/observed outcome, executed-operation count, check outcomes and
metrics. It contains no arbitrary result payload, transcript, endpoint, credential
or exception-text field. The runner collects/persists observations; none are measured by this schema alone. A caller-constructed record is not independently verified proof.

Metrics include calls, reported prompt/completion tokens, wall time, retries,
timeouts, required approvals, optional process CPU/sampled RSS and optional per-role
calls/tokens/time. Unknown measurements stay null, not invented zeroes. Process
metrics do not measure worker, Ollama or GPU memory. Per-role call counts, if supplied,
must sum to the total; role identifiers must be unique.

Passing analysis requires completed work and nonempty passing checks. Passing
refusal requires observed refusal and exactly zero executed operations; unknown
execution counts cannot pass. Skipped tasks must have zero calls/operations and no
dispatch. Unsupported gaps are explicitly marked, with no executed operations.
Real-model records require a model name. Critic advisory status is separate from
execution and deterministic scores. A run without source-version provenance is not
a reproducible published baseline. None of these fields provides execution
authority or lets a model decide benchmark correctness.

## B1 verification (preceding slice)

Tests use synthetic temporary fixtures only. Focused contract/layer/compatibility
checks: 84 passed; strict layer check has zero debt and compatibility has zero
errors. Full source-only `make test`: **2,878 passed**, 13 existing spatial warnings,
757.41 seconds, with CI/GitHub/frontend-required flags. Final current-example/contract/
context checks: 63 passed (0.50 s); all 369 local documentation links resolve. No owner state/config/private
data was copied. [Handoff and logs](../context/WORK_RESUME.md). No frontend code changed,
so no new browser or interface acceptance journey is required for P1-B1.

The three native Python modules are classified in the existing layer policy. Its
baseline hash is rebound to that policy; no dependency exception was added. R11's
current census becomes 617 modules / 500 native; its original 290 retired and 117
retained public boundaries and historical manifests remain unchanged.

B2/B3 delivery is described below. B4 expands to 20–30 tasks; B5 records a labelled
fixture and actual local-model baseline.
Provider profiles, egress enforcement and comparison remain the other P1 lane.


## Run the benchmark CLI (B2/B3)

Using the existing development installation, from the checkout:

```bash
.venv/bin/geoagent benchmark list --project-root .
.venv/bin/geoagent benchmark run --suite v1 --fixture --project-root .
```

If the console script is unavailable, the identical native entrypoint is:

```bash
.venv/bin/python -m geoagent_harness.apps.cli.main benchmark run --fixture --project-root .
```

The one current synthetic task should pass its column/count checks. JSON output
contains `run_id`, `directory`, evidence kind, status counts and per-task result with
separate `critic` status. This exercises the actual CSV service and governed workflow;
the model reply is a fixed `fixture-plan.json`, independent of expected answers.
Fixture logical model calls/tokens are not measurements of an actual model.

Inspect `summary.json` in the printed directory. For each task, `<id>.json` is its
content-free result and `<id>.inputs.json` binds staged input paths/bytes/hashes.
Raw request, fixed fixture reply, workflow state and source copies stay private under
`tasks/<id>/`; these may contain data and are not public benchmark exports. Do not
commit raw run folders. A started marker survives interrupted runs; previous task
results and raw evidence remain available. Re-running always creates a new run;
there is no automatic resume or write replay.

Use `--task <id>` to select one definition. Only suite `v1` and implicit profile
`local` exist before M1. B4 has not yet supplied the complete 20–30-task suite.

### Local model mode and writes

Omit `--fixture` to use the existing `MODEL_NAME`/`MODEL_BASE_URL` configuration.
Before M2, only loopback endpoints without embedded credentials are admitted; other
providers fail before dispatch. No actual local-model baseline was run in B2/B3.
Automated endpoint checks use a fake local server and are fixture evidence only.

Present local inputs still skip unless `--include-local-data` is explicit. Missing
inputs report `missing_local_data`; present but non-opted-in inputs report
`local_data_not_enabled`. Local-data tasks cannot enable fixture writes. The runner
copies data, never changes the original, and caps inputs at 256 MB per task and
512 MB per run (including retained partial staging). Staging detects changed sources.

Writes remain off unless the operator passes `--allow-fixture-writes`. That flag
permits only the normal exact review/approval/run path for temporary local-file
operations over fixture inputs; YAML/model text cannot enable it. Each run gets fresh
scope/approvals. The worker's admitted operations are the existing local CSV/vector/
raster inspection/conversion and typed table transformations. Database, GeoServer,
installation, shell/code generation and arbitrary execution are not admitted by this
runner. Disposable database dispatch is still a later suite adapter; receipt scoring
below is implemented without touching a live database.

### Budget, interruption and metrics

All injected Planner/helper/recipe/Critic clients share a call budget. Existing
bounded schema corrections are counted, not hidden; the runner adds no retry.
Unknown tokens remain null. Wall time, observed calls by role, reported tokens,
corrections/timeouts, approval count and sampled worker RSS/child CPU are recorded.
CPU intervals can include concurrent children; sampled memory omits peaks between
samples, worker descendants and model/GPU memory. Missing resource measurements are null.

Ctrl+C stops the active worker process group and retains an incomplete summary.
Deadline termination also retains partial files. It may interrupt a fixture write;
unknown execution state is never reported as zero or a successful refusal. This
is a fixed-process boundary over registered operations, not Docker/MicroVM isolation
or a general sandbox for third-party code. Source credentials, proxy variables and
host runtime-root overrides are not inherited. The staged project uses a minimal
context and empty dataset catalog; expected answers/gold labels never enter prompts.

### Deterministic scoring

Only completed/validated operation outcomes are considered. Model prose and Critic
assessment never become scoring facts. Checks have bounded, content-free reasons:

| Check | Evidence required |
|---|---|
| Columns | A unique recorded columns/fields list; optional `step_id` selects an exact operation in a multistep run |
| Row count | One integer at the requested selector; booleans and floats are not counts |
| Numeric tolerance | One finite number within absolute tolerance; no coercion/evaluation |
| File | Safe regular output, matching successful operation receipt path and actual SHA-256 |
| Table | Exact target and passed committed PostgreSQL verification receipt, or passed PostGIS existence receipt; no new connection/query |
| Refusal | Recorded deterministic refusal, zero operations and zero output files; timeout/schema/model failure cannot count as refusal |

Selectors are dictionary/list lookups only. Use `step_2.row_count` to disambiguate
multiple outcomes; missing/ambiguous evidence errors rather than guessing. For
example, a column check can add `step_id: step_2`. Failed checks yield `checks_failed`
even when workflow execution completed. Critic failures are visible separately.
Unsupported declarations remain explicit gaps, excluded from passed counts. CLI exit
0 means no failed/error/timeout result; skipped/unsupported tasks remain visible in
counts and are not proof of capability. Cancelled/incomplete runs exit nonzero.

## B2/B3 verification and next work

Full source-only suite: 2,903 passed, 13 existing spatial warnings, 777.77 seconds.
Subsequent current-source focused gates: **117 passed** (27.79 seconds), including
final diagnostic/budget refinements and explicit step selection. Installed CLI
fixture smoke also passed in a disposable project. The regression
suite snapshot precedes those localized refinements; no new live-model quality,
real data or live database acceptance is claimed. R7's original snapshots remain
byte-identical; only the additive benchmark group is excluded from historical
comparisons. R11 census is now 621 modules/504 native, retaining 290 retired and
117 public boundaries. Strict layer/compatibility checks remain required.

B4 expands the suite and disposable adapters, B5 records real-model baselines;
M1/M2 supplies profiles/egress. Per-role routing, agent-mode redesign, Data Card,
new data operations and learning remain outside this delivery. No frontend changed.
