# Checkpoint 17W — Planner Agent interface entry point

Checkpoint 17W begins the agent workflow that was still missing from the
interface: natural-language request to Planner Agent to a validated visual plan.

## Implemented

- A top-level **Plan** workspace accepts one request of at most 8,000 characters.
- The operator selects the exact implemented skills the model may propose from
  a registry-backed catalog; arbitrary or unknown skill IDs fail before a model
  call.
- The selector supports text search across skill name, kind and access class,
  keyboard navigation, removable selected-skill chips, and deterministic
  request-based recommendations.
- Recommendations never become allowed automatically; only explicit selection
  changes the `allowed_skill_ids` sent to the backend.
- `POST /api/v1/plans/create` accepts only `{action: "plan_task", request}`.
- The endpoint calls the existing `plan_task` service with trusted project and
  agent roots. That service builds the context pack, loads the Planner manifest,
  calls the configured model client and validates the returned plan schema.
- The interface displays the model, summary, exact proposed steps, and approval
  requirements.
- The validated result can be viewed as a Blueprint-style planning graph.
- The model receives a compact payload containing the request, relevant dataset
  metadata and only the selected skill metadata. Full project status,
  architecture and decision history are excluded from the generation prompt.

## Authority boundary

This is planning only. The endpoint accepts no model URL, agent root, command,
approval, or execution flag from the browser. Selected skill IDs are treated as
untrusted input and checked against the trusted registry. The returned plan must
remain a subset of that exact selection. It saves no plan, records no approval,
invokes no skill, and executes no proposed step.

## Next

Add separate reviewed plan persistence, then connect the existing plan digest,
approval verification, execution-envelope, executor, critic and release gates.
