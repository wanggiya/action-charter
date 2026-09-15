# Interface design direction

This document preserves the intended design standard after the primitive
read-only interface is complete. The reference experience is a professional
node editor such as Blender Geometry Nodes or Unreal Engine Blueprints, adapted
to ActionCharter's governed execution model rather than copied visually.

## Two independent visual identities

A node communicates two different facts. These must not be collapsed into one
color.

### Node kind

Stable shape, header treatment, icon and port pattern identify what a node is:

| Kind | Visual identity | Meaning |
| --- | --- | --- |
| Input | intake/tab shape | Operator request or bounded source |
| Agent | framed process shape | Planner, Executor, Critic or Builder reasoning role |
| Control | shield/diamond treatment | Deterministic policy or validation |
| Approval | gate treatment | Human decision boundary |
| Tool | strong operation block | Allowlisted professional-tool operation |
| Evidence | document/output shape | Immutable result, report or verification |

Kind identity must remain recognizable in grayscale and must not depend on
color alone.

### Lifecycle state

Border, status badge and a small state indicator identify what happened:

| State | Suggested treatment |
| --- | --- |
| Pending | neutral gray, unfilled indicator |
| Ready | blue, quiet pulse or ready marker |
| Approved | amber/gold approval badge |
| Running | animated blue progress treatment |
| Completed | solid teal completion badge |
| Verified | green verification mark |
| Failed | red error border and explicit text/icon |
| Rolled back | violet return marker |
| Blocked | orange warning marker |

State must always include readable text and an icon; color is supplementary.

## Connection and port standard

- Ports have declared input/output types rather than decorative dots.
- Compatible ports share a type marker and accessible label.
- Direction remains unambiguous in horizontal and vertical layouts.
- Connection style distinguishes data, control, approval and evidence flow.
- Failed or blocked paths are visible without implying that later nodes ran.
- Selecting a connection explains its source, destination and contract.

## Detailed inspector

Selecting any node should eventually show the following information when it is
available and safe to disclose:

1. identity, kind, role and current lifecycle state;
2. plain-language purpose and result summary;
3. bounded inputs and outputs with schema names;
4. authority and prohibited actions;
5. policy checks and approval requirements;
6. evidence files, digests and verification state;
7. start/finish time, duration and relevant versions;
8. validation findings, warnings and redacted errors;
9. upstream/downstream lineage;
10. safe next actions.

The inspector must distinguish observed evidence from inferred presentation.
Secrets, unrestricted payloads, private reasoning and arbitrary filesystem paths
must never be exposed. On phones and narrow tablets, the inspector should become
an accessible bottom sheet or full-screen detail view rather than disappearing.

## Interaction modes

### Read-only mode

The current primitive mode supports selection, inspection, pan, zoom, fit,
minimap navigation, run selection and horizontal/vertical layout. Nodes cannot
be dragged or connected.

### Proposal-editing mode

A later explicitly labeled mode may support node repositioning, compatible-port
connections, form-based configuration, undo/redo and deterministic graph
validation. Editing produces a proposal only. It cannot approve or execute a
workflow, install packages, expose secrets or bypass typed backend contracts.

### Governed execution mode

Any future execution action remains separate from graph editing and must use the
existing plan, digest, human approval, exact-scope execution, validation and
independent evidence boundaries.

## Implementation sequence

1. Finish the primitive read-only workflow and evidence slices.
2. Define a versioned node, port, edge, state and inspector schema.
3. Apply the visual identity system and accessibility rules.
4. Add complete evidence-backed inspector sections.
5. Add responsive phone/tablet inspection behavior.
6. Add proposal-only editing after the read-only contracts are stable.

This is a design commitment and backlog direction, not a claim that the richer
interactions are already implemented.

Checkpoint 17D completes the first evidence-backed inspector slice in step 4:
safe summaries, aggregate facts, timing and findings are available on every
projected node. Artifact navigation and richer responsive inspection remain
future slices.

Checkpoint 17E adds the first compact evidence-card visual language: category
color, recorded state, safe reference, integrity metadata and expandable facts.
Future artifact-specific viewers should extend this contract instead of
embedding raw JSON or unrestricted logs.

Checkpoint 17F removes the fixed eight-node assumption for validated runtime
traces. Recorded governed operations become individual connected nodes and the
canvas adapts to the projected topology in either orientation.

Nodes remain process-centric: the action is the primary title and the
responsible user, agent, policy service or tool boundary is embedded as a
performer label. This keeps complex workflows readable while the separate
Agents view remains available for an actor-centric representation.

Checkpoint 17G formalizes that direction. Process category controls color and
visual identity, performer identifies responsibility, and owner group controls
the surrounding container. The palette uses charcoal surfaces with moderate
blue, cyan, purple, amber, orange, green and slate accents. Category color is
limited to rails, icons, borders and selection states rather than filling the
entire node.

The semantic stroke and category text must remain clearly visible at normal
zoom. Muting belongs primarily to secondary descriptions and inactive state,
not to the main category border, action title or performer identity. Timeline
events place state above the marker and the action label below it.

Timeline success does not erase process identity: completed markers retain the
category hue with moderate saturation. Validation green is reserved for
validation semantics, while failure and pending states override category color.
Ownership-frame padding must preserve visible separation between adjacent
groups in both graph orientations.

The theme applies to the whole application shell, not only the graph canvas:
navigation, headings, controls, inspector sections, status surfaces and the
timeline use the same charcoal, divider and typography tokens. Evidence uses a
high-contrast off-white/slate identity. Agent-owned planning and execution
actions receive a subtly squared upper-right corner.

The next topology contract separates agent interaction/control edges from
typed tool-data edges. Agents will occupy a coherent upper interaction lane;
tool and data operations will sit below their owning agent group. This must be
modeled in projection data so the graph does not imply false execution order.

Checkpoint 17H implements that contract for completed traces. Control edges are
solid off-white with arrows, governance edges are dashed amber with arrows,
tool relationships are dashed teal without control arrows, typed data edges
are cyan without control arrows and evidence edges are dotted off-white.
User Request and bounded Input Data enter Planner through different socket
families. Planner and Executor use hollow triangular interaction sockets and
circular data/tool sockets. Executor connects to the first recorded operation,
the recorded operation path continues in trace order, and only the final result
connects to validation. Components without supporting trace fields are omitted.
Horizontal layouts place sockets on left/right sides and
vertical layouts place them on top/bottom sides. Connections always use the
same hollow endpoint shape at both ends and sockets render above lines.
Selected-run load failures are explicit rather than silently replaced by the
demonstration. Completed evidence views stay fixed; future proposal mode may
move nodes and reconnect only compatible typed sockets.

The minimap is intentionally schematic: transparent node interiors, semantic
outlines and thin connections. Overlay controls expose drag handles, the graph
is clipped beneath the inspector, and the viewport does not add a second
rounded frame. Snakemake is projected only when recorded metadata supports it;
execution-engine inference from names is prohibited.
