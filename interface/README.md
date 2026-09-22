# ActionCharter interface

The Checkpoint 17 interface provides immutable evidence inspection and a separate browser-local proposal editor. It renders schema-validated workflow projections as a Blueprint-style node graph, supports draft block and typed-connection editing, and can create a non-executable proposal from the existing trusted recipe-template catalog.

## Technology

- React 19 provides the component model and interaction state.
- TypeScript provides static type checking.
- Vite 7 provides the local development server and production build.
- Zod validates workflow data at runtime.
- Lucide React provides icons.
- Plain CSS provides the visual system; there is no Tailwind dependency.

This directory remains a browser client and contains no database,
authentication system, OpenAI integration, Cloudflare configuration, or
deployment configuration. Its `/api` requests are proxied only to the separate
loopback ActionCharter interface service. The `.openai` directory from the
earlier draft was a hosting manifest from a site starter and is intentionally
absent.

## Prerequisites

- Linux Node.js 22.12 or newer
- pnpm 10

In WSL, verify that both commands resolve to Linux paths before installing:

```bash
type -a node pnpm
node --version
pnpm --version
```

Paths under `/mnt/c/`, executables ending in `.cmd`, or a command that starts `CMD.EXE` indicate that Windows Node/pnpm is being used from WSL. Install Node and pnpm inside the WSL distribution, then open a new shell.

## Export local runtime projections

From the repository root, export the trusted recipe catalog before starting the interface:

```bash
mkdir -p interface/public/runtime
.venv/bin/geoagent recipe-template-catalog --project-root . --pretty > interface/public/runtime/recipe-templates.json
```

The generated runtime file is ignored by Git.

## Run

```bash
cd interface
pnpm install --frozen-lockfile
pnpm build
pnpm dev
```

Open the local URL printed by Vite. Evidence mode is immutable. Proposal edits
remain in browser memory and are discarded on exit. The loopback service can
compile and store reviewed recipes, record and verify approval, preview exact
execution, and—only when explicitly started with write tools enabled—execute
that exact approved preview through the existing governed runner. The interface
cannot install packages, open arbitrary sockets, or bypass any policy,
approval, validation, or evidence boundary.
## Local typed API

Governed interface operations require the loopback service. Start it
from the repository root:

```bash
.venv/bin/geoagent serve-interface-api --project-root .
```

When iterating on backend routes, prefer `bash scripts/serve_interface_dev.sh` from
the repository root so the running API is pinned to the edited `src` tree. See
`docs/INTERFACE_API_TROUBLESHOOTING.md`.

Then start this Vite application in another terminal. Vite proxies `/api` to
`127.0.0.1:8765`. Execution remains disabled unless the service process is
started with `ENABLE_WRITE_TOOLS=true`; the health endpoint reports that fact.

After successful compilation, the interface can immutably save the reviewed
recipe. It requires confirmation of the displayed SHA-256 and step order, then
the backend recompiles and checks the digest again. Saved recipe JSON is local
runtime state under `workflow-recipes/` and is ignored by Git. This does not
approve or execute the recipe.

The top-level **Runs** workspace reads bounded durable progress from
`workflow-state/interface-executions/`. It can restore an eligible attempt's
run-specific graph after restarting the browser or API. This inventory is
observational only and cannot resume, retry, approve, or execute an attempt.

The top-level **Plan** workspace calls the existing Planner Agent through the
loopback service and configured model provider. It returns a schema-validated,
planning-only result and visual graph. It does not save, approve, or execute the
plan; those remain separate authority increments. The operator explicitly
selects the exact implemented skills the Planner may use. The backend verifies
those IDs against the trusted registry and sends only that compact selection to
the model.
# Input and output filenames

Trusted template forms accept either a filename or an explicit path. A
filename-only input is resolved under `data/input`; a filename-only output is
resolved under `data/output`. Always review the canonical paths in the compiled
recipe before preparing approval. The CLI remains available for explicit root
and path control.
