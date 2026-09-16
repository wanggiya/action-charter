# ActionCharter interface

The Checkpoint 17 interface provides immutable evidence inspection and a separate browser-local proposal editor. It renders schema-validated workflow projections as a Blueprint-style node graph, supports draft block and typed-connection editing, and can create a non-executable proposal from the existing trusted recipe-template catalog.

## Technology

- React 19 provides the component model and interaction state.
- TypeScript provides static type checking.
- Vite 7 provides the local development server and production build.
- Zod validates workflow data at runtime.
- Lucide React provides icons.
- Plain CSS provides the visual system; there is no Tailwind dependency.

This directory has no backend, database, authentication system, OpenAI integration, Cloudflare configuration, or deployment configuration. The `.openai` directory from the earlier draft was a hosting manifest from a site starter and is intentionally absent.

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

Open the local URL printed by Vite. Evidence mode is immutable. Proposal edits remain in browser memory and are discarded on exit. A downloaded template proposal must still pass the existing backend compiler and later approval/execution gates. The interface cannot currently approve, execute, install packages, open arbitrary sockets, or contact ActionCharter services.
## Local typed API

Proposal compilation requires the Checkpoint 17M loopback service. Start it
from the repository root:

```bash
.venv/bin/geoagent serve-interface-api --project-root .
```

Then start this Vite application in another terminal. Vite proxies `/api` to
`127.0.0.1:8765`. The service compiles proposals in memory only; it cannot save,
approve or execute them.

After successful compilation, the interface can immutably save the reviewed
recipe. It requires confirmation of the displayed SHA-256 and step order, then
the backend recompiles and checks the digest again. Saved recipe JSON is local
runtime state under `workflow-recipes/` and is ignored by Git. This does not
approve or execute the recipe.
