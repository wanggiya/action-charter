# Checkpoint 17T — First governed interface execution

Checkpoint 17T adds the interface's first real execution action for one exact,
approved and previewed recipe.

## Required gates

The interface permits execution only when all of these are true:

1. an immutable recipe was compiled and explicitly saved;
2. an append-only approval was recorded;
3. the approval was independently verified;
4. the exact execution envelope was previewed;
5. the operator confirms the displayed preview SHA-256;
6. `ENABLE_WRITE_TOOLS=true` was explicitly present when the local API started.

The server reconstructs every artifact and envelope from fixed roots. It does not
trust browser-supplied steps, arguments or output paths. It compares the rebuilt
preview digest and invokes the existing server-side `run_approved_recipe`
boundary, which revalidates the recipe and approval again, dispatches only
registered skills, performs required post-write validation, and persists run,
evidence and report records.

## Operator setup

Keep write execution disabled for ordinary interface inspection. To perform the
deliberate execution test, stop the local interface API and restart it from the
project root with:

```bash
ENABLE_WRITE_TOOLS=true .venv/bin/geoagent serve-interface-api --project-root .
```

Do not enable `ALLOW_OVERWRITE`. Use a fresh output target in the recipe.

## Current scope

This checkpoint executes the existing approved recipe runner. Live incremental
progress, interruption, recovery and richer failure localization belong to
Checkpoint 17U. A failed response must be treated as requiring inspection of
outputs and evidence before any retry.

The template form exposes both required and optional parameters. Vector
conversion therefore presents `target_format`, `source_layer` and `target_layer`
instead of silently hiding them. GeoPackage remains the initial format selection,
and the backend still validates format and target-path consistency.

Only the current gate is visible: saved-recipe selection yields to decision
recording, decision recording yields to verification, and verification yields to
the execution preview. Completed gates remain recorded but no longer stack over
the active panel. Step outcomes use one compact line, while run, evidence and
report locations receive full-width result cards.

The completed-run panel also projects bounded, recursively redacted outcome and
validation facts from each step. This lets the operator inspect useful results
such as feature counts, output targets, pass/fail findings and other structured
metadata without opening raw evidence first. Each per-step projection is capped
at 16 KiB; larger results direct the operator to the durable evidence artifact.

`target_format` is not decorative UI metadata. The typed proposal schema accepts
only `geojson` or `geopackage`; deterministic proposal assessment rejects a
format that conflicts with the `.geojson` or `.gpkg` target suffix; and the
conversion policy derives the corresponding real driver and output format from
that validated target. The selector therefore constrains compilation while the
runtime conversion continues to use the compiled target path.

All optional selectors use the same field styling as required parameters. The
approval and later recipe-flow stages also expose one persistent close control,
which clears transient interface state and closes the complete active flow.
The approval header reserves a dedicated right-side slot for that control, so
the **No execution** indicator remains immediately to its left and unobstructed.
