# Composition, implementation and agent structure

Discussion recorded 2026-10-27; documentation only. Complements the
[consolidation plan](GENERALIZATION_AND_CONSOLIDATION_PLAN.md).

Clarification after repository/history inspection: the legacy Builder already proposes
Python implementation artifacts and supports an explicit extension lifecycle. The
proposed addition is conversational analytical execution/qualification/reuse, not the
first code generator. See [reuse and integration](BUILDER_REUSE_AND_CAPABILITY_INTEGRATION.md).

## Composition is parameterized execution, not a fixed age example

Existing tabular contracts are in `src/geoagent_harness/tabular/schemas.py`.
Its `ARGUMENTS` mapping includes inspect, select, filter, missing-value handling,
join, aggregation, restricted calculations, export, codebook decoding and vector
attribute extraction. `operations/registry.py` combines these with spatial,
database and other operation contracts. `recipes/dispatcher.py` validates and
dispatches workflow steps to the implementations; `tabular/service.py` performs
the tabular work. A Markdown skill supplies guidance, not the computation itself.

For aggregation the current contract has `by: list[str]`, and aggregations with
`column`, `function` and `output_column`. Supported aggregation functions here are
sum, mean, min, max and count. The in-memory implementation groups by `args.by`;
there is no hard-coded age field. Streaming aggregation has its own supported path.

Example operation arguments, using fictional input/output names:

```json
{
  "path": "data/input/encounters.csv",
  "by": ["age"],
  "aggregations": [
    {"column": "time_in_hospital", "function": "mean", "output_column": "mean_stay"}
  ],
  "target_path": "data/output/mean_stay_by_age.csv"
}
```

The same operation can use `by: ["region", "asset_type"]` and calculate mean
`inspection_cost` on an unrelated compatible asset table. Column names are actual
schema-bound data values, not Python expressions or invented semantic placeholders.
Unknown columns reject; successful execution does not establish that the chosen
grouping or statistic is scientifically appropriate. Computing/saving this CSV is
a write. A read-only analytical grouping instead uses supported inspection analysis.

Composition means selecting these implemented capabilities, supplying parameters
and connecting their outputs/dependencies. It is richer than changing one groupby
argument, but limited by available contracts. No arbitrary pandas function becomes
available merely because pandas is installed. A restricted expression tree is a
middle ground between fixed parameters and arbitrary Python.

Implementation means generating new executable logic, such as a Python program,
when existing operations cannot express the method. That optional capability is
proposed, not delivered arbitrary Python execution. It needs worker isolation,
resource limits, provenance and result checks. Prefer tested composition for solved
tasks; do not automatically register a successful one-off program as a reusable tool.

## One agent versus role contexts

An agent context is not synonymous with a model, container or single model call.
Single mode uses a primary context for planning, work-order checking and outcome
self-review. Three mode uses Planner, Executor preflight and Critic contexts,
sequentially using the configured model. Fixed services perform the operations.

| Criterion | Single context | Separate role contexts |
| --- | --- | --- |
| Effort | Less handoff overhead for supported tasks | Additional calls/context preparation |
| Continuity | Full task context stays together within its limits | Handoffs can omit details |
| Review | Can remain anchored to its own interpretation | May expose assumptions through focused review |
| Quality | Depends on evidence and checks | Not guaranteed independent; same model can repeat errors |
| Laptop resources | Simpler coordination | Sequential operation avoids simultaneous model copies, but adds latency |
| Authority | Shared deterministic controls | Identical controls; extra agents do not grant stronger permissions |

Proposed Auto starts with one primary context and requests named, bounded assistance
when uncertainty, novelty, separable work or verification gaps justify it. Keep explicit
Single/Three selection. Evaluate cost and verified outcomes; tokens alone and workflow
length do not establish difficulty. Automatic routing is not implemented yet.

## Current project responsibility graph

```text
USER
  |
  +-- Frontend --------+
  +-- Terminal / CLI --+--> Python application entry points
  +-- MCP client -----+                |
                       +--------------+----------------+
                       |                               |
              Conversation / task state        Operation / package discovery
                       |                               |
                       +--------------+----------------+
                                      |
                               Task coordinator
                                      |
                   +------------------+-------------------+
                   |                                      |
             Single context                         Three contexts
             Primary planning                       Planner
             Work-order self-check                  Executor preflight
                                                    Critic preflight
                   |                                      |
                   +------------------+-------------------+
                                      |
                          Typed workflow and policy
                                      |
                         Exact execution preparation
                                      |
              Read only: Execute / Writes: Allow writes, Authorize, Execute
                                      |
                             Execution services
                                      |
                    +-----------------+------------------+
                    |                 |                  |
                 Tabular           Spatial        PostgreSQL / PostGIS
                    |                 |                  |
                    +-----------------+------------------+
                                      |
                         Local / configured worker execution
                                      |
                        Verification and durable evidence
                                      |
                    Primary self-review / separate Critic outcome review
                                      |
                          Reports, tables, charts, maps, history
```

This is a responsibility map, not proof that all entry-point actions already share
one internal implementation. Consolidating duplicated paths is planned. Narrow
deterministic inspection can bypass model planning. Not all registered operations
are necessarily exposed as individual MCP tools; coverage must be checked.

Ollama supplies model responses; it does not grant authority. Docker can host
workers and database services, not necessarily one container per agent. Persistent
stores retain conversations/plans/runs; history is evidence/context, not permission.
Tests and acceptance scripts verify the platform; they are not production agents.

## Proposed flexible capability path

```text
Relevant capability retrieval
             |
       Can existing skills / operations express the task?
             | yes                          | no
       Compose workflow              Optional generated Python task
             |                              |
             |                       Isolated worker and checks
             +---------------+--------------+
                             |
                  Shared evidence and result presentation
                             |
                  Candidate method reuse only after qualification
```

The shared runtime should not be copied for the code path. Generated code must not
receive unrestricted files/network/database credentials, and must not bypass normal
authorization for retained outputs or live data changes. No such new execution
capability is implemented by this design document.
