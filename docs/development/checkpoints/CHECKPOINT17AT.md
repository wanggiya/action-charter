# Checkpoint 17AT — explicit read-only Critic assessment

Checkpoint 17AT connects Assurance to the existing Critic Agent without
combining model assessment, evidence recording, and release authority.

## Boundary

The operator selects one stored `WorkflowTrace` and matching report, reviews
its deterministic status, and explicitly confirms the model call. The request
contains both reviewed SHA-256 values. The service rebuilds the evidence pack
and rejects changed evidence before invoking the model.

The existing Critic service remains authoritative for prompt construction,
schema validation, and policy validation. A model cannot change deterministic
status or claim success where deterministic evidence does not support it.

The validated response appears in memory with a prominent `NOT RECORDED`
label. This checkpoint does not create a Critic record or release, execute a
tool, or mutate a database or governed artifact.

## Local validation

Restart the source-pinned API with the configured model environment, start the
Vite interface, open **Assurance**, and select stored evidence in the lower-left
Critic panel. Confirm the exact-evidence checkbox and choose **Run read-only
Critic**. A valid response shows its conclusion, model, summary, digest, and
validation basis while retaining the `NOT RECORDED` boundary.

Changing evidence clears confirmation and the prior result. Stale trace or
report digests are rejected before a model call. Model, JSON, schema, or policy
failures remain visible errors and create no record.
