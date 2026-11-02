# Checkpoint 17AD — verified plan to governed recipe candidate

Checkpoint 17AD adds a non-executing bridge from one independently verified
Planner result to the existing typed workflow-recipe contract.

The server reloads and verifies the immutable plan and approval evidence. It
accepts only recipe-dispatcher skills (`inspect_vector`, `convert_vector`,
`inspect_raster`, and `convert_raster`), preserves step order as dependencies,
runs deterministic recipe policy, and returns a canonical recipe SHA-256.

This boundary deliberately does **not** save, approve, or execute the compiled
recipe. Plan approval authorizes the reviewed plan; it does not transfer into
recipe approval. A later checkpoint must persist the exact candidate and route
it through the existing recipe review, approval, preview, and execution path.

## Manual validation

Select only `convert_vector`, then request:

> Create exactly one step using convert_vector with arguments
> path=data/input/sample_points.geojson and
> target_path=data/output/planner_recipe_test.gpkg. Set
> requires_approval=true and validation_required=true. Plan only; do not
> execute.

Generate, review and save the plan; prepare, record, and independently verify
its approval; then select **Compile as governed recipe**. The interface must
show `COMPILED · NOT SAVED`, a recipe digest, the canonical `path` and
`target_path` arguments, and an explicit nothing-executed statement.

Older Planner artifacts using `source` and `target` are intentionally rejected;
the recipe dispatcher contract uses `path` and `target_path`.
