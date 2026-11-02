# Checkpoint 28.2 — execution interaction and paired evaluation

## Delivered behavior

- Normal read-only CSV/vector/raster inspection runs from one header Execute
  click. The interface prepares the exact backend review internally and starts
  a durable run without an authorization action or Allow writes. Ordinary
  read-only plans do not show the Authorize button.
- Write workflows retain Allow writes -> Authorize -> Execute. Authorize records
  exact scope and never dispatches operations. Execute re-prepares the review,
  checks the matching authorization and lets the backend recheck current policy.
- A changed chat, saved-plan identity or pending edit during preparation blocks
  continuation. Repeated header clicks cannot start concurrent preparations.
- Registered access/gates determine the normal toolbar presentation; backend
  review is authoritative. Unknown operations are not assumed read-only. Historic
  deliberately stricter approval gates are preserved, not silently removed.
- Allow writes does not authorize overwriting. CSV transforms still require
  fresh output paths; arbitrary replacement is not implemented by this change.
- Recommendation receipts include policy version, matching operation contract,
  recorded check counts, baseline/supplied recipe ordering and whether ordering
  changed. They explicitly say model adoption is not measured. Malformed stored
  observation classifications fail back to baseline instead of becoming scores.

Planner still handles interpreting requests, composing registered operations and
optional capability preparation. Backend allocates omitted fresh CSV paths,
checks typed dataflow and gates, runs the approved dependency sequence and checks
outputs. No additional agent, model training or manual JSON authoring is added.
This improves routine automation without interpreting chat text as authority.

## Paired evaluation protocol

`scripts/checkpoint28_paired_evaluation.py` shares existing conversation, review,
authorization, runtime write-policy, durable execution and output-check services.
All sources, outputs, evidence and authority are under a disposable project.
Live databases/services and the operator's project data are not used.

Fixed cases:

1. CSV metadata and bounded preview.
2. CSV column selection, preserving identifiers.
3. Numeric row filtering.
4. Calculated numeric column, preserving originals.
5. Vector feature metadata and CRS.
6. Vector attributes -> CSV -> grouped regional sums.

For each case a fixed training workflow is actually executed and checked with a
fixture Planner. That project, including the same private chat, latest workflow,
transcript and versioned check evidence, is cloned for the paired runs. The
new-input fixture has changed identifiers/values. ON/OFF changes only the
recommendation preference. Both runs use identical selected operation scope,
request, model settings and source bytes. Existing own-chat successful-method
retrieval is available to both; this is an incremental ranking comparison, not
memory versus no memory. Acquisition/helper actions are not enabled.

Run order alternates across cases and repetitions. No failed model request is
retried outside the existing bounded correction/discovery budget. Output checks
are independent of the model's narrative and supplement runtime validation.
Unexpected operation IDs, wrong original input and redundant step counts stop
the harness before execution. The available test operations exclude databases.

For writes the harness checks writes-OFF denial and missing-authorization denial
before issuing fresh, explicit temporary-fixture authority. It never reuses seed
approvals. Read-only cases require no scripted authorization. Reports distinguish
scripted test authorizations from human intervention; they are not a claim that
production writes require no user decision.

Reports record valid plans, correct outputs, failures, correction attempts,
model calls, available token counts, wall time, supplied recommendations, input
hashes and case order. Fixture-mode results are explicitly labelled harness
self-tests. Model mode records its settings; a small local trial cannot establish
broad reliability or causation. Background load and model warmup can affect timing.

Predeclared threshold: all six cases, at least two repetitions, all expected
results and safety checks passing, no paired correctness regression, more correct
results or fewer model calls, and ON elapsed time <= 1.20 times OFF. Passing the
harness alone or one repetition cannot establish model benefit. Runtime remains
optional OFF when this threshold is not demonstrated. No exploratory writes or
weight training are performed.

Run the fixture harness with:

    .venv/bin/python scripts/checkpoint28_paired_evaluation.py

An actual-model run additionally accepts `--model`, `--timeout`, `--max-tokens`,
`--repetitions` (1–3), optional `--case`, and an explicit report `--output` path.
The default report is under /tmp, outside Git. No models are installed/downloaded.

## Manual frontend acceptance

Restart the existing launcher and refresh. In a new chat paste:

    Inspect sample_orders.csv. Return row count, column names and a bounded
    preview. No writes.

Confirm the plan contains inspection only. Leave Allow writes OFF. Click the
header Execute once: Outcome should open without an Authorize action. Inspection
completion alone still adds no independently verified transformation check.

Then paste in the same chat:

    Keep the inspection. Select order_id and region from sample_orders.csv
    into a fresh CSV. Preserve the original file. Prepare without executing.

Execute must remain unavailable before authorization. Enable Allow writes,
click Authorize, review the displayed scope and record the decision. No output
should be created yet. Click Execute; check selected columns and passed output
validation. A subsequent related message with recommendations ON can display
those checks in the existing recommendation disclosure. No restart is needed
to change supported runtime write availability.

Remaining learning acceptance depends on the actual model results. Do not claim
that rankings improve general planning, that all library functions are executable,
or that the full pre-demo gates/advanced knowledge work are complete.

## Initial actual-model comparison (before the follow-up decoder fixes)

Installed `qwen3:4b-instruct`, reasoning effort none, temperature 0, 1024 output
tokens, 90-second model timeout, one repetition. Temporary CSV and GeoJSON data
only. Report: `/tmp/actioncharter-checkpoint28-paired-before-typed-fix.json`.

| Metric | Recommendations OFF | Recommendations ON |
|---|---:|---:|
| Correct task results | 3/6 | 2/6 |
| Valid complete proposals | 3/6 | 2/6 |
| Model calls | 10 | 10 |
| Turns requiring correction | 4 | 4 |
| Elapsed seconds | 337.457 | 395.012 |
| Reported prompt tokens | 46,113 | 48,429 |
| Reported completion tokens | 2,413 | 2,875 |

Both sides completed CSV/vector inspection. Filtering completed only with OFF.
Selection on both sides and filtering ON mixed workflow actions with replacement
operations. Calculations omitted the requested operation. Combined workflows
copied occupied prior output targets. All rejected proposals were blocked before
a task execution; the successful filtering write used fresh exact authority.
The scripted comparison needed zero manual repair, but that does not mean it
completed the failed tasks. It issued one evaluation authorization, excluding
training setup.

This is negative evidence for enabling ranking by default. One trial cannot
establish broad failure rates, causation or stable timing; some early verification
work overlapped this exploratory run, and model warmup/background load were not
controlled. It does not satisfy the two-repetition benefit threshold. Failures
remain in the report rather than being silently retried or omitted.

## Follow-up fixes

Ordinary supplied tabular operations now reuse their existing typed argument
models in the decoder, including exclusive original-path/intermediate-source
choices. This also enables the existing closed full-proposal versus exchange
boundary for selection/filtering, which previously bypassed that decoder path.
The simple calculation guide supports an existing two-operation inspection and
calculation workflow; arbitrary larger workflows retain the general path.

When the latest user request explicitly asks for fresh CSV outputs, an inherited
occupied CSV target can be allocated a fresh UUID proposal path if that filename
was not explicitly named in the request. Original files and authority are never
changed. Explicit filenames, non-fresh/negative requests and non-CSV resources
are not automatically replaced. This extends mechanical output allocation;
it is not overwrite permission or a generated fallback workflow.

## Additional request and source checks

Explicit CSV selection/filtering requests now have narrow operation-coverage
checks. A replacement consisting of repeated inspections cannot be saved as a
complete answer to those commands. Negated/removal requests and selecting a file
are not interpreted as instructions to add a table operation. Concrete missing
semantic choices can still produce a clarification rather than a partial plan.
These are limited command recognizers, not a proof of arbitrary prose intent.

Simple inspection-plus-selection/filter requests focus descriptive schemas while
retaining the full registered allowlist. With one explicit source they bind the
original CSV and dependency in the existing decoder guide. Compatible simple
vector attribute/sum-grouping requests receive the same source/dependency guide,
including automatic skill selection. Prior filenames cannot silently replace an
explicitly supplied new source. Model arguments and all proposed operations still
pass the authoritative validators. No executable fallback plan is fabricated.

## Intermediate rerun and oracle correction

The intermediate report is preserved at
`/tmp/actioncharter-checkpoint28-paired-intermediate.json`. Its raw tally was
OFF 3/6, ON 4/6, six calls each. These tallies are **not a clean benefit comparison**:
both filtering runs completed with an extra final inspection, and the first
oracle incorrectly assumed the final step held a CSV artifact, raising KeyError.
Their independent CSV checks were therefore incomplete; expired temporary
fixtures were not retroactively marked correct. A regression now verifies the
producer-based oracle. The harness reports extra read steps separately, rejects
unexpected/repeated writes and locates the actual requested producing operation.

That rerun completed both calculation cases and the ON combined case. It also
exposed omitted selection operations and a historical-source substitution in
combined OFF; the later explicit coverage/source guides address those findings.
The raw intermediate report remains unchanged. Focused post-fix cases must be
labelled as focused regressions, not combined into a synthetic six-case score
across different code revisions. No general speedup or RL benefit is established.

## Verification

- Full backend suite: 1,901 passed. A subsequent calculation-only scope boundary
  adjustment passed both focused regression cases; it keeps that workflow on
  its existing general path rather than inserting an unrequested inspection.
- Frontend typecheck and production build passed; the existing bundle-size
  advisory remains.
- Browser journeys passed: execution paths 4 cases, acquisition/settings 9 cases,
  Results workspace 17 cases. No page errors or live database/service calls.
- Fixtures cover all six paired tasks with actual temporary execution, fresh
  authorization and independent output checks. They are not model benchmarks.
- Historical status body remains intact and CURRENT_STATUS stays under 128 KB.
- No dependency downloads, Git mutations, live database changes or publication.

## Final focused actual-model regression

After the explicit coverage/source guides and producer-oracle fix, the same
installed `qwen3:4b-instruct` profile was run on selection, filtering and the
combined vector-to-table workflow, one repetition. Report:
`/tmp/actioncharter-checkpoint28-paired-model.json` (three cases, not six).

| Metric | OFF | ON |
|---|---:|---:|
| Correct independent task results | 3/3 | 3/3 |
| Model calls | 3 | 3 |
| Correction turns | 0 | 0 |
| Extra read steps | 0 | 0 |
| Elapsed seconds | 140.704 | 125.704 |
| Reported prompt tokens | 13,935 | 14,671 |
| Reported completion tokens | 976 | 884 |

All six paired executions used fresh exact temporary-fixture authorization,
passed writes-OFF/missing-authority checks, and produced independently checked
results from the new original inputs. No manual intervention or live-service
calls. The final focused profile had no intentionally concurrent full-suite or
browser workload; background load and model caching still limit timing claims.

This verifies these concrete regressions after the fixes. It is not a replacement
six-case benchmark, is not pooled with older revisions, and does not meet the
predeclared six-case/two-repetition benefit threshold. Both modes were correct
with the same call count. Recommendation ranking therefore remains experimental
and OFF by default; no general speedup, learning advantage or model adoption is
claimed. Broader pre-demo model/knowledge acceptance remains open.
