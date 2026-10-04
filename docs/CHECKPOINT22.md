# Checkpoint 22 — reviewed context and intent reasoning

Goal: interpret user intent with relevant, reviewed history before the capability Planner proposes executable work. Historic text is evidence-backed context, not instructions or approval authority. The existing plan/recipe/approval/execution boundaries remain in place.

## 22A ZIP summary — explicit context retrieval

- Added retrieve-task-context CLI and read-only POST /api/v1/context/retrieve.
- Search 1–5 explicitly selected histories after full chain verification. Reject missing/invalid sources rather than quietly omitting them.
- Return up to eight excerpts of at most 1,000 characters, original event path/digest, matched terms and source-head snapshots. Keyword overlap is deterministic, not semantic search. Ties use task ID and latest sequence.
- Derived package digest changes when the checked source snapshots change. Query and stored text are redacted. History remains untrusted text.
- Result status retrieved_not_reviewed; no review, model call, inferred approval, artifact write or execution.
- Three focused retrieval tests and Python compilation passed locally. API/CLI/full-suite checks remain for WSL. Frontend unchanged.

## Validate in WSL

```bash
.venv/bin/pytest -q tests/test_context_retrieval.py tests/test_task_history.py tests/test_task_relationships.py tests/test_interface_api.py
make test
```

No model, database write or recipe execution is needed. The fixtures test selected scope, deterministic citations, bounds, no matches, redaction, snapshot changes and tamper rejection.

CLI check with the previously denied task:

```bash
.venv/bin/geoagent retrieve-task-context \
  --query denied \
  --task-id task-63f0cd2f3f3f42ffa42e16a381822d32 \
  --project-root .
```

Restart the usual launcher, then API check:

```bash
curl -sS -X POST http://127.0.0.1:8765/api/v1/context/retrieve \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://localhost:5173' \
  -d '{"action":"retrieve_task_context","query":"denied","task_ids":["task-63f0cd2f3f3f42ffa42e16a381822d32"]}' \
  | .venv/bin/python -m json.tool
```

Expected: status retrieved_not_reviewed; selected_task_ids contains only that task; at least its denial note should match; each excerpt has a source path and sha256. review_performed, approval_inferred, execution_performed and model_called must all be false. CLI/API packages should match while source histories remain unchanged.

Repeat with query unmatchedword to check an empty excerpts list, then with task-missing to check an explicit error (HTTP 400/API or nonzero CLI). Do not tamper real task history; the tests use temporary records.

## Limits and next steps

This is not long-context memory or semantic reasoning yet. It does not automatically select tasks, summarize them through a model, inspect current artifact relationships, save reviewed context or feed history to the Planner. Review/storage must recheck the selected source snapshot and exact digest before a later model consumes it.

Next 22B: exact review and immutable context storage. Then bounded Intent Agent clarification and intent output, validated before any capability Planner handoff. Keep the future conversation/context-plus-graph and Advanced relationship view in the Checkpoint 23 interface direction.

## 22B implemented for validation

Exact context review/storage and stale-source rejection are now available through CLI/API. See `CHECKPOINT22B.md` for commands and tests. No Intent model or frontend panel is implemented yet.


## Checkpoint 22C — Intent reasoning

CLI `reason-task-intent` now consumes a rechecked context review and proposes intent or clarification without creating a plan or granting authority. Context is checked again after inference. See `docs/CHECKPOINT22C.md` for validation. API/UI integration and reviewed Intent-to-Planner handoff remain next.


## Checkpoint 22D — Intent clarification API

Explicit clarification answers are available through `reason-task-intent --clarification` and `POST /api/v1/intent/reason`. Each stateless call checks reviewed history, proposes intent or questions and grants no work authority. Current-task prompt improved after live model feedback. See `docs/CHECKPOINT22D.md`; UI and reviewed Planner handoff follow.


## Checkpoint 22E — resolved Intent review

Intent may make one fresh re-evaluation when supplied answers leave a clarification response. Unresolved output stays blocked. CLI proposal inspection and explicit digest review now store resolved reasoning under ignored `reviewed-intents/`; reopening rechecks sources and record bytes. This grants no work authority. See `docs/CHECKPOINT22E.md`. Actual Planner handoff and review API/UI follow.


## Checkpoint 22F — reviewed Planner handoff

CLI `plan-reviewed-intent` now produces an unsaved plan from a rechecked intent review, initially bounded to one exact `inspect_vector` input and metadata output scope. It rejects broader capabilities and never executes or infers approval. See `docs/CHECKPOINT22F.md`. Review/handoff API, conversation UI and broader supported envelopes follow.


## Checkpoint 22G — Intent review/handoff API

The local API now supports checked proposal inspection, exact resolved-intent review, rechecked reopening and bounded Planner handoff through the same CLI services. No work approval or execution is granted. See `docs/CHECKPOINT22G.md`; conversation UI beside the graph follows.


## Checkpoint 22H — Context & intent interface

The new **Context & intent** panel uses explicitly selected history, checked review storage, structured reasoning and the bounded Planner handoff. It sits beside the graph on wide screens and above it on narrow screens. No plan is saved or executed. See `docs/CHECKPOINT22H.md` for the full frontend test flow. Saved-review recovery and integration with the existing governed run flow follow.
