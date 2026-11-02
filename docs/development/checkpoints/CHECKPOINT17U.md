# Checkpoint 17U — live execution state and recovery

Checkpoint 17U follows the first governed interface execution with observable,
failure-localized operations. This first increment adds a typed live-state
contract without widening execution authority.

## Implemented in 17U-A

- The existing recipe runner emits `running`, `completed`,
  `validated_success`, `validation_failed`, and `failed` transitions.
- The approved-recipe boundary forwards those transitions without changing
  recipe, approval, or execution-envelope verification.
- The loopback interface API exposes progress only by the exact confirmed
  execution-preview SHA-256.
- The interface polls that bounded projection during execution and identifies
  the failed step when one is known.
- Saving or selecting an immutable recipe creates a read-only active-run graph
  for that exact recipe digest. Approval, runner transitions, validation and
  evidence update their corresponding nodes instead of leaving the earlier
  template draft or historical trace on screen.
- A visible `View live workflow graph` action dismisses the gate panels without
  discarding the current governed-run state.
- A persistent top-bar action resumes the current approval or execution after
  the operator inspects the graph.
- The active graph separates User Request and Input Data, uses triangular
  control flow through policy, human approval and execution, and keeps the
  Governance and Executor + Tools group bounds separate.
- Approval identity and reason fields no longer rebuild the full graph on every
  keystroke.
- Human denial is a distinct `denied` graph and timeline state rather than an
  execution failure.
- `Exit workflow` intentionally clears the active browser workflow while
  preserving immutable recipes, approvals, outputs and evidence on disk.
- The final authoritative execution response still determines success or
  failure; progress polling cannot create a success claim.
- Progress snapshots are atomically persisted beneath
  `workflow-state/interface-executions/`, keyed only by the exact execution
  preview digest.
- A persisted `running` attempt with no matching live process is classified as
  `interrupted`; its active step is localized and the interface displays
  fail-closed recovery guidance.
- Denied human authority is rendered in red as an explicit stop outcome while
  retaining the distinct `denied` label instead of misreporting a failure.

## Security boundary

The progress endpoint accepts only a 64-character SHA-256 identifier. It does
not accept paths, commands, SQL, arbitrary artifact names, or request bodies.
It has no execution authority. Its only write is the bounded atomic progress
snapshot produced by the execution service itself.

## Remaining 17U work

Elapsed-time presentation, a durable run inventory, browser-session restoration,
and a separately approved retry workflow remain future increments. An
interrupted write is never automatically retried: the operator must inspect
outputs and durable evidence, select a fresh target where applicable, and create
a new approval.
