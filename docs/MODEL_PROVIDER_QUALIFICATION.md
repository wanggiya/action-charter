# Real-provider qualification (P1-M3c)

Tracking: [#95](https://github.com/wanggiya/action-charter/issues/95).
This is an opt-in development check, separate from the B6 provider benchmark.
It reuses the [benchmark worker](BENCHMARKS.md), temporary
[provider profiles](MODEL_PROVIDERS.md) and the [egress gate](MODEL_EGRESS.md).
No new agent, execution permission, product UI or normal-launcher dependency is added.
The optional real gateway has its own pinned environment, described below.

## Run the check

Start Ollama with an installed model available. The application launcher may stay
running; this check does not change its selected model, provider or settings.
From the repository root:

```bash
.venv/bin/python scripts/qualify_model_providers.py \
  --model qwen3.5:9b \
  --output /tmp/actioncharter-provider-qualification.json
```

Choose a new output filename each time; existing results are never overwritten.
Python, httpx and application dependencies come from the existing `.venv`.
Linux `unshare` with unprivileged user/network namespaces is needed only for the
isolated mode. WSL can support it; a denied namespace is an unavailable/failed
check, not evidence of successful isolation. No browser or browser cache is used.

Each mode gets a separate temporary project containing the three-row synthetic
`orders.csv` fixture. The runner saves/selects a temporary profile through shared
services, asks the Planner for an inspection workflow, validates it, executes it
and asks the Critic to assess the recorded result. The deterministic expected
answers are used only by the scorer, not supplied in model prompts. Only
`inspect_csv` is admitted; output writes and databases are disabled. The model
must actually be called for planning; a model-free shortcut cannot qualify.
The shared Critic generation schema now restricts reusable-method operation IDs
to successfully observed steps. Stopped runs permit no reusable method. Final
assessment validation still rejects fabricated operations; no reply is coerced
into a successful review and no execution is repeated to repair advice.
Expected evidence is exactly one completed operation, three rows, the columns
`order_id`, `region`, `amount`, no data output files and no approval requirement.
The run still writes its own history/evidence into temporary state.

| Mode | What it establishes | Limit |
|---|---|---|
| `direct` | Application workflow against the supplied loopback model endpoint | One model/task, not general model quality |
| `compatible-relay` | Same workflow through a second compatible HTTP endpoint | Same Ollama backend; not an independent runtime/second host |
| `authenticated-relay` | Synthetic-key auth gate, correct-key workflow, missing/wrong key rejection, missing reference refusal, leak scan | Test harness; **not LiteLLM qualification** |
| `isolated` | Full workflow in a new user/network namespace, fixed-destination Unix broker to the approved model | Network isolation only; host filesystem remains accessible |
| `gateway` | Actual local LiteLLM, automatically managed or externally supplied | Managed mode requires the optional installation; external process logs need separate inspection |
| `secondary` | A separately operated model server | Managed WSL mode starts an owned Windows Ollama process, reusing installed weights; same vendor, separate process |

For namespace evidence, inspect `network.namespace_changed`, `interfaces` (only
`lo`), `external_network_unreachable`, successful execution and broker request
counts together. A closed port or arbitrary socket error does not pass the probe.
`--map-current-user` preserves the operator UID. The broker accepts only the fixed
chat-completions route, does not follow redirects and cannot act as a generic
HTTP proxy. The parent broker/model remain outside the namespace; their broader
network isolation is **not** established by this test.

## Read the result

```bash
.venv/bin/python -m json.tool /tmp/actioncharter-provider-qualification.json
```

Each mode separates connectivity, validated planning, deterministic execution and
Critic completion. Calls record role, phase, elapsed time and tokens when reported;
missing usage is `null`, never zero. `egress.blocked_before_dispatch` must be true.
Relay rejection tests must show zero upstream calls. A missing credential reference
must block before sending; the HTTP missing/wrong-key checks independently test
the gate. Keys, endpoints, prompts, raw responses and private paths are not exported.
Transient state is scanned for the key and then removed, including on normal error
returns. The child receives an allowlisted environment and temporary HOME/cache,
not inherited owner credentials or workspace-root overrides.

The result includes model/runtime versions when discoverable, runner/worker/task
and managed-controller hashes, gateway dependency-lock hash and explicit budgets. A cancelled process leaves `complete: false`; inspect
the retained file rather than automatically resubmitting. The runner stops its child
on interruption. There is no automatic timeout retry or workflow replay. Planner
schema correction retains the existing maximum of one under the three-call budget.

Exit `0` requires **all six** modes to pass, with managed real-LiteLLM and second-process
provenance. Externally supplied endpoints can pass functional checks but their identity
is not automatically certified. Exit `2` means incomplete qualification,
including an intentionally selected subset, an unavailable real gateway or a Critic
timeout after correct execution. Inspect stages before diagnosing an execution bug.
Other setup failures can return a nonzero process error; never interpret that as a
passed test. Only sanitized results should be retained; do not copy temporary jobs.

The product's default standalone Critic timeout stays 15 seconds. An explicit
follow-up can use its existing project preference in the temporary workspace:

```bash
.venv/bin/python scripts/qualify_model_providers.py \
  --model qwen3.5:9b --critic-timeout 60 \
  --output /tmp/actioncharter-provider-qualification-60s.json
```

Retain the first timeout result. This follow-up is an operator-selected experiment,
not a silent default change, automatic retry or speed comparison. Request timeout
defaults to 120 seconds; each workflow has a 240-second wall limit and at most three
model calls. Output is bounded at 1,536 tokens. No planning timeout is retried.

## An existing real gateway

Use the [official LiteLLM setup guidance](https://docs.litellm.ai/docs/proxy/quick_start)
and a separately reviewed/pinned installation. Bind it locally, configure one
Ollama model alias, disable retries/fallbacks/remote callbacks and supply a test key
through its own configuration. Keep its upstream local. The runner does not install
or modify the gateway or any owner dependency environment. A custom auth relay is
not a substitute for this independently implemented adapter.

With the test key already in an environment variable (never in the command text):

```bash
.venv/bin/python scripts/qualify_model_providers.py \
  --model qwen3.5:9b --critic-timeout 60 \
  --gateway-url http://127.0.0.1:4000/v1 \
  --gateway-model qualification-model \
  --gateway-credential-env QUALIFICATION_GATEWAY_KEY \
  --output /tmp/actioncharter-provider-with-gateway.json
```

The runner's public result omits the key and URL. Gateway-owned logs and downstream
traffic require separate inspection: the application's state scan cannot certify
an external process's log or network policy. Explicit nonloopback profiles remain
blocked. Public API/data-card redaction and a second independent runtime/host have
not been established by the relay checks. The separately owned Ollama process tests
another server process on this laptop; it does not establish vLLM/LM Studio support.

## Optional managed LiteLLM

For Linux x86_64 / Python 3.12, from the source root:

```bash
bash scripts/install_qualification_gateway.sh
.venv/bin/python scripts/qualify_model_providers.py \
  --model qwen3.5:9b --modes gateway --critic-timeout 90 \
  --litellm-python .local/qualification/venv/bin/python \
  --output /tmp/actioncharter-managed-gateway.json
```

The installer uses `uv`, prebuilt wheels and the fully pinned/hash-checked
`requirements/model-qualification.txt` (117 packages). It never installs into
`.venv`; a repeat install reuses the isolated download cache. LiteLLM 1.109.1 includes
the [upstream GHSA-2rwg-2wh4-7c4f patch](https://github.com/BerriAI/litellm/security/advisories/GHSA-2rwg-2wh4-7c4f).
No model or browser download is involved. The measured environment occupies about
658 MiB and its download cache 627 MiB, both beneath ignored `.local/qualification`.
Cache files can be removed independently after installation because packages are
copied into the environment. Removing the optional environment/cache does not
affect normal ActionCharter/Ollama use. Future reinstalls then download them again.
Once populated, `UV_OFFLINE=true bash scripts/install_qualification_gateway.sh`
verifies/reuses the cached installation without network access. The ordinary installer
may refresh PyPI metadata; it reuses cached package wheels.

The runner generates a test key, private configuration/HOME/cache/logs, disables
retries/fallbacks/callbacks and telemetry, and starts one process on an ephemeral
loopback port. A 420-second external watchdog and explicit process-group cleanup
bound its lifetime. Readiness does not call the model. Correct-key generation uses
the existing model gateway and normal deterministic workflow checks. The upstream
broker counts requests; the gateway is stopped before its state/log key scan.
These are local process/environment controls, not a filesystem sandbox or proof
about the gateway's own network traffic.

LiteLLM's database-free master-key configuration returns missing-key **401/auth_error**
but wrong-key **400/no_db_connection**. The negative probes use valid request bodies.
The latter is accepted only for the pinned managed gateway, its exact typed error,
zero counted upstream calls, and a passing correct-key connection/workflow. Arbitrary
HTTP 400 and external gateways do not get this exception. Core authorization and
HTTP error policy are unchanged; no database is added for key management.

## A separate Windows Ollama process from WSL

Supply the installed executable and its actual cached-model directory. Windows
may store models in a custom location: read only its `OLLAMA_MODELS` user setting
in PowerShell, or use the known installation location. An empty default cache is
not evidence that the running server has no models. No pull/install endpoint is used.

Replace these example paths with your own:

```bash
.venv/bin/python scripts/qualify_model_providers.py \
  --model qwen3.5:9b --secondary-model qwen3:4b-instruct \
  --modes secondary --critic-timeout 90 \
  --ollama-executable /mnt/c/Users/YOUR_USER/AppData/Local/Programs/Ollama/ollama.exe \
  --ollama-models /mnt/e/your-existing-model-cache \
  --output /tmp/actioncharter-secondary-model-server.json
```

`qualification_ollama.ps1` starts a separate process with a cleared child environment
and private HOME/temp/AppData. Windows allocates the port: a Linux-free port can
still be reserved on Windows. No cloud/pruning is enabled. Stop commands compare
the captured PID and start time before terminating the owned process tree; a
420-second lifetime also applies. The report records software/binary identity,
no new model downloads and a before/after cache inventory. This checks blob sizes/
mtimes and exact small manifests, not a fresh cryptographic reread of every weight.

For a full matrix, combine both managed configurations and select modes in this
order: `secondary direct compatible-relay authenticated-relay isolated gateway`.
The smaller secondary model is explicit and recorded; model differences mean these
timings are not a provider-speed comparison. Tests run the services sequentially,
without changing the normal launcher's selection or stopping its model server.

## Automated checks

`tests/test_model_qualification.py` uses fake endpoints and fixed proposals only;
it is **fixture evidence**, including its actual governed CSV execution. It checks
the fixed broker route, missing/wrong auth before upstream dispatch, Unix transport,
egress refusal, bounded schema rejection/timeout without retry, clean child
environment, temporary review preferences and refusal of database operation scope.
Existing Critic journey tests verify the evidence-bound schema, independent final
rejection and stopped-run restrictions.
`tests/test_qualification_services.py` uses fake processes/endpoints to check
environment isolation, pinned-version admission, bounded cleanup, Windows metadata
and the narrow typed-error exception. CI does not install LiteLLM or run Windows.
These tests are included in `make test`. Real-model checks remain explicitly opt-in.

Current observations and blockers: [recorded evidence](../benchmarks/results/README.md),
[work resume](../context/WORK_RESUME.md). General per-profile comparison is B6;
M3c does not implement per-role routing (M3), Data Cards or new data processing.

Current [acceptance manifest](../benchmarks/results/2026-11-16-m3c-acceptance.json)
records all six modes passing across two matching-source captures, with failed
attempts retained. Actual LiteLLM and a separate Windows Ollama process are now
qualified for this synthetic local task. Different vendors/remote hosts and public
project-data use remain unqualified. The explicit temporary review budget was90s;
the default15s and earlier failures stay unchanged. Latest automated validation is
recorded in [the handoff](../context/WORK_RESUME.md). The earlier Nov15 full suite
(3,044 cases) and166 final-contract checks remain historical verification evidence;
M3c introduces no frontend change and retains the previous interface validation.

Managed follow-up validation (2026-11-16): source-only CI/GitHub/frontend-required
`make test`: **3,060 passed**,13 existing spatial warnings,1006.40s. Focused service/
provider/egress checks:130 passed10.27s. Final context checks:15 passed0.66s. Strict
layers/compatibility and both repeat/cached-offline installer checks passed. No
frontend code changed in this follow-up; previous interface validation is retained.
