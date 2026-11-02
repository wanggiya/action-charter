# Checkpoint 17J — Typed proposal connection editing

Checkpoint 17J makes browser-local proposal topology editable without granting
the browser execution or persistence authority.

## Editor behavior

In **New proposal** mode, selecting a block opens clearly labeled Inspector
controls for:

- editing its title, description and performer;
- deleting the selected block and its incident proposal connections;
- selecting a connection family and target block;
- adding a compatible directed connection;
- pressing an output socket, dragging a live wire and releasing it on a
  compatible input socket, following Blueprint/node-editor interaction;
- listing and deleting incoming or outgoing connections on that block.

The performer field is a bounded selection of project roles rather than an
unrestricted text field. Performer values already present in a validated
projection remain selectable so opening a historical run does not erase its
recorded ownership label.

The bounded connection families are `control`, `governance`, `tool`, `data`
and `evidence`. The editor maps them to compatible endpoint socket families and
rejects self-connections, exact duplicates, incompatible endpoints and cycles.

## Socket semantics

- A filled triangle is a connected agent/control socket.
- A hollow triangle is an available agent/control socket.
- A filled circle is a connected data/tool socket.
- A hollow circle is an available data/tool socket.
- Governance and evidence sockets follow the same filled/available rule.

Connections have no duplicate arrowhead: their direction is represented by
the source/output and target/input positions plus the Inspector listing.

## Authority boundary

All edits remain in the in-memory draft and are discarded by **Exit draft**.
This checkpoint cannot save or compile a proposal, invoke Planner, evaluate
backend policy, approve work, call MCP, execute tools, access secrets, alter
source evidence or write runtime projections.

The next interface slice must introduce a versioned proposal contract and a
safe backend save/compile boundary before policy or execution integration.

## Validation

```bash
cd interface
corepack pnpm build
cd ..
.venv/bin/pytest -q
git diff --check
```

Manual validation should cover adding a compatible connection, observing its
sockets become filled, deleting it and observing the sockets become hollow,
dragging an output socket onto a compatible empty input socket, rejection of
occupied, mismatched, duplicate or cyclic connections, block deletion with
incident connections, performer selection, and complete draft discard on exit.
