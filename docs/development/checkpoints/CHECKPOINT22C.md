# Checkpoint 22C — reasoning-only Intent Agent

Interprets the current request using an exact reviewed context record. Returns intent or clarification questions, bounded inputs/outputs/constraints and checked excerpt citations. It does not select tools, create a plan, approve work, save proposals, or execute. Historical text remains untrusted. Source history is rechecked before and after inference. Model output is a proposal requiring human review, not a correctness guarantee.

CLI-only backend slice; API/UI and Intent-to-Planner handoff follow. Uses the existing shared Ollama client, JSON mode and model environment settings. Invalid JSON/schema, unavailable citations, incomplete responses, stale reviews and invalid outer authority metadata fail closed. No silent output repair.

## WSL validation

```bash
.venv/bin/pytest -q tests/test_intent.py tests/test_context_retrieval.py tests/test_context_review.py
make test
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_NAME=qwen3:4b-instruct
export MODEL_TIMEOUT_SECONDS=300
export MODEL_MAX_TOKENS=4096
.venv/bin/geoagent reason-task-intent \
  --review-filename context-review.d51d9312efd83616364b6a7032ef243c0c452b43dbc55ff87aa4ded2a67e03e2.json \
  --request 'Explain the historical denial. I want to inspect a new dataset, but have not selected the file yet. Ask what you need to know. Do not reuse the denied approval.' \
  --project-root .
```

Expected outer status proposed_not_saved, human_review_required true, model_called true, plan_created/approval_inferred/execution_performed/tools_called false. Proposal should ask which dataset (clarification_required); wording may vary. Cite only available excerpt sequences. If the review is stale, repeat retrieval/review first and use the new filename. No write authority flag required. The denied task remains denied.

Automated fake-model tests check valid intent and clarification, forbidden extra authority fields, invented citations, inconsistent status, and stale history before/during inference. Full suite and live Ollama run require WSL verification. Frontend unchanged.
