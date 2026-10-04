# Checkpoint 22B — exact context review and immutable storage

## ZIP summary

- Explicit context review re-retrieves the selected histories and compares the exact package digest. Shared append locks keep source snapshots stable during storage.
- Stores a canonical, content-addressed review record atomically without overwriting an existing record. Reviewer/reason are redacted. Runtime records are ignored under reviewed-contexts/.
- Reopening verifies record bytes and current source snapshots. Stale, tampered, empty and unsafe records cannot enter the future reviewed-context path.
- Added review-task-context and inspect-reviewed-context CLI commands; POST /api/v1/context/review and GET /api/v1/context/reviews/<filename>.
- Six focused retrieval/review tests and Python compilation passed locally. HTTP regression added; full WSL API/CLI checks remain pending. No frontend review panel yet.

Context review is a human confirmation of historical text for reasoning. It does not approve a plan, recipe, tool or execution. Inner context status remains retrieved_not_reviewed because it is the exact original candidate; the outer stored record says reviewed_context_only and review_performed true. Historical text remains untrusted.

## Validate in WSL

```bash
.venv/bin/pytest -q tests/test_context_retrieval.py tests/test_context_review.py tests/test_interface_api.py
make test
```

Retrieve the current candidate again and inspect it before confirming:

```bash
.venv/bin/geoagent retrieve-task-context \
  --query denied \
  --task-id task-63f0cd2f3f3f42ffa42e16a381822d32 \
  --project-root .
```

Copy its current context_sha256. Then explicitly review it:

```bash
.venv/bin/geoagent review-task-context \
  --query denied \
  --task-id task-63f0cd2f3f3f42ffa42e16a381822d32 \
  --confirmed-context-sha256 PASTE_CURRENT_CONTEXT_DIGEST \
  --reviewer operator \
  --reason 'Review denial as historical context only.' \
  --project-root .
```

Expected: reviewed_context_stored, review_performed true, plan_approved false, execution_performed false and model_called false. Copy the returned review_filename and reopen:

```bash
.venv/bin/geoagent inspect-reviewed-context PASTE_REVIEW_FILENAME --project-root .
```

It should show the same candidate plus review metadata. No model, approval or execution is needed. The existing task stays denied.

Restart the launcher to test the corresponding API routes. POST context/review accepts action review_task_context, query, task_ids, confirmed_context_sha256, reviewer and reason. GET context/reviews/<filename> rechecks the record and its sources. Stale review gets HTTP 409; retrieve and review again. The HTTP regression uses temporary source/review files.

Use automated temporary fixtures for changed-source/tamper rejection; do not modify real evidence. A subsequent event in the selected task makes the old review stale, even when the matching excerpt itself is unchanged. Stored reviews remain historical records but cannot be used as current context until reviewed again.

## Next

Bounded Intent Agent reasoning will consume only a rechecked reviewed record and produce structured clarification or intent, never work authority. This ZIP does not yet connect reviewed context to the Planner or add conversation UI. Backend implementation remains the priority.
