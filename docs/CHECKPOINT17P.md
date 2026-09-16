# Checkpoint 17P — exact approval-request preparation

Checkpoint 17P lets an operator select one immutable stored recipe and prepare
the exact scope of a future approval. Preparation is read-only: it records no
human decision and cannot execute the recipe.

## Interface behavior

Each saved recipe with approval-required steps provides **Prepare approval
request**. The resulting review card displays:

- recipe identity, canonical filename and SHA-256;
- a separate canonical approval-request SHA-256;
- every approval-required step and its skill;
- an explicit `Prepared only · no decision recorded · nothing executed` state.

Preparing automatically scrolls and moves keyboard focus to the result card,
so the result cannot be inserted outside the visible portion of a long recipe
inventory. Template-derived proposal mode also provides **Back to template
setup**, preserving the current request and parameters after graph preview.
The prepared-only, no-decision and no-execution authority statement is rendered
as a large high-contrast amber boundary banner rather than secondary footnote
text so it remains visible during operator review.

## Backend enforcement

`POST /api/v1/recipes/prepare-approval` accepts only a safe canonical recipe
filename, its confirmed SHA-256, and the literal action
`prepare_recipe_approval`. The service:

1. rejects traversal, arbitrary paths and malformed digests;
2. loads the recipe only beneath the fixed recipe root;
3. recomputes and verifies its canonical digest;
4. reruns deterministic recipe policy against the trusted registry;
5. refuses recipes without approval-required steps;
6. returns bounded step and gate metadata plus a canonical request digest;
7. performs no recipe mutation, approval recording or execution.

No approver, reason, decision, expiration or correction text is accepted in
this checkpoint. Those belong to the later explicit decision-recording action.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py tests/test_interface_parity_fixture.py
corepack pnpm@10.17.1 --dir interface build
.venv/bin/pytest -q
git diff --check
```

## Next boundary

The next slice may collect an explicit human decision bound to this exact
request and recipe digest. It must write append-only approval evidence and
still must not execute the recipe.
