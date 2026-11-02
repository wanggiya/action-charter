# Checkpoint 17G — Semantic node design system

Checkpoint 17G gives the workflow editor a stable semantic and visual language.
It separates what happened, who performed it and which responsibility boundary
contains it.

## Three independent concepts

- **Category** identifies the process: input, planning, policy, approval,
  execution, tool, validation or evidence.
- **Performer** identifies responsibility: user, agent, deterministic service
  or controlled tool boundary.
- **Group** collects related work: intake, planning, governance, execution or
  assurance.

Process nodes remain the primary graph objects. Performer labels appear inside
nodes, while translucent group frames provide ownership context without
doubling every action into a separate actor node.

## Visual contract

| Category | Accent |
| --- | --- |
| Input | Cyan |
| Planning | Purple |
| Policy | Amber |
| Human approval | Orange |
| Execution | Technical blue |
| Tool | Teal |
| Validation | Green |
| Evidence | Slate |

Nodes use charcoal bodies, moderate accents, a three-pixel category rail,
consistent ten-pixel corners, clear system typography and category-aware
selection glow. The minimap repeats the category palette and failure/pending
states. Human approval no longer combines an eighteen-pixel outer corner with
an eight-pixel header corner.

Semantic borders use two-pixel high-contrast accents, titles remain near-white,
secondary labels use accessible cool gray and performers appear as compact
outlined badges. Timeline events use a consistent three-level hierarchy:
status above, connected marker in the middle and process action below.
Successful timeline markers inherit their process-category accent rather than
turning every stage validation green. Status uses a restrained tinted capsule,
moderate glow and normal-weight text. Green remains primarily associated with
validation and verified outcomes.

The same charcoal and neutral-text tokens cover the top bar, navigation rail,
workflow heading, controls, inspector, status panels and timeline. Evidence
uses an off-white/slate accent so it remains legible without borrowing
validation green. Planning and execution use a restrained squared upper-right
corner to distinguish agent-owned actions from ordinary process cards.

## Navigation and responsive behavior

- the wheel listener is explicitly non-passive so graph zoom can safely prevent
  native scrolling;
- Shift plus wheel retains horizontal graph navigation;
- dragging empty canvas space pans in both axes;
- buttons and nodes remain clickable rather than initiating canvas drag;
- tablet and phone layouts place the inspector below the graph instead of
  hiding it.

Review at 1440×900 desktop, 1024×768 tablet, 412×915 common Android and 390×844
compact phone sizes. The supported minimum review width is 360 pixels.

The next structural graph slice will distinguish control/interaction edges
from typed data edges and arrange agents in an interaction lane above tool and
data operations. That requires an explicit edge/lane contract and is not
represented through styling alone.

## Compatibility and boundaries

New projections include strict category and group values. The frontend derives
deterministic display semantics for older runtime files and the demonstration
fixture. Group frames are presentation only. This checkpoint adds no editing,
approval or execution authority.

## Validation

```bash
.venv/bin/pytest tests/test_interface_projection.py -q

cd interface
pnpm install --frozen-lockfile
pnpm build
```
