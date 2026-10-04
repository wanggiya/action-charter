# Checkpoint 22J — checked context and intent recovery

Context & intent now has a collapsible **Resume a saved context or intent review** section. Load saved reviews performs a bounded, read-only inventory. Available reviews have been rechecked against their exact stored bytes and current history sources; stale, damaged or unsafe reviews remain blocked entries. No model, approval or execution authority is invoked by inventory or reopening.

The inventory shows at most 50 reviews, with up to 200 directory entries inspected per review root. Truncation is explicit. The UI can sort the displayed subset newest/oldest or name A–Z/Z–A. Blocked entries have no trusted date or summary. A checked list is a snapshot; reopening rechecks again.

Reopening context restores selected histories, query, reviewer and checked context. Describe a new task next. Reopening intent restores its source context, original request, explicit answers and resolved reviewed proposal; Generate inspection plan becomes available. It does not restore an unsaved plan or execution decision. Previously stored plans remain in the existing Plan → Saved plans flow. No automatic association with a historical denied task is created.

## Terminal validation

```bash
make test
make interface-validate
.venv/bin/geoagent list-reviewed-context --project-root .
```

Expected inventory flags: files_modified=false, model_called=false, approval_inferred=false, execution_performed=false. Your existing source-backed reviews should be available, unless their histories have changed. Empty inventory is valid if no reviews have been stored.

## Frontend validation

1. Stop the old launcher with Ctrl+C and restart with your existing model settings: `bash scripts/start_actioncharter.sh`. Execution authority can remain disabled.
2. If you stored a resolved intent during 22H/22I, refresh the browser. Open Context & intent.
3. Expand **Resume a saved context or intent review**, then click **Load saved reviews**. Expect Context and Intent entries with source status, date and summary. Try all four order selections; they only reorder the displayed inventory.
4. Click **Reopen intent review** on your vector metadata intent. Expect the original request, both answers, input, outputs and constraints to return. The source context is also restored. Expect a message stating no model called, work approved or executed.
5. **Generate inspection plan** should now be enabled. Only click it when ready to make a new Planner model request. Recovery itself has no inference.
6. Refresh again and reopen a **context review**. Its history selection/query return; the new task request and answers are empty. Reason about task stays disabled until you provide a new request.
7. Collapse the recovery section. The normal context/intent controls remain usable. Editing upstream values clears downstream local proposals but does not delete stored evidence.
8. A stale review must show **Reopening blocked** with a disabled button. Do not modify real histories just to trigger this: automated tests cover changed sources, unsafe paths, damaged artifacts and inventory limits.

Recovery replaces current unsaved drafts; the panel states this before selection. History review is never approval. Older reviews may be blocked if their source history changed. This checkpoint does not add durable chat, automatic context selection, or new Intent execution capabilities.
