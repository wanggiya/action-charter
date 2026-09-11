# Checkpoint 17A — Read-only workflow interface foundation

Checkpoint 17A creates the first product-facing interface without creating a
second execution boundary. The first view is a connected workflow canvas that
makes agents, deterministic controls, human approval, tools, validation and
evidence visible as distinct node types.

## Delivered surface

- blueprint-style node graph with curved directional connections;
- selectable nodes and an evidence/authority inspector;
- execution timeline, live graph minimap and bounded zoom controls;
- measured fit-to-viewport behavior and switchable horizontal/vertical layouts;
- vertical-by-default graph presentation on narrow phone-sized screens;
- viewport controls and minimap pinned above the scrolling graph canvas;
- responsive desktop, tablet and phone layouts;
- a schema-validated, sanitized demonstration workflow;
- explicit read-only state in the interface and data contract;
- an isolated frontend application beneath `interface/`.

## Implementation stack

The interface is a conventional local single-page application: React 19 and
TypeScript for components, Vite 7 for development and builds, Zod for runtime
fixture validation, Lucide React for icons, and plain CSS for presentation.
It has no Next.js/Vinext, Tailwind, Cloudflare, database, authentication or
OpenAI hosting dependency. In particular, no `.openai/` directory is required.

## Trust boundary

The interface is a projection of governed evidence. It does not become a
policy engine and has no route for approval, execution, filesystem access,
database access, secret access, arbitrary network access or package
installation. Frontend status labels are demonstration data, not authoritative
claims about a live run.

Future evidence loading must occur through a bounded backend projection that
validates known schemas, caps response size, redacts sensitive fields and
exposes only repository-controlled evidence roots.

## Graph editing direction

The node model deliberately separates stable node identity, node kind,
authority, evidence reference and canvas position. A later checkpoint may add
dragging, connecting and form-based node configuration, but editing will create
a proposal only. It must never directly execute a graph.

## Capability growth direction

Pandas is a sensible future tabular-data adapter. New tools should enter through
a reviewed capability manifest containing a pinned dependency set, access
class, schemas, resource limits, deterministic validator and evidence contract.
The product will not offer arbitrary package installation, raw sockets or
unrestricted code execution from the graph.

The preserved design and sequencing notes are in
[`context/CAPABILITY_EXPANSION.md`](../context/CAPABILITY_EXPANSION.md).

## Validation

```bash
cd interface
pnpm install --frozen-lockfile
pnpm build
```

The existing Python regression suite and Compose configuration remain separate
required checks before merge.

For the Windows/WSL command-boundary check and Linux-local Node setup, see
[`docs/WSL_FRONTEND_SETUP.md`](WSL_FRONTEND_SETUP.md).
