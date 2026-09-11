# Checkpoint 17B — Bounded workflow evidence projection

Checkpoint 17B lets the read-only interface display one real, validated
ActionCharter workflow trace without turning the browser into a filesystem or
execution client.

## Boundary

The projector accepts an exact safe task ID and loads only `<task-id>.json`
from the configured trace root. It rejects traversal, symlinked roots/files,
files larger than 1 MB, invalid trace schemas, identity mismatches and traces
without a true redaction claim.

The output contains only graph labels, bounded statuses, authority labels and
safe evidence basenames. It never projects the original request, context,
tool arguments, tool results, artifact paths, approval identifier or secrets.
The browser requests only `/runtime/workflow.json` from its own origin, caps the
response at 250 KB and validates the complete graph with Zod. Missing or invalid
runtime data safely falls back to the sanitized demonstration graph.

## Try one local trace

From the repository root:

```bash
mkdir -p interface/public/runtime
.venv/bin/geoagent project-interface-workflow <task-id> \
  --trace-root traces \
  --pretty > interface/public/runtime/workflow.json

cd interface
pnpm dev
```

Replace `<task-id>` with the basename of a validated file in `traces/`, without
the `.json` suffix. The header changes from `Demonstration` to `Validated trace`.

`interface/public/runtime/workflow.json` is local runtime output and is ignored
by Git. Only `interface/public/runtime/.gitkeep` is tracked.

## Validation

```bash
python -m pytest tests/test_interface_projection.py
cd interface && pnpm build
```

Checkpoint 17B does not add approval, execution, graph editing, arbitrary file
selection, directory listing, cross-origin requests or a web-server backend.
