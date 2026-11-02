# Checkpoint 21H — selected-skill Planner prompt correction

## Why the rejection repeated

The rejection was a Planner failure before human decision, not the expected Denied test. The backend prompt unconditionally described a PostGIS load/validate/report workflow even for a conversion-only selection. Its hardcoded required-argument table also omitted convert_vector. This was a source of misleading instructions for the local model; policy still correctly blocked the unrelated skill.

## ZIP summary

- Build required-argument instructions from the same selected-skill policy mapping, including conversion path and target_path.
- Include PostGIS/report dependency instructions only when those skills are selected.
- Restrict the prompt schema skill enum to the actual allowlist and include selected approval/validation requirements.
- Add one fresh correction proposal on deterministic policy rejection. Revalidate the corrected proposal against the unchanged schema/policy; stop after the second invalid response. No silent output rewriting, save, approval or execution.
- A successful correction appears in Planner warnings. Transport errors and initial malformed JSON/schema errors do not trigger this policy-only retry.
- 54 focused Planner/context/task tests and Python compilation passed locally. CLI test collection is blocked here by missing click. Full WSL suite and live Ollama validation remain pending. Frontend unchanged.

The schema enum is prompt guidance, not a model-server guarantee. Deterministic validation remains the boundary. One repair can add another model request and its latency. Some local-model requests may still fail safely.

## Validate in WSL

```bash
.venv/bin/pytest -q tests/test_planner_selected_scope.py tests/test_planner_agent.py tests/test_planner_prompt.py tests/test_planner_policy.py tests/test_context_pack.py tests/test_context_pack_bounds.py tests/test_task_history.py tests/test_task_relationships.py
make test
```

Restart both services using your usual launcher and Ollama settings; old processes retain the old prompt code.

In Plan, explicitly select **only convert_vector**, then select sample_points.geojson as input. Enter:

> Create exactly one convert_vector step. Set path to data/input/sample_points.geojson and target_path to data/output/task_reference_demo_02.gpkg. Set requires_approval true and validation_required true. No PostGIS loading, reports or other steps. Plan only.

Expected: a validated one-step conversion proposal, no saved artifact or execution. If correction was needed, inspect the warnings. Check that the returned plan really has the specified skill, arguments and flags before saving; policy does not independently prove full natural-language intent alignment.

Then save, prepare its decision and record **Denied** to complete the previous reference test. That is the expected human denial; a Planner rejection is not equivalent. If the model still proposes a rejected skill twice, the backend must remain blocked; capture the final message and selected skill list. Do not broaden the allowlist to bypass it.

Remaining: recipe/outcome links and context/intent reasoning. Checkpoint 21 is still open.
