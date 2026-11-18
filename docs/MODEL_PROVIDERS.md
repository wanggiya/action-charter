# Model-provider profiles (P1-M1)

[Task #93](https://github.com/wanggiya/action-charter/issues/93). M1 implements
profiles/credential references over the existing gateway. [M2 context policy](MODEL_EGRESS.md)
now checks classified requests; M3c provider qualification and B6 profile benchmarks
remain separate work. No new
agent roles, model installation or execution permission is introduced.

## Use Settings

Start the existing launcher, open Settings, then scroll to **Model service**.
The **local** profile preserves MODEL_NAME/MODEL_BASE_URL and the existing project
model/reasoning preferences. Listing models and changing selection generate no text.

The built-in option is labelled **local · launcher settings**. Compatibility checks
currently require a saved explicit profile; the disabled button explains this.
Different profiles may share the same Ollama endpoint. Use distinct lowercase IDs
such as ollama-test; local is reserved. Changing only the model does not create a
profile. Save shows missing-ID/endpoint hints and reports errors inside its editor.

1. Expand **Add or replace a provider**. Enter a unique ID, compatible endpoint
   ending in /v1, optional default model, listing method and credential reference.
2. Save, choose the profile and press **Use provider**. Model discovery uses the
   compatible /v1/models endpoint, or optional Ollama /api/tags and /api/ps listing.
3. Select a listed model and press **Use selected model**. Changes apply to new
   requests; an active request keeps its captured configuration.
4. **Check compatibility** sends only a fixed synthetic JSON request. The model attempts share
   the configured timeout budget capped at 120 seconds, at most three format
   attempts and at most 64 output tokens per attempt (or a lower profile limit).

Auto format starts with json_schema. Only the explicit synthetic check may try
json_object then text, and only after the service explicitly rejects the previous
format. Authentication, timeout, malformed reply and 5xx errors stop the check.
Ordinary user requests never automatically downgrade or retry. Text-mode replies
still pass the same deterministic plan/result validation. A successful tiny check
is not proof that the model can complete arbitrary workflow schemas.

The finding is bound to the profile configuration and exact model. Editing the
profile clears its finding; switching models does not reuse another model's finding.
Concurrent changes fail with a refresh/stale result, preserving newer configuration.

## Locality and data limits

New explicit profiles are blocked before credential resolution/network access
unless their endpoint is localhost or a loopback IP. Saving a future external
profile does not enable it, and selecting it is rejected pending M3c qualification.
The implicit legacy path now passes the same M2 gate. Loopback and the existing
implicit host.docker.internal runtime bridge retain raw compatibility by default;
MODEL_DATA_ALLOWED can restrict this path. Other nonloopback generation is capped
at none during this phase.
Do not interpret a profile's kind/location label as verified network isolation.

M2 uses private content-bound context tags for implicit and explicit requests.
Unclassified/changed parts and free user/model text count as raw. The fixed synthetic
check is none. Lower allowances block ordinary planning rather than silently
removing context. The gateway records highest/effective class and decision in
content-free diagnostics; [coverage, uncertainty and limits](MODEL_EGRESS.md) apply.
No model/conversation text can edit profiles, lower classification or grant authority.

## Credentials and storage

Only references are accepted:

- env:MODEL_GATEWAY_KEY reads the API/CLI process environment at send time.
- secret:model-key reads the bounded regular project .secrets/model-key file;
  links, hard links, missing/empty/oversized/non-header-safe values are rejected.

There is no key-value field in Settings or the profile contract. Unknown fields,
embedded URL credentials, query/fragment parameters and invalid configuration are
rejected. Values are attached privately as Bearer headers; redirects and ambient
HTTP proxy settings are disabled. Secret-reflection responses are rejected before
returning model content/model names. Error responses and diagnostics omit raw
service bodies, credential values and endpoint URLs.

Environment references must exist in the process that runs the API. Exporting a
variable in another terminal cannot change an already-running API environment.
A profile switch itself needs no launcher restart; adding a new environment
credential to an existing API process does. Secret files are read at send time.
M1 never edits owner secrets, pulls models or starts a proxy.

Profiles, selected profile/model and successful capability findings live in the
configured workspace's model-providers.json, outside source. Reads do not create
configuration. Writes use existing bounded atomic JSON storage and serialize
revision checks under the metadata write transaction. A crash after replacement
can leave the new revision even if the caller saw an error: refresh, never replay
blindly. Invalid files fail closed and require owner repair/backup restoration.
The JSON format reuses repository storage; the earlier YAML example was illustrative.

## CLI and HTTP parity

[Example profile](../examples/model-providers/local-proxy.json) contains a reference,
not a key, and does not install a gateway. From a development checkout:

```bash
.venv/bin/geoagent models profiles --project-root .
.venv/bin/geoagent models save examples/model-providers/local-proxy.json --expected-revision 0 --project-root .
.venv/bin/geoagent models use local-proxy --expected-revision 1 --project-root .
.venv/bin/geoagent models list --project-root .
```

Use the returned revisions, not those illustrative numbers, for later updates.
`models select MODEL --expected-revision N` selects an available model;
`models check PROFILE MODEL --expected-revision N` performs the synthetic check.
The existing benchmark --profile local remains the implicit environment profile
and ignores saved provider selection until B6 adds explicit profile benchmarking.

HTTP uses the same task actions: GET /api/v1/providers, POST /providers/save,
/providers/select and /providers/check, plus existing /api/v1/models selection.
All paths are under /api/v1; existing origin checks remain. API/CLI results return
configuration summaries, no credentials or workflow authority.

## Verification and limits

Fake-server tests cover authentication, missing credentials, invalid profiles,
secret reflection, redirects, synthetic format negotiation, no generation retry,
request pinning, revision races and HTTP/CLI parity. The isolated browser journey
uses the real API, a fake model endpoint, a temporary workspace and ephemeral browser
profile. It verifies save/select/check/reload/CLI and return to legacy configuration,
with two synthetic calls, no workflow actions, no page errors or secret leakage.
The follow-up browser also checks two profiles sharing one endpoint, missing-field
and reserved-ID feedback, an inline save conflict and pending-provider explanations.
The owner-reported unresponsive Save action remains unconfirmed; a duplicate
Ollama endpoint is not a configured rejection condition. Follow-up targeted tests:
44 passed (2.48 s), with frontend validation and the isolated browser also passing.
No owner browser profile/cache, model selection or workspace state is modified.

Real Ollama smoke, qwen3.5:9b, synthetic JSON only: an initial 15-second environment
probe timed out before any profile call. The explicit follow-up used a 120-second
ceiling: legacy environment path returned valid JSON in 29.478 s; a temporary profile
returned the same JSON in 2.823 s. Both reported 29 prompt / 6 completion tokens.
The second call may be warm: this proves connection compatibility, not speed gains,
a full workflow or a completed Critic review. Bearer authentication and format
fallback were exercised against fake servers, not a qualified live LiteLLM service.
M3c owns broader real-provider validation. The B5 baseline remains unchanged.

The original M1 verification covered all 2,959 collected tests across the initial full regression
and corrected-native-guard completion batches; interface typecheck/build and strict
layer/compatibility gates passed. Exact batch accounting and logs are recorded in
[work resume](../context/WORK_RESUME.md). Provider profiles do not make the current
planning failures or 15-second standalone Critic limit disappear; those budgets
and agent responsibilities remain unchanged.

Protocol references: [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility),
[compatible model listing](https://developers.openai.com/api/reference/resources/models/methods/list).
