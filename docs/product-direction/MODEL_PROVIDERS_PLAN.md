# Multiple model sources — how, when and how to verify

Recorded 2026-11-03. **Plan, not implemented.** Decision:
[2026-11-03 model providers](../decisions/2026-11-03-model-providers.md).
Code references are from a scan of `src/geoagent_harness/model/` on 2026-11-03.

## Goal

Work with any model the user is allowed to use, and let **policy**, not the model or
the chat, decide what each model may see.

| Source | Examples | Typical user |
|---|---|---|
| Local | Ollama, llama.cpp, LM Studio on the same machine | Individual, air-gapped laptop |
| On-site / private cloud | vLLM or TGI on site GPUs; a model in the organisation's own cloud tenant | Lab, hospital, company server |
| Organisation AI gateway | LiteLLM proxy, Azure API Management, Kong/other internal gateways | Organisation that routes all AI use through one controlled endpoint |
| Public API | Claude, OpenAI, Gemini, … | Non-sensitive data, or where policy allows |

Default stays **local-first**: a fresh install sends nothing off the machine.

## What exists today

- `model/client.py` calls one **OpenAI-compatible** `/chat/completions` endpoint set by
  `MODEL_BASE_URL` (must end in `/v1`) and `MODEL_NAME`. Works with Ollama, vLLM,
  LM Studio and most gateways **that do not require a key**.
- Structured output via `json_schema`, fallback `json_object` (`MODEL_RESPONSE_FORMAT`),
  reasoning effort, timeout and max-token limits; 401/403/429/5xx/schema-rejection
  errors are classified.
- Per-project model and reasoning preference (`model/catalog.py`); request telemetry and
  diagnostics (`model/telemetry.py`, `model/diagnostics.py`).
- `model/catalog.py` `native_url` lists models through the provider's native API
  (Ollama-style), which other providers do not have.

**Gaps:** no API key or auth header; one endpoint for the whole process; no record of
which provider saw which data; no rule about what data may be sent to a non-local model;
no per-role routing; model listing assumes Ollama.

## Design

### Provider profiles
A provider profile is trusted configuration (file or settings UI, never chat text):

```yaml
id: lab-gateway
kind: gateway                # local | onsite | gateway | public
base_url: https://ai.lab.example/v1
api: openai-compatible       # later: anthropic, others via adapters
credential: secret:lab-gateway-key   # reference only; value from secret store/env
location: organisation       # machine | site | organisation | external
data_allowed: data_card      # none | metadata | data_card | aggregates | raw
models: [qwen3-32b, llama-3.3-70b]
capabilities: auto           # detected: json_schema, tools, context length
limits: { timeout_s: 120, max_tokens: 4096, budget_per_day: optional }
```

### Data-egress classes
Every piece of context sent to a model is tagged by the code that builds it
(`context_pack`, planner prompts, Critic prompts), not by the model:

| Class | Contains |
|---|---|
| `none` | Instructions and operation catalog only |
| `metadata` | File names, column names, types, row counts |
| `data_card` | Data Card: schema, profile statistics, quality flags, **no row values** |
| `aggregates` | Computed results (means, counts, model outputs) |
| `raw` | Row values / samples / free text from data |

The **model gateway** compares the highest class in a request with the profile's
`data_allowed` **before any network call**. If it is higher, the request is refused and
recorded; the user can choose a more permitted profile, never the model.

Local profiles default to `raw`; all non-local profiles default to `none` until the
user or administrator raises them.

### Routing
Each agent role can name a profile and model (e.g. small local model for routing and
Executor checks; larger model for planning). Default: one profile for all roles.

### Audit
Every model call records profile id, kind, location, model, highest data class sent,
tokens, time and cost (if known) in the ledger/telemetry. Credentials never appear in
prompts, logs, diagnostics, exports or evidence.

## Steps and when to do them

| Step | What | When | Why then |
|---|---|---|---|
| **M0 Provider interface** | Move `model/` into `platform/model_gateway/` (RESTRUCTURE R6); define `ModelProvider` interface; current client becomes `openai_compatible` provider; settings come from `platform/settings` (R2) | Phase 0, with R2/R6 | Avoid building on the old location |
| **M1 Profiles + credentials** | Profile file + settings UI; credential by reference from env/secret store; `Authorization` header; replace Ollama-only model listing with `/v1/models` plus optional native listing; capability detection (json_schema → json_object → text) | Start of Phase 1 | The benchmark should compare models and providers from the start |
| **M2 Egress classes + gate** | Tag context parts; enforce `data_allowed` in the gateway before network calls; record class per call; UI shows active provider and allowed class | Phase 1, **before any non-local profile may receive project data** | Hard gate: until M2 passes, non-local profiles are limited to `none` |
| **M3 Per-role routing** | Role → profile/model mapping in agent manifests; per-call budget | Phase 2 (efficiency) | Routing is an efficiency tool; measure it with the benchmark |
| **M4 Other API styles** | Adapters for non-OpenAI-compatible APIs (e.g. Anthropic Messages API) if users need them; many gateways already expose OpenAI-compatible APIs | Phase 6 (interop) | Only when a real user needs it |
| **M5 Server gateway features** | Shared profiles for many users, quotas, per-user audit, admin-managed `data_allowed` | Phase 7 (server profile) | Needs login and admin console |

## How to verify

Label every result **fixture** or **real provider** (provider kind, model, date).

### Automated (in `make test`)
1. **Settings:** valid/invalid profiles; unknown `data_allowed` rejected; profile from
   chat/model text is ignored.
2. **Fake OpenAI-compatible server** (local test server) records each request:
   - auth header present when a credential is set, absent otherwise;
   - payload matches capability (json_schema vs json_object fallback);
   - 401/403/429/5xx/timeout mapped to the existing error codes.
3. **Egress gate:** for each class × `data_allowed` pair, a request above the allowed
   class is refused **and the fake server receives zero requests**.
4. **Secret leakage:** run a full fixture workflow with a known fake key; scan logs,
   telemetry, diagnostics export, evidence JSON and chat history for the key — must be absent.
5. **Audit:** every recorded model call has profile id, model and highest data class.
6. **Routing (M3):** each role calls its configured profile; fallback works when one is down.

### Real-provider checks (manual or scripted, recorded with evidence)
| Check | How | Pass |
|---|---|---|
| Local | Ollama with the current qwen model; one benchmark task | Same result as before M1 |
| On-site style | vLLM (or a second Ollama host) on another machine/port | Same task passes |
| Gateway | Run a **LiteLLM proxy locally** with a key, in front of Ollama | Works with key; fails clearly without key; no key in logs. Tests gateway auth without sending data off the machine |
| Public API | Synthetic data only, `data_allowed: data_card` | Request content inspected through the gateway log contains no row values |
| Network | Local-only profile with outbound network blocked except the model host | No other outbound connections during a full task |

### Benchmark
From Phase 1, run the benchmark for each configured provider/model and record
correctness, model calls, tokens, time and cost. This shows users the trade-off and
shows whether routing (M3) helps.

## Not decided yet
- Which secret store to support first besides environment variables (OS keyring, Vault).
- Whether `aggregates` from small groups count as sensitive (small-cell disclosure);
  likely needs a minimum-group-size rule for health data.
