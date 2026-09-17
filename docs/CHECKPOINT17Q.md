# Checkpoint 17Q — append-only recipe approval decision

Checkpoint 17Q records one explicit human approve or deny decision for the
exact request prepared in 17P. Recording creates approval evidence only; it
cannot execute the recipe.

## Interface behavior

Preparing a request opens a distinct **Human decision** drawer while preserving
the highlighted request and its digests. The operator provides:

- decision: approve the exact steps or deny the request;
- approver name or role;
- required reason;
- optional expiration from 1 to 1440 minutes;
- explicit confirmation that the decision applies to the displayed request
  digest and exact step scope.

Changing any decision field clears confirmation. After recording, the drawer
shows the append-only approval filename, decision, fixed step scope and expiry,
together with a prominent **nothing executed** statement.

## Backend enforcement

`POST /api/v1/recipes/record-approval` accepts a strict Pydantic contract with
no extra fields. The service:

1. reprepares the approval request from the canonical stored recipe;
2. recomputes and checks the recipe and request SHA-256 values;
3. reruns deterministic policy and obtains required steps server-side;
4. never accepts arbitrary step IDs from the browser;
5. redacts operator and reason text through the existing approval service;
6. writes one append-only record beneath the fixed `approvals/` root;
7. blocks symlink roots and overwriting;
8. reports `approval_recorded=true` and `execution_performed=false`.

The API health response now accurately reports bounded recipe and approval
evidence write authority while continuing to report no execution authority.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py
corepack pnpm@10.17.1 --dir interface build
.venv/bin/pytest -q
git diff --check
```

## Next boundary

The next slice should independently reload and verify the exact approval
against the stored recipe and current policy. Execution must remain unavailable
until that separate verification is visible and successful.
