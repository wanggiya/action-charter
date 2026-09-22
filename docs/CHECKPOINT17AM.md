# Checkpoint 17AM — rooted interface data paths

Checkpoint 17AM separates the common input and output locations from the file
names entered in the recipe-template interface.

## Behavior

- An input filename such as `sample_points.geojson` is compiled as
  `data/input/sample_points.geojson`.
- An output filename such as `result.gpkg` is compiled as
  `data/output/result.gpkg`.
- An explicit path such as `data/input/nested/source.geojson` is preserved.
- Existing compiler, approval, execution, and filesystem policies retain final
  authority over every normalized or explicit path.
- The compiled recipe and approval scope display the canonical path that will
  execute; the browser-only value is never treated as execution authority.

The CLI remains unchanged and continues to accept explicit paths and root
options. This checkpoint is an interface convenience over the same governed
backend, not a separate execution implementation.

## Validation

```bash
.venv/bin/pytest -q tests/test_interface_api.py
make test
pnpm --dir interface build
```
