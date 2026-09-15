# Checkpoint 17I — Proposal edit mode foundation

Checkpoint 17I separates immutable evidence inspection from editable proposal
composition. It is the first interface slice that changes graph presentation,
but it grants no execution authority.

## Two explicit modes

### Evidence view

- Loads schema-validated projections of completed traces.
- Allows selection, navigation and evidence inspection only.
- Does not allow node movement, creation, deletion or field editing.
- Never modifies the source projection.

### Proposal edit

- Starts from a deep in-memory copy of the displayed workflow.
- Labels the workspace `Draft only` and disables run switching.
- Allows proposal nodes to be added, selected, renamed, described, assigned a
  performer, repositioned or deleted.
- Shows compatible agent control and data/tool sockets before they are wired:
  hollow sockets are available, while filled sockets are connected to an edge.
- Uses socket fill, rather than a separate line arrowhead, to identify connected
  endpoints without displaying a duplicate triangle on agent connections.
- Removes incident draft edges when a node is deleted.
- Supports dragging in horizontal and vertical presentation modes.
- Discards the draft when the operator exits this mode.

The proposal remains browser-local. It cannot approve work, call MCP, execute
tools, access secrets, write evidence, modify runtime traces or replace CLI
contracts. Newly added nodes remain unconnected until the typed-connection
editing slice is implemented.

## Product direction

The complete interface is intended to cover the same governed lifecycle as the
CLI:

1. compose a request and select bounded inputs;
2. ask Planner for a structured proposal;
3. edit nodes and compatible typed connections;
4. compile and validate the proposal through backend-owned contracts;
5. review the digest-bound plan and policy findings;
6. record explicit human approval;
7. execute through the existing Executor-to-MCP boundary;
8. observe timing, failures, validation and evidence.

The CLI remains a supported first-class interface for automation, debugging,
CI and expert operation. The web interface will call the same contracts rather
than implementing a second execution system.

## Validate

```bash
cd interface
pnpm install --frozen-lockfile
pnpm build
```

Manual checks should confirm that evidence nodes remain fixed, entering
Proposal edit creates a separate draft, node dragging works in both layouts,
connected sockets are filled, available sockets are hollow, and exiting
discards every draft change.
