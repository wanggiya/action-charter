# Checkpoint 22F — reviewed Intent to exact read-only Planner handoff

## Summary

The operator confirmed a resolved reviewed intent for metadata inspection of data/input/sample_points.geojson, including permission to read memory and no persistent writes/database loading. New plan-reviewed-intent CLI rechecks that immutable review and its context, invokes the existing capability Planner with an explicit inspect_vector allowlist, then deterministically checks the returned plan. Exactly one step, exact reviewed input argument, and no validation-required flag. A conservative approval-required flag is accepted and preserved; it never implies approval. The result remains planned_not_saved with no tools/execution/approval authority. It is not saved or assigned to a task automatically.

Initial supported envelope is deliberately small: one normalized project-relative input under data/input and requested outputs from feature count, fields and CRS. Other skills, multiple inputs, other outputs, extra arguments, changed target, extra steps or stale sources are rejected. This is an implemented vertical slice, not a claim that arbitrary natural-language constraints are verified. Read-only inspection capability prevents write steps; operator still reviews model text and any future plan before execution. Data is not opened or inspected by this command.

The handoff calls the existing Planner service and its schema/policy checks; the Planner can use its existing single policy-correction attempt. Reviewed Intent/history does not bypass allowlists, approve work or revive a denied decision. Recheck after inference rejects changed context/intent. CLI only in this slice; review/handoff API and conversation frontend are next. Broader write workflows need their own supported handoff envelopes and existing exact approval flow.

## WSL validation

```bash
.venv/bin/pytest -q tests/test_intent_handoff.py tests/test_intent.py tests/test_intent_review.py tests/test_context_retrieval.py tests/test_context_review.py tests/test_interface_api.py
make test
```

Locate the filename for the exact intent digest you confirmed. This reads records only:

```bash
python3 - <<'PYCODE'
import json
from pathlib import Path
for path in sorted(Path('reviewed-intents').glob('intent-review.*.json')):
    record = json.loads(path.read_text())
    if record.get('intent_sha256') == '207efbf9186dff1ecb98d99255def61b40708e3abacfbb90a15a9eda9f9f7283':
        print(path.name)
PYCODE
```

Use the printed bare filename (not a relative path) below, with the existing model environment settings:

```bash
.venv/bin/geoagent plan-reviewed-intent PASTE_INTENT_REVIEW_FILENAME \
  --allowed-skill inspect_vector \
  --project-root .
```

Expected outer status planned_not_saved, reviewed_intent_rechecked true, model_called true, plan_saved/approval_inferred/execution_performed/tools_called false. Inside planner_result.plan.steps: exactly step_1, skill inspect_vector, arguments path data/input/sample_points.geojson, validation_required false. requires_approval may be false, or true when the Planner adds a conservative human gate; the original value stays in the plan. additional_human_approval_required and warnings report that gate. False validation_required means this inspection step has no separate post-write verifier, not that the generated plan skipped schema/policy validation. Context/intent digest should match the reviewed record. It still does not execute the inspection.

A genuinely unavailable or stale review rejects before the model call. If source history changed, repeat context retrieval/review and intent reasoning/review before using a new record. If the Planner proposes the wrong scope, it is rejected instead of repaired into authority. Share the rejection message if a live model fails this acceptance.

Negative check using the same existing filename:

```bash
.venv/bin/geoagent plan-reviewed-intent PASTE_INTENT_REVIEW_FILENAME \
  --allowed-skill convert_vector \
  --project-root .
echo "Exit code: $?"
```

Expected unsupported capability rejection, exit 2, no model or execution. Automated fixtures also cover changed path, extra steps and sources changing during planning; do not change real evidence to test those cases.

22F local validation: all 55 focused tests and the full Python suite passed (exit 0), plus CLI help and compilation. Live Ollama handoff acceptance remains with the operator.

## Live rejection diagnostics (v35)

The operator received a generic exact-scope mismatch. The rejected plan was not returned, so its cause is not yet known. Diagnostics now name step count, wrong argument/skill, requires_approval or validation_required mismatch. Received arguments are credential-redacted and bounded; arbitrary full model output is not printed. Scope checks remain unchanged. Reapply this ZIP and rerun the same plan-reviewed-intent command, then inspect the detailed rejection. No need to recreate the valid context or intent review. A later plan may differ because the model is called anew; diagnostics describe that new response, not the previously rejected response.

v35 verification: all four focused handoff tests and Python compilation passed. Full suite was not repeated for this diagnostic-only change.

## Conservative approval gate correction (v36)

The live model returned requires_approval true on the exact read-only step. The former handoff incorrectly treated that additional restriction as broader authority. It now accepts and preserves true, reports additional_human_approval_required true with a warning, and leaves plan_saved/approval_inferred/execution_performed false. It does not rewrite the model's gate to false. Existing approval requirements apply if the plan is later saved or executed. Wrong paths, extra steps, different skills and unsupported validation requirements remain rejected. No new Planner call or prompt retry was added by this correction.

Rerun the same plan-reviewed-intent command after applying this ZIP; keep the existing review filename. The new model response can differ. An exact plan with either approval flag is accepted, and a true flag stays explicit in the output. Twenty focused Intent/context tests passed locally, including five handoff tests. Compilation passed. Full suite was not repeated for this narrow correction.
