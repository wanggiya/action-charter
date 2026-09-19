# Checkpoint 17AA — plan-decision inspection and verification

Checkpoint 17AA makes the exact approval scope visible before a decision and
independently verifies recorded plan authority afterward.

Before approval, the interface now shows every planned step's purpose,
secret-redacted arguments, `requires_approval`, and `validation_required` values.
The human no longer needs to inspect the stored JSON with `jq` to understand
the scope presented for approval.

Verification is a separate typed action. The server reloads the immutable plan
and approval record, reprepares and compares the exact request digest, reruns
deterministic plan policy, checks the plan digest, decision, expiry, and complete
required-step coverage through the existing approval verifier, and modifies
neither artifact. A denial or expired/incomplete record remains blocked.

No execution preview or Executor action is exposed in this checkpoint.

## Validate

```bash
.venv/bin/pytest -q tests/test_interface_api.py
corepack pnpm@10.17.1 --dir interface build
```

After recording a decision, select **Verify recorded decision**. A valid approval
must show `APPROVAL VERIFIED` and `Nothing executed`.

## Next

Build a non-executing preview of the exact approved Planner execution envelope.
