# Checkpoint 22G — Intent review and Planner handoff API

## Changes

The operator confirmed a live exact inspect_vector handoff and preserved requires_approval true. These API routes now call the same CLI backend services:

| Route | Action | Effect |
|---|---|---|
| POST /api/v1/intent/inspect | inspect_intent_proposal | Checked proposal/digest/readiness; no model, storage or approval |
| POST /api/v1/intent/review | review_task_intent | Exact resolved intent review evidence only; no model or work approval |
| GET /api/v1/intent/reviews/intent-review.<digest>.json | none | Rechecks record and context; no model or execution |
| POST /api/v1/intent/plan | plan_reviewed_intent | Existing Planner with one exact inspect_vector capability; unsaved plan, no tool execution |

Existing Intent reasoning endpoint remains POST /api/v1/intent/reason. Requests inherit loopback, origin, JSON content type and bounded body checks. Strict actions/fields; review requires exact confirmed digest and reviewer/reason. Unsupported skills or unresolved intent reject with 400; changed digest, duplicate exact review and stale/unavailable context reject with 409. Model transport/config failures return redacted 502. Existing Planner errors retain their structured failure handling. Extra execute/authority fields reject rather than enabling work. Runtime review roots are fixed to the project, not supplied by the caller.

No frontend panel yet and no automatic saving of plans, recipe compilation, execution or task association. Review stores reasoning evidence, not work approval. The initial handoff remains one normalized input under data/input with requested feature count, fields and CRS metadata. Broader capabilities need explicit supported handoff envelopes later. Additional human approval gates remain preserved.

## Validate locally in WSL

```bash
.venv/bin/pytest -q tests/test_interface_api.py tests/test_intent_handoff.py tests/test_intent.py tests/test_intent_review.py tests/test_context_retrieval.py tests/test_context_review.py
make test
```

Stop the old launcher with Ctrl+C so the new routes load. Start in a terminal with the existing model settings:

```bash
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_NAME=qwen3:4b-instruct
export MODEL_TIMEOUT_SECONDS=300
export MODEL_MAX_TOKENS=4096
bash scripts/start_actioncharter.sh
```

No write-tools flag needed. Another terminal, project root:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8765/api/v1/intent/reviews/intent-review.fbdae498300e3e19a829cca934c2cfd83980fdbe4b040159306aa98a5728afb6.json
```

Expect 200, reviewed_intent_only, intent digest 207efbf9186dff1ecb98d99255def61b40708e3abacfbb90a15a9eda9f9f7283, no plan approval/execution. This does not call a model.

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8765/api/v1/intent/plan \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://127.0.0.1:5173' \
  --data '{"action":"plan_reviewed_intent","review_filename":"intent-review.fbdae498300e3e19a829cca934c2cfd83980fdbe4b040159306aa98a5728afb6.json","allowed_skill_ids":["inspect_vector"]}'
```

This calls Ollama/Planner and can take time. Expect 200, planned_not_saved, exact input and one inspect_vector step; model_called true, plan_saved/approval_inferred/execution_performed/tools_called false. Approval true stays true and is reported by additional_human_approval_required; a model proposal with false is also allowed. No dataset is inspected. A stale review requires repeating context/intent reviews; never delete evidence to get past rejection.

Negative capability check (no model call expected):

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8765/api/v1/intent/plan \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://127.0.0.1:5173' \
  --data '{"action":"plan_reviewed_intent","review_filename":"intent-review.fbdae498300e3e19a829cca934c2cfd83980fdbe4b040159306aa98a5728afb6.json","allowed_skill_ids":["convert_vector"]}'
```

Expect 400 unsupported capability, execution_performed false. HTTP tests use temporary fixtures to exercise all four routes, mismatched digest, unresolved proposal, extra authority fields, preserved approval and stale sources before a second model call. Do not mutate real evidence for these tests.

## Optional API proposal inspection/review

If /tmp/actioncharter-intent22e.json remains from the earlier successful generation, inspect it over HTTP without another model call:

```bash
python3 - <<'PYCODE'
import json
from pathlib import Path
proposal=json.loads(Path('/tmp/actioncharter-intent22e.json').read_text())
Path('/tmp/actioncharter-intent-inspect22g.json').write_text(json.dumps({'action':'inspect_intent_proposal','intent':proposal}))
PYCODE
curl -sS http://127.0.0.1:8765/api/v1/intent/inspect \
  -H 'Content-Type: application/json' -H 'Origin: http://127.0.0.1:5173' \
  --data-binary @/tmp/actioncharter-intent-inspect22g.json
```

Review POST body: action review_task_intent, intent the complete validated proposal envelope, confirmed_intent_sha256 the inspected digest, reviewer and reason. It intentionally creates another operator review; this is optional when your existing stored review already passes reopening. CLI equivalents remain available. Review is not a model provenance attestation or proof that natural-language content is correct; human semantic review is still required.

Next: conversation/context UI consuming these services, with graph beside it and advanced evidence details collapsed by default.

22G local validation: all 58 focused Intent/context/API tests and the full Python suite passed (exit 0), plus compilation. Live API/Ollama acceptance remains with the operator. Frontend unchanged.
