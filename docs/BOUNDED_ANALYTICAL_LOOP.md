# Bounded analytical conversation and flexible-role handoff

## Latest proposed follow-up — 2026-10-25

[Executor sandbox/workspace structure](EXECUTOR_SANDBOX_WORKSPACE_PLAN.md) and
[comprehensive inspection/Outcome requirements](COMPREHENSIVE_DATASET_INSPECTION_PLAN.md)
preserve the latest discussion and next implementation order. They extend this task;
they do not claim container isolation or comprehensive profiling already works.


Implemented slice: 2026-10-25. This extends the
[full data-science task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md); it does not complete
statistics, sampling writes, capability learning or a multi-agent server deployment.

## Graph and information integration — follow-up delivered

[Recorded analytical graph](ANALYTICAL_GRAPH_AND_INSPECTOR.md) now visualizes saved
inputs, actual tool calls and findings, with node-specific information. It restores
without replay, preserves executable plans and labels advisory versus computed evidence.
This extends the original chat-only evidence view; no new execution authority is added.

## User journey and current delivery

Place source, codebook and existing samples under data/input/test. This folder was
empty at implementation time; original files elsewhere were not moved or modified.
In a new chat, ask:

```text
Explore the data in data/input/test. Identify the main dataset, codebook and any samples. Assess whether full-source profiling is feasible. Summarize data quality and propose useful next analyses. Do not write files.
```

The conversation now has a separate bounded analytical action contract, rather than
asking the small model to generate a general workflow with every operation schema.
It discovers files, asks the model to assess a source, requests a typed profile when
eligible, then requests a short evidence-based explanation. Model choices select paths,
operation assessments and analytical parameters; the backend validates them and computes.
The current action stages constrain redundant assessments and unsupported actions.

Read-only discovery/analysis on this explicit exploration request does not require
Execute. Normal workflow proposals and writes retain their existing paths. An existing
workflow is preserved. The receipt states that exploration occurred, rather than
incorrectly claiming that no source was read. No workflow run or approval is dispatched.

Analytical evidence beneath the chat response shows files, operation feasibility,
complete-source coverage, computed profiles, distinct counts, checks and the tool journal.
It is collapsed by default to conserve space. These facts are separate from model
interpretation. Refresh restores the saved session without model calls or repeated reads.

Supported continuation prefixes: “Continue exploring”, “Explore further”, “Summarize
these findings”, “Explain these findings”, “Compare these groups”. These reuse only this
chat's scope and historical summary, with new verified reads before fresh measurements.
A new explicit folder exploration starts a fresh source-binding session. Other messages
retain normal Planner behaviour; arbitrary natural-language follow-up recognition is
not claimed. A new chat does not inherit another chat's analytical evidence.

## Services, tools and roles

```text
Chat / CLI / external MCP-capable agent
                  |
          analytical role adapter
                  |
       bounded action loop + model client
           |          |          |
     discover      assess      profile
           \          |          /
           shared validated read services
                      |
      observations + source hashes + tool journal
                      |
       model explanation / saved evidence display
```

- tabular/strategy.py owns directory discovery and operation-specific assessment.
- tabular/analyst.py owns the role-neutral model/tool loop. It is independently callable
  from CLI and the conversation adapter; no dedicated agent container is required.
- MCP exports discover_inputs, assess_table and the existing typed profile_table. The
  in-process conversation calls the same services directly; it does not require a
  separate MCP HTTP server or duplicate calculation engine.
- CLI exposes discover-inputs, assess-table and explore-data, plus existing profile-csv.
- Conversation persistence, revision leases, selected model and workflow authority reuse
  existing services. The analytical role has no write/install/approval/network-search tools.

MCP publishes callable contracts, not an autonomous skill store or a trained model.
An operation's existence does not grant execution authority. Tools and their scope are
independent of which actor is assigned a semantic role.

## Strategy and sample semantics

Discovery examines one normalized input directory, at most 200 entries and 40 supported
files. It follows no symlinks, recurses nowhere, skips hidden files and exposes no raw
rows. Up to eight CSV headers receive bounded probes (at most three seconds each within
an approximately 20-second discovery budget). Non-CSV files are listed; this first loop
only calculates CSV/TSV profiles. Use existing spatial workflow tools separately.

A special metadata-only strategy probe can inspect bounded headers of files exceeding
1 GiB. Ordinary discovery/full inspection retain their existing limits. A successful
header probe is never full-file verification or evidence that an operation will fit.

Assessment differs by operation:

- profile/quality/group: full-source streaming eligible up to the current 1 GiB byte
  limit, subject to actual time, cardinality and memory enforcement during execution.
- existing dataframe transforms: 8 MiB byte limit and 10,000-row runtime limit. Metadata
  assessment does not yet know the row count and cannot certify actual success.
- statistical_model: unavailable; no fit is invented or attempted.

A possible sample is a filename hint. Matching headers are recorded as schema-compatible
candidates, with provenance and representativeness still unverified. An eligible complete
source is preferred; the model must explain any provisional sample scope. No population
extrapolation or full-source totals may be inferred from a sample.

Sample creation is **not implemented in this slice**. If an operation needs an alternative
and no usable sample exists, report that missing capability. A later sampling adapter must
record source identity, method, size, seed and encounter-versus-patient unit, produce a
normal write proposal, and require Allow writes → Authorize → Execute. Do not ask the user
to approve a supposedly executable sampling operation before it is actually registered.

## Budgets, evidence and failures

Each turn: up to five model calls, six tool calls including batched discovery, 150-second
loop budget, per-model timeout at most 30 seconds, model output cap at most 1,200 tokens
and the configured model cap. Requests cap 30 KB and observations 22 KB. Header probes
are bounded subreads of one discovery invocation. Existing profile worker/resource and
response limits remain authoritative. These are bounded operations, not unlimited dataframes.

Profiles passed to the model omit raw previews and individual category examples. The
model gets selected aggregate profiles and at most 20 grouped summaries. Individual-ID
grouping is blocked; coded identifier groups require a supplied codebook. This is data
minimization, not a guarantee that arbitrary aggregate labels are anonymous.

Explicitly named mean/distinct statistics cannot silently disappear from the tool request.
Null numeric statistics mean not requested, not proof that a column is non-numeric.
Final explanations are short and advisory. Narrow checks reject invented measurement units
and unsupported claims that an unverified sample is biased/not representative; these checks
are not a general factual verifier or a substitute for later Critic/domain validation.

Invalid action JSON receives a bounded correction. A repeated identical read is blocked.
Timeouts are not retried automatically. Discovery and completed results remain saved even
when the explanation fails; partial is distinct from completed. Runtime worker reads enforce
remaining deadlines. Interactive cancellation of the conversation loop and live incremental
streaming of its journal remain follow-ups; the current UI receives the final/partial record.

## Verification and honest limits

Synthetic tests cover operation-dependent strategy, oversized-header versus full-read
limits, directory boundaries, symlinks, sample uncertainty, explicit statistic coverage,
identifier blocking, tool failures/timeouts, action budgets and refresh without rereads.
An isolated browser journey covers the new conversation/evidence/refresh path alongside
existing quality/group/export and failure recovery. No shared browser cache or download.

scripts/analytical_strategy_acceptance.py copies the existing real source, 5,000-row
sample and mapping file to a temporary project. It compares independent CSV counts,
checks schema compatibility without certifying provenance, and verifies that full-file
profiles and dataframe transforms receive different feasibility decisions. Originals
and live services remain unchanged. It makes no model calls.

Actual small-model trials use only a temporary synthetic 5,000-row file. Initial trials
omitted numeric/distinct arguments, repeated assessments, invented units/sample claims,
and timed out. These exposed real contract/interaction gaps and led to stage-specific
schemas, argument coverage and claim guards. Final synthetic qwen3:4b-instruct trial passed: 5,000 source rows, 2,500 distinct
patients, mean stay approximately 3, calibrated summary, three model calls and three
tool calls in about 21.1 seconds (maximum prompt approximately 7.6 KiB). Earlier failed
trials remain part of the evidence; this is not broad small-model reliability or a
same-task performance comparison. Reproduce explicitly with
`.venv/bin/python scripts/analytical_loop_model_evaluation.py --model qwen3:4b-instruct`.
Full make test passed 2,083 tests with 13 existing Rasterio warnings. Final focused
strategy/loop/discovery/security checks passed 40 tests; subsequent source-target
binding checks passed all 11 analytical-session tests. Frontend validation and isolated
browser conversation/evidence/refresh journey passed with zero page errors.

## Flexible agents and Linux-server testing — future sequence

The user clarifies that Planner, Executor and Critic are roles. After this data process
works, actors may take several roles to finish a whole task, or cooperate in groups.
Role assignment can vary experimentally, including randomized assignments among actors
that support the required contracts. Assignment never changes tool permissions or scope.
No such scheduler or multi-agent deployment is added here.

1. Stabilize the single-actor data journey and analytical correctness first.
2. Define role input/output contracts and one lifecycle owner per task. A shared actor
   can plan, invoke services and critique; specialists use the same contracts.
3. Add structured handoffs: task/session ID, role/actor identity, parent action ID,
   objective, source hashes, evidence references, proposed next action, uncertainties,
   budget and cancellation state. Share bounded references rather than full transcripts.
4. Separate recommendations from verified facts and permissions. Track revisions,
   acknowledge receipt, reject stale results, deduplicate dispatch and preserve partial
   outputs. A Critic opinion or agent message cannot authorize a write/retry.
5. Compare one actor versus grouped actors on identical tasks/models: correctness,
   time, calls, memory, interventions, recovery and communication overhead.
6. Test in an isolated simulated Linux-server environment: temporary data/state volumes,
   resource quotas, model connectivity, concurrent sessions, restart/interruption and
   cancellation/recovery. Reuse existing launcher/package boundaries after inspecting
   deployment support. No live PostGIS/GeoServer mutation or release/publication.

This role/communication work is recorded as follow-up, not an excuse to add agents before
one successful journey. Knowledge/memory architecture and RL remain separate decisions.
