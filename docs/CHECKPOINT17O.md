# Checkpoint 17O — stored recipe inventory

Checkpoint 17O gives the successful 17N save action a clear destination. The
save result remains visible until the operator selects **Done — view saved
recipes**; the interface then closes the template workspace and opens a
read-only inventory. A persistent **Recipes** control can reopen it later.

The interface does not close immediately after saving because doing so would
hide the immutable filename and authority result before the operator could
verify them.

## Read-only inventory boundary

`GET /api/v1/recipes` scans at most 200 canonical JSON recipes beneath the
fixed recipe root. It rejects symlinks, escaped paths, invalid recipes and
policy failures. Each bounded response includes only:

- safe recipe ID, filename and SHA-256;
- ordered step IDs and skill IDs;
- approval-required step IDs;
- validation-required step IDs;
- explicit non-mutation, non-approval and non-execution claims.

Arguments, secrets, arbitrary paths and approval identities are not projected.
The browser cannot approve or execute from this inventory yet.

## Test

Restart the interface API, open **Recipes**, and confirm the recipe stored in
17N appears with `convert_vector` labelled **Approval required**. Opening the
inventory or moving to it from the save result must not create an approval,
output dataset, run result or execution evidence.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py tests/test_interface_parity_fixture.py
corepack pnpm@10.17.1 --dir interface build
.venv/bin/pytest -q
git diff --check
```

## Next boundary

The next slice can prepare and display an exact approval request for one
selected recipe. Recording a human decision must remain a separate explicit
action, and execution must remain unavailable.
