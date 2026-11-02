# Reuse Builder for agent-driven capability acquisition

Recorded 2026-10-27. Documentation/design only. No new execution capability,
registration policy, agent, worker or source refactor is implemented by this record.

[Expanded scope and deployment sequence](DATA_SCIENCE_FORMATS_MEMORY_AND_REMOTE_PLAN.md)
records statistical/reporting and format targets, the corrected role graph, and the
user's requirement to establish memory before autonomous isolated Linux operation.

## Correction to the earlier discussion

Implementation generation is not absent from this project. Git history records
proposal-only Builder contracts/model generation on 2026-08-28, activation planning
and activation on 2026-09-01, and activated-file verification on 2026-09-02.
The missing capability is an integrated task-driven analytical generation/reuse loop,
not the absence of all code-generation infrastructure. Inspect and reuse this work
before adding another parallel subsystem. Preserve the earlier decision that a separate
permanent Builder reasoning agent is unnecessary for ordinary planning/recipe authoring.

| Existing component | Evidence/location | Use and limitation |
| --- | --- | --- |
| Skill scaffold generation | `skill_scaffolding/generator.py` | Produces package structure and placeholders; not a completed calculation |
| Builder model boundary | `builder/agent.py`, `agents/builder/manifest.yaml` | LLM proposes exact requested candidate artifacts; no tools, direct execution or writes |
| Builder candidate contracts | `builder/schemas.py`, `builder/policy.py` | Typed kinds, bounded content and requested paths; current prefixes target extension/source files, not general analytical jobs |
| Candidate materialization | `builder/materialization.py` | Existing isolated candidate storage/digest machinery; review assumptions before reuse |
| Test evidence | `builder/testing.py`, `builder/test_evidence.py` | Binds successful isolated test receipts to exact candidates; evidence assessment is not itself the code executor |
| Promotion and activation | `builder/promotion.py`, `builder/activation.py` and related plans/reviews | Existing explicit extension lifecycle; not automatic runtime installation or task execution |
| Post-activation verification | `builder/post_activation_verification.py` | Checks exact activated bytes/evidence without executing them; not proof of analytical correctness |
| Closed text acquisition | `capabilities/`, `docs/CHECKPOINT28_1.md` | Planner-led finite transformation definitions with tests/installation; no arbitrary Python |
| Analytical worker | `sandbox/` | Existing worker boundary for supported tasks; arbitrary generated Python requires a separate boundary assessment |

Paths above are under `src/geoagent_harness/` unless otherwise indicated. These are
inspected implementations, not claims that every path currently has reliable real-model
acceptance. README already describes Builder as a legacy extension path.

## Current and desired journeys

```text
Existing extension-development path
  Explicit artifact request
    -> Builder model proposal
    -> candidate materialization / isolated tests
    -> review / promotion / activation
    -> exact-file verification

Proposed task-driven path
  User's analytical request
    -> Planner retrieves existing operations, recipes and relevant capabilities
    -> existing method sufficient? compose it; no generation
    -> otherwise record a concrete capability gap
    -> optional implementation-generation role using existing Builder machinery
    -> isolated candidate execution and independent checks
    -> task result with evidence
    -> qualify a parameterized reusable method
    -> project-visible registered capability when installation policy permits
    -> later compatible workflow reuses it through ordinary governed execution
```

Do not automatically call the old source-activation mechanism from conversation.
Developing project extensions and installing a task-local method have different trust
and deployment requirements. Generated methods should not routinely edit trusted `src`,
registries, policy, approvals or their own test evidence.

## Dependency-ordered implementation plan

1. **Audit and map existing ownership.** Trace one Builder candidate from request to
   activation, its actual runner/tests, current package installer and current analytical
   worker. Classify reusable primitives, developer-only paths and duplication. Record
   what is currently reachable from CLI/MCP/chat. Acceptance: concrete call-path map,
   compatibility cases and an explicit reuse/retain/replace decision for each stage.
2. **Define one task-level candidate contract.** Purpose, applicability, typed inputs/
   outputs, source-independent parameters, code/files, dependency versions, effects,
   budgets and verification requirements. Adapt existing Builder envelopes where valid;
   current source-path constraints must not simply be removed. Retain legacy contracts
   and digests. Acceptance: bounded validated candidate with no credentials, arbitrary
   installation requests or implicit source changes; malformed contracts reject.
3. **Share lifecycle primitives.** Reuse compatible materialization, content identity,
   evidence and package-storage functions. Keep legacy extension activation supported
   through adapters. No second copy of equivalent candidate/test/install services.
   Acceptance: new flow and existing lifecycle agree on identity/evidence invariants
   without reserializing historical receipts or silently broadening trust.
4. **Connect Planner to implementation assistance.** Planner first tries existing
   capabilities. A gap request states the missing method, evidence, expected result
   and budget. Single mode can generate within the primary role; separate assistance
   uses the coordinator and an explicit context handoff. Reuse Builder generation
   boundary/prompt construction where applicable, not a compulsory extra model service.
   Acceptance: supported tasks generate no candidates; unsupported tasks produce a
   bounded proposal or a concrete limitation, never an invented registered operation.
5. **Validate the worker boundary before executing code.** Selected input mounts,
   private scratch, permitted installed dependencies, restricted network, CPU/memory/
   process/output/time bounds, cancellation and artifact manifests. No host/database
   credentials or container-engine socket. Reuse existing worker components only after
   proving required boundaries; temporary directories, AST checks and model instructions
   alone are insufficient. Acceptance: escape/resource/failure tests plus useful execution
   on temporary fixtures; unavailable isolation refuses rather than silently downgrades.
6. **Qualify and register reuse.** Separate code execution success, numerical checks,
   held-out applicability, optional Critic review and installation eligibility. Reuse
   existing package/registry services via a versioned generated-method adapter if needed.
   User enables acquisition once for the scope; agent prepares technical artifacts.
   Preserve current explicit installation until a replacement eligibility policy is
   defined and tested. No per-file approval burden; consequential retained writes still
   use ordinary exact authorization. Acceptance: reuse on a second compatible dataset
   without regeneration, reject incompatible schema/effects, and no authority transfer.
7. **Present and measure the whole journey.** Graph identifies generated capability,
   execution and verification; outcome shows actual values, provenance and limitations.
   Shared CLI/MCP actions and durable failures remain available. Acceptance: refresh
   restores the correct proposal/run/report without silent calls or repeated writes;
   actual-model results are distinguished from authored fixtures.

## First bounded demonstration

Select a small numerical method not already expressible through the registered
contracts; verify that gap through the registry first. Use two unrelated temporary
tabular datasets with independently computable reference results. Generate and check
the method on the first, qualify and install under the supported policy, then reuse
it on the second. Do not hard-code diabetic columns or use real private rows as public
training/test fixtures. Demonstrate failure on incompatible input as well as success.

The operator should not type JSON manifests, source files or test definitions. Agent
prepares them; deterministic services enforce constraints. Reuse remains independent
of data-write authority, and meaningful domain validation cannot be inferred from a
passing Python test or an LLM's favorable review alone.

## Structural outcome and exclusions

- Keep Planner ownership of the task, a shared coordinator and existing role modes.
- Existing `builder` becomes a reusable generation/lifecycle foundation, not another
  competing chat workflow. Legacy developer tooling remains compatible.
- Existing operation registry, installer, evidence store and workers are extended
  only where an audited gap requires it. Additions must remove equivalent duplicate paths.
- Capability index describes installed resources; it does not approve every function.
- No automatic dependency downloads, arbitrary SQL/live database mutation, model-weight
  training/RL or production domain-maintenance claim. These require separate designs.
- Record actual generation success, independent correctness, calls/time/resources and
  successful reuse. More files, passing fixture responses or candidate count are not
  evidence of useful learning.
