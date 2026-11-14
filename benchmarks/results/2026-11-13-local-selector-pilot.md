# ActionCharter benchmark baseline

Evidence: **real_model**; complete: **false**.
Run: `78f70bc8cd28493f9683e491a976fa66`.

Counts: passed=1, failed=2, error=1, timeout=0, skipped=0, unsupported=1.

Started: 2026-11-14T02:17:51Z. Python: 3.12.3.
Source SHA-256: `7307a24259a230c97f1f52ef2d64b1cf6a7b7cc7c00496b6d66c58e1fe330a3e`; unchanged during run: **true**.
Model configuration: `{"max_tokens": 1024, "reasoning_effort": "none", "response_format": "json_schema", "timeout_seconds": 120.0}`.
Runtime options: allow_fixture_writes=true, disposable_database=true, include_local_data=false.

Totals: model_calls=7, prompt_tokens=unknown, completion_tokens=unknown, wall_seconds=280.3967721579975, process_cpu_seconds=unknown, retries=1, timeouts=2, approvals_required=2.
Reported usage (partial sums, not inferred totals): `{"completion_tokens": {"reported_sum": 291, "tasks_reported": 1, "tasks_with_calls": 4}, "prompt_tokens": {"reported_sum": 18681, "tasks_reported": 1, "tasks_with_calls": 4}}`.

| Task | Status | Reason | Model | Calls | Seconds | Critic |
|---|---|---|---|---:|---:|---|
| e-attributes-001 | passed | workflow_completed | qwen3.5:9b | 2 | 87.87 | unavailable |
| e-cad-gap-001 | unsupported | declared_capability_gap | qwen3.5:9b | 0 | 0.00 | not_requested |
| e-convert-001 | failed | checks_failed | qwen3.5:9b | 2 | 58.90 | unavailable |
| e-pipeline-001 | failed | planner_policy_rejected | qwen3.5:9b | 2 | 74.42 | not_requested |
| e-postgis-001 | error | cancelled | qwen3.5:9b | 1 | 59.20 | not_requested |

Skipped and unsupported cases are not capability passes. Critic assessment is separate from deterministic scores.
Reported tokens may be unknown; CPU and sampled worker RSS exclude model/GPU memory. Fixture calls are logical calls, not model measurements.
This report omits prompts, data values, endpoint addresses, credentials and private workspace paths.
Source/task hashes identify measured bytes; a dirty checkout is not an immutable released revision. No learning or performance improvement is inferred.
