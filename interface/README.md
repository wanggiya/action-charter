# ActionCharter interface

Checkpoint 17A is a read-only workflow explorer. It renders a bounded JSON fixture as a blueprint-style node graph and validates that fixture before rendering it.

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

## Run

```bash
cd interface
pnpm install --frozen-lockfile
pnpm build
pnpm dev
```

Open the local URL printed by Vite. The demo is intentionally non-mutating: it cannot approve, execute, install packages, open sockets, or contact ActionCharter services.
