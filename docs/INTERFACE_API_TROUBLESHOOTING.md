# Interface API development and troubleshooting

## Start the repository source explicitly

From the repository root, use:

```bash
bash scripts/serve_interface_dev.sh
```

The launcher pins `PYTHONPATH` to the current repository's `src` directory,
uses its `.venv`, prints the imported server file, and reports how many times
the Planner recipe-save path occurs in the HTTP handler. The expected count is
`2`: request allowlist plus dispatch.

The launcher does not create model or execution authority. Export the required
model settings and `ENABLE_WRITE_TOOLS` before starting it when those features
are being tested.

To use another port:

```bash
INTERFACE_API_PORT=8766 bash scripts/serve_interface_dev.sh
```

## Identify the process actually serving a port

```bash
ss -ltnp | rg ':8765'
ps -p PID -o pid,lstart,etime,time,args
readlink -f /proc/PID/cwd
```

`etime` is elapsed wall-clock runtime. `time` is accumulated CPU time, so a
mostly idle server may show only a few seconds of CPU after running for hours.
Running `ps` or `readlink` does not activate or reveal the server; those commands
only inspect an existing process. A process may appear later because startup or
imports were still completing, the earlier PID was wrong, or a stale process
already held the port.

## Probe a POST route

```bash
curl --noproxy '*' -i -X POST \
  http://127.0.0.1:8765/api/v1/plans/save-reviewed-recipe \
  -H 'Content-Type: application/json' \
  -d '{}'
```

HTTP 400 with `request payload is invalid` proves the route exists and reached
schema validation. The empty object is deliberately invalid; it is not a real
save request. `endpoint is not available` means the running handler lacks or
rejects the route.

## Avoid stale processes

Before restarting, find and stop the exact PID that owns the port. Confirm the
port is free before launching another service. Do not infer process age from the
CPU `TIME` column, and do not assume `.venv/bin/geoagent` imports the edited
checkout unless the package is installed editable or `PYTHONPATH` is pinned.

## Development-page refreshes

`pnpm dev` runs Vite with a file watcher and a browser WebSocket. Editing,
extracting an archive over, switching branches, merging, pulling, or otherwise
touching files beneath `interface/` may trigger hot-module replacement or a
full browser reload. An API response also causes ordinary React state updates,
which can look like a refresh without reloading the document. Neither behavior
means a governed recipe changed repository source.

Use the browser console to distinguish them: Vite reports `hot updated` or
`page reload`; an ordinary state update has no such message. The production
build has no development hot-reload client.

Pressing `Ctrl+C` is the normal way to stop the source-pinned API. The launcher
catches Python's `KeyboardInterrupt`, lets the HTTP server close its socket, and
prints `Interface API stopped.` without treating operator shutdown as failure.
