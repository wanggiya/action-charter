# Checkpoint 17Y — exact plan-approval preparation

Checkpoint 17Y adds a separate, non-writing approval-preparation action after
reviewed Planner-result storage.

The loopback service accepts only the canonical plan filename and confirmed
plan SHA-256. It reloads the full `PlannerResult` beneath `plans/`, rejects
unsafe paths and symlinks, recomputes the digest, reruns deterministic Planner
policy against the implemented registry, and derives approval-required step IDs
from the plan itself. It returns a canonical approval-request SHA-256.

No approver, reason, decision, expiry, or browser-selected step scope is
accepted. No approval is recorded and nothing is executed. A plan containing
only read operations is reported accurately as `approval_not_required`.

## Validate

```bash
.venv/bin/pytest -q tests/test_interface_api.py
corepack pnpm@10.17.1 --dir interface build
```

For the one-step `inspect_vector` test plan, save the reviewed plan and select
**Prepare approval request**. The expected state is **APPROVAL NOT REQUIRED**,
because that exact plan contains no write step. This is not approval and does
not execute inspection.

## Next

For plans with approval-required steps, add explicit append-only human approve
or deny recording bound to the prepared request digest.
