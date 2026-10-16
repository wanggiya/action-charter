# Checkpoint 26 closeout: conversational recipes and governed execution

## Delivered boundary

One conversation remains one private task. Opening it restores its latest validated
workflow without a model call. Planner discovers registered operations/recipes,
composes and revises the explicit graph, and drafts reusable definitions and small
synthetic fixtures. Recipe authoring is a module of Planner, not a separate Builder
reasoning role. Legacy Builder extension commands/imports remain compatible.

Backend services bind mechanical CSV output paths, expand recipes, check schemas,
paths, dependencies, contracts and authorization, and run isolated fixture tests.
Semantic choices (columns, filters, joins, database targets) remain explicit; the
system does not guess them. Explicit filenames are preserved. Previously occupied,
automatically assigned CSV outputs receive fresh paths on revision, without
reusing old approval. No files are created merely by planning.

Critic reviews candidate fixture findings and recorded execution observations.
Reusable-method suggestions are unvalidated advice. Registration is optional and
never a prerequisite for executing a task. Registration retests the exact candidate;
it neither installs a dependency nor grants operation authority.

The deterministic Execution engine follows reviewed dependency order. It has
durable step records, bounded previews, cooperative cancellation, restart
interruption detection and conservative recovery. Cancellation finishes the active
operation/verification boundary and skips later dispatch; it is not rollback.
Remaining read-only work can be proposed again. Write recovery prepares fresh
targets and requires fresh exact authority. No automatic write replay, parallel
execution, verified write-intermediate reuse or transactional resume is claimed.

## Model and service boundaries

- Ordinary chat retains bounded generation/correction. Recipe authoring uses one
  Planner call, at most one repair, and one sequential Critic candidate review.
- Normal interface execution requests one backend outcome assessment after durable
  completion. It survives closing the interface. Direct API/CLI callers opt in with
  `review_outcome: true` on `start`; the default remains no assessment call.
- Outcome review uses one bounded call (at most 15 seconds/1,024 tokens), caches its
  result and reports unavailable on failure. Explicit `assess` with
  `retry_assessment: true` retries assessment only, never processing. Interrupted
  assessments do not silently repeat model calls.
- Critic receives bounded status/count/column observations rather than complete
  transcripts or raw previews. A failed/stopped run cannot be labelled supported.
  Evidence is recorded observations, not proof that targets are still unchanged.
- Current-chat recipe evidence matches both conversation ownership and plan digest.
  Cross-chat retrieval/sharing is absent. Historical text, model assessments,
  summaries, recipe registration and installed libraries never grant authority.

API `/api/v1/reusable-recipes` and `/api/v1/workflow/runs` share services with CLI
`reusable-recipes` and `workflow-runs`, using `--request-file FILE --project-root DIR`.
Advanced forms remain optional inspectors; normal composition is conversational.

## Graph interaction follow-up

Wheel zoom is proportional to wheel/trackpad deltas and anchored at the cursor
within scroll limits. Shift+wheel pans horizontally. Zoom buttons share the camera
animation, with reduced-motion support. Drag uses the displayed scale, preserves
fractional coordinates and updates attached wires without full-interface frame
renders. Advanced recipe controls remain available; recipe headings/disclosures
match the outline edge gradient. Right-side action controls explicitly use the same
material; disabled header controls dim text/icons and borders while retaining
the gradient. Solid-fill styling and disabled behavior are unchanged.

Manual check: zoom around different nodes, reverse wheel direction, try small
trackpad gestures, then drag and release a node. Check attached wires, final position,
Fit, orientation and zoom buttons. Plan inputs/operations and authorization must not
change from these presentation interactions. Smoothness on the operator's laptop
still requires observation; automated checks do not establish a frame-rate target.

## Manual acceptance

Start using the existing `bash scripts/start_actioncharter.sh` launcher with the
configured model. Use the temporary/sample CSV fixture from the tabular examples;
these instructions assume `sample_orders.csv` with `region` and `amount` columns.
Do not substitute production database targets.

1. Open a new Planner chat. Send: “Clean sample_orders.csv: keep region and amount,
   and replace missing regions with Unknown.” Confirm input, operation order and
   fresh CSV outputs in graph/inspector. Planning must create no output files.
2. Send: “Make this current workflow reusable.” Check fixture findings and Critic
   review. Optionally register once; do not type JSON. Refresh: the same chat,
   workflow and candidate return without regeneration.
3. Review exact inputs/outputs, Authorize, then Execute. Check deterministic step
   validation and actual output rows. Critic appears separately; unavailable model
   assessment must not erase the completed execution or change its result.
4. Send: “Also group by region and sum amount.” Inspect the added aggregation and
   fresh output paths. Old files must remain intact. Reauthorize the new exact
   workflow, execute, and compare totals against the source data.
5. Reopen Execution History. Inspect intermediate previews. For a longer fixture
   workflow, Cancel during processing: later steps must not start. Recovery must
   identify incomplete work and require fresh authority for writes. Restarting
   must never silently replay an interrupted operation.

Source-contract follow-up: argument schemas now explicitly require exactly one original
path or CSV-producing ancestor. Conflicting proposals receive step-specific repair
feedback; ambiguous sources are never silently chosen.

A model may still fail or time out on a small laptop; deterministic fixture
acceptance does not establish local-model quality. Report the structured error and
preserved workflow rather than weakening validation to accept a proposal.

## Verification and next checkpoints

Backend full suite: **1,625 passed**. Frontend typecheck/build passes (existing
bundle-size advisory remains). Automated browsers use isolated temporary profiles,
fixture model replies and real shared backend CSV execution; no personal browser
cache, external model or live GIS/database is used. Initial closeout browser acceptance: **27 groups passed** (5 conversational Planner/recipe,
6 recipe/cancellation/recovery/restart, 10 private-chat/helper, 6 CSV). All report
zero page errors and zero live-service calls. The camera follow-up reran the expanded
Planner browser suite: **6 groups passed**, including proportional zoom, cursor
anchoring within scroll limits, fractional dragging and outline material. Backend
remains **1,620 passing tests**; frontend typecheck/build passes.

Checkpoint 26 closes this bounded orchestration/private-chat/recipe delivery.
The earlier indexed-memory/curator proposals remain design history, deferred to
28–29 after evaluation; experimental private method notes remain OFF by default.
Checkpoint 27 covers laptop/model evaluation, charts/maps, example/demo journeys
and prototype installation/release preparation. Cross-chat memory stays at 30 or
later and requires a fresh decision. No platform parity or release readiness is
implied; no Git publication or live-service mutation is performed here.

## Agent-container CI follow-up

Push and PR checks exposed the same CLI startup failure: importing a conversation
CLI adapter initialized the interface server and GIS dispatcher, requiring
`geopandas` in the lightweight agent image. Interface public exports now load lazily;
CLI help, three manifest inspections and recipe-template catalog retain their
existing dependency boundary. Fresh-interpreter tests block GIS imports explicitly.
Verified: all five GIS-blocked startup contracts, existing API compatibility tests
and the full backend suite (**1,625 passed**). Full image verification still
requires a running Docker daemon or the next CI run; no daemon is running locally.
