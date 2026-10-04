# Local model troubleshooting

## Start with the actual API process

A running API keeps the environment it inherited at startup. Exporting MODEL_NAME in another terminal or after launch does not update it. The launcher supplies a default endpoint but does not select a model name. A healthy interface API does not mean the model is configured or reachable.

Stop the combined launcher once with Ctrl+C. In the same WSL terminal, for Windows Ollama reachable via localhost:

```bash
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_NAME=qwen3:4b-instruct
export MODEL_TIMEOUT_SECONDS=300
export MODEL_MAX_TOKENS=4096
bash scripts/start_actioncharter.sh
```

Keep it running. Use a second WSL terminal for diagnosis:

```bash
curl -sS --max-time 5 http://127.0.0.1:8765/api/v1/model-status | python3 -m json.tool
curl -sS --max-time 10 http://127.0.0.1:11434/api/tags | python3 -m json.tool
```

The first checks API-process configuration without calling the model; configured does not mean connected. It shows presence flags and numeric limits, never credentials or endpoint values. The second checks local Ollama connectivity and installed names; confirm your configured name exists. Container-side Ollama may need a different address; localhost is correct only when reachable from the process making the request.

## Frontend

In Task workspace expand Model service and recovery and click Check API model configuration. Missing MODEL_NAME explains a configuration block. After restarting with corrected settings, check again, choose the input and resubmit the task. No automatic reasoning retry or tool execution occurs during diagnosis.

| Failure code | What to check |
|---|---|
| model_name_missing | MODEL_NAME in the launch terminal; restart the API |
| model_endpoint_invalid | Compatible /v1 URL in the API environment |
| model_settings_invalid | Timeout greater than 0 and no more than 600 seconds; token limit 1–32768 |
| model_unavailable | Ollama running and reachable from WSL/container |
| model_timeout | Cold model, competing requests, resource pressure and configured timeout |
| model_http_error | Exact installed model name and compatible endpoint; Ollama logs |
| model_authentication_failed | Endpoint access requirements; current client does not send an API key |
| model_invalid_response | Compatible chat-completion response; service/model logs |

Raw exception text, remote response bodies and credential-bearing addresses are not returned. If the issue remains, share the failure code and API model-status output. Do not share password files or credentials.

## Optional warm-up

This is a model call, not data execution. Only use the known local Ollama endpoint and installed model:

```bash
curl -sS --max-time 120 http://127.0.0.1:11434/api/generate   -H 'Content-Type: application/json'   -d '{"model":"qwen3:4b-instruct","prompt":"Return only {\"status\":\"ok\"}","stream":false}'
```

Warm-up success establishes that this model call worked, not that your real Intent or Planner proposal will pass policy.

## Planner response structure correction

A planner_invalid_schema failure means the model returned JSON with invalid plan fields or types. It does not establish that the user's context is wrong. The Planner prompt includes a concrete single-inspection response shape for the exact reviewed path. It sends selected capabilities/datasets and warnings, not the complete checkpoint history.

JSON, schema and policy failures share one correction budget: at most two model calls. The second response is a fresh complete proposal, validated against schema and policy; reviewed input and output scope are rechecked separately. No invalid JSON is patched into approval or execution authority. Transport failures are not automatically retried. A second failure returns up to six safe field findings without rejected model values.

Validation: run make test and make interface-validate. Restart the combined launcher with the same model environment, reopen the existing reviewed Intent, choose Vector metadata and click Generate inspection plan. No new Intent review is needed for unchanged supported scope. On success inspect the exact path, skill and approval flags; nothing has executed. On failure the blocked card must show field findings and One correction attempted. Share those findings instead of repeatedly changing the reviewed request. A retry can take a second full model timeout. Automated fixture tests do not verify local Ollama quality or browser behavior.

## Confirm the running correction code

After extracting this update, stop and restart the combined launcher. Startup must print Planner contract revision: schema-correction-v52. In a second terminal run:

```bash
curl -sS http://127.0.0.1:8765/api/v1/health | python3 -m json.tool
```

The response must include planner_contract_revision: schema-correction-v52 and planner_correction_limit: 1. Absence means the running API has not loaded this update, even if the source files were replaced. Python imports remain in the running process until restart.

A repeated generation can succeed after a malformed response: JSON mode does not enforce WorkflowPlan, and temperature zero does not guarantee every response meets schema. Do not rebuild context to hide a structure failure. The read-only prompt explicitly distinguishes planning from approval; any extra approval requirement still remains in the accepted plan. No flag is silently removed.

Frontend acceptance: reopen the same reviewed Intent, choose Vector metadata and generate once. Expect exactly one inspect_vector step for the reviewed path, or a blocked card with field findings and the correction-attempt indicator. Saving remains separate from execution. Local Ollama behavior must be tested manually.
