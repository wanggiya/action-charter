# Checkpoint 17X — reviewed Planner-result storage

Checkpoint 17X adds the first persistent step after the live Planner workspace.
The operator reviews the exact validated plan, its ordered steps, arguments,
approval requirements and canonical SHA-256 before selecting **Save reviewed
plan**.

## Authority boundary

The save endpoint accepts the exact typed `PlannerResult`, the explicit
registry-backed skill selection and the confirmed plan digest. The server:

1. validates the complete Planner-result schema;
2. verifies every selected skill is still implemented;
3. reruns deterministic Planner policy using only the selected skills;
4. recomputes and compares the canonical plan SHA-256; and
5. creates one non-overwriting JSON artifact beneath `plans/`.

The stored file is the same full `PlannerResult` accepted by the existing CLI
approval loader. It can therefore enter the later plan-approval path without a
parallel interface-only format.

The endpoint rejects digest drift, overwrite attempts and symlinked plan roots.
It does not record an approval, invoke a skill, call the Executor, or execute
anything.

## Validate

```bash
.venv/bin/pytest -q tests/test_interface_api.py
corepack pnpm@10.17.1 --dir interface build
```

For a manual browser check, generate a one-step plan, review the displayed
SHA-256, select the review confirmation, and save it. Confirm that the large
result state changes to `STORED · NOT APPROVED` and that exactly one
`plans/planner-plan.<sha256>.json` file exists. A second save of the same plan
must be rejected rather than overwrite the artifact.

## Next

Add a distinct plan-approval request and decision flow bound to this immutable
Planner result. Approval and execution must remain separate actions.
