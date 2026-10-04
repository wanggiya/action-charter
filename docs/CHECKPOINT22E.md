# Checkpoint 22E — bounded Intent correction and resolved-intent review

## Summary

Live 22D output redundantly asked for a dataset path that had been supplied. It passed structural checks but was not useful enough to enter planning. When explicit clarification answers exist and a validated proposal still needs clarification, Intent now makes at most one fresh corrective model call. The second proposal must pass the same schema/citation/context checks. It can remain unresolved; status is never silently rewritten. correction_attempted records the extra call. Invalid initial JSON/schema does not trigger this retry. Latency can increase by one model call.

New CLI commands inspect-intent-proposal, review-task-intent and inspect-reviewed-intent check and store a resolved intent only. Storage binds the operator's confirmation to the canonical validated proposal digest (JSON whitespace is irrelevant; missing legacy correction_attempted normalizes to false). Reopening checks content-addressed record bytes and current reviewed context. Writes are atomic, exclusive and mode 600, under ignored reviewed-intents/. Duplicate exact records are not overwritten. Intent review is reasoning-only, not plan/recipe approval. It does not prove the model's statements are true or independently attest model provenance. The operator must inspect the proposal.

This slice adds CLI review only. The existing Intent reasoning API receives the correction behavior, but review API/frontend controls and the actual reviewed Intent-to-Planner handoff remain next. No Planner or executable tool is called by the new review commands.

## Terminal validation

```bash
.venv/bin/pytest -q tests/test_intent.py tests/test_intent_review.py tests/test_context_retrieval.py tests/test_context_review.py tests/test_interface_api.py
make test
```

With your existing Ollama settings, capture a fresh proposal outside the repository. Check the command's exit code before proceeding; shell redirection can leave an empty file if generation fails.

```bash
.venv/bin/geoagent reason-task-intent \
  --review-filename context-review.d51d9312efd83616364b6a7032ef243c0c452b43dbc55ff87aa4ded2a67e03e2.json \
  --request 'Help me inspect a new dataset. Treat the earlier denial as history only, never approval. Its reason is unknown; explaining that reason is not part of this new task.' \
  --clarification 'The input is data/input/sample_points.geojson.' \
  --clarification 'Return feature count, fields and CRS only. No writes or database loading.' \
  --project-root . > /tmp/actioncharter-intent22e.json

echo "Exit code: $?"
.venv/bin/geoagent inspect-intent-proposal /tmp/actioncharter-intent22e.json --project-root .
```

If proposal.status is intent_proposed, inspection returns ready_for_intent_review and review_allowed true with intent_sha256. Review objective, actual input path, requested outputs and no-write constraints, not just the digest. known_inputs should identify the dataset instead of treating output instructions as data. If semantic content is wrong, do not confirm it. If clarification_required persists, review_allowed is false and storage rejects it; provide genuinely needed answers and rerun. Never manually change status merely to pass the gate.

Copy the current intent_sha256 from inspection and explicitly confirm:

```bash
.venv/bin/geoagent review-task-intent /tmp/actioncharter-intent22e.json \
  --confirmed-intent-sha256 PASTE_INTENT_DIGEST \
  --reviewer operator \
  --reason 'Reviewed the exact new read-only inspection intent; no work approved.' \
  --project-root .
```

Expect reviewed_intent_stored, review_performed true, plan_approved/execution_performed/model_called false. Copy its returned review_filename:

```bash
.venv/bin/geoagent inspect-reviewed-intent PASTE_INTENT_REVIEW_FILENAME --project-root .
git status --short --untracked-files=all -- reviewed-intents/
```

Reopen returns reviewed_intent_only; the embedded intent keeps model_called true as the original proposal metadata while the outer review performed no model call. Git should show nothing for reviewed-intents/. The denied task is unchanged. A new event in selected history invalidates the context for reuse; retrieve/review context again, then reason/review intent anew. Do not tamper with real evidence for testing; regression fixtures cover stale context, duplicate storage, changed digest, forged authority fields, invented citations, symlink destinations and record tampering.

No frontend build is needed. Restart an existing launcher if testing changed Intent reasoning through the API. Full suite and live local-model semantic acceptance should also be checked in WSL.

22E local validation: 52 focused Intent/context/API tests and the full Python suite passed (exit 0), along with CLI help and compilation. Live model quality and operator acceptance remain to be checked.
