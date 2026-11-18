# Model data-egress gate (P1-M2)

[Issue #94](https://github.com/wanggiya/action-charter/issues/94). The existing shared
model gateway checks the full request against the active provider's effective data
allowance before resolving credentials or opening a completion connection. This
controls model context, not workflow execution authority. [Profiles](MODEL_PROVIDERS.md)
remain the connection configuration; Planner, Critic, Executor and helpers keep their
roles. No new agent, model route, container, Data Card or processing operation is added.

## Classification

| Class | Intended context |
|---|---|
| none | Fixed instructions, public operation contracts, synthetic checks |
| metadata | Names, schema/types and row counts without values/free text |
| data_card | A bounded schema/profile/quality projection without row values; the product Data Card is Phase 2 |
| aggregates | Computed results; this class alone does not establish anonymity or statistical disclosure safety |
| raw | Rows, samples, user/model prose, notes, history and unprojected evidence |

Trusted Python prompt assembly attaches private tags to exact message/schema content
using fingerprints. They are not accepted through JSON, returned in a model prompt,
or derived from a model's self-description. The old serialized context_class field
cannot lower classification. Gateway copying binds the checked content to the sent
snapshot. Changed/appended messages and schemas, missing tags and JSON-round-tripped
requests fall back to raw. The highest class of all parts governs the whole request.
An unchanged copy retains its tags; a correction containing free text remains raw.

All current product request constructors use the classifier. Most real conversations
require raw: prompts mix free user/model text with contextual information. The gate
does not silently strip context, infer safe semantic summaries, or promise that
redacted text is metadata. Only the fixed synthetic compatibility request is none.
The metadata/data_card/aggregates classes support trusted bounded assembly, not an
LLM deciding its own disclosure permissions. Current messages are text; a future
attachment/provider adapter must extend this coverage before sending new payloads.

## Effective policy and compatibility

Local explicit profiles use their saved data_allowed. The implicit local launcher
profile accepts allowlisted MODEL_DATA_ALLOWED (default raw), captured with the other
request settings. Changing process environment later does not change an active
request. Conversation or model text cannot change either policy.

Ordinary non-loopback endpoints are capped at none in this phase, including the
legacy launcher path. Raising a profile's configured allowance does not remove this
cap. Explicit non-loopback connections remain disabled pending M3c qualification;
M2 does not enable sending project data to a cloud model. Labels such as local or
onsite are not verified network isolation.

The existing implicit host.docker.internal runtime bridge retains its machine-local
compatibility scope. Like a loopback relay, it is trusted operator configuration,
not proof about DNS configuration or downstream forwarding. Redirects and ambient
HTTP proxies remain disabled. This application gate is not an OS firewall or an
end-to-end guarantee about what a separately administered relay does with requests.

Requests within the allowance use the existing payload, budgets and output validation.
A rejection has code model_data_class_blocked, no automatic retry, and no credential
resolution or completion HTTP request. It cannot be fixed with authorization text.
Model listing remains a bounded configuration lookup, not a data-bearing generation.

## Evidence and interface

Settings shows the active provider and effective allowance. Request diagnostics
shows provider, highest required class, effective allowance, allowed/blocked decision,
and dispatch state. New fields are optional when reading older records. Prompts,
values, fingerprints, endpoint URLs and credentials are not added to audit records.
An attempted HTTP dispatch does not prove that the service received/completed it.
A started allowed call records unknown dispatch, avoiding a false "not attempted"
claim if the process crashes. Explicitly blocked calls record not_attempted.

Scoped application calls reuse existing request diagnostics storage. Configured
standalone calls reuse that store without inventing a chat/turn. Direct Python
embedders without a workspace root receive a content-free model_egress logging
event and must configure their logging sink. Monitoring storage remains best effort,
reported as incomplete when observable; the gate still blocks even if recording
fails. This adds no new durable ledger or mandatory audit-storage availability rule.

## Manual validation

Keep Allow writes OFF. Use a saved loopback Ollama profile with data_allowed none:

1. Select it explicitly in Settings; confirm Effective data allowance: none.
2. Check compatibility should still pass with its fixed synthetic request.
3. In a new chat send: "Explain what a read-only inspection of sample_orders.csv
   would establish. Propose only inspection, without execution."
4. Expect an allowance rejection. Open View request diagnostics and expand the
   failed model call: required raw, allowance none, decision blocked, Not attempted.
5. Restore the permitted raw local profile. Existing normal planning remains subject
   to its own model/schema validation; M2 does not improve small-model quality.

If the saved-profile editor remains unresponsive, that M1 owner-reported issue is
still unconfirmed. A backend-only check can use the existing local profile: stop the
launcher, run MODEL_DATA_ALLOWED=none bash scripts/start_actioncharter.sh, perform
step 3, then stop it and restart normally to restore the normal environment setting.
This does not edit .env or authorize writes. An exact inspection may use a model-free
path, so use the reasoning request above when testing model egress rejection.

Automated checks cover the full class/allowance matrix for explicit and implicit
profiles, pre-credential refusal, real local HTTP zero-request evidence, changed
messages/schemas, serialized labels, pinning and snapshot races. A synthetic
Planner->Executor->report journey scans artifacts/logs/diagnostics for a fake key.
Verification completed 2026-11-15: all 3,028 collected tests have passing coverage
in three batches. Final completion passed 1,085 tests (237.74 s, 13 existing spatial
warnings); interface validation and strict gates passed. Fixture endpoint corrections
and the nested CLI-selector fix preserve original response/budget/help assertions.
The isolated browser uses actual API/gateway services and a fake HTTP model, with
separate state and browser profile. It checks synthetic success and real planning
rejection without a workflow run. [Current evidence](../context/WORK_RESUME.md).

No real gateway qualification, new local-model performance result or completed
Critic baseline is claimed. M3c, B6 comparison and Phase 1 closeout remain separate.
