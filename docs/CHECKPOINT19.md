# Checkpoint 19 — navigable default journey

For a real operator acceptance run through Planner, PostGIS execution,
evidence, Critic, release, and Snakemake export, follow
`docs/CHECKPOINT19_FULL_INTERFACE_RUN.md` and record each observed status.

The default workspace presents four visible tasks: **Plan → Review graph → Run → Check outcome**. Advanced opens the existing templates, stored recipes, run inventory, Assurance, draft graph editing, and trace selector. The CLI continues to work.

| Stage | Current action | Boundary |
| --- | --- | --- |
| Plan | Opens the Planner request and allowed skill controls | Planning alone saves or executes nothing |
| Review graph | Projects the current validated plan when available, then shows the graph | The graph is a projection, not authority |
| Run | Resumes an active recipe; otherwise continues an unfinished plan, selects its saved recipe, or opens the saved recipe chooser | The existing separate review, approval, preview, and execution gates apply |
| Check outcome | Opens the durable run inventory | Evidence is inspected without rerunning work |

This is a navigation and responsive layout change. It does not add new execution authority, automatically approve a plan, or remove the underlying expert workflows. The operator reports completing a fresh Planner-to-PostGIS run and downstream evidence, Critic, release, and export path. This is an operator acceptance report; the artifacts were not independently inspected in this workspace.

**Product limitation:** the path still requires too many manual plan, recipe,
approval, preview and evidence interactions. The one-decision task experience
is scheduled after governed history and context integration; see
`context/POST_HISTORY_INTERFACE.md`. Checkpoint 19 establishes navigability,
not the final ease-of-use target.

The planned context-and-graph workspace comes after governed task history and
context assembly (Checkpoints 21–22). At that point, task conversation and
source-backed context can sit beside the process graph and cross-link to its
nodes. The present interface does not claim persistent conversational memory.

## Local validation

1. Run `make interface-validate` and `make test` in the repository. Run `make interface-check` only while the launcher is stopped, because it checks the same loopback ports.
2. Start the interface with `bash scripts/start_actioncharter.sh` and open the printed local URL.
3. Confirm the four stages are visible. Plan opens the request form; Review graph displays the current validated plan if one exists; Run resumes an unfinished plan before offering saved recipes, or opens saved recipes when no plan or recipe is active; Check outcome opens the run inventory. No stage click itself should approve or execute work.
4. Open Advanced and confirm Templates, Recipes, Runs, Assurance, New draft graph, and the trace selector remain accessible. Close Advanced and confirm the graph expands into the freed space.
5. Test at desktop width and at 390 px phone width. The stage labels and Advanced control should remain reachable; the Exit workflow button remains accessible when a workflow is active.

A reviewed recipe with valid approval evidence is still necessary for an actual run. Use an existing safe test recipe for the full execution path, and inspect the resulting durable record under Check outcome.

For the new-plan path, validate one supported request: generate a plan, click
Review graph without first clicking View plan graph, then click Run. The plan
review controls should reopen with its current state intact. After a reviewed
recipe is stored, Run should open the saved recipe chooser focused on that
recipe. Approval and execution must remain separate explicit actions.

The Planner panel now displays a sticky **Current boundary** guide. It derives
the next action from the current plan, approval, compilation, and stored-recipe
state. **Go to step** scrolls to the existing control; it never performs the
action. Verify the guide changes after a validated plan, after saving the plan,
and after preparing the exact approval scope. Denied and read-only plans should
remain clearly described without implying that they can execute.

## Graph layout acceptance

At desktop width, narrow desktop width (around 1000 px), and phone width
(around 390 px), check that the minimap remains at the graph canvas's upper
right and that the timeline stays within the graph column. Neither should
extend under the inspector. Drag the zoom controls and connection legend by
their grip handles. They should follow the pointer smoothly and stop at the
canvas edge; releasing should preserve their positions. Zoom buttons and
minimap panning should still work after dragging. The connection legend is
intentionally hidden at phone width.

The timeline has its own horizontal scroll and left/right controls. At a
narrow width, scroll fully right and confirm the final event's status, marker,
and label are all visible with space beyond them; the inspector must remain
separate. Repeat for a workflow with more nodes than the demonstration graph.
