# ActionCharter interface

This is the frontend developer guide. For product capabilities and one-command startup, use the [root README](../README.md). The browser provides graph/evidence views, reviewed planning and governed recipe actions through the loopback backend; it does not itself enforce or grant execution authority.

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

## Frontend-only development

For normal use, run `make interface-start` from the repository root to start both services. The commands below start only Vite and are for frontend debugging; API-backed actions also need the backend.


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
`127.0.0.1:8765` by default; `INTERFACE_API_PORT` selects the proxy target for alternate-port development. Write execution remains disabled unless the service process is
started with `ENABLE_WRITE_TOOLS=true`; the health endpoint reports that fact. Direct read-only inspection remains separately available.

After successful compilation, the interface can immutably save the reviewed
recipe. It requires confirmation of the displayed SHA-256 and step order, then
the backend recompiles and checks the digest again. Saved recipe JSON is local
runtime state under `workflow-recipes/` and is ignored by Git. This does not
approve or execute the recipe.

The primary **Planner agent** generates and automatically stores validated proposals. **Saved records** browses plans/recipes; **Execution History** browses durable inspection and governed recipe attempts. **Outcome** shows the current result. **Execute** opens exact-scope review for supported saved plans. Read-only vector/raster inspection does not need fabricated approval; writes retain exact approval, validation and evidence checks. Technical Plan and Task workspace remain under Advanced.

Current-plan operation edits require backend validation and new proposal storage before execution. Presentation-only Advanced drafts remain separate. See the [interface acceptance process](../docs/INTERFACE_ACCEPTANCE.md) for isolated sessions, live-model and deterministic cases, evidence capture and bug retesting.

# Input and output filenames

Trusted template forms accept either a filename or an explicit path. A
filename-only input is resolved under `data/input`; a filename-only output is
resolved under `data/output`. Always review the canonical paths in the compiled
recipe before preparing approval. The CLI remains available for explicit root
and path control.

Planner agent now uses a persistent conversation with clarification and complete, validated revisions. Send uses Enter; Shift+Enter inserts a newline. The conversation selector lists the 20 most recent saved chats. Open conversation plan restores its last proposal explicitly. New chat keeps the current workflow available as context. Block tools expands secondary editing buttons, and Expand reveals the full timeline. See [dialogue frontend tests](../docs/PLANNER_DIALOGUE_ACCEPTANCE.md).

The optional searchable Skills picker remains below Send. Empty selection uses automatic capability choice; selected chips persist across messages. Each user message records its submitted selection and replies show workflow skill snapshots/deltas. Opening a saved chat restores its last submitted selection. See the staged 27-case checklist in the dialogue acceptance guide before local conversion or a reviewed PostGIS run.

Outline material now fades its category/control color from the top/bottom edges into a transparent center. Compact timeline markers and their connector are aligned; full stage titles appear on hover. Follow the [vector-to-PostGIS frontend walkthrough](../docs/FRONTEND_VECTOR_POSTGIS_WALKTHROUGH.md) for the next acceptance pass.

The normal host launcher now reads allowlisted non-secret project .env settings and resolves local secret-file paths under the project root. Terminal exports win. Container postgis/geoserver defaults resolve to loopback for this host process; /run/secrets defaults resolve to the corresponding .secrets host file unless explicitly overridden in the terminal. Password contents stay in files, and startup logs show only file readiness. .env write/overwrite flags do not grant execution authority.

Main-workflow Snakemake export and static verification now appear in Add/Planner. Add Export automatically appends Verify and binds the original saved plan. Completed source operations reuse independently checked historical evidence; no PostGIS reload or Snakemake process runs. See [block acceptance](../docs/WORKFLOW_SNAKEMAKE_BLOCKS.md). This supersedes the earlier export-only-in-Advanced limitation for completed governed workflows.
