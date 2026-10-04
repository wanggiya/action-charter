# Checkpoint 22D — explicit Intent clarification and API

## Changes

- CLI repeatable --clarification supplies up to five explicit user answers, each 1–1000 characters. Answers are redacted and echoed in the proposal response. Each call is stateless: it needs the original current request and all answers to consider. No hidden conversation memory, saved intent, automatic Planner call or tool authority.
- POST /api/v1/intent/reason exposes the same reasoning service under the existing loopback/origin/JSON boundary. Strict fields; stale context returns 409 before model use, invalid proposal/answers return 400, model failures return redacted 502. Existing execution-disabled settings remain effective.
- Prompt emphasizes the current task, missing dataset paths and unknown historical denial reasons; known_inputs is for concrete data inputs, not keywords. This guides the model but does not guarantee semantic correctness. Human review remains required.
- Context is checked before and after inference. Explicit answers cannot revive denied approval.
- No frontend controls yet; API integration enables the coming conversation UI. Reviewed Intent-to-Planner handoff remains future work.

## Validate in WSL

```bash
.venv/bin/pytest -q tests/test_intent.py tests/test_context_retrieval.py tests/test_context_review.py tests/test_interface_api.py
make test
```

Keep the MODEL_BASE_URL/MODEL_NAME/timeout settings used for 22C. Repeat the original call with a concrete answer:

```bash
.venv/bin/geoagent reason-task-intent \
  --review-filename context-review.d51d9312efd83616364b6a7032ef243c0c452b43dbc55ff87aa4ded2a67e03e2.json \
  --request 'Explain the historical denial briefly, then help me inspect a new dataset. Do not reuse the denied approval.' \
  --clarification 'The new input is data/input/sample_points.geojson.' \
  --clarification 'I want feature count, fields and CRS only. Do not write or load anything.' \
  --project-root .
```

Expect proposed_not_saved, both answers echoed, concrete dataset in known_inputs, human_review_required/model_called true and all plan/approval/execution/tool flags false. An intent_proposed result is reasonable with these answers, but clarification_required is allowed when the model identifies a remaining ambiguity. Old denial reason should be unknown because the excerpt contains no reason. Output wording is not a deterministic test. No dataset is inspected by this command.

## API smoke check

Stop any existing launcher with Ctrl+C. Restart so new source/routes load, with the same model settings:

```bash
bash scripts/start_actioncharter.sh
```

In another terminal:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8765/api/v1/intent/reason \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://127.0.0.1:5173' \
  --data '{"action":"reason_task_intent","review_filename":"context-review.d51d9312efd83616364b6a7032ef243c0c452b43dbc55ff87aa4ded2a67e03e2.json","request":"Inspect the new dataset without reusing denied approval.","clarification_answers":["Use data/input/sample_points.geojson.","Return feature count, fields and CRS only; no writes."]}'
```

Expect HTTP_STATUS=200 and the same reasoning-only envelope. This calls Ollama once and may take time. Review stale? Retrieve/review again and substitute the new filename. No --enable-write-tools is needed.

Use automated fixtures to validate stale/invalid rejection; never modify real evidence. The HTTP test verifies success with explicit answers, stale-source rejection without a second model call, and forbidden authority fields. No frontend build needed for this backend-only change. Full suite and live model acceptance should also run in WSL.

Local validation: all 47 tests in Intent, retrieval, review and interface API modules passed; CLI help and Python compilation passed. Live Ollama prompt-quality acceptance remains with the operator.

The full Python test suite also passed locally (exit 0), with existing Rasterio pending-deprecation warnings.
