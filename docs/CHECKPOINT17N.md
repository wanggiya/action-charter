# Checkpoint 17N — digest-bound reviewed recipe storage

Checkpoint 17N adds the interface's first persistent operation. It stores one
compiled recipe only after the operator reviews the displayed step order and
exact recipe SHA-256 and performs a separate explicit save action.

## Interaction

1. Select a trusted template and fill its parameters.
   Choose a unique conservative recipe ID for the stored identity.
2. Select **Compile proposal**.
3. Inspect the recipe identity, complete ordered skill list, approval gates,
   validation gates and recipe SHA-256.
4. Check **I reviewed this exact recipe digest and step order**.
5. Select **Save reviewed recipe**.

Editing the request or any parameter clears the compilation and confirmation.
The operator must compile and review the updated recipe again.

## Backend enforcement

`POST /api/v1/recipe-proposals/save-reviewed` accepts only:

- the exact validated `RecipeProposal`;
- the exact displayed recipe SHA-256;
- the literal action `save_reviewed_recipe`.

The service then:

1. validates the request contract and digest format;
2. reloads the trusted skill registry;
3. recompiles the proposal deterministically;
4. calculates the recipe digest again;
5. rejects any digest mismatch before creating a directory or file;
6. redacts and immutably stores the recipe under `workflow-recipes/`;
7. returns only the safe filename and digest;
8. reports `approval_performed=false` and `execution_performed=false`.

The browser cannot choose a storage directory. Existing recipe identities are
never overwritten; repeating the same save fails closed. The generated recipe
file is runtime state and remains ignored by Git.

Saving a recipe is not approving its execution. Approval must remain a later,
separate digest-bound action.

## Local test

Start the 17M/17N service and Vite in separate terminals:

```bash
.venv/bin/geoagent serve-interface-api --project-root .
corepack pnpm@10.17.1 --dir interface dev
```

Use a new recipe ID or template selection that has not already been stored.
After saving, inspect the ignored runtime file:

```bash
find workflow-recipes -maxdepth 1 -type f -name '*.json' -printf '%f\n'
git status --short --ignored workflow-recipes
```

The JSON recipe should be ignored, while `workflow-recipes/.gitkeep` remains
tracked. No approval, output dataset, run result or execution evidence should
be created.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py tests/test_interface_parity_fixture.py
corepack pnpm@10.17.1 --dir interface build
.venv/bin/pytest -q
git diff --check
```

## Next boundary

The next slice should inventory saved recipes and prepare an exact approval
request. It must not combine approval recording with execution.
