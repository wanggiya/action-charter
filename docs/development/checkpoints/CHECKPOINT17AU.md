# Checkpoint 17AU — immutable Critic-result recording

Checkpoint 17AU separates model assessment from durable evidence recording.

## Boundary

After reviewing an in-memory Critic assessment, the operator explicitly
confirms its complete SHA-256. The recording request carries the exact result,
stored trace/report names, and reviewed evidence hashes.

Before writing, the service independently rebuilds deterministic evidence and
compares the trace hash, report hash, task, deterministic status, evidence
references, gaps, workflow warnings, human corrections, and result hash. Any
change fails closed.

The existing record builder validates conclusion policy, and existing atomic
storage writes one digest-addressed `CRITIC_RESULT.json` package without
overwriting. Recording calls no model, creates no release, and executes no
tool, recipe, database action, or workflow.

## Interface validation

1. Restart the source-pinned API and open **Assurance**.
2. Run a read-only Critic assessment over stored evidence.
3. Review its summary, basis, risks, and SHA-256.
4. Confirm the immutable-record checkbox.
5. Choose **Record exact Critic result**.
6. Confirm the interface displays `RECORDED · NO RELEASE`, the record path,
   record SHA-256, and `nothing executed`.

Changing the result or evidence digest is rejected. Repeating the same write is
also rejected because Critic packages are immutable and non-overwriting.
