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
