# Checkpoint 20 — verified authority and evidence graph

Checkpoint 20 projects existing durable records into read-only flow graphs. Opening or refreshing a graph never approves, executes, records a Critic decision, or creates a release. The workflow remains Plan → Flow graph → Run → Check outcome, with detailed records in Advanced.

## What the graph connects

| Source | Relationship shown | Required check |
| --- | --- | --- |
| Saved plan | Plan decision | Canonical plan digest, exact required steps, decision and current expiry |
| Saved recipe | Saved Planner definition | Reconstruct the recipe from one canonical saved Planner result and compare the exact recipe digest; this proves definition equivalence, not the historical creation event |
| Saved recipe | Recipe decision to defined execution | Reverify recipe digest, complete approval scope, decision and expiry |
| Durable run | Decision to execution | Reverify the recorded recipe and approval identity at the attempt's start time |
| Durable run | Result and evidence | Load the canonical run result and recipe evidence, compare their digests, nested identities and final status |
| Durable run | Recorded output | Show at most 20 paths and stored digests from verified recipe evidence, connected to recorded producer steps |
| Durable run | Stored trace and report | Require one exact run candidate and compare the stored trace and report to the adapted evidence |
| Stored trace and report | Critic result | Verify a canonical Critic record against current trace/report evidence and references |
| Critic result | Immutable release | Verify the release package and exact component paths and hashes |

Missing, denied, expired, ambiguous, altered or legacy records do not gain a verified edge. The plan-to-recipe edge appears only for a matching Planner-derived definition. Other recipes can still be inspected without that edge. Recorded output digests describe the result at execution time; opening the graph does **not** freshly hash physical output files. The trace, Critic and release blocks appear on a durable run only when the bounded read-only Assurance inventory verifies each relationship.

The graph selector offers a current unsaved plan, saved plans, saved recipes, durable runs and separately exported validated traces. Refresh after storing or recording evidence. The primary graph and timeline emphasize status; full digests remain in expandable audit details. At wide desktop widths, Plan, Flow graph, Run and Check outcome share the top bar. At narrower widths they occupy a second row, and short graph windows scroll to keep the timeline reachable.

## Validate in the WSL checkout

1. Apply the cumulative checkpoint files, restart the local interface API, then run `.venv/bin/pytest -q tests/test_interface_api.py`, `make test`, and `make interface-validate`.
2. Open Flow graph, refresh sources, and select a saved plan and its matching saved recipe. Inspect exact verified or blocked decisions. For a Planner-derived recipe, check the definition-match connection; a manually created recipe need not have one.
3. Select a completed durable run. Check run-start authority, result status and recorded output nodes. If an exact trace/report, Critic result and release exist, the linked blocks should appear in order. Older runs can show unavailable links.
4. At 1920 × 1080 and a half-width window, check the navigation placement, minimap, inspector and reachable timeline. Selecting a graph source must not execute anything.

The Python tests and live browser acceptance require the operator's WSL environment with the project's virtual environment and durable evidence. This package was built and syntax-checked in the scratch workspace; its Python suite could not be run there because test dependencies were unavailable.
