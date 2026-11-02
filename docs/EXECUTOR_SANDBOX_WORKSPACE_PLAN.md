# Executor-managed sandbox workers and analytical workspace — proposed

**Implementation update — 2026-10-25:** the CSV/TSV profiling, shared typed tool,
Docker job pilot, recorded graph and interactive Outcome portions are implemented.
See [delivered scope and acceptance](COMPREHENSIVE_INSPECTION_DELIVERY.md) for tested
boundaries and remaining limitations. The original design below is preserved history;
it is not evidence that every planned operation or future sandbox adapter is complete.

## Docker versus MicroVM clarification — 2026-10-25

Docker is the initial worker backend. MicroVM is a later isolation option, not a claim
of smaller size than a container: containers share the host kernel; MicroVMs add a
guest kernel and virtualization lifecycle. Image size depends on packaged dependencies.
“Micro” compares with traditional VMs. Evaluate stronger containment against resource
and deployment costs; neither runtime proves security without boundary tests.


## Latest scope clarification — integrated delivery

[Real-data frontend delivery](REAL_DATA_FRONTEND_DELIVERY_PLAN.md) is the latest
coordinated scope/order. It includes the Executor Docker worker together with typed
comprehensive profiling, agent behaviour, graph and interactive Outcome. This document's
technical requirements remain relevant; its earlier standalone ordering does not replace
the complete user-facing acceptance target. All additions remain planned, not delivered.


Recorded 2026-10-25 from the operator discussion. **Design only.** This update does
not implement a worker launcher, build an image, start a container/MicroVM, install a
dependency, process data or change live services. Preserve existing user changes and
checkpoint history. No Git staging, commits, pushes, merges or publication.

Read with [comprehensive inspection requirements](COMPREHENSIVE_DATASET_INSPECTION_PLAN.md),
[the analytical loop](BOUNDED_ANALYTICAL_LOOP.md) and the
[full diabetes task](DIABETES_EXPLORATORY_ANALYSIS_TASK.md).

## Operator decisions and boundary

Planner, Executor and Critic are responsibilities, not necessarily separate agents or
containers. One compatible actor may take several roles; groups can share responsibilities
later through explicit contracts. Sandbox-worker management belongs to the Executor
responsibility, implemented through reusable backend services. A worker is a calculation
runtime, not another reasoning agent or competing Executor.

Reusable code/services and an isolated runtime are complementary. A helper module, job
folder, process boundary or service name does not prove operating-system isolation. The
calculation must actually run in a restricted container/MicroVM, and boundary tests must
pass before claiming that guarantee. Merely placing every service in one container does
not establish per-job isolation.

Initial direction: hardened Docker workers, with a runtime interface that could support
MicroVMs later. Do not implement both backends at once. Reuse images and operation code;
initially allocate a fresh calculation environment per job rather than pool live workers.

## Before — inspected implementation

```text
Frontend / CLI
   |
   +-- Planner / analytical reasoning
   |       |
   |       +-- Shared discovery / assessment / profile services
   |                     |
   |                     +-- Local resource-bounded Python subprocess
   |                                   |
   |                              Input data reads
   |
   +-- Governed workflow execution services
             |
             +-- Scope / approval validation
             +-- Supported operation dispatch
             +-- Output validation and durable evidence

Optional container/MCP route
   Deterministic Executor service
             |
   Approval-gated composite MCP tools
             |
   Recipe / calculation services
```

The local interface launcher does not start containers. The analytical path currently
uses local subprocesses with path/resource controls, not a fresh per-job container.
Compose defines agent/tool/testing containers, but this does not make the local path
containerized. In particular, the executor Compose command is `agent-info executor`;
starting it alone does not create a continuous execution coordinator. The independent
Executor implementation uses deterministic_mcp_runtime and approved composite MCP calls.

The MCP tool container has broader input/output mounts and backend credentials/network
access for supported operations. Do not treat it as a generic untrusted scratch sandbox.
Existing containers and services must be audited/reused where appropriate rather than
silently bypassed or copied into another competing execution system.

## After — proposed structure

```text
Frontend / CLI / MCP caller
             |
Agent runtime: one actor or cooperating actors
Planner / execution reasoning / Critic roles
             |
        Typed operation request
             |
+-- Executor subsystem ---------------------------------------+
| Execution controller                                       |
|   scope / required authority / lifecycle / scheduling       |
|                       |                                    |
| Sandbox and workspace manager                              |
|   approved image / selected inputs / quotas / job identity  |
|                       |                                    |
| +-- Job-specific Docker or MicroVM boundary --------------+ |
| | Fixed supported operation + validated parameters       | |
| | Selected inputs read-only                              | |
| | Private scratch writable within a hard storage limit   | |
| | CPU / memory / processes / time / network restrictions  | |
| +--------------------------------------------------------+ |
|                       |                                    |
| Result validation / artifact registration / evidence        |
+------------------------------------------------------------+
             |
Recorded results for agent explanation / optional Critic review
             |
Conversation + graph + results workspace
```

Controller/manager services may themselves be containerized. Calculation jobs still
need their own enforced boundaries. Agents and calculation workers receive no Docker
socket or manager credentials. The manager is trusted infrastructure and must validate
launch parameters rather than proxy arbitrary container commands from the model.

LLM reasoning normally stays outside calculation workers so it can use its configured
model service without giving workers network access or loading a model per job. A future
LLM-assisted execution role can explain failures/propose recovery; deterministic services
still enforce permissions and dispatch. No model text authorizes writes or retries.

## Before and after workflow

```text
BEFORE
Question -> tool selection -> validate arguments
         -> local subprocess / existing service calculates
         -> record and validate results -> explanation and UI

AFTER
Question -> typed tool/operation selection
         -> validate scope, feasibility and required authority
         -> allocate job workspace and constrained environment
         -> worker calculates using selected bound inputs
         -> validate outputs and register artifacts/evidence
         -> explanation and UI
         -> stop worker and expire/clean eligible scratch
```

For samples/exports, approved user-visible writes are an explicit gate before dispatch.
Read-only inspection may use declared internal scratch under application policy; this
must not become a way to create retained datasets without the normal write process.

## Proposed contracts and ownership

Define contracts before adding a general container launcher. Final names follow the
repository's existing registry/execution conventions.

A validated job request needs job/task/conversation identity, operation ID/version,
typed parameters, bound input artifact IDs/digests, effects, approved output scope when
needed, resource budget, runtime profile and cancellation/deduplication identity.

The manager resolves artifact references to allowed storage. Models cannot choose host
mounts, commands, capabilities, network modes, image tags/digests or secret mounts freely.
A worker receives only the selected input and job parameters plus its own scratch.
Source staging must preserve package semantics where required (for example shapefile
sidecars); this first pilot only targets a supported CSV profile.

A result manifest needs source bindings, schema, operation/runtime/image identity,
completion/partial status, bounded diagnostics, resources, exit status and artifact
references/digests. Worker-reported success alone is not validation. Validate files,
paths, sizes, types and checks before registering or publishing them.

The workspace manager owns job leases, atomic publication of internal artifacts,
quota accounting, crash cleanup and expiry. Never clean an active workspace. Missing
scratch after restart is not a durable completed artifact. Never automatically repeat
writes or reuse expired/mismatched approval. Read recovery must also be explicit where
it would rerun a calculation.

An artifact record should carry owner/scope, source hashes, query/operation version,
schema, size, lifecycle and expiry. Agent-facing references are identifiers, not arbitrary
host paths. Caches may reuse validated facts/intermediates, never execution authority.
Do not assume different projects/users may share cached data.

## Isolation target and proof

Docker template: non-root worker, read-only root, only selected read-only inputs,
private writable scratch, no network by default, no credentials or management socket,
dropped capabilities, no privilege escalation and explicit CPU/memory/process/deadline
limits. Select an actual hard storage mechanism; directory-size polling is not a hard
quota and tmpfs consumes memory. Audit Docker/rootless availability and current images
before deciding settings. Do not silently fall back to host execution when a sandbox is
required but unavailable; report the unavailable execution environment.

Docker containers share a host kernel; a MicroVM adds a guest-kernel boundary but also
requires VM images/lifecycle and supported virtualization. Do not claim either provides
perfect isolation. The runtime adapter must expose its actual guarantees and limitations.

| Negative test | Required evidence |
| --- | --- |
| Read an unsupplied host file | Unavailable/denied |
| Read another job's workspace | Unavailable/denied |
| Modify a selected input | Write denied; source digest unchanged |
| Access secrets or Docker socket | Unavailable |
| Reach unauthorized network | Blocked |
| Traverse paths or escape via symlinks | Rejected |
| Exceed memory/process/time limits | Worker stopped and failed/partial status recorded |
| Exhaust scratch | Hard bound enforced; host protected |
| Cancel/crash job | Worker cleaned/stopped; incomplete artifacts not published |
| Refresh/retry after uncertain write | No automatic replay or inherited authority |

Record image digest, sandbox/job identity, mounts, network policy, limits and exit status.
Use disposable fixtures. Tests must exercise the boundary rather than only assert that
configuration fields exist. Compare numerical results against current shared services.

## Dependency-ordered next implementation

1. Audit actual execution paths, worker protocol, existing images and host runtime
   support. Define the job/artifact/runtime contracts and a minimal supported CSV-profile
   pilot. Separate the local subprocess compatibility path from sandbox-required mode.
2. Implement Executor-owned Docker/workspace management for that operation only, behind
   existing shared services. No new agent, generic shell or permission expansion. Surface
   startup/runtime availability clearly; do not add an unrelated frontend redesign.
3. Run isolation, quota, cancellation/cleanup and result-parity tests. Integrate the pilot
   through existing MCP/API/CLI entry points and graph evidence. Use temporary files;
   container builds/startup require their ordinary explicit execution/approval handling.
4. Extend comprehensive typed profiling and its result UI using the same contracts;
   prioritize visible dataset understanding, not a large sandbox framework. See the
   inspection requirements for numerical/category/identifier distinctions and Outcome UI.
5. Add retained sampling only as a typed registered write operation with provenance and
   normal authorization. Continue descriptive/relationship/adjusted-analysis stages.
6. After the complete single-actor data journey works, test flexible role assignment and
   structured group communication, then the isolated simulated Linux-server environment.
   Compare correctness, performance, resources, interventions and recovery. MicroVM is
   a later adapter evaluated against actual requirements, not a prerequisite to the pilot.

This integrates the existing roadmap without declaring a new completed checkpoint or
superseding parked memory/RL decisions. Preserve the operator's comprehensive profiling,
left-to-right graph and interactive Outcome requests alongside sandbox implementation.

References: [Docker security](https://docs.docker.com/engine/security/),
[Firecracker setup](https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md).
These explain platform mechanisms, not evidence that ActionCharter already enforces them.
