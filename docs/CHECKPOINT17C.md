# Checkpoint 17C — Bounded workflow run selector

Checkpoint 17C removes the need to remember trace task IDs. One operator command
exports a capped, sanitized catalog and matching browser projections; the
read-only interface presents those validated runs in its header selector.

## Export and view

```bash
.venv/bin/geoagent export-interface-workflows \
  --trace-root traces \
  --output-root interface/public/runtime \
  --pretty

cd interface
pnpm dev
```

Refresh the page and select a run from the header. The catalog and projections
under `interface/public/runtime/` are generated local files and remain ignored.

## Boundary

- at most 50 trace files are accepted;
- every trace must pass the 17B identity, size, symlink, schema and redaction checks;
- catalog task IDs and projection paths must match exactly;
- the browser constructs only `/runtime/<safe-task-id>.json` paths;
- catalog and projection responses are each capped at 250 KB and validated;
- source traces are never modified and no workflow is executed;
- invalid or absent catalogs preserve the existing demonstration/17B fallback.

The exporter atomically replaces only derived runtime JSON in its configured
output directory. It does not delete stale files, inspect arbitrary directories
from the browser, or expose trace payloads.
